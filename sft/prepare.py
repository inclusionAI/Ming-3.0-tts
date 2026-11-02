# Copyright (c) Ant Group. All rights reserved.
"""Validate local training data and optionally cache CampPlus speaker vectors."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torchaudio
from transformers import AutoTokenizer

from configuration_bailingmm import BailingMMConfig
import prompt_contract
from sft.data import TTSDataset, prefix_for, resolve_model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model_path', required=True)
    parser.add_argument('--data', nargs='+', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--cache_speakers', action='store_true')
    parser.add_argument('--min_duration', type=float, default=1.0)
    parser.add_argument('--max_duration', type=float, default=30.0)
    parser.add_argument('--max_sequence_length', type=int, default=1024)
    args = parser.parse_args()
    model_dir = resolve_model(args.model_path)
    config = BailingMMConfig.from_pretrained(model_dir)
    if config.model_type != 'dense':
        raise ValueError('SFT currently supports Ming-3.0-tts-0.5b only')
    tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
    prompt_contract.validate_tokenizer(tokenizer, 'dense')
    dataset = TTSDataset(args.data, tokenizer, config, min_duration=args.min_duration,
                         max_duration=args.max_duration, max_sequence_length=args.max_sequence_length)
    output = Path(args.output).resolve()
    if output.exists():
        raise FileExistsError(f'Choose a new prepared manifest: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    extractor = None
    if args.cache_speakers:
        from spkemb_extractor import SpkembExtractor
        extractor = SpkembExtractor(str(Path(model_dir) / 'campplus.onnx'))
    preview, prepared = [], []
    for i in range(len(dataset)):
        sample = dataset[i]  # Decode every accepted file to detect corrupt audio.
        if extractor is not None and sample['speaker_condition'] in {'target', 'reference'} and not sample.get('speaker_embedding'):
            key = 'prompt_wav' if sample['speaker_condition'] == 'reference' else 'audio'
            stat = Path(sample[key]).stat()
            digest = hashlib.sha256(f'{model_dir}:{sample[key]}:{stat.st_size}:{stat.st_mtime_ns}'.encode()).hexdigest()
            cache = output.parent / (output.stem + '_speakers') / (digest + '.npy')
            cache.parent.mkdir(exist_ok=True)
            if not cache.exists():
                waveform = sample['_reference'] if key == 'prompt_wav' else sample['_waveform']
                speech = torchaudio.functional.resample(waveform, dataset.sample_rate, 16000)
                np.save(cache, extractor(speech[None]).numpy().reshape(192))
            sample['speaker_embedding'] = str(cache)
        prepared.append({k: v for k, v in sample.items() if not k.startswith('_')})
        if len(preview) < 8:
            ids, _, _ = prefix_for(sample, tokenizer, sample['_reference_steps'])
            preview.append({'id': sample['_id'], 'prefix': tokenizer.decode(ids),
                            'target_audio_steps': sample['_steps']})
    output.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in prepared))
    summary = {'accepted': len(prepared), 'filtered': dataset.filtered, 'preview': preview}
    output.with_suffix('.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps({'accepted': len(prepared), 'filtered': len(dataset.filtered), 'output': str(output)}))


if __name__ == '__main__':
    main()
