# Copyright (c) Ant Group. All rights reserved.
"""Local JSONL input; target recordings and acoustic references stay separate."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio
from torch.utils.data import Dataset

import prompt_contract
import tts_tasks


FIELDS = {'id', 'audio', 'text', 'language', 'task', 'instruction', 'controls',
          'instruction_schema', 'prompt_wav', 'prompt_text', 'speaker_condition',
          'speaker_embedding'}


def resolve_model(path):
    if Path(path).is_dir():
        return str(Path(path).resolve())
    from huggingface_hub import snapshot_download
    return snapshot_download(repo_id=path)


def load_audio(path, sample_rate):
    values, rate = sf.read(path, dtype='float32', always_2d=True)
    # Match the native audio preprocessor's first-channel convention.
    waveform = torch.from_numpy(values[:, 0].copy())
    if not waveform.numel() or not torch.isfinite(waveform).all():
        raise ValueError(f'Empty or nonfinite audio: {path}')
    if rate != sample_rate:
        waveform = torchaudio.functional.resample(waveform, rate, sample_rate)
    return waveform


def resolve_row(row, directory):
    unknown = set(row) - FIELDS
    if unknown:
        raise ValueError(f'Unknown sample fields: {sorted(unknown)}')
    row = dict(row)
    for name in ('audio', 'text'):
        if not isinstance(row.get(name), str) or not row[name].strip():
            raise ValueError(f'{name} must be a nonempty string')
    for name in ('audio', 'prompt_wav', 'speaker_embedding'):
        if row.get(name):
            row[name] = str((directory / row[name]).resolve())
            if not Path(row[name]).is_file():
                raise FileNotFoundError(row[name])
    if bool(row.get('prompt_wav')) != bool(row.get('prompt_text')):
        raise ValueError('prompt_wav and its exact prompt_text must be provided together')
    if row.get('speaker_embedding'):
        embedding = np.load(row['speaker_embedding'], allow_pickle=False)
        if embedding.size != 192 or not np.isfinite(embedding).all():
            raise ValueError('speaker_embedding must be a finite 192-dimensional .npy array')
    task = str(row.get('task', 'tts')).upper().replace('-', '_')
    if task in {'VOICE_DESIGN', 'STYLE'}:
        default = 'none'
    elif row.get('prompt_wav'):
        default = 'reference'
    elif task == 'FREEFORM':
        default = 'none'
    elif task == 'IP':
        default = 'zero'
    else:
        default = 'target'
    condition = row.setdefault('speaker_condition', default)
    if condition not in {'none', 'zero', 'target', 'reference'}:
        raise ValueError('speaker_condition must be none, zero, target or reference')
    if task in {'VOICE_DESIGN', 'STYLE'} and (condition != 'none' or row.get('prompt_wav')):
        raise ValueError('Voice Design must not use a target speaker or reference audio')
    if condition == 'reference' and not row.get('prompt_wav'):
        raise ValueError('reference speaker conditioning requires prompt_wav')
    if row.get('speaker_embedding') and condition not in {'target', 'reference'}:
        raise ValueError('speaker_embedding requires target or reference speaker_condition')
    # Validate control fields through the same resolver used for inference.
    request_for(row)
    return row


def request_for(row):
    task = str(row.get('task', 'tts')).upper().replace('-', '_')
    if task == 'PARALINGUISTIC':
        task = 'TTS'
    return tts_tasks.build_task_generation_kwargs(
        task, text=row['text'], language_id=row.get('language'),
        instruction=row.get('instruction'), controls=row.get('controls'),
        instruction_schema=row.get('instruction_schema'))


def prefix_for(row, tokenizer, reference_steps=0):
    request = request_for(row)
    return prompt_contract.build_input_ids(
        tokenizer, 'dense', request['prompt'], request['text'],
        num_speakers=int(row['speaker_condition'] != 'none'),
        instruction=request['instruction'], prompt_text=row.get('prompt_text'),
        prompt_latent_steps=reference_steps)


def audio_steps(path, config):
    info = sf.info(path)
    if info.frames <= 0:
        raise ValueError(f'Empty audio: {path}')
    audio = config.audio_tokenizer_config
    samples = math.ceil(info.frames * audio.sample_rate / info.samplerate)
    frames = math.ceil(samples / audio.enc_kwargs['hop_size'])
    frames = math.ceil(frames / max(1, audio.patch_size))
    patch = config.ditar_config['patch_size']
    return math.ceil(frames / patch), info.duration


class TTSDataset(Dataset):
    def __init__(self, manifests, tokenizer, model_config, *, min_duration=1.0,
                 max_duration=30.0, max_sequence_length=1024):
        self.rows, self.lengths, self.filtered = [], [], []
        self.sample_rate = model_config.audio_tokenizer_config.sample_rate
        digest = hashlib.sha256()
        for filename in manifests:
            path = Path(filename).resolve()
            digest.update(str(path).encode())
            digest.update(path.read_bytes())
            for line, text in enumerate(path.read_text().splitlines(), 1):
                if not text.strip():
                    continue
                try:
                    row = resolve_row(json.loads(text), path.parent)
                    steps, duration = audio_steps(row['audio'], model_config)
                    if not min_duration <= duration <= max_duration:
                        self.filtered.append({'source': str(path), 'line': line, 'reason': 'duration'})
                        continue
                    if steps < 5:
                        raise ValueError('Need at least five output steps for native stop supervision')
                    reference_steps = 0
                    if row.get('prompt_wav'):
                        reference_steps, _ = audio_steps(row['prompt_wav'], model_config)
                    ids, _, _ = prefix_for(row, tokenizer, reference_steps)
                    length = len(ids) + steps
                    if length > max_sequence_length:
                        self.filtered.append({'source': str(path), 'line': line, 'reason': 'sequence_length'})
                        continue
                    row['_id'] = row.get('id', f'{path.name}:{line}')
                    row['_reference_steps'] = reference_steps
                    row['_steps'] = steps
                    for key in ('audio', 'prompt_wav', 'speaker_embedding'):
                        if row.get(key):
                            stat = Path(row[key]).stat()
                            digest.update(f'{row[key]}:{stat.st_size}:{stat.st_mtime_ns}'.encode())
                    self.rows.append(row)
                    self.lengths.append(length)
                except Exception as error:
                    raise ValueError(f'{path}:{line}: {error}') from error
        if not self.rows:
            raise ValueError('No eligible training samples')
        self.fingerprint = digest.hexdigest()

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = dict(self.rows[index])
        row['_waveform'] = load_audio(row['audio'], self.sample_rate)
        if row.get('prompt_wav'):
            row['_reference'] = load_audio(row['prompt_wav'], self.sample_rate)
        return row

    def batch_plan(self, *, epoch, seed, token_budget, rank=0, world_size=1, sort_buffer=256):
        if token_budget < max(self.lengths):
            raise ValueError('max_tokens_per_batch is smaller than a training sample')
        indices = np.random.default_rng(seed + epoch).permutation(len(self))
        ordered = []
        for start in range(0, len(indices), sort_buffer):
            ordered.extend(sorted(indices[start:start + sort_buffer], key=lambda i: self.lengths[i]))
        batches, batch, longest = [], [], 0
        for index in ordered:
            length = self.lengths[index]
            if batch and max(longest, length) * (len(batch) + 1) > token_budget:
                batches.append(batch)
                batch, longest = [], 0
            batch.append(int(index))
            longest = max(longest, length)
        if batch:
            batches.append(batch)
        # Pad deterministically so every rank executes the same collectives.
        batches += [batches[-1]] * ((-len(batches)) % world_size)
        return batches[rank::world_size]


def identity_collate(rows):
    return rows
