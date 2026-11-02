# Copyright (c) Ant Group. All rights reserved.
"""Teacher-forced training against the released 0.5B prompt/weight layout."""
from pathlib import Path

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pad_sequence
from transformers import AutoTokenizer

from configuration_bailingmm import BailingMMConfig
from modeling_bailingmm import BailingMMNativeForConditionalGeneration
import prompt_contract
from sft.data import prefix_for, resolve_model
from sft.losses import global_means, stop_statistics


HEADS = ('linear_proj_audio', 'flowloss', 'stop_head', 'spk_head')


def load_network(model_path, device):
    directory = resolve_model(model_path)
    config = BailingMMConfig.from_pretrained(directory)
    if config.model_type != 'dense':
        raise ValueError('SFT currently supports Ming-3.0-tts-0.5b only')
    network = BailingMMNativeForConditionalGeneration.from_pretrained(
        directory, config=config, torch_dtype=torch.float32, low_cpu_mem_usage=True)
    network.tokenizer = AutoTokenizer.from_pretrained(directory, trust_remote_code=True)
    network.audio.requires_grad_(False)
    network.to(device)
    if torch.device(device).type == 'cuda':
        network.audio.to(torch.bfloat16)
    network.audio.eval()
    network.model.config.use_cache = False
    return network, directory


def configure_training(network, config):
    mode = config.get('mode', 'full')
    if mode == 'lora':
        from peft import LoraConfig, get_peft_model
        network.model = get_peft_model(network.model, LoraConfig(
            task_type='CAUSAL_LM', bias='none',
            **config.get('lora', {'r': 8, 'lora_alpha': 16, 'lora_dropout': 0.05,
                                'target_modules': ['q_proj', 'k_proj', 'v_proj', 'o_proj']})))
    elif mode != 'full':
        raise ValueError('mode must be full or lora')
    heads = config.get('train_heads', list(HEADS))
    unknown = set(heads) - set(HEADS)
    if unknown:
        raise ValueError(f'Unknown train_heads: {sorted(unknown)}')
    for name in HEADS:
        getattr(network, name).requires_grad_(name in heads)
    if config.get('gradient_checkpointing', True):
        network.model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={'use_reentrant': False})
    return mode


