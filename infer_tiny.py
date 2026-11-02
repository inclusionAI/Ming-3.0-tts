#!/usr/bin/env python3
"""Command line inference for Ming-3.0-tts-tiny (7.9B total, 1.3B active).

The two models keep separate entry points because they share no tokenizer
and no prompt layout. Tasks: seed, multilingual, basic, emotion, dialect, ip,
voice_design, freeform, podcast, paralinguistic.
"""

from __future__ import annotations

import argparse
import json
import os

from ming_tiny import task_protocol


def parse_args():
    parser = argparse.ArgumentParser(
        description="Controllable speech synthesis with Ming-3.0-tts-tiny"
    )
    parser.add_argument("--model_path", required=True,
                        help="checkpoint directory or Hugging Face repo id")
    parser.add_argument("--task", required=True,
                        help=f"one of: {', '.join(task_protocol.TASKS)}")
    parser.add_argument("--text", required=True,
                        help="text to speak; for podcast one 'speaker_N: ...' line per turn")
    parser.add_argument("--output_path", default="output_tiny.wav")
    parser.add_argument("--target_language", default=None,
                        help="seed / paralinguistic: Chinese or English; "
                             "multilingual: German, Spanish, French, Korean or Japanese")

    voice = parser.add_argument_group("voice conditioning")
    voice.add_argument("--prompt_wav", action="append", default=[],
                       help="reference wav; repeat in speaker order for podcast")
    voice.add_argument("--prompt_text", action="append", default=[],
                       help="exact transcript of --prompt_wav; repeat for podcast")

    controls = parser.add_argument_group("task controls")
    controls.add_argument("--instruction", help="freeform: natural-language direction")
    controls.add_argument("--speed", choices=sorted(task_protocol.SPEED_VALUES))
    controls.add_argument("--pitch", choices=sorted(task_protocol.PITCH_VALUES))
    controls.add_argument("--volume", choices=sorted(task_protocol.VOLUME_VALUES))
    controls.add_argument("--emotion", help="中性 / 悲伤 / 愤怒 / 高兴 / 惊讶 / 恐惧 / 厌恶")
    controls.add_argument("--dialect", help="川渝话 / 广粤话")
    controls.add_argument("--style", help="voice_design: voice description")
    controls.add_argument("--ip", help="built-in voice name")

    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--seed", type=int, default=None,
                        help="defaults to 1235 for podcast and 1234 for other tasks")
    parser.add_argument("--cfg_scale", type=float, default=task_protocol.FORMAL_CFG)
    parser.add_argument("--flow_steps", type=int, default=task_protocol.FORMAL_FLOW_STEPS)
    parser.add_argument("--sigma", type=float, default=task_protocol.FORMAL_SIGMA)
    parser.add_argument("--temperature", type=float,
                        default=task_protocol.FORMAL_TEMPERATURE)
    # Unset, these take the checkpoint's own values, as the published
    # evaluation did. Podcast derives its budget from the dialogue instead.
    parser.add_argument("--min_decode_steps", type=int)
    parser.add_argument("--max_decode_steps", type=int)
    parser.add_argument("--stop_threshold", type=float)
    parser.add_argument("--log_every", type=int, default=0,
                        help="print decode diagnostics every N steps; 0 disables")
    parser.add_argument("--no_text_normalization", action="store_true",
                        help="skip Chinese/English text normalization")
    parser.add_argument("--max_length", type=int, default=24,
                        help="target semantic length for punctuation-based text splitting")
    parser.add_argument("--raw_text", action="store_true",
                        help="bypass text preparation and splitting")
    parser.add_argument("--no_trim_silence", action="store_true",
                        help="keep each fragment's trailing silence")
    return parser.parse_args()


def _collapse(values: list[str]):
    if not values:
        return None
    return values[0] if len(values) == 1 else values


def main():
    args = parse_args()
    prompt_wav = _collapse(args.prompt_wav)
    prompt_text = _collapse(args.prompt_text)
    request = dict(
        task=args.task,
        text=args.text,
        prompt_wav=prompt_wav,
        prompt_text=prompt_text,
        target_language=args.target_language,
        instruction=args.instruction,
        dialect=args.dialect,
        emotion=args.emotion,
        style=args.style,
        speed=args.speed,
        pitch=args.pitch,
        volume=args.volume,
        ip=args.ip,
    )

    # Fail on the contract before paying for CUDA init and the weights.
    try:
        task_protocol.resolve_task_request(**request)
    except ValueError as error:
        raise SystemExit(str(error))
    for path in args.prompt_wav:
        if not os.path.isfile(path):
            raise SystemExit(f"prompt wav not found: {path}")

    from ming_tiny import MingTinyTTS

    tts = MingTinyTTS.from_pretrained(
        args.model_path, device=args.device,
        text_normalization=not args.no_text_normalization,
    )
    output = tts.generate(
        **request,
        output_path=args.output_path,
        seed=args.seed,
        cfg_scale=args.cfg_scale,
        flow_steps=args.flow_steps,
        sigma=args.sigma,
        temperature=args.temperature,
        min_decode_steps=args.min_decode_steps,
        max_decode_steps=args.max_decode_steps,
        stop_threshold=args.stop_threshold,
        log_every_n_steps=args.log_every,
        max_length=args.max_length,
        raw_text=args.raw_text,
        trim_silence=not args.no_trim_silence,
    )
    print(json.dumps({
        "task": task_protocol.normalize_task(args.task),
        "output": os.path.abspath(args.output_path),
        "seconds": round(output.waveform.shape[-1] / tts.sample_rate, 2),
        "stopped": bool(output.stopped),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
