# Copyright (c) Ant Group. All rights reserved.
"""Export a full or LoRA training checkpoint for the existing infer.py API."""
import argparse
import json
from pathlib import Path
import shutil

import torch

from sft.checkpoint import FORMAT_VERSION, restore_parameters
from sft.model import configure_training, load_network


def export_network(network, model_dir, output, *, dtype=torch.bfloat16):
    output = Path(output)
    if output.resolve() == Path(model_dir).resolve():
        raise ValueError('Export directory must differ from the base model directory')
    if hasattr(network.model, 'merge_and_unload'):
        network.model = network.model.merge_and_unload()
    network.eval().to(dtype=dtype)
    network.model.config.use_cache = True
    network.save_pretrained(output, safe_serialization=True, max_shard_size='4GB')
    network.tokenizer.save_pretrained(output)
    for name in ('campplus.onnx', 'configuration.json'):
        source = Path(model_dir) / name
        if source.is_file():
            shutil.copy2(source, output / name)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--model_path', help='override the base checkpoint location')
    args = parser.parse_args()
    saved = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
    if saved.get('format_version') != FORMAT_VERSION:
        raise ValueError('Unsupported SFT checkpoint format')
    network, directory = load_network(args.model_path or saved['config']['model_path'], 'cpu')
    configure_training(network, saved['config'])
    restore_parameters(network, saved['trainable'])
    output = export_network(network, directory, args.output)
    (output / 'sft_provenance.json').write_text(json.dumps(
        {'base_model': saved['config']['model_path'], 'mode': saved['config']['mode'],
         'step': saved['progress']['step']}, indent=2))
    print(f'Exported inference model to {output}')


if __name__ == '__main__':
    main()
