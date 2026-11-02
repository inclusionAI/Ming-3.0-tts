# Copyright (c) Ant Group. All rights reserved.
"""Atomic resumable training state, separate from inference exports."""
import random
from pathlib import Path

import numpy as np
import torch


FORMAT_VERSION = 1


def rng_state():
    return {'python': random.getstate(), 'numpy': np.random.get_state(),
            'torch': torch.get_rng_state(), 'cuda': torch.cuda.get_rng_state()}


def restore_rng(state):
    random.setstate(state['python'])
    np.random.set_state(state['numpy'])
    torch.set_rng_state(state['torch'])
    torch.cuda.set_rng_state(state['cuda'])


def trainable_state(network):
    return {name: p.detach().cpu() for name, p in network.named_parameters() if p.requires_grad}


def restore_parameters(network, state):
    parameters = {name: p for name, p in network.named_parameters() if p.requires_grad}
    if set(parameters) != set(state):
        raise ValueError('Checkpoint trainable parameters do not match the training configuration')
    with torch.no_grad():
        for name, tensor in state.items():
            parameters[name].copy_(tensor)


def save_checkpoint(directory, network, optimizer, scheduler, config, progress, states, fingerprint):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'step_{progress["step"]:08d}.pt'
    temporary = path.with_suffix('.pt.tmp')
    torch.save({'format_version': FORMAT_VERSION, 'trainable': trainable_state(network),
                'optimizer': optimizer.state_dict(), 'scheduler': scheduler.state_dict(),
                'config': config, 'progress': progress, 'rng_states': states,
                'dataset_fingerprint': fingerprint}, temporary)
    temporary.replace(path)
    pointer = directory / 'latest.txt.tmp'
    pointer.write_text(path.name + '\n')
    pointer.replace(directory / 'latest.txt')
    keep = int(config.get('keep_last_checkpoints', 2))
    for old in sorted(directory.glob('step_*.pt'))[:-keep]:
        old.unlink()
    return path
