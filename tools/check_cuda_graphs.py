"""Check that ``MingTTS(cuda_graphs=True)`` is bit-identical to the eager sampler, and time both.

Renders each case with the eager sampler, then enables CUDA graphs on the same
model and renders it again from the same seed, and compares the waveforms
sample for sample. The cases cover zero-shot cloning, a built-in voice, voice
design (which reuses the first fragment as the prompt), emotion and attribute
control, multi-fragment text and a non-zero temperature.

    python tools/check_cuda_graphs.py --model_path Ming-3.0-tts-0.5b
"""
import argparse
import os
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from infer import seed_everything  # noqa: E402
from ming_tts import MingTTS  # noqa: E402
from cuda_graph_sampler import enable_cuda_graphs  # noqa: E402

LINGGUANG = ("data/voice_presets/voice_audio/lingguang.wav", "诶，你今天有空吗？我们能不能聊聊这件事啊？")
CASES = {
    "zero_shot_zh": dict(task="TTS", text="傍晚的风从山口吹过来，远处的云慢慢染成了金色。",
                         prompt_wav_path=LINGGUANG[0], prompt_text=LINGGUANG[1], use_spk_emb=True),
    "zero_shot_en_long": dict(task="TTS", prompt_wav_path=LINGGUANG[0], prompt_text=LINGGUANG[1], use_spk_emb=True,
                              text="The garden will remain open until sunset, provided the weather stays clear. "
                                   "Visitors are asked to keep to the marked paths, and to leave the lower meadow "
                                   "undisturbed while the spring flowers are in bloom."),
    "ip_voice": dict(task="IP", controls={"ip": "UK_George"},
                     text="The garden will remain open until sunset, provided the weather stays clear."),
    "voice_design": dict(task="VOICE_DESIGN", controls={"style": "成熟沉稳的男性纪录片旁白，吐字清晰，节奏舒缓。"},
                         text="冰川在漫长岁月中缓缓移动，也悄悄记录着气候变化的痕迹。科学家们通过冰芯，"
                              "可以读出数十万年前的大气成分，这些记录对理解今天的气候至关重要。"),
    "emotion": dict(task="EMOTION", controls={"emotion": "高兴"}, prompt_wav_path="data/wavs/emotion_prompt.wav",
                    text="所有测试都顺利通过了，我们终于可以把这个好消息告诉大家！"),
    "basic_speed": dict(task="BASIC", controls={"speed": "高"}, prompt_wav_path=LINGGUANG[0],
                        text="请大家注意，列车即将进站，请站在安全线以内。"),
    "temperature": dict(task="TTS", prompt_wav_path=LINGGUANG[0], prompt_text=LINGGUANG[1], use_spk_emb=True,
                        temperature=0.6, text="今天的会议推迟到下午三点，请大家相互转告。"),
    "cfg_3": dict(task="TTS", prompt_wav_path=LINGGUANG[0], prompt_text=LINGGUANG[1], use_spk_emb=True,
                  cfg=3.0, text="今天的会议推迟到下午三点，请大家相互转告。"),
    "max_decode_steps": dict(task="TTS", prompt_wav_path=LINGGUANG[0], prompt_text=LINGGUANG[1], use_spk_emb=True,
                             max_decode_steps=20, text="傍晚的风从山口吹过来，远处的云慢慢染成了金色。"),
}


def render(tts, case, seed):
    # Prompt encoding samples the VAE posterior, so each render starts from an
    # empty prompt cache and the same seed.
    tts._prompt_cache.clear()
    seed_everything(seed)
    torch.cuda.synchronize()
    start = time.perf_counter()
    wav = tts.synthesize(language_id=None, **case)
    torch.cuda.synchronize()
    return wav, time.perf_counter() - start


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--seed", type=int, default=1895)
    parser.add_argument("--repeats", type=int, default=3, help="timed renders per case and mode; the fastest counts")
    args = parser.parse_args()
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    tts = MingTTS(args.model_path, text_normalization=False)
    render(tts, CASES["ip_voice"], args.seed)  # first-use setup outside the timings
    eager = {}
    for name, case in CASES.items():
        runs = [render(tts, case, args.seed) for _ in range(args.repeats)]
        eager[name] = (runs[0][0], min(t for _, t in runs))

    start = time.perf_counter()
    assert enable_cuda_graphs(tts.model), "this model configuration is not supported"
    print(f"graph capture: {time.perf_counter() - start:.1f}s, "
          f"{torch.cuda.max_memory_allocated() / 2**30:.1f} GiB peak allocated")

    failures = 0
    total_eager = total_graph = total_audio = 0.0
    for name, case in CASES.items():
        runs = [render(tts, case, args.seed) for _ in range(args.repeats)]
        wav, t_graph = runs[0][0], min(t for _, t in runs)
        ref, t_eager = eager[name]
        same = wav.shape == ref.shape and torch.equal(wav, ref) and all(torch.equal(r[0], ref) for r in runs)
        failures += not same
        audio = wav.shape[-1] / tts.sample_rate
        total_eager += t_eager; total_graph += t_graph; total_audio += audio
        print(f"{name:18s} audio {audio:5.2f}s  eager {t_eager:6.2f}s  graphs {t_graph:5.2f}s  "
              f"x{t_eager / t_graph:4.1f}  bit_identical={same}")
    print(f"total: audio {total_audio:.1f}s, eager {total_eager:.1f}s (RTF {total_eager / total_audio:.2f}), "
          f"graphs {total_graph:.1f}s (RTF {total_graph / total_audio:.2f}), x{total_eager / total_graph:.1f}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
