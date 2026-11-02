# Copyright (c) Ant Group. All rights reserved.
"""Single-GPU or torchrun/DDP supervised fine-tuning of Ming-3.0-tts-0.5b."""
import argparse
import json
import math
import os
from pathlib import Path
import random

import numpy as np
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel
from torch.utils.data import DataLoader
import yaml

from sft.checkpoint import (FORMAT_VERSION, restore_parameters, restore_rng,
                            rng_state, save_checkpoint)
from sft.data import TTSDataset, identity_collate
from sft.model import DenseSFT, configure_training, load_network


DEFAULTS = dict(mode='full', seed=42, epochs=1, max_steps=None, learning_rate=1e-5,
                min_learning_rate=1e-6, warmup_steps=100, weight_decay=0.01,
                gradient_clip=1.0, max_tokens_per_batch=2048, sort_buffer=256,
                min_duration=1.0, max_duration=30.0, max_sequence_length=1024,
                speaker_dropout=0.5, gradient_checkpointing=True,
                num_workers=0, save_every_steps=100, keep_last_checkpoints=2,
                log_every_steps=10)
EXTRA_KEYS = {'model_path', 'train_data', 'output_dir', 'lora', 'train_heads'}


def read_config(filename):
    config = yaml.safe_load(Path(filename).read_text())
    if not isinstance(config, dict):
        raise ValueError('Expected a YAML mapping')
    unknown = set(config) - set(DEFAULTS) - EXTRA_KEYS
    if unknown:
        raise ValueError(f'Unknown training options: {sorted(unknown)}')
    config = dict(DEFAULTS, **config)
    for key in ('model_path', 'train_data', 'output_dir'):
        if not config.get(key):
            raise ValueError(f'Missing {key}')
    if isinstance(config['train_data'], str):
        config['train_data'] = [config['train_data']]
    if not isinstance(config['train_data'], list) or not config['train_data'] or not all(
            isinstance(path, str) and path for path in config['train_data']):
        raise ValueError('train_data must be a JSONL path or a nonempty list of paths')
    for key in ('epochs', 'max_tokens_per_batch', 'sort_buffer', 'keep_last_checkpoints', 'log_every_steps'):
        if not isinstance(config[key], int) or config[key] < 1:
            raise ValueError(f'{key} must be a positive integer')
    if config['max_steps'] is not None and (not isinstance(config['max_steps'], int) or config['max_steps'] < 1):
        raise ValueError('max_steps must be null or a positive integer')
    if not 0 < config['min_learning_rate'] <= config['learning_rate'] or config['gradient_clip'] <= 0:
        raise ValueError('Invalid learning rate or gradient clip')
    if config['num_workers'] < 0 or config['warmup_steps'] < 0 or config['save_every_steps'] < 0:
        raise ValueError('Worker, warmup and save intervals must be nonnegative')
    if not 0 <= config['min_duration'] <= config['max_duration']:
        raise ValueError('Invalid audio duration limits')
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--resume', help='training .pt checkpoint, or latest')
    args = parser.parse_args()
    config = read_config(args.config)
    if not torch.cuda.is_available():
        raise RuntimeError('Training requires a CUDA GPU')
    world = int(os.environ.get('WORLD_SIZE', 1))
    rank, local_rank = int(os.environ.get('RANK', 0)), int(os.environ.get('LOCAL_RANK', 0))
    torch.cuda.set_device(local_rank)
    device = torch.device('cuda', local_rank)
    if world > 1:
        dist.init_process_group('nccl')
    random.seed(config['seed'] + rank)
    np.random.seed(config['seed'] + rank)
    torch.manual_seed(config['seed'] + rank)
    output = Path(config['output_dir'])
    existing = [(output / 'resolved_config.json').exists() if rank == 0 else None]
    if world > 1:
        dist.broadcast_object_list(existing)
    if not args.resume and existing[0]:
        raise ValueError('Output directory already has a run; use --resume latest or a new output_dir')
    output.mkdir(parents=True, exist_ok=True)
    network, model_dir = load_network(config['model_path'], device)
    config['model_path'] = model_dir
    configure_training(network, config)
    model = DenseSFT(network, model_dir, speaker_dropout=config['speaker_dropout']).train()
    dataset = TTSDataset(config['train_data'], network.tokenizer, network.config,
                         **{k: config[k] for k in ('min_duration', 'max_duration', 'max_sequence_length')})
    plan_args = dict(seed=config['seed'], token_budget=config['max_tokens_per_batch'],
                     rank=rank, world_size=world, sort_buffer=config['sort_buffer'])
    target_steps = config['max_steps'] or sum(
        len(dataset.batch_plan(epoch=e, **plan_args)) for e in range(config['epochs']))
    if rank == 0:
        print(json.dumps({'trainable_parameters': sum(p.numel() for p in network.parameters() if p.requires_grad),
                          'samples': len(dataset), 'steps': target_steps, 'world_size': world}), flush=True)
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),
                                 lr=config['learning_rate'], weight_decay=config['weight_decay'])
    def lr_factor(step):
        warmup = config['warmup_steps']
        if step < warmup:
            return (step + 1) / max(warmup, 1)
        ratio = config['min_learning_rate'] / config['learning_rate']
        progress = min(1.0, (step - warmup) / max(1, target_steps - warmup))
        return ratio + (1 - ratio) * (1 + math.cos(math.pi * progress)) / 2
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_factor)
    step, epoch, next_batch = 0, 0, 0
    if args.resume:
        path = Path(args.resume)
        if args.resume == 'latest':
            directory = output / 'checkpoints'
            path = directory / (directory / 'latest.txt').read_text().strip()
        saved = torch.load(path, map_location='cpu', weights_only=False)
        if saved.get('format_version') != FORMAT_VERSION:
            raise ValueError('Unsupported SFT checkpoint format')
        if (saved['config'] != config or saved['dataset_fingerprint'] != dataset.fingerprint
                or saved['progress']['world_size'] != world or saved['progress']['target_steps'] != target_steps):
            raise ValueError('Resume requires the same config, data, world size and training length')
        restore_parameters(network, saved['trainable'])
        optimizer.load_state_dict(saved['optimizer'])
        scheduler.load_state_dict(saved['scheduler'])
        progress = saved['progress']
        step, epoch, next_batch = progress['step'], progress['epoch'], progress['next_batch']
        restore_rng(saved['rng_states'][rank])
        del saved
    if rank == 0:
        (output / 'resolved_config.json').write_text(json.dumps(config, indent=2, ensure_ascii=False))
        (output / 'data_summary.json').write_text(json.dumps(
            {'accepted': len(dataset), 'filtered': dataset.filtered,
             'fingerprint': dataset.fingerprint}, indent=2, ensure_ascii=False))
    wrapped = DistributedDataParallel(model, device_ids=[local_rank], find_unused_parameters=True) if world > 1 else model
    while step < target_steps:
        plan = dataset.batch_plan(epoch=epoch, **plan_args)
        # A dedicated DataLoader generator leaves the model RNG unchanged on resume.
        generator = torch.Generator().manual_seed(config['seed'] + epoch + rank)
        loader = DataLoader(dataset, batch_sampler=plan[next_batch:], collate_fn=identity_collate,
                            num_workers=config['num_workers'], generator=generator)
        for batch_index, rows in enumerate(loader, start=next_batch):
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast('cuda', dtype=torch.bfloat16):
                losses = wrapped(rows)
            if not torch.isfinite(losses['loss']):
                raise RuntimeError('Nonfinite training loss')
            losses['loss'].backward()
            gradient = torch.nn.utils.clip_grad_norm_(
                (p for p in model.parameters() if p.requires_grad), config['gradient_clip'], error_if_nonfinite=True)
            learning_rate = optimizer.param_groups[0]['lr']
            optimizer.step()
            scheduler.step()
            step += 1
            if rank == 0 and (step % config['log_every_steps'] == 0 or step == 1):
                record = dict(step=step, epoch=epoch, loss=float(losses['loss'].detach()),
                              flow_loss=float(losses['flow_loss']), stop_loss=float(losses['stop_loss']),
                              gradient_norm=float(gradient), learning_rate=learning_rate)
                print(json.dumps(record), flush=True)
                with (output / 'train.jsonl').open('a') as stream:
                    stream.write(json.dumps(record) + '\n')
            next_batch = batch_index + 1
            if step == target_steps or (config['save_every_steps'] and step % config['save_every_steps'] == 0):
                states = [None] * world
                if world > 1:
                    dist.all_gather_object(states, rng_state())
                else:
                    states[0] = rng_state()
                if rank == 0:
                    path = save_checkpoint(output / 'checkpoints', network, optimizer, scheduler,
                        config, dict(step=step, epoch=epoch, next_batch=next_batch,
                                     world_size=world, target_steps=target_steps), states, dataset.fingerprint)
                    print(f'Saved {path}', flush=True)
                if world > 1:
                    dist.barrier()
            if step >= target_steps:
                break
        epoch += 1
        next_batch = 0
    if world > 1:
        dist.destroy_process_group()


if __name__ == '__main__':
    main()
