<h1 align="center">
  <img src="./figures/ant-bailing.png" width="60" alt="Ming-3.0-tts Logo" align="middle" />
  Ming-3.0-tts
</h1>

<p align="center">Multilingual speech synthesis with free-form and paralinguistic control.</p>

<p align="center">🤗 <a href="https://huggingface.co/inclusionAI/Ming-3.0-tts-0.5b">Hugging Face</a>｜ 🤖 <a href="https://modelscope.cn/models/inclusionAI/Ming-3.0-tts-0.5b">ModelScope</a> ｜ 📑 <a href="https://nomorecoding.github.io/Ming-3.0-tts/">Blog & Demos</a> ｜ 💬 <a href="https://qr.dingtalk.com/action/joingroup?code=v1,k1,O7MiZqrOrB2c7PnUZVBNvmDh/6tghNLMEtXqMteyRIpuRVJIwrSsXmL8oFqU5ajJ&_dt_no_comment=1&origin=11">DingTalk(钉钉)</a></p>

Ming-3.0-tts provides two speech-generation models: **0.5b**, a dense model, and **tiny**, a MoE model built on Ling V3 (7.9B total · 1.3B active).

## <a id="artificial-analysis-leaderboards"></a>🏆 Artificial Analysis Leaderboards

On the independent [Artificial Analysis](https://artificialanalysis.ai/text-to-speech) text-to-speech leaderboards (October 2026), Ming-3.0-tts ranks **1st among open-weights models on Controlled Voice**, **1st overall on Pronunciation Robustness**, and **3rd among open-weights models on Provider Voice**. Ranks change as new models are added.

| Leaderboard | Setting | Ming-3.0-tts | Rank |
| --- | --- | :---: | --- |
| [Controlled Voice](https://artificialanalysis.ai/text-to-speech/leaderboard/controlled-voice) | Arena preference Elo; every model clones the same 8 voices (4 US, 4 UK) | 1069 | **1st among open-weights** · 13th overall |
| [Pronunciation Robustness](https://artificialanalysis.ai/text-to-speech) | Share of highlighted spans in English text that human reviewers judged correctly pronounced | 93.2% | **1st overall** |
| [Provider Voice](https://artificialanalysis.ai/text-to-speech/leaderboard/provider-voice) | Arena preference Elo; each model uses its own native voices | 1188 | **3rd among open-weights** · 17th overall |

<p align="center">
    <img src="./figures/aa_leaderboards.png" width="900" alt="Artificial Analysis leaderboards: Controlled Voice and Provider Voice (open weights), Pronunciation Robustness"/>
</p>

Within Pronunciation Robustness, Ming-3.0-tts also ranks **1st** on Expanding Shorthand (text normalization, 96.5%) and Preserving Exact Sequences (sequence fidelity, 90.6%).

## Featured Abilities

- **Voice creation:** clone a reference voice, design one from text, or choose from 100+ Chinese and five English built-in voices.
- **Free-form control:** guide speech delivery with natural-language instructions.
- **Paralinguistic control:** insert 14 inline tags for laughter, sighs, and other vocal expressions in Chinese or English.
- **Languages and dialects:** synthesize Chinese, English, German, Spanish, French, Korean and Japanese, plus Sichuanese and Cantonese.
- **Emotion and attributes:** control emotion, or adjust speed, pitch and volume.
- **Multi-speaker dialogue:** generate a conversation from a script and speaker references (**tiny only**).

Capabilities use separate task modes, not arbitrary combinations. See the [Cookbook](#cookbook) for supported inputs, [Performance](#performance) for benchmarks, and [Blog & Demos](https://nomorecoding.github.io/Ming-3.0-tts/) for audio examples.

## <a id="demo-video"></a>Demo Video

https://github.com/user-attachments/assets/4062ba4c-7d2d-4a45-a19b-760100b79f9c

## Architecture

Text and task-specific control tokens condition a language model with a DiT patch head and an audio tokenizer. Both models share this generation framework.

<p align="center">
    <img src="./figures/ming-3.0-tts.png" width="760"/>
</p>

## News

- 🔥 **[2026.10]** Ming-3.0-tts-0.5b and Ming-3.0-tts-tiny are released, with inference code, a task cookbook and the evaluation tables below.

## Roadmap

- [x] Ming-3.0-tts-0.5b weights and inference code
- [x] Ming-3.0-tts-tiny weights and inference code
- [x] Ming-3.0-tts-tiny benchmarks
- [x] vLLM-Omni accelerated inference
- [ ] Technical report

## Contents

- [Demo Video](#demo-video)
- [Models](#models)
- [Quick Start](#quick-start-)
- [Cookbook](#cookbook)
- [Built-in voices](#built-in-voices)
- [Performance](#performance)
- [Limitations](#limitations)
- [Usage Disclaimer](#usage-disclaimer)

## <a id="models"></a>Models

<div align="center">
<table style="border-collapse: collapse; border-top: 1.5px solid black; border-bottom: 1.5px solid black; margin: 16px 0;">
  <thead>
    <tr>
      <th style="padding: 8px 20px; border: none; border-bottom: 1px solid black;">Model</th>
      <th style="padding: 8px 20px; border: none; border-bottom: 1px solid black;">Architecture</th>
      <th style="padding: 8px 20px; border: none; border-bottom: 1px solid black;">Parameters</th>
      <th style="padding: 8px 20px; border: none; border-bottom: 1px solid black;">Download</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center" style="padding: 8px 20px; border: none;">Ming-3.0-tts-0.5b</td>
      <td align="center" style="padding: 8px 20px; border: none;">Dense</td>
      <td align="center" style="padding: 8px 20px; border: none;">0.5b</td>
      <td align="center" style="padding: 8px 20px; border: none;">
        <a href="https://huggingface.co/inclusionAI/Ming-3.0-tts-0.5b">🤗 HuggingFace</a><br>
        <a href="https://modelscope.cn/models/inclusionAI/Ming-3.0-tts-0.5b">🤖 ModelScope</a>
      </td>
    </tr>
    <tr>
      <td align="center" style="padding: 8px 20px; border: none; border-top: 1px solid rgb(221, 221, 221);">Ming-3.0-tts-tiny</td>
      <td align="center" style="padding: 8px 20px; border: none; border-top: 1px solid rgb(221, 221, 221);">MoE</td>
      <td align="center" style="padding: 8px 20px; border: none; border-top: 1px solid rgb(221, 221, 221);">7.9B total · 1.3B active</td>
      <td align="center" style="padding: 8px 20px; border: none; border-top: 1px solid rgb(221, 221, 221);">
        <a href="https://huggingface.co/inclusionAI/Ming-3.0-tts-tiny">🤗 HuggingFace</a><br>
        <a href="https://modelscope.cn/models/inclusionAI/Ming-3.0-tts-tiny">🤖 ModelScope</a>
      </td>
    </tr>
  </tbody>
</table>
</div>

Each release checkpoint bundles the backbone, DiT head, audio tokenizer, speaker encoder and text tokenizer. The 0.5b release layout is shown below; tiny uses sharded weights with `model.safetensors.index.json`.

```text
Ming-3.0-tts-0.5b/
├── config.json              # model_type: dense, auto_map -> BailingMMConfig
├── configuration.json       # ModelScope task descriptor
├── model.safetensors        # backbone + audio VAE + DiT head + aggregator
├── campplus.onnx            # speaker embedding extractor
├── tokenizer.json           # plus vocab.json / merges.txt / added_tokens.json
├── tokenizer_config.json    #      special_tokens_map.json / chat_template.jinja
└── README.md
```

## <a id="quick-start-"></a>Quick Start 🚀

### Installation

```bash
git clone https://github.com/inclusionAI/Ming-3.0-tts.git
cd Ming-3.0-tts
pip install -r requirements.txt        # Ming-3.0-tts-0.5b
```

Or build the 0.5b Docker image (torch 2.6, CUDA 12.4, `transformers==4.46.3`):

```bash
docker build -f docker/Dockerfile -t ming-tts .
```

The 0.5b environment has been tested on NVIDIA H800-80GB and H20-96G. For 0.5b, `flash-attn` is optional; inference falls back to PyTorch SDPA.

On RTX 50-series (Blackwell, sm_120) GPUs, the pinned torch 2.6.0 CUDA 12.4 wheels have no kernels for the GPU, and inference stops with `CUDA error: no kernel image is available for execution on the device`. Replace torch with a CUDA 12.8 build after installing the requirements:

```bash
pip install -r requirements.txt
pip install torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
```

Tiny uses a separate reference inference environment: Python **3.10.15**, PyTorch and torchaudio **2.7.1+cu118** (CUDA 11.8 wheels), and `transformers==4.46.3`. Install the pinned dependencies from [requirements-tiny.txt](requirements-tiny.txt) in a dedicated environment, as other dependency versions differ from 0.5b. We recommend using NVIDIA H800 for inference.

```bash
conda create -n ming-tiny python=3.10.15 -y && conda activate ming-tiny
pip install -r requirements-tiny.txt
```

### Model Download

```bash
pip install "huggingface_hub[cli]"
hf download inclusionAI/Ming-3.0-tts-0.5b --local-dir Ming-3.0-tts-0.5b
```

In mainland China, ModelScope is usually faster:

```bash
pip install modelscope
modelscope download --model inclusionAI/Ming-3.0-tts-0.5b --local_dir Ming-3.0-tts-0.5b
```

Replace `0.5b` with `tiny` for the other variant.

### Text Normalization

Numbers, dates, units and symbols are normalized with FST grammars, which need `pynini`. It has no universal wheel:

```bash
conda install -c conda-forge pynini==2.1.6   # or: pip install pynini==2.1.6
```

It is loaded lazily; pass `--no_text_normalization` to skip it.

### <a id="ming-30-tts-05b"></a>Ming-3.0-tts-0.5b

```bash
python infer.py \
  --model_path inclusionAI/Ming-3.0-tts-0.5b \
  --task TTS \
  --language_id Chinese \
  --text "傍晚的风从山口吹过来，远处的云慢慢染成了金色。" \
  --prompt_wav_path data/voice_presets/voice_audio/lingguang.wav \
  --prompt_text "诶，你今天有空吗？我们能不能聊聊这件事啊？" \
  --use_spk_emb \
  --output output/tts.wav
```

Or from Python:

```python
from ming_tts import MingTTS

model = MingTTS("inclusionAI/Ming-3.0-tts-0.5b")
model.synthesize(
    task="TTS",
    language_id="Chinese",             # English for English text
    text="傍晚的风从山口吹过来，远处的云慢慢染成了金色。",
    prompt_wav_path="data/voice_presets/voice_audio/lingguang.wav",
    prompt_text="诶，你今天有空吗？我们能不能聊聊这件事啊？",
    use_spk_emb=True,
    output_path="output/tts.wav",
)
```

### Ming-3.0-tts-tiny

Every task has a one-line script in [examples/one_click/](examples/one_click/); variables such as `MODEL`, `TEXT` and `OUT` can be overridden from the environment:

```bash
bash examples/one_click/run_seed.sh
MODEL=/path/to/Ming-3.0-tts-tiny OUT=outputs/yue.wav bash examples/one_click/run_dialect.sh
```

The same call from Python. Loading configures the release runtime (bf16, portable MoE loop, fp32 recurrent state) and checks the checkpoint against it; `generate()` defaults to `cfg_scale=2.0`, `temperature=0`, `flow_steps=10`, `sigma=0.25`, and seed 1234 (1235 for `podcast`):

```python
from ming_tiny import MingTinyTTS

tts = MingTinyTTS.from_pretrained("inclusionAI/Ming-3.0-tts-tiny", device="cuda:0")

tts.generate(
    task="seed",
    text="傍晚的风从山口吹过来，远处的云慢慢染成了金色。",
    prompt_wav="data/voice_presets/voice_audio/lingguang.wav",
    prompt_text="诶，你今天有空吗？我们能不能聊聊这件事啊？",
    target_language="Chinese",          # English for English text
    output_path="outputs/seed.wav",
)

tts.generate(
    task="podcast",
    text="speaker_1: 你最近是不是又去那家面馆了？\nspeaker_2: 对啊，排了半个小时的队，不过真的值得。",
    prompt_wav=["data/voice_presets/voice_audio/lingguang.wav", "data/voice_presets/voice_audio/db30.wav"],
    prompt_text=["诶，你今天有空吗？我们能不能聊聊这件事啊？", "感谢你的认可。"],
    output_path="outputs/podcast.wav",
)
```

Each call selects one task and accepts the inputs listed below:

| Task | Reference audio | Reference text | `target_language` | Controls |
| --- | --- | --- | --- | --- |
| `seed` | one | required | `Chinese` / `English`, required | — |
| `multilingual` | one | required | `German` / `Spanish` / `French` / `Korean` / `Japanese` | — |
| `paralinguistic` | one | required | `Chinese` / `English` | inline tags in `text` |
| `podcast` | one per speaker | one per speaker, same order | inferred from the text | `speaker_N:` at the start of every line |
| `basic` | one | not accepted | — | `speed`, `pitch`, `volume`, all three |
| `emotion` | one | not accepted | — | `emotion` |
| `dialect` | one | not accepted | — | `dialect`: `川渝话` / `广粤话` |
| `freeform` | none by default (recommended); optional | not accepted | — | `instruction` |
| `voice_design` | none | — | — | `style` |
| `ip` | none | — | — | `ip` |

`python infer_tiny.py --help` lists the same arguments for the command line; repeat `--prompt_wav` and `--prompt_text` for podcast.

| | Ming-3.0-tts-0.5b | Ming-3.0-tts-tiny |
| --- | --- | --- |
| Python API | `ming_tts.MingTTS` | `ming_tiny.MingTinyTTS` |
| CLI | `infer.py` | `infer_tiny.py`, `examples/one_click/` |
| Preflight | `tools/preflight.py` | `tools/preflight_tiny.py` |
| Tasks | TTS (inline paralinguistic tags included), FREEFORM, VOICE_DESIGN, MULTILINGUAL, BASIC, EMOTION, DIALECT, IP | the same abilities as lower-case tasks (`seed`, `paralinguistic`, ...), plus `podcast` |

### Verify Your Setup

Check the checkpoint and tokenizer without loading weights:

```bash
python tools/preflight.py --model_path /path/to/Ming-3.0-tts-0.5b
python tools/preflight_tiny.py --model_path /path/to/Ming-3.0-tts-tiny
```

## <a id="cookbook"></a>Cookbook

Ordered the way a line gets made: who speaks, how it is said, what goes beyond the words, and where it is heard. Each example is one task; controls from another task are rejected. Texts and controls are the ones on the [demo page](https://nomorecoding.github.io/Ming-3.0-tts/), so you can compare against what you hear there. 0.5b API; full value lists in [English](cookbooks/instruction_en.md) / [简体中文](cookbooks/instructions.md), every task end to end in [cookbooks/cookbook.ipynb](cookbooks/cookbook.ipynb).

### Who speaks

**Zero-shot Cloning**: the `TTS` call in [Quick Start](#ming-30-tts-05b) clones the voice of `prompt_wav_path`.

**Voice Design**: describe the voice; no reference audio.

```python
model.synthesize(
    task="VOICE_DESIGN",
    text="冰川在漫长岁月中缓缓移动，也悄悄记录着气候变化的痕迹。",
    controls={"style": "成熟沉稳的男性纪录片旁白，吐字清晰，节奏舒缓，语气理性而有厚度。"},
    use_zero_spk_emb=True,
)
```

**Built-in Voices**: recommended **US_James**, **US_Stella**, **灵小柔** and **灵楷**. See the [full voice list](cookbooks/instruction_en.md#built-in-premium-voices).

```python
model.synthesize(
    task="IP",
    text="The garden will remain open until sunset, provided the weather stays clear.",
    controls={"ip": "US_James"},
    use_zero_spk_emb=True,
)
```

### How it is said

**Freeform**: describe the voice and delivery with one natural-language instruction. Both models default to generation without reference audio; adding a reference is not recommended. Not combined with voice design, a built-in voice, emotion, dialect or attribute controls.

```python
model.synthesize(
    task="FREEFORM",
    text="The old radio crackled softly as the storm moved across the valley.",
    instruction="Speak in a warm, intimate storytelling voice, with a gentle pace and a hint of nostalgia.",
    use_zero_spk_emb=True,
)
```

For Tiny, omit `prompt_wav` and `prompt_text`:

```python
tts.generate(
    task="freeform",
    text="The old radio crackled softly as the storm moved across the valley.",
    instruction="Speak in a warm, intimate storytelling voice, with a gentle pace and a hint of nostalgia.",
)
```

**Emotion**: `高兴 / 悲伤 / 愤怒 / 恐惧 / 厌恶 / 惊讶 / 中性`.

```python
model.synthesize(
    task="EMOTION",
    text="所有测试都顺利通过了，我们终于可以把这个好消息告诉大家！",
    controls={"emotion": "高兴"},
    prompt_wav_path="data/wavs/emotion_prompt.wav",
    use_spk_emb=True,
)
```

**Speed, Pitch and Volume**: speed `慢速 / 中速 / 快速`, pitch and volume `低 / 中 / 高`.

```python
model.synthesize(
    task="BASIC",
    text="今晚的观测将在云层散开后开始，请耐心等待下一次通知。",
    controls={"speed": "慢速", "pitch": "中", "volume": "中"},
    spk_emb_path="/path/to/speaker_embedding.pt",
    use_spk_emb=True,
)
```

### Beyond the words

**Paralinguistic Tags**: inline, anywhere in the sentence, in Chinese or English. `[Breathing]`, `[Cough]`, `[Sigh]`, `[Laughter]`, `[Surprise-ah]`, `[Surprise-oh]`, `[Dissatisfaction-hnn]`, `[Uhm]`, `[Confirmation-en]`, `[Question-ei]`, `[Question-ah]`, `[Question-en]`, `[Question-oh]`, `[Question-huh]`.

```python
model.synthesize(
    task="TTS",
    text="[Sigh]雨还是没有停，[Cough]我们恐怕只能把活动改到室内了。",
    prompt_wav_path="data/voice_presets/voice_audio/lingguang.wav",
    prompt_text="诶，你今天有空吗？我们能不能聊聊这件事啊？",
    use_spk_emb=True,
)
```

### Where it is heard

**Multilingual**: `language_id` is required for the five new languages; short codes and full names both work.

```python
model.synthesize(
    task="MULTILINGUAL",
    text="週末、駅前の小さな喫茶店で、季節限定の抹茶パフェを食べました",
    language_id="Japanese",     # ja / ko / de / fr / es
    prompt_wav_path="/path/to/japanese_prompt.wav",
    prompt_text="参考音频对应的日语文本。",
    use_spk_emb=True,
)
```

**Dialects**: `chuanyu dialect` or `cantonese`; this task takes no `language_id`.

```python
model.synthesize(
    task="DIALECT",
    text="今日天气几好，我哋食完饭一齐去海边行下啦。",
    controls={"dialect": "cantonese"},
    prompt_wav_path="data/wavs/yue_prompt.wav",
    use_spk_emb=True,
)
```

## <a id="built-in-voices"></a>Built-in voices

### Recommended voices

| Voice | Language | Character |
| :--- | :--- | :--- |
| US_James | English (US) | Male. Narration, explainers and documentary. |
| US_Stella | English | — |
| 灵小柔 | Chinese | Bright, sweet young female voice with clear diction. Assistants and customer service. |
| 灵楷 | Chinese | Warm, resonant young male voice. Radio, documentary and audiobooks. |

Over 100 Chinese voices and five English voices are available. See [the voice catalog](cookbooks/instruction_en.md#built-in-premium-voices) for the full list, including emotion-specific variants.

## <a id="performance"></a>Performance

Open benchmarks are below; independent arena results are in [Artificial Analysis Leaderboards](#artificial-analysis-leaderboards).

<p align="center">
    <img src="./figures/benchmark_basic_1018.png" width="900"/>
</p>
<p align="center">
    <img src="./figures/benchmark_control_1018.png" width="900"/>
</p>

Below, **tiny** is Ming-3.0-tts-tiny and **0.5b** is Ming-3.0-tts-0.5b. Ranks and marks are computed per metric among the listed open-source models; Seed-TTS and NVbench-GT are reference rows and are not ranked. Where a historical Ming-omni-tts result beats a bolded Ming-3.0-tts value, it is noted below the table and no SOTA is claimed. **Bold** marks the best value and <u>underline</u> the second-best value in each column; ties share a mark. Other systems' results use their reported inference settings.

### Summary

1. **Paralinguistic:** together, the two models reach **SOTA on all six NVBench single-tag metrics**; tiny reaches **SOTA on all three English multi-tag metrics**.
2. **Dialect:** 0.5b reaches **SOTA** on Cantonese Base CER and ACC; tiny reaches **SOTA** on Sichuanese Hard CER and Easy ACC.
3. **Multilingual:** tiny reaches **SOTA** on German and Spanish WER, ranks **2nd** on French WER, and ties for **2nd** on Japanese CER.
4. **Emotion:** tiny ties for **SOTA** on CV3 text-related Happy and reaches **SOTA** on both CV3N Sad subsets; 0.5b reaches **SOTA** on CV3 text-related Angry. Tiny's CV3 average ranks **2nd**.
5. **Attribute control:** 0.5b leads the current comparison on average ACC and pitch, while tiny leads on WER and SIM. Historical Ming-omni-tts results still hold the corresponding overall records.
6. **Podcast:** tiny achieves CER 2.03%, cpSIM 0.561 and UTMOS 2.12, ranking **1st**, **2nd** and **2nd**; historical Ming-omni-tts retains lower CER.
7. **Voice Design:** tiny ranks **2nd** on average ACC (75.37%), APS (85.10%) and DSD (79.90%).
8. **Chinese and English:** 0.5b's Chinese WER ranks **3rd**; tiny reaches **SOTA** on Chinese and English SIM.
9. **Next:** improve multilingual and Cantonese speaker similarity, tiny's Korean accuracy and pitch control, text-unrelated emotion, role-play instruction following, and predicted podcast audio quality.

### Chinese and English (seed-tts-eval)

<table style="border-collapse: collapse; border-top: 1.5px solid black; border-bottom: 1.5px solid black; margin: 16px 0;">
  <thead>
    <tr><th rowspan="2" style="padding: 6px 12px; border: none; border-bottom: 1px solid black;">Model</th><th colspan="2" style="padding: 6px 12px; border: none; border-bottom: 1px solid black;">seed-tts-eval-zh</th><th colspan="2" style="padding: 6px 12px; border: none; border-bottom: 1px solid black;">seed-tts-eval-en</th></tr>
    <tr><th style="padding: 6px 12px; border: none; border-bottom: 1px solid black;">WER ↓</th><th style="padding: 6px 12px; border: none; border-bottom: 1px solid black;">SIM ↑</th><th style="padding: 6px 12px; border: none; border-bottom: 1px solid black;">WER ↓</th><th style="padding: 6px 12px; border: none; border-bottom: 1px solid black;">SIM ↑</th></tr>
  </thead>
  <tbody>
    <tr><td style="padding: 5px 12px; border: none; color: rgb(119, 119, 119);"><i>Seed-TTS</i></td><td align="center" style="padding: 5px 12px; border: none; color: rgb(119, 119, 119);">1.110%</td><td align="center" style="padding: 5px 12px; border: none; color: rgb(119, 119, 119);">0.796</td><td align="center" style="padding: 5px 12px; border: none; color: rgb(119, 119, 119);">2.240%</td><td align="center" style="padding: 5px 12px; border: none; color: rgb(119, 119, 119);">0.762</td></tr>
    <tr><td style="padding: 5px 12px; border: none;">GLM-TTS</td><td align="center" style="padding: 5px 12px; border: none;">1.030%</td><td align="center" style="padding: 5px 12px; border: none;">0.761</td><td align="center" style="padding: 5px 12px; border: none;">2.230%</td><td align="center" style="padding: 5px 12px; border: none;">0.672</td></tr>
    <tr><td style="padding: 5px 12px; border: none;">Qwen3-TTS</td><td align="center" style="padding: 5px 12px; border: none;">1.070%</td><td align="center" style="padding: 5px 12px; border: none;">—</td><td align="center" style="padding: 5px 12px; border: none;">1.390%</td><td align="center" style="padding: 5px 12px; border: none;">—</td></tr>
    <tr><td style="padding: 5px 12px; border: none;">Qwen3-TTS-12Hz-0.6B-Base</td><td align="center" style="padding: 5px 12px; border: none;">0.920%</td><td align="center" style="padding: 5px 12px; border: none;">—</td><td align="center" style="padding: 5px 12px; border: none;"><u>1.320%</u></td><td align="center" style="padding: 5px 12px; border: none;">—</td></tr>
    <tr><td style="padding: 5px 12px; border: none;">Qwen3-TTS-12Hz-1.7B-Base</td><td align="center" style="padding: 5px 12px; border: none;"><u>0.770%</u></td><td align="center" style="padding: 5px 12px; border: none;">—</td><td align="center" style="padding: 5px 12px; border: none;"><b>1.240%</b></td><td align="center" style="padding: 5px 12px; border: none;">—</td></tr>
    <tr><td style="padding: 5px 12px; border: none;">CosyVoice3-0.5B</td><td align="center" style="padding: 5px 12px; border: none;">1.160%</td><td align="center" style="padding: 5px 12px; border: none;"><u>0.780</u></td><td align="center" style="padding: 5px 12px; border: none;">2.020%</td><td align="center" style="padding: 5px 12px; border: none;"><u>0.718</u></td></tr>
    <tr><td style="padding: 5px 12px; border: none;">CosyVoice3-1.5B</td><td align="center" style="padding: 5px 12px; border: none;"><b>0.710%</b></td><td align="center" style="padding: 5px 12px; border: none;">0.775</td><td align="center" style="padding: 5px 12px; border: none;">1.450%</td><td align="center" style="padding: 5px 12px; border: none;">0.695</td></tr>
    <tr><td style="padding: 5px 12px; border: none;">F5-TTS</td><td align="center" style="padding: 5px 12px; border: none;">1.560%</td><td align="center" style="padding: 5px 12px; border: none;">0.741</td><td align="center" style="padding: 5px 12px; border: none;">1.830%</td><td align="center" style="padding: 5px 12px; border: none;">0.647</td></tr>
    <tr><td style="padding: 5px 12px; border: none; border-top: 1px solid black;"><b>Ming-3.0-tts-0.5b</b></td><td align="center" style="padding: 5px 12px; border: none; border-top: 1px solid black;">0.800%</td><td align="center" style="padding: 5px 12px; border: none; border-top: 1px solid black;">0.758</td><td align="center" style="padding: 5px 12px; border: none; border-top: 1px solid black;">1.584%</td><td align="center" style="padding: 5px 12px; border: none; border-top: 1px solid black;">0.691</td></tr>
    <tr><td style="padding: 5px 12px; border: none;"><b>Ming-3.0-tts-tiny</b></td><td align="center" style="padding: 5px 12px; border: none;">0.820%</td><td align="center" style="padding: 5px 12px; border: none;"><b>0.781</b></td><td align="center" style="padding: 5px 12px; border: none;">1.666%</td><td align="center" style="padding: 5px 12px; border: none;"><b>0.728</b></td></tr>
  </tbody>
</table>

Tiny achieves **SOTA speaker similarity** in Chinese and English. 0.5b has lower WER in both languages and ranks **3rd** on Chinese WER.

### Multilingual (MiniMaxAI TTS-Multilingual-Test-Set)

<table style="border-collapse: collapse; border-top: 1.5px solid black; border-bottom: 1.5px solid black; margin: 16px 0;">
  <thead>
    <tr><th rowspan="2" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Model</th><th colspan="2" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">German</th><th colspan="2" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Spanish</th><th colspan="2" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">French</th><th colspan="2" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Korean</th><th colspan="2" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Japanese</th></tr>
    <tr><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">WER ↓</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">SIM ↑</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">WER ↓</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">SIM ↑</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">WER ↓</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">SIM ↑</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">CER ↓</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">SIM ↑</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">CER ↓</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">SIM ↑</th></tr>
  </thead>
  <tbody>
    <tr><td style="padding: 5px 10px; border: none;">dots.tts</td><td align="center" style="padding: 5px 10px; border: none;">0.452%</td><td align="center" style="padding: 5px 10px; border: none;"><u>0.798</u></td><td align="center" style="padding: 5px 10px; border: none;">2.593%</td><td align="center" style="padding: 5px 10px; border: none;"><u>0.839</u></td><td align="center" style="padding: 5px 10px; border: none;">19.878%</td><td align="center" style="padding: 5px 10px; border: none;"><u>0.789</u></td><td align="center" style="padding: 5px 10px; border: none;">4.837%</td><td align="center" style="padding: 5px 10px; border: none;"><u>0.853</u></td><td align="center" style="padding: 5px 10px; border: none;">5.134%</td><td align="center" style="padding: 5px 10px; border: none;"><b>0.838</b></td></tr>
    <tr><td style="padding: 5px 10px; border: none;">VoxCPM2</td><td align="center" style="padding: 5px 10px; border: none;">0.963%</td><td align="center" style="padding: 5px 10px; border: none;">0.790</td><td align="center" style="padding: 5px 10px; border: none;">1.324%</td><td align="center" style="padding: 5px 10px; border: none;">0.836</td><td align="center" style="padding: 5px 10px; border: none;"><b>3.380%</b></td><td align="center" style="padding: 5px 10px; border: none;">0.761</td><td align="center" style="padding: 5px 10px; border: none;">3.547%</td><td align="center" style="padding: 5px 10px; border: none;">0.839</td><td align="center" style="padding: 5px 10px; border: none;">4.358%</td><td align="center" style="padding: 5px 10px; border: none;"><u>0.825</u></td></tr>
    <tr><td style="padding: 5px 10px; border: none;">Fish Audio S2</td><td align="center" style="padding: 5px 10px; border: none;">1.045%</td><td align="center" style="padding: 5px 10px; border: none;">0.714</td><td align="center" style="padding: 5px 10px; border: none;">1.216%</td><td align="center" style="padding: 5px 10px; border: none;">0.748</td><td align="center" style="padding: 5px 10px; border: none;">3.636%</td><td align="center" style="padding: 5px 10px; border: none;">0.698</td><td align="center" style="padding: 5px 10px; border: none;"><u>1.675%</u></td><td align="center" style="padding: 5px 10px; border: none;">0.761</td><td align="center" style="padding: 5px 10px; border: none;"><u>3.427%</u></td><td align="center" style="padding: 5px 10px; border: none;">0.755</td></tr>
    <tr><td style="padding: 5px 10px; border: none;">FireRedTTS3</td><td align="center" style="padding: 5px 10px; border: none;"><u>0.348%</u></td><td align="center" style="padding: 5px 10px; border: none;"><b>0.825</b></td><td align="center" style="padding: 5px 10px; border: none;"><u>1.086%</u></td><td align="center" style="padding: 5px 10px; border: none;"><b>0.868</b></td><td align="center" style="padding: 5px 10px; border: none;">4.366%</td><td align="center" style="padding: 5px 10px; border: none;"><b>0.807</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>1.644%</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>0.864</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>3.418%</b></td><td align="center" style="padding: 5px 10px; border: none;"><u>0.825</u></td></tr>
    <tr><td style="padding: 5px 10px; border: none; border-top: 1px solid black;"><b>Ming-3.0-tts-0.5b</b></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">0.365%</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">0.753</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">1.099%</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">0.763</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">4.264%</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">0.675</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">1.728%</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">0.793</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">3.765%</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">0.765</td></tr>
    <tr><td style="padding: 5px 10px; border: none;"><b>Ming-3.0-tts-tiny</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>0.325%</b></td><td align="center" style="padding: 5px 10px; border: none;">0.791</td><td align="center" style="padding: 5px 10px; border: none;"><b>0.971%</b></td><td align="center" style="padding: 5px 10px; border: none;">0.797</td><td align="center" style="padding: 5px 10px; border: none;"><u>3.470%</u></td><td align="center" style="padding: 5px 10px; border: none;">0.733</td><td align="center" style="padding: 5px 10px; border: none;">6.000%</td><td align="center" style="padding: 5px 10px; border: none;">0.797</td><td align="center" style="padding: 5px 10px; border: none;"><u>3.427%</u></td><td align="center" style="padding: 5px 10px; border: none;">0.780</td></tr>
  </tbody>
</table>

<sub>Each open-source model was evaluated using its recommended inference settings under a unified ASR-based WER/CER evaluation protocol.</sub>

Tiny achieves **SOTA WER in German and Spanish**, ranks **2nd** in French WER and ties for **2nd** in Japanese CER. 0.5b is more accurate in Korean; speaker similarity remains a gap for both models.

### Paralinguistic control (NVBench)

CER, PCER (paralinguistic CER) and OCER are reported. NVbench-GT is human-labelled reference, shown for context and not ranked.

<table style="border-collapse: collapse; border-top: 1.5px solid black; border-bottom: 1.5px solid black; margin: 16px 0;">
  <thead>
    <tr><th rowspan="3" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">Model</th><th colspan="6" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">Single</th><th colspan="6" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">Multi</th></tr>
    <tr><th colspan="3" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">Chinese</th><th colspan="3" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">English</th><th colspan="3" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">Chinese</th><th colspan="3" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">English</th></tr>
    <tr><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">CER</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">PCER</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">OCER</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">CER</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">PCER</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">OCER</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">CER</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">PCER</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">OCER</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">CER</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">PCER</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">OCER</th></tr>
  </thead>
  <tbody>
    <tr><td style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);"><i>NVbench-GT</i></td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">3.86</td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">9.38</td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">4.07</td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">6.73</td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">8.31</td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">6.90</td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">3.79</td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">23.71</td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">5.07</td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">7.26</td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">21.41</td><td align="center" style="padding: 5px 8px; border: none; color: rgb(119, 119, 119);">8.62</td></tr>
    <tr><td style="padding: 5px 8px; border: none;">Orpheus-TTS</td><td align="center" style="padding: 5px 8px; border: none;">11.36</td><td align="center" style="padding: 5px 8px; border: none;">88.77</td><td align="center" style="padding: 5px 8px; border: none;">13.91</td><td align="center" style="padding: 5px 8px; border: none;">9.03</td><td align="center" style="padding: 5px 8px; border: none;">71.92</td><td align="center" style="padding: 5px 8px; border: none;">10.63</td><td align="center" style="padding: 5px 8px; border: none;">19.83</td><td align="center" style="padding: 5px 8px; border: none;">84.85</td><td align="center" style="padding: 5px 8px; border: none;">24.38</td><td align="center" style="padding: 5px 8px; border: none;">8.68</td><td align="center" style="padding: 5px 8px; border: none;">71.46</td><td align="center" style="padding: 5px 8px; border: none;">11.89</td></tr>
    <tr><td style="padding: 5px 8px; border: none;">SMIIP-NV-CV2</td><td align="center" style="padding: 5px 8px; border: none;">8.80</td><td align="center" style="padding: 5px 8px; border: none;">75.64</td><td align="center" style="padding: 5px 8px; border: none;">11.34</td><td align="center" style="padding: 5px 8px; border: none;">17.92</td><td align="center" style="padding: 5px 8px; border: none;">56.80</td><td align="center" style="padding: 5px 8px; border: none;">19.47</td><td align="center" style="padding: 5px 8px; border: none;">10.66</td><td align="center" style="padding: 5px 8px; border: none;">77.20</td><td align="center" style="padding: 5px 8px; border: none;">14.79</td><td align="center" style="padding: 5px 8px; border: none;">20.93</td><td align="center" style="padding: 5px 8px; border: none;">54.49</td><td align="center" style="padding: 5px 8px; border: none;">23.87</td></tr>
    <tr><td style="padding: 5px 8px; border: none;">Emilia-NV-CV2</td><td align="center" style="padding: 5px 8px; border: none;">5.05</td><td align="center" style="padding: 5px 8px; border: none;">40.00</td><td align="center" style="padding: 5px 8px; border: none;">6.64</td><td align="center" style="padding: 5px 8px; border: none;">12.50</td><td align="center" style="padding: 5px 8px; border: none;">55.30</td><td align="center" style="padding: 5px 8px; border: none;">13.21</td><td align="center" style="padding: 5px 8px; border: none;">5.54</td><td align="center" style="padding: 5px 8px; border: none;">48.74</td><td align="center" style="padding: 5px 8px; border: none;">8.09</td><td align="center" style="padding: 5px 8px; border: none;">11.71</td><td align="center" style="padding: 5px 8px; border: none;">60.28</td><td align="center" style="padding: 5px 8px; border: none;">14.63</td></tr>
    <tr><td style="padding: 5px 8px; border: none;">CosyVoice3</td><td align="center" style="padding: 5px 8px; border: none;">3.85</td><td align="center" style="padding: 5px 8px; border: none;">57.69</td><td align="center" style="padding: 5px 8px; border: none;">5.86</td><td align="center" style="padding: 5px 8px; border: none;">7.87</td><td align="center" style="padding: 5px 8px; border: none;">62.75</td><td align="center" style="padding: 5px 8px; border: none;">9.06</td><td align="center" style="padding: 5px 8px; border: none;">4.75</td><td align="center" style="padding: 5px 8px; border: none;">61.94</td><td align="center" style="padding: 5px 8px; border: none;">8.26</td><td align="center" style="padding: 5px 8px; border: none;"><u>6.39</u></td><td align="center" style="padding: 5px 8px; border: none;">57.84</td><td align="center" style="padding: 5px 8px; border: none;">10.69</td></tr>
    <tr><td style="padding: 5px 8px; border: none;">NV-FlexiVoice</td><td align="center" style="padding: 5px 8px; border: none;">6.98</td><td align="center" style="padding: 5px 8px; border: none;">31.08</td><td align="center" style="padding: 5px 8px; border: none;">8.15</td><td align="center" style="padding: 5px 8px; border: none;">11.88</td><td align="center" style="padding: 5px 8px; border: none;">50.43</td><td align="center" style="padding: 5px 8px; border: none;">13.21</td><td align="center" style="padding: 5px 8px; border: none;">8.20</td><td align="center" style="padding: 5px 8px; border: none;">39.37</td><td align="center" style="padding: 5px 8px; border: none;">10.39</td><td align="center" style="padding: 5px 8px; border: none;">9.60</td><td align="center" style="padding: 5px 8px; border: none;">51.32</td><td align="center" style="padding: 5px 8px; border: none;">13.76</td></tr>
    <tr><td style="padding: 5px 8px; border: none;">NV-CV3</td><td align="center" style="padding: 5px 8px; border: none;">3.80</td><td align="center" style="padding: 5px 8px; border: none;">27.69</td><td align="center" style="padding: 5px 8px; border: none;"><u>4.90</u></td><td align="center" style="padding: 5px 8px; border: none;">8.33</td><td align="center" style="padding: 5px 8px; border: none;">46.13</td><td align="center" style="padding: 5px 8px; border: none;">9.44</td><td align="center" style="padding: 5px 8px; border: none;"><b>3.44</b></td><td align="center" style="padding: 5px 8px; border: none;"><b>30.04</b></td><td align="center" style="padding: 5px 8px; border: none;"><b>4.84</b></td><td align="center" style="padding: 5px 8px; border: none;">6.70</td><td align="center" style="padding: 5px 8px; border: none;"><u>47.13</u></td><td align="center" style="padding: 5px 8px; border: none;"><u>10.10</u></td></tr>
    <tr><td style="padding: 5px 8px; border: none; border-top: 1px solid black;"><b>Ming-3.0-tts-0.5b</b></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><b>2.70</b></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><u>22.80</u></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><b>3.20</b></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><u>7.60</u></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><u>37.00</u></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><u>8.90</u></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><u>3.50</u></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;">36.60</td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;">8.10</td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;">7.90</td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;">47.30</td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;">10.40</td></tr>
    <tr><td style="padding: 5px 8px; border: none;"><b>Ming-3.0-tts-tiny</b></td><td align="center" style="padding: 5px 8px; border: none;"><u>2.80</u></td><td align="center" style="padding: 5px 8px; border: none;"><b>17.23</b></td><td align="center" style="padding: 5px 8px; border: none;"><b>3.20</b></td><td align="center" style="padding: 5px 8px; border: none;"><b>5.86</b></td><td align="center" style="padding: 5px 8px; border: none;"><b>32.95</b></td><td align="center" style="padding: 5px 8px; border: none;"><b>7.05</b></td><td align="center" style="padding: 5px 8px; border: none;">4.49</td><td align="center" style="padding: 5px 8px; border: none;"><u>32.88</u></td><td align="center" style="padding: 5px 8px; border: none;"><u>5.81</u></td><td align="center" style="padding: 5px 8px; border: none;"><b>5.12</b></td><td align="center" style="padding: 5px 8px; border: none;"><b>46.13</b></td><td align="center" style="padding: 5px 8px; border: none;"><b>7.68</b></td></tr>
  </tbody>
</table>

Together, the two models achieve **SOTA on all six Chinese and English single-tag metrics**; tiny also leads all three English multi-tag metrics. Chinese multi-tag control remains behind NV-CV3.

### Dialect

<table style="border-collapse: collapse; border-top: 1.5px solid black; border-bottom: 1.5px solid black; margin: 16px 0;">
  <thead>
    <tr><th rowspan="2" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">Model</th><th colspan="3" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">WSC-Eval-TTS-easy</th><th colspan="3" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">WSC-Eval-TTS-hard</th><th colspan="3" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">WSYue-TTS-eval-Base</th><th colspan="3" style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">WSYue-TTS-eval-Coverage</th></tr>
    <tr><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">CER ↓</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">SIM ↑</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">ACC ↑</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">CER ↓</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">SIM ↑</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">ACC ↑</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">CER ↓</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">SIM ↑</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">ACC ↑</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">CER ↓</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">SIM ↑</th><th style="padding: 6px 8px; border: none; border-bottom: 1px solid black;">ACC ↑</th></tr>
  </thead>
  <tbody>
    <tr><td style="padding: 5px 8px; border: none;">Qwen3-TTS</td><td align="center" style="padding: 5px 8px; border: none;">4.13%</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">7.35%</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td></tr>
    <tr><td style="padding: 5px 8px; border: none;">CosyVoice3-0.5B</td><td align="center" style="padding: 5px 8px; border: none;">3.17%</td><td align="center" style="padding: 5px 8px; border: none;">0.696</td><td align="center" style="padding: 5px 8px; border: none;">76.05%</td><td align="center" style="padding: 5px 8px; border: none;">4.07%</td><td align="center" style="padding: 5px 8px; border: none;"><u>0.723</u></td><td align="center" style="padding: 5px 8px; border: none;">81.41%</td><td align="center" style="padding: 5px 8px; border: none;">8.36%</td><td align="center" style="padding: 5px 8px; border: none;">0.611</td><td align="center" style="padding: 5px 8px; border: none;">91.70%</td><td align="center" style="padding: 5px 8px; border: none;">8.95%</td><td align="center" style="padding: 5px 8px; border: none;">0.658</td><td align="center" style="padding: 5px 8px; border: none;"><b>95.80%</b></td></tr>
    <tr><td style="padding: 5px 8px; border: none;">CosyVoice3-1.5B + DiffRO-EMO</td><td align="center" style="padding: 5px 8px; border: none;">7.14%</td><td align="center" style="padding: 5px 8px; border: none;">0.703</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">9.06%</td><td align="center" style="padding: 5px 8px; border: none;">0.601</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">14.38%</td><td align="center" style="padding: 5px 8px; border: none;"><u>0.812</u></td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">13.74%</td><td align="center" style="padding: 5px 8px; border: none;"><u>0.826</u></td><td align="center" style="padding: 5px 8px; border: none;">—</td></tr>
    <tr><td style="padding: 5px 8px; border: none;">CosyVoice2-WSC</td><td align="center" style="padding: 5px 8px; border: none;">4.28%</td><td align="center" style="padding: 5px 8px; border: none;"><u>0.728</u></td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">8.87%</td><td align="center" style="padding: 5px 8px; border: none;">0.626</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td></tr>
    <tr><td style="padding: 5px 8px; border: none;">CosyVoice2-WSC-SFT</td><td align="center" style="padding: 5px 8px; border: none;">4.08%</td><td align="center" style="padding: 5px 8px; border: none;"><b>0.788</b></td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">7.22%</td><td align="center" style="padding: 5px 8px; border: none;">0.680</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td></tr>
    <tr><td style="padding: 5px 8px; border: none;">CosyVoice2-Yue</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">10.33%</td><td align="center" style="padding: 5px 8px; border: none;"><b>0.821</b></td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">9.49%</td><td align="center" style="padding: 5px 8px; border: none;"><b>0.834</b></td><td align="center" style="padding: 5px 8px; border: none;">—</td></tr>
    <tr><td style="padding: 5px 8px; border: none;">Sparks-TTS</td><td align="center" style="padding: 5px 8px; border: none;">10.83%</td><td align="center" style="padding: 5px 8px; border: none;">0.677</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">12.52%</td><td align="center" style="padding: 5px 8px; border: none;">0.545</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">27.79%</td><td align="center" style="padding: 5px 8px; border: none;">0.762</td><td align="center" style="padding: 5px 8px; border: none;">—</td><td align="center" style="padding: 5px 8px; border: none;">24.25%</td><td align="center" style="padding: 5px 8px; border: none;">0.781</td><td align="center" style="padding: 5px 8px; border: none;">—</td></tr>
    <tr><td style="padding: 5px 8px; border: none; border-top: 1px solid black;"><b>Ming-3.0-tts-0.5b</b></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><b>2.27%</b></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;">0.689</td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><u>80.68%</u></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><u>3.35%</u></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;">0.691</td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><u>87.64%</u></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><b>6.15%</b></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;">0.586</td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><b>98.00%</b></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><b>8.15%</b></td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;">0.622</td><td align="center" style="padding: 5px 8px; border: none; border-top: 1px solid black;"><u>95.27%</u></td></tr>
    <tr><td style="padding: 5px 8px; border: none;"><b>Ming-3.0-tts-tiny</b></td><td align="center" style="padding: 5px 8px; border: none;"><u>2.53%</u></td><td align="center" style="padding: 5px 8px; border: none;">0.721</td><td align="center" style="padding: 5px 8px; border: none;"><b>86.09%</b></td><td align="center" style="padding: 5px 8px; border: none;"><b>3.11%</b></td><td align="center" style="padding: 5px 8px; border: none;"><b>0.738</b></td><td align="center" style="padding: 5px 8px; border: none;"><b>88.94%</b></td><td align="center" style="padding: 5px 8px; border: none;"><u>7.40%</u></td><td align="center" style="padding: 5px 8px; border: none;">0.605</td><td align="center" style="padding: 5px 8px; border: none;"><u>92.90%</u></td><td align="center" style="padding: 5px 8px; border: none;"><u>8.67%</u></td><td align="center" style="padding: 5px 8px; border: none;">0.653</td><td align="center" style="padding: 5px 8px; border: none;">95.16%</td></tr>
  </tbody>
</table>

Tiny is stronger in Sichuanese control accuracy and achieves **SOTA Sichuanese Hard CER and Easy ACC**, while 0.5b achieves **SOTA Cantonese Base CER and ACC**. Cantonese speaker similarity remains below CosyVoice2-Yue. Historical Ming-omni-tts results remain stronger on Sichuanese Easy CER (2.25%), Hard SIM (0.750) and Hard ACC (90.45%), and on Cantonese Coverage CER (7.87%).

### Emotion control (CV3)

<table style="border-collapse: collapse; border-top: 1.5px solid black; border-bottom: 1.5px solid black; margin: 16px 0;">
  <thead>
    <tr><th rowspan="2" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Model</th><th rowspan="2" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Average</th><th colspan="3" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Text-Related</th><th colspan="3" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Text-Unrelated</th></tr>
    <tr><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Happy</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Sad</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Angry</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Happy</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Sad</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Angry</th></tr>
  </thead>
  <tbody>
    <tr><td style="padding: 5px 10px; border: none;">CosyVoice3-0.5B</td><td align="center" style="padding: 5px 10px; border: none;">66.33%</td><td align="center" style="padding: 5px 10px; border: none;">92%</td><td align="center" style="padding: 5px 10px; border: none;">70%</td><td align="center" style="padding: 5px 10px; border: none;">72%</td><td align="center" style="padding: 5px 10px; border: none;">64%</td><td align="center" style="padding: 5px 10px; border: none;">42%</td><td align="center" style="padding: 5px 10px; border: none;">58%</td></tr>
    <tr><td style="padding: 5px 10px; border: none;">CosyVoice3-1.5B</td><td align="center" style="padding: 5px 10px; border: none;">63.00%</td><td align="center" style="padding: 5px 10px; border: none;">86%</td><td align="center" style="padding: 5px 10px; border: none;">64%</td><td align="center" style="padding: 5px 10px; border: none;">72%</td><td align="center" style="padding: 5px 10px; border: none;">64%</td><td align="center" style="padding: 5px 10px; border: none;">44%</td><td align="center" style="padding: 5px 10px; border: none;">48%</td></tr>
    <tr><td style="padding: 5px 10px; border: none;">CosyVoice3-1.5B + DiffRO-EMO</td><td align="center" style="padding: 5px 10px; border: none;"><b>77.67%</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>98%</b></td><td align="center" style="padding: 5px 10px; border: none;">68%</td><td align="center" style="padding: 5px 10px; border: none;">84%</td><td align="center" style="padding: 5px 10px; border: none;"><b>98%</b></td><td align="center" style="padding: 5px 10px; border: none;"><u>50%</u></td><td align="center" style="padding: 5px 10px; border: none;">68%</td></tr>
    <tr><td style="padding: 5px 10px; border: none;">F5-TTS</td><td align="center" style="padding: 5px 10px; border: none;">64.67%</td><td align="center" style="padding: 5px 10px; border: none;">92%</td><td align="center" style="padding: 5px 10px; border: none;">52%</td><td align="center" style="padding: 5px 10px; border: none;">72%</td><td align="center" style="padding: 5px 10px; border: none;"><u>80%</u></td><td align="center" style="padding: 5px 10px; border: none;">28%</td><td align="center" style="padding: 5px 10px; border: none;">64%</td></tr>
    <tr><td style="padding: 5px 10px; border: none;">Sparks-TTS</td><td align="center" style="padding: 5px 10px; border: none;">55.33%</td><td align="center" style="padding: 5px 10px; border: none;">80%</td><td align="center" style="padding: 5px 10px; border: none;">56%</td><td align="center" style="padding: 5px 10px; border: none;">50%</td><td align="center" style="padding: 5px 10px; border: none;">50%</td><td align="center" style="padding: 5px 10px; border: none;"><b>60%</b></td><td align="center" style="padding: 5px 10px; border: none;">36%</td></tr>
    <tr><td style="padding: 5px 10px; border: none; border-top: 1px solid black;"><b>Ming-3.0-tts-0.5b</b></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">72.33%</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>96%</u></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>76%</u></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><b>94%</b></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">52%</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">36%</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><b>80%</b></td></tr>
    <tr><td style="padding: 5px 10px; border: none;"><b>Ming-3.0-tts-tiny</b></td><td align="center" style="padding: 5px 10px; border: none;"><u>74.00%</u></td><td align="center" style="padding: 5px 10px; border: none;"><b>98%</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>82%</b></td><td align="center" style="padding: 5px 10px; border: none;"><u>90%</u></td><td align="center" style="padding: 5px 10px; border: none;">60%</td><td align="center" style="padding: 5px 10px; border: none;">36%</td><td align="center" style="padding: 5px 10px; border: none;"><u>78%</u></td></tr>
  </tbody>
</table>

Tiny and 0.5b rank **2nd** and **3rd** in average ACC. Tiny is stronger on text-related Happy and Sad, while 0.5b is stronger on Angry; text-unrelated emotion remains a shared limitation. Historical Ming-omni-tts results remain higher on text-related Sad (86%) and text-unrelated Angry (82%).

### Emotion control (CV3N, hard emotion control)

<table style="border-collapse: collapse; border-top: 1.5px solid black; border-bottom: 1.5px solid black; margin: 16px 0;">
  <thead>
    <tr><th rowspan="2" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Model</th><th rowspan="2" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Average</th><th colspan="3" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Text-Related</th><th colspan="3" style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Text-Unrelated</th></tr>
    <tr><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Happy</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Sad</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Angry</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Happy</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Sad</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Angry</th></tr>
  </thead>
  <tbody>
    <tr><td style="padding: 5px 10px; border: none;">CosyVoice3-0.5B</td><td align="center" style="padding: 5px 10px; border: none;"><b>40.00%</b></td><td align="center" style="padding: 5px 10px; border: none;"><u>68%</u></td><td align="center" style="padding: 5px 10px; border: none;">30%</td><td align="center" style="padding: 5px 10px; border: none;"><b>78%</b></td><td align="center" style="padding: 5px 10px; border: none;"><u>14%</u></td><td align="center" style="padding: 5px 10px; border: none;"><u>4%</u></td><td align="center" style="padding: 5px 10px; border: none;"><b>46%</b></td></tr>
    <tr><td style="padding: 5px 10px; border: none; border-top: 1px solid black;"><b>Ming-3.0-tts-0.5b</b></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>37.33%</u></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><b>70%</b></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>36%</u></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>70%</u></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>14%</u></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>4%</u></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>30%</u></td></tr>
    <tr><td style="padding: 5px 10px; border: none;"><b>Ming-3.0-tts-tiny</b></td><td align="center" style="padding: 5px 10px; border: none;">30.67%</td><td align="center" style="padding: 5px 10px; border: none;">60%</td><td align="center" style="padding: 5px 10px; border: none;"><b>40%</b></td><td align="center" style="padding: 5px 10px; border: none;">44%</td><td align="center" style="padding: 5px 10px; border: none;"><b>18%</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>10%</b></td><td align="center" style="padding: 5px 10px; border: none;">12%</td></tr>
  </tbody>
</table>

0.5b and tiny rank **2nd** and **3rd** in average ACC. Tiny achieves **SOTA on both Sad subsets**, while 0.5b has higher overall accuracy. Historical Ming-omni-tts results remain higher on text-related Happy (78%) and text-unrelated Happy (30%).

### Voice Design (InstructTTSEval-ZH)

<table style="border-collapse: collapse; border-top: 1.5px solid black; border-bottom: 1.5px solid black; margin: 16px 0;">
  <thead>
    <tr><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Model</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Average</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">APS</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">DSD</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">RP</th></tr>
  </thead>
  <tbody>
    <tr><td style="padding: 5px 10px; border: none;">Qwen3-TTS</td><td align="center" style="padding: 5px 10px; border: none;"><b>77.13%</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>85.20%</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>81.10%</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>65.10%</b></td></tr>
    <tr><td style="padding: 5px 10px; border: none;">Mimo-Audio-7B-Instruct</td><td align="center" style="padding: 5px 10px; border: none;">70.50%</td><td align="center" style="padding: 5px 10px; border: none;">75.70%</td><td align="center" style="padding: 5px 10px; border: none;">74.30%</td><td align="center" style="padding: 5px 10px; border: none;"><u>61.50%</u></td></tr>
    <tr><td style="padding: 5px 10px; border: none;">VoiceSculptor</td><td align="center" style="padding: 5px 10px; border: none;">67.30%</td><td align="center" style="padding: 5px 10px; border: none;">75.70%</td><td align="center" style="padding: 5px 10px; border: none;">64.70%</td><td align="center" style="padding: 5px 10px; border: none;"><u>61.50%</u></td></tr>
    <tr><td style="padding: 5px 10px; border: none;">VoxInstruct</td><td align="center" style="padding: 5px 10px; border: none;">47.47%</td><td align="center" style="padding: 5px 10px; border: none;">47.50%</td><td align="center" style="padding: 5px 10px; border: none;">52.30%</td><td align="center" style="padding: 5px 10px; border: none;">42.60%</td></tr>
    <tr><td style="padding: 5px 10px; border: none; border-top: 1px solid black;"><b>Ming-3.0-tts-0.5b</b></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">72.29%</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">78.54%</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">77.28%</td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;">61.06%</td></tr>
    <tr><td style="padding: 5px 10px; border: none;"><b>Ming-3.0-tts-tiny</b></td><td align="center" style="padding: 5px 10px; border: none;"><u>75.37%</u></td><td align="center" style="padding: 5px 10px; border: none;"><u>85.10%</u></td><td align="center" style="padding: 5px 10px; border: none;"><u>79.90%</u></td><td align="center" style="padding: 5px 10px; border: none;">61.10%</td></tr>
  </tbody>
</table>

Tiny and 0.5b rank **2nd** and **3rd** in average ACC, behind Qwen3-TTS. Role-play instruction following remains the main gap for both models.

### Basic attribute control

<table style="border-collapse: collapse; border-top: 1.5px solid black; border-bottom: 1.5px solid black; margin: 16px 0;">
  <thead>
    <tr><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Model</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Speed</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Volume</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Pitch</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">Average</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">WER ↓</th><th style="padding: 6px 10px; border: none; border-bottom: 1px solid black;">SIM ↑</th></tr>
  </thead>
  <tbody>
    <tr><td style="padding: 5px 10px; border: none;">CosyVoice3-0.5B</td><td align="center" style="padding: 5px 10px; border: none;"><b>100.00%</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>97.67%</b></td><td align="center" style="padding: 5px 10px; border: none;">65.33%</td><td align="center" style="padding: 5px 10px; border: none;">87.67%</td><td align="center" style="padding: 5px 10px; border: none;">1.210%</td><td align="center" style="padding: 5px 10px; border: none;">0.580</td></tr>
    <tr><td style="padding: 5px 10px; border: none; border-top: 1px solid black;"><b>Ming-3.0-tts-0.5b</b></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>99.00%</u></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>95.00%</u></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><b>86.00%</b></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><b>93.30%</b></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>0.317%</u></td><td align="center" style="padding: 5px 10px; border: none; border-top: 1px solid black;"><u>0.712</u></td></tr>
    <tr><td style="padding: 5px 10px; border: none;"><b>Ming-3.0-tts-tiny</b></td><td align="center" style="padding: 5px 10px; border: none;">93.00%</td><td align="center" style="padding: 5px 10px; border: none;">93.00%</td><td align="center" style="padding: 5px 10px; border: none;"><u>78.70%</u></td><td align="center" style="padding: 5px 10px; border: none;"><u>88.23%</u></td><td align="center" style="padding: 5px 10px; border: none;"><b>0.274%</b></td><td align="center" style="padding: 5px 10px; border: none;"><b>0.742</b></td></tr>
  </tbody>
</table>

0.5b has higher control accuracy, while tiny has lower WER and higher speaker similarity. Historical Ming-omni-tts models retain the overall records for average ACC, pitch, WER and SIM.

### Podcast

<table style="border-collapse: collapse; border-top: 1.5px solid black; border-bottom: 1.5px solid black; margin: 16px 0;">
  <thead>
    <tr><th style="padding: 6px 12px; border: none; border-bottom: 1px solid black;">Model</th><th style="padding: 6px 12px; border: none; border-bottom: 1px solid black;">CER ↓</th><th style="padding: 6px 12px; border: none; border-bottom: 1px solid black;">cpSIM ↑</th><th style="padding: 6px 12px; border: none; border-bottom: 1px solid black;">UTMOS ↑</th></tr>
  </thead>
  <tbody>
    <tr><td style="padding: 5px 12px; border: none;">FireRedTTS2</td><td align="center" style="padding: 5px 12px; border: none;">3.34%</td><td align="center" style="padding: 5px 12px; border: none;">0.512</td><td align="center" style="padding: 5px 12px; border: none;">1.90</td></tr>
    <tr><td style="padding: 5px 12px; border: none;">SoulX-Podcast</td><td align="center" style="padding: 5px 12px; border: none;"><u>2.20%</u></td><td align="center" style="padding: 5px 12px; border: none;"><b>0.599</b></td><td align="center" style="padding: 5px 12px; border: none;">2.09</td></tr>
    <tr><td style="padding: 5px 12px; border: none;">VibeVoice-1.5B</td><td align="center" style="padding: 5px 12px; border: none;">12.87%</td><td align="center" style="padding: 5px 12px; border: none;">0.455</td><td align="center" style="padding: 5px 12px; border: none;">1.74</td></tr>
    <tr><td style="padding: 5px 12px; border: none;">MOSS-TTSD</td><td align="center" style="padding: 5px 12px; border: none;">8.62%</td><td align="center" style="padding: 5px 12px; border: none;">0.421</td><td align="center" style="padding: 5px 12px; border: none;">1.70</td></tr>
    <tr><td style="padding: 5px 12px; border: none;">ZipVoice-Dia</td><td align="center" style="padding: 5px 12px; border: none;">3.39%</td><td align="center" style="padding: 5px 12px; border: none;">0.553</td><td align="center" style="padding: 5px 12px; border: none;"><b>2.24</b></td></tr>
    <tr><td style="padding: 5px 12px; border: none;">MoonCast</td><td align="center" style="padding: 5px 12px; border: none;">27.43%</td><td align="center" style="padding: 5px 12px; border: none;">0.441</td><td align="center" style="padding: 5px 12px; border: none;">1.76</td></tr>
    <tr><td style="padding: 5px 12px; border: none; border-top: 1px solid black;"><b>Ming-3.0-tts-tiny</b></td><td align="center" style="padding: 5px 12px; border: none; border-top: 1px solid black;"><b>2.03%</b></td><td align="center" style="padding: 5px 12px; border: none; border-top: 1px solid black;"><u>0.561</u></td><td align="center" style="padding: 5px 12px; border: none; border-top: 1px solid black;"><u>2.12</u></td></tr>
  </tbody>
</table>

Tiny ranks **1st** in CER and **2nd** in cpSIM and UTMOS. Historical Ming-omni-tts retains lower CER and higher UTMOS.

## <a id="limitations"></a>Limitations

- **Speaker similarity.** Tiny ranks third on German SIM (0.791), but neither model reaches the top three in the other four new languages. French SIM is 0.675 for 0.5b and 0.733 for tiny; both also trail CosyVoice2-Yue on Cantonese SIM.
- **Several events in one line.** NVBench *Multi* works, but trails *Single*; stability with many tags per sentence is still improving.
- **Emotion from delivery alone.** When the words carry no emotional signal (CV3-Eval Text-Unrelated, and most of the hard set), accuracy drops well below the Text-Related half.
- **Pitch on tiny.** Pitch is the least accurate attribute for both models. Tiny's 78.70% ranks 2nd, 7.30 percentage points below 0.5b's 86.00%; the historical Ming-omni-tts-0.5B score is 91.33%.
- **Role-play voice design.** RP is the lowest voice design sub-score, ranking 4th for tiny (61.10%) and 5th for 0.5b (61.06%).
- **Korean on tiny.** Tiny's Korean CER (6.000%) ranks 6th, well behind 0.5b's 1.728% (3rd).
- **Podcast audio quality.** Tiny's UTMOS of 2.12 ranks 2nd, below ZipVoice-Dia's 2.24 and the historical Ming-omni-tts-0.5B score of 2.25.

## <a id="usage-disclaimer"></a>Usage Disclaimer

- Voice cloning and built-in character voices are provided for research and legitimate creative use. Do not use them to impersonate a real person without consent, to deceive, or for any illegal purpose.
- Label synthetic speech as synthetic where it could be mistaken for a real recording.
- The authors accept no liability for misuse. If you find abuse of this project, please report it to us.

## Acknowledgements

- [CAM++](https://modelscope.cn/models/iic/speech_campplus_sv_zh-cn_16k-common) for speaker embedding extraction
- [Ming-omni-tts](https://github.com/inclusionAI/Ming-omni-tts) for the audio tokenizer

## License

Released under the [MIT](LICENSE) license.
