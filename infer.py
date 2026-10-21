# Copyright (c) Ant Group. All rights reserved.
"""Command line entry point for Ming-3.0-tts.

    python infer.py --model_path inclusionAI/Ming-3.0-tts-0.5b \
        --task TTS --text "雨后的山谷很安静。" \
        --prompt_wav_path data/voice_presets/voice_audio/lingguang.wav \
        --prompt_text "诶，你今天有空吗？我们能不能聊聊这件事啊？" \
        --use_spk_emb --output output/tts.wav
"""

import argparse
import random

import numpy as np
import torch

import tts_tasks
from ming_tts import MingTTS


def seed_everything(seed=1895):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def build_controls(args):
    values = {
        "speed": args.speed,
        "pitch": args.pitch,
        "volume": args.volume,
        "emotion": args.emotion,
        "dialect": args.dialect,
        "style": args.style,
        "ip": args.ip,
    }
    controls = {key: value for key, value in values.items() if value is not None}
    return controls or None


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_path", required=True,
                        help="local checkpoint directory or Hub repo id")
    parser.add_argument("--task", required=True, type=str.upper,
                        choices=tts_tasks.TASKS)
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--seed", type=int, default=1895)

    parser.add_argument("--language_id",
                        help="required for MULTILINGUAL; optional elsewhere")
    parser.add_argument("--instruction", help="FREEFORM natural-language control")
    parser.add_argument("--instruction_schema", choices=("zh", "en"))

    controls = parser.add_argument_group("task controls")
    controls.add_argument("--speed", choices=tts_tasks.BASIC_ATTRIBUTE_VALUES["speed"])
    controls.add_argument("--pitch", choices=tts_tasks.BASIC_ATTRIBUTE_VALUES["pitch"])
    controls.add_argument("--volume", choices=tts_tasks.BASIC_ATTRIBUTE_VALUES["volume"])
    controls.add_argument("--emotion", choices=tts_tasks.EMOTION_VALUES)
    controls.add_argument("--dialect", choices=tts_tasks.DIALECT_VALUES)
    controls.add_argument("--style", help="voice design description")
    controls.add_argument("--ip", help="built-in premium voice name")

    voice = parser.add_argument_group("voice conditioning")
    voice.add_argument("--prompt_wav_path", nargs="+")
    voice.add_argument("--prompt_text")
    voice.add_argument("--spk_emb_path", nargs="+")
    voice.add_argument("--use_spk_emb", action="store_true")
    voice.add_argument("--use_zero_spk_emb", action="store_true")

    parser.add_argument("--cfg", type=float, default=2.0)
    parser.add_argument("--sigma", type=float, default=0.25)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max_length", type=int, default=24,
                        help="target semantic length; split at punctuation, keeping long clauses intact")
    parser.add_argument("--max_decode_steps", type=int, default=1000)
    parser.add_argument("--no_text_normalization", action="store_true")
    parser.add_argument("--raw_text", action="store_true",
                        help="send the text as given: no splitting or normalization")
    parser.add_argument("--no_trim_silence", action="store_true",
                        help="keep the trailing silence the model emits")
    return parser.parse_args()


def main():
    args = parse_args()
    seed_everything(args.seed)

    model = MingTTS(
        args.model_path,
        device=args.device,
        text_normalization=not args.no_text_normalization,
    )
    prompt_wav_path = args.prompt_wav_path
    if prompt_wav_path is not None and len(prompt_wav_path) == 1:
        prompt_wav_path = prompt_wav_path[0]

    waveform = model.synthesize(
        task=args.task,
        text=args.text,
        language_id=args.language_id,
        instruction=args.instruction,
        controls=build_controls(args),
        instruction_schema=args.instruction_schema,
        prompt_wav_path=prompt_wav_path,
        prompt_text=args.prompt_text,
        spk_emb_path=args.spk_emb_path,
        use_spk_emb=args.use_spk_emb,
        use_zero_spk_emb=args.use_zero_spk_emb,
        cfg=args.cfg,
        sigma=args.sigma,
        temperature=args.temperature,
        max_length=args.max_length,
        max_decode_steps=args.max_decode_steps,
        trim_silence=not args.no_trim_silence,
        raw_text=args.raw_text,
        output_path=args.output,
    )
    duration = waveform.shape[-1] / model.sample_rate
    print(f"saved={args.output} sample_rate={model.sample_rate} "
          f"duration_seconds={duration:.3f}")


if __name__ == "__main__":
    main()
