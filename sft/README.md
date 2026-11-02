# Fine-tuning Ming-3.0-tts-0.5b

Supports full fine-tuning and LoRA on CUDA GPUs. Run commands from the repository root:

```bash
pip install -r requirements-sft.txt
```

## Data and controls

For example, one emotion-training sample in a UTF-8 JSONL file:

```json
{"audio":"wavs/001.wav","text":"终于见到你了！","language":"Chinese","task":"emotion","controls":{"emotion":"高兴"}}
```

`audio` is the target recording, relative to the JSONL file; `text` is its exact
transcript. Put `controls` alongside `task` and `text`. The script serializes
`controls` into the assistant-side instruction, before the audio tokens:

```text
<|im_start|>user
... Text input:
终于见到你了！<|im_end|>
<|im_start|>assistant
{"audio_sequence": [{"序号": 1, "说话人": "speaker_1", "方言": null, "风格": null, "语速": null, "基频": null, "音量": null, "情感": "高兴", "BGM": {"Genre": null, "Mood": null, "Instrument": null, "Theme": null, "ENV": null, "SNR": null}, "IP": null}]}<|im_end|><audio><audioPatch>...
```

The user-side prefix is abbreviated above. Do not put the control JSON into
`text` or assemble special tokens yourself. Control names follow the
[0.5B inference API](../README.md#cookbook).

## Prepare and train

```bash
python -m sft.prepare \
  --model_path inclusionAI/Ming-3.0-tts-0.5b \
  --data /path/to/train.jsonl \
  --output output/sft/train.jsonl --cache_speakers
```

Set `model_path`, `train_data` and `output_dir` in the
[full](configs/dense_full.yaml) or [LoRA](configs/dense_lora.yaml) config, then run:

```bash
python -m sft.train --config sft/configs/dense_full.yaml
# LoRA
python -m sft.train --config sft/configs/dense_lora.yaml
```

For multiple GPUs, launch the same training module with `torchrun`.
Add `--resume latest` to resume with the same config, data and GPU count.

## Export

```bash
python -m sft.export \
  --checkpoint output/sft/full/checkpoints/step_00000100.pt \
  --output output/sft/model
```

Replace the checkpoint path with one saved by your run. The exported directory
can be used directly with `infer.py`; LoRA weights are merged during export.