class DenseSFT(nn.Module):
    def __init__(self, network, model_dir, *, speaker_dropout=0.5):
        super().__init__()
        self.network = network
        self.model_dir = model_dir
        self.speaker_dropout = float(speaker_dropout)
        if not 0 <= self.speaker_dropout <= 1:
            raise ValueError('speaker_dropout must be in [0, 1]')
        self.extractor = None
        self.speaker_cache = {}

    def train(self, mode=True):
        super().train(mode)
        self.network.audio.eval()
        return self

    @property
    def device(self):
        return next(self.network.parameters()).device

    def encode(self, waveform):
        with torch.inference_mode():
            waveform = waveform.to(self.device)
            latent, lengths = self.network.audio.encode_latent(
                waveform[None], torch.tensor([waveform.numel()], device=self.device))
        # Inference tensors cannot be saved for backward by the Aggregator.
        return latent[0, :int(lengths[0])].clone()

    def speaker(self, row):
        condition = row['speaker_condition']
        if condition == 'none':
            return None
        if condition == 'zero':
            return torch.zeros(192, device=self.device)
        path = row.get('speaker_embedding') or (
            row['prompt_wav'] if condition == 'reference' else row['audio'])
        if path not in self.speaker_cache:
            if row.get('speaker_embedding'):
                embedding = torch.from_numpy(np.load(path, allow_pickle=False).reshape(192).copy())
            else:
                if self.extractor is None:
                    from spkemb_extractor import SpkembExtractor
                    campplus = Path(self.model_dir) / 'campplus.onnx'
                    if not campplus.is_file():
                        raise FileNotFoundError(f'Speaker conditioning needs {campplus}')
                    self.extractor = SpkembExtractor(str(campplus))
                import torchaudio
                waveform = row['_reference'] if condition == 'reference' else row['_waveform']
                speech = torchaudio.functional.resample(
                    waveform, self.network.audio.config.sample_rate, 16000)
                embedding = self.extractor(speech[None]).reshape(192)
            self.speaker_cache[path] = embedding.float()
        embedding = self.speaker_cache[path].to(self.device)
        if self.training and torch.rand(()) < self.speaker_dropout:
            embedding = torch.zeros_like(embedding)
        return embedding

    def forward(self, rows):
        net = self.network
        patch, history_size = net.patch_size, net.history_patch_size
        if history_size < patch or history_size % patch:
            raise ValueError('history_patch_size must be a positive multiple of patch_size')
        sequences, targets, histories, starts, counts, valid_masks = [], [], [], [], [], []
        for row in rows:
            target = self.encode(row['_waveform'])
            valid_length = target.size(0)
            target = F.pad(target, (0, 0, 0, (-valid_length) % patch))
            n = target.size(0) // patch
            if n < 5:
                raise ValueError(f'{row["_id"]}: too few audio steps for stop supervision')
            reference = self.encode(row['_reference']) if '_reference' in row else None
            if reference is not None:
                reference = F.pad(reference, (0, 0, 0, (-reference.size(0)) % patch))
                if reference.size(0) // patch != row['_reference_steps']:
                    raise ValueError(f'{row["_id"]}: reference length differs from the indexed length')
            ids, speaker_slots, reference_start = prefix_for(
                row, net.tokenizer, 0 if reference is None else reference.size(0) // patch)
            start = len(ids)
            ids += [net.tokenizer.convert_tokens_to_ids(prompt_contract.AUDIO_PATCH)] * n
            if len(ids) != start + row['_steps']:
                raise ValueError(f'{row["_id"]}: actual audio length differs from the indexed length')
            embedding = net.get_input_embeddings()(torch.tensor(ids, device=self.device))
            speaker = self.speaker(row)
            if speaker is not None:
                value = net.spk_head(speaker)
                # Match native condition dropout, including the projection bias.
                value = value.masked_fill(speaker.abs().lt(1e-9).all(), 0)
                embedding = embedding.clone()
                embedding[speaker_slots[0]] = value.to(embedding.dtype)
            if reference is not None:
                projected = net.linear_proj_audio(reference.reshape(-1, patch, net.latent_dim))[:, 0]
                embedding = embedding.clone()
                embedding[reference_start:start] = projected.to(embedding.dtype)
            projected = net.linear_proj_audio(target.reshape(-1, patch, net.latent_dim))[:, 0]
            embedding = embedding.clone()
            embedding[start:] = projected.to(embedding.dtype)
            sequences.append(embedding)
            targets.append(target.reshape(n, patch, net.latent_dim))
            history = target.new_zeros(history_size, net.latent_dim)
            if reference is not None:
                copied = min(history_size, reference.size(0))
                history[-copied:] = reference[-copied:]
            history = torch.cat([history, target[:-patch]], dim=0)
            histories.append(history.unfold(0, history_size, patch).permute(0, 2, 1))
            valid_masks.append(torch.arange(target.size(0), device=self.device).lt(valid_length).reshape(n, patch))
            starts.append(start)
            counts.append(n)
        lengths = torch.tensor([len(s) for s in sequences], device=self.device)
        inputs = pad_sequence(sequences, batch_first=True)
        mask = torch.arange(inputs.size(1), device=self.device)[None] < lengths[:, None]
        position_ids = mask.long().cumsum(-1).sub(1).masked_fill(~mask, 0)
        llm = net.model.get_base_model() if hasattr(net.model, 'get_base_model') else net.model
        # TTS has no supervised text tokens; avoid the large vocabulary logits.
        output = llm.model(inputs_embeds=inputs, attention_mask=mask,
                           position_ids=position_ids, use_cache=False, return_dict=True)
        hidden = output.last_hidden_state
        conditions = torch.cat([hidden[i, start-1:start-1+n]
                                for i, (start, n) in enumerate(zip(starts, counts))])[:, None]
        flow_sum, flow_count = net.flowloss.cfm(
            cond=conditions, target=torch.cat(targets), latent_history=torch.cat(histories),
            mask=torch.cat(valid_masks), patch_size=patch, reduction='sum_and_count')
        # Native stop targets include <audio> (or the final reference frame),
        # ignore the three pre-terminal positions, and stop after the last input.
        stop_hidden = pad_sequence([hidden[i, start-1:start+n]
                                    for i, (start, n) in enumerate(zip(starts, counts))], batch_first=True)
        labels = torch.full(stop_hidden.shape[:2], -100, device=self.device, dtype=torch.long)
        for i, n in enumerate(counts):
            labels[i, :n+1] = 0
            labels[i, n-3:n] = -100
            labels[i, n] = 1
        pos_sum, pos_count, neg_sum, neg_count = stop_statistics(net.stop_head(stop_hidden), labels)
        flow_loss, positive, negative = global_means(
            [flow_sum, pos_sum, neg_sum], [flow_count, pos_count, neg_count])
        stop_loss = (positive + negative) / 2
        return {'loss': flow_loss + 0.01 * stop_loss,
                'flow_loss': flow_loss.detach(), 'stop_loss': stop_loss.detach(),
                'audio_steps': sum(counts), 'text_tokens': int(lengths.sum()) - sum(counts)}
