"""High-level API for Ming-3.0-tts-tiny multi-task inference."""

from __future__ import annotations

import os
import tempfile
from dataclasses import replace
from typing import Any, Optional, Sequence

from packaging.version import Version

from frontend.audio_processing import trim_trailing_silence
from frontend.text_processing import prepare_text, split_text

from .task_protocol import (
    FORMAL_CFG,
    FORMAL_FLOW_STEPS,
    FORMAL_SIGMA,
    FORMAL_TEMPERATURE,
    configure_release_environment,
    podcast_frame_bounds_to_decode_steps,
    podcast_generation_frame_bounds,
    resolve_generation_seed,
    resolve_task_request,
    validate_release_bundle,
    validate_release_engine,
)


REQUIRED_TRANSFORMERS = "4.46.3"


def resolve_model_dir(model_path: str) -> str:
    """Return a local checkpoint directory, downloading a Hub repo id."""

    if os.path.isdir(model_path):
        return model_path
    from huggingface_hub import snapshot_download

    return snapshot_download(repo_id=model_path)


def require_transformers() -> None:
    import transformers

    if Version(transformers.__version__) != Version(REQUIRED_TRANSFORMERS):
        raise RuntimeError(
            f"Ming-3.0-tts-tiny requires transformers=={REQUIRED_TRANSFORMERS}, "
            f"found {transformers.__version__}; install requirements-tiny.txt"
        )


class MingTinyTTS:
    """Load one Ming-3.0-tts-tiny checkpoint once and run every released task.

    Use :meth:`from_pretrained` rather than constructing the low-level engine
    directly.  Task-specific conditioning and prompt policies are resolved by
    this class so callers never need to pick a speaker mode or serialize
    structured-control JSON by hand.
    """

    def __init__(self, engine: Any, *, text_normalization: bool = True) -> None:
        self.engine = engine
        self.text_normalization = text_normalization
        self._normalizer = None

    @property
    def normalizer(self):
        """Share the Chinese/English TN without loading it for other languages."""
        if self._normalizer is None:
            try:
                from frontend.talker_tn.talker_tn import TalkerTN
            except ModuleNotFoundError as error:
                if error.name not in {"pynini", "inflect"}:
                    raise
                raise ImportError(
                    "Text normalization requires pynini and inflect. Install "
                    "the text frontend dependencies or set text_normalization=False "
                    "(--no_text_normalization on the command line)."
                ) from error
            self._normalizer = TalkerTN()
        return self._normalizer

    def _normalize_request(self, request):
        def normalize(text):
            # Keep loading lazy: dialect and non-zh/en requests never need TN.
            text = prepare_text(
                text, task=request.task, language=request.target_language,
                normalizer=(lambda value, language: self.normalizer.normalize(
                    value, language=language)) if self.text_normalization else None,
            )
            if not any(char.isalnum() for char in text):
                raise ValueError("text produced no synthesizable content after normalization")
            return text

        if request.task == "podcast":
            # The resolver has canonicalized the speaker labels and newlines.
            # Normalize only each turn's speech; role IDs and reference
            # transcripts are part of the model protocol.
            turns = []
            for line in request.text.splitlines():
                speaker, speech = line.split(":", 1)
                turns.append(f"{speaker}:{normalize(speech)}\n")
            text = "".join(turns)
        else:
            text = normalize(request.text)
        return replace(request, text=text)

    @property
    def sample_rate(self) -> int:
        return self.engine.sample_rate

    @classmethod
    def from_pretrained(
        cls,
        model_path: str,
        *,
        device: str = "cuda:0",
        dtype: str = "bf16",
        moe_backend: str = "auto",
        runtime_state_dtype: str = "auto",
        text_normalization: bool = True,
    ) -> "MingTinyTTS":
        """Load a local checkpoint directory or a Hugging Face repo id."""

        if dtype != "bf16":
            raise ValueError("Ming-3.0-tts-tiny public runtime requires dtype='bf16'")
        if moe_backend not in {"auto", "loop"}:
            raise ValueError(
                "Ming-3.0-tts-tiny public runtime requires moe_backend='auto' or 'loop'"
            )
        if runtime_state_dtype not in {"auto", "stable_fp32"}:
            raise ValueError(
                "Ming-3.0-tts-tiny public runtime requires runtime_state_dtype="
                "'auto' or 'stable_fp32'"
            )
        require_transformers()
        configure_release_environment()
        model_dir = resolve_model_dir(model_path)
        validate_release_bundle(model_dir)
        from .inference import MingTinyEngine

        engine = MingTinyEngine(
            model_dir,
            device=device,
            dtype=dtype,
            moe_backend=moe_backend,
            runtime_state_dtype=runtime_state_dtype,
        )
        validate_release_engine(engine)
        return cls(engine, text_normalization=text_normalization)

    def generate(
        self,
        *,
        task: str,
        text: str,
        output_path: Optional[str] = None,
        prompt_wav: Optional[str | Sequence[str]] = None,
        prompt_text: Optional[str | Sequence[str]] = None,
        target_language: Optional[str] = None,
        instruction: Optional[str] = None,
        dialect: Optional[str] = None,
        emotion: Optional[str] = None,
        style: Optional[str] = None,
        speed: Optional[str] = None,
        pitch: Optional[str] = None,
        volume: Optional[str] = None,
        ip: Optional[str] = None,
        seed: Optional[int] = None,
        cfg_scale: float = FORMAL_CFG,
        flow_steps: int = FORMAL_FLOW_STEPS,
        sigma: float = FORMAL_SIGMA,
        temperature: float = FORMAL_TEMPERATURE,
        min_decode_steps: Optional[int] = None,
        max_decode_steps: Optional[int] = None,
        stop_threshold: Optional[float] = None,
        min_generation_frames: Optional[int] = None,
        max_generation_frames: Optional[int] = None,
        log_every_n_steps: int = 0,
        max_length: int = 24,
        raw_text: bool = False,
        trim_silence: bool = True,
    ):
        """Generate speech using the same text frontend as the 0.5B API.

        Normalized text is grouped at punctuation with a target of max_length.
        Split Voice Design/Freeform uses the first fragment as the reference.
        Podcast keeps its multi-speaker dialogue in one generation. raw_text
        bypasses all text preparation and splitting.
        """
        request = resolve_task_request(
            task,
            text=text,
            prompt_wav=prompt_wav,
            prompt_text=prompt_text,
            target_language=target_language,
            instruction=instruction,
            dialect=dialect,
            emotion=emotion,
            style=style,
            speed=speed,
            pitch=pitch,
            volume=volume,
            ip=ip,
        )
        seed = resolve_generation_seed(request.task, seed)
        self._validate_reference_paths(request.prompt_wav)
        if not raw_text:
            request = self._normalize_request(request)
        fragments = ([request.text] if raw_text or request.task == "podcast"
                     else split_text(request.text, max_length))

        decode_alignment_override = None
        if request.task == "podcast":
            if min_decode_steps is not None or max_decode_steps is not None:
                raise ValueError(
                    "Podcast uses 12.5 Hz generation-frame bounds; do not "
                    "pass decode-step bounds directly"
                )
            if (min_generation_frames is None) != (max_generation_frames is None):
                raise ValueError(
                    "min_generation_frames and max_generation_frames must be paired"
                )
            if min_generation_frames is None:
                min_generation_frames, max_generation_frames = (
                    podcast_generation_frame_bounds(request.text)
                )
            geometry = getattr(self.engine, "prompt_geometry", None)
            if not isinstance(geometry, dict):
                raise RuntimeError("Podcast requires checkpoint prompt geometry")
            min_decode_steps, max_decode_steps = podcast_frame_bounds_to_decode_steps(
                min_generation_frames,
                max_generation_frames,
                int(geometry["flow_patch_size"]),
            )
            alignments = getattr(self.engine, "task_decode_alignment", None)
            decode_alignment_override = (
                alignments.get("podcast") if isinstance(alignments, dict) else None
            )
            if decode_alignment_override not in {"old_shift", "unshifted"}:
                raise RuntimeError(
                    "Podcast requires task_decode_alignment.podcast in config.json"
                )
        elif min_generation_frames is not None or max_generation_frames is not None:
            raise ValueError("generation-frame bounds are Podcast-only")

        outputs = []
        fragment_request = request
        reference_first = request.task in {"voice_design", "freeform"} and len(fragments) > 1
        # A float WAV preserves generated audio without PCM16 quantization.
        # The existing engine then applies the same resampling/alignment as
        # it does for a user-provided reference.
        with tempfile.TemporaryDirectory(prefix="ming-tiny-") as temporary_dir:
            for index, fragment in enumerate(fragments):
                fragment_request = replace(fragment_request, text=fragment)
                output = self.engine.synthesize(
                    fragment_request.text,
                    instruction=fragment_request.instruction,
                    prompt_wav=fragment_request.prompt_wav,
                    prompt_text=fragment_request.prompt_text,
                    target_language=fragment_request.target_language,
                    include_target_language=fragment_request.include_target_language,
                    conditioning=fragment_request.conditioning,
                    assistant_instruction=fragment_request.assistant_instruction,
                    allow_mixed_rml=fragment_request.allow_mixed_rml,
                    decode_alignment_override=decode_alignment_override,
                    seed=seed,
                    cfg_scale=cfg_scale,
                    flow_steps=flow_steps,
                    sigma=sigma,
                    temperature=temperature,
                    min_decode_steps=min_decode_steps,
                    max_decode_steps=max_decode_steps,
                    stop_threshold=stop_threshold,
                    log_every_n_steps=log_every_n_steps,
                )
                self._validate_output_contract(fragment_request, output)
                if trim_silence:
                    output.waveform = trim_trailing_silence(output.waveform, self.sample_rate)
                outputs.append(output)
                if reference_first and index == 0:
                    import torchaudio

                    reference_path = os.path.join(temporary_dir, "first_fragment.wav")
                    waveform = output.waveform.detach().float().cpu().reshape(1, -1)
                    torchaudio.save(reference_path, waveform, self.sample_rate,
                                    encoding="PCM_F", bits_per_sample=32)
                    fragment_request = replace(
                        request, prompt_wav=reference_path, prompt_text=fragment,
                        conditioning="prompt_latent",
                    )

        output = outputs[0]
        if len(outputs) > 1:
            import torch

            output = replace(
                output,
                waveform=torch.cat([part.waveform for part in outputs], dim=-1),
                latents=torch.cat([part.latents for part in outputs], dim=1),
                stop_probabilities=[value for part in outputs for value in part.stop_probabilities],
                stopped=all(part.stopped for part in outputs),
                prompt_token_count=sum(part.prompt_token_count for part in outputs),
                prompt_latent_steps=sum(part.prompt_latent_steps for part in outputs),
                segments=outputs,
            )
        if output_path is not None:
            from .inference import save_waveform

            save_waveform(output_path, output.waveform, self.engine.sample_rate)
        return output

    @staticmethod
    def _validate_reference_paths(
        prompt_wav: Optional[str | tuple[str, ...]],
    ) -> None:
        if prompt_wav is None:
            return
        paths = (prompt_wav,) if isinstance(prompt_wav, str) else prompt_wav
        for path in paths:
            if not os.path.isfile(path):
                raise FileNotFoundError(path)

    @staticmethod
    def _validate_output_contract(request, output) -> None:
        speaker_count = (
            len(request.prompt_wav) if request.conditioning == "multi_speaker" else None
        )
        expected = {
            "prompt_latent": (1, 1, True),
            "multi_speaker": (speaker_count, speaker_count, True),
            "speaker_only": (1, 1, False),
            "masked_speaker": (1, 0, False),
            "zero_speaker": (1, 0, False),
            "no_rml": (0, 0, False),
            "prompt_latent_no_rml": (0, 0, True),
        }
        slots, rows, needs_prompt_latent = expected[request.conditioning]
        actual_slots = getattr(output, "speaker_slot_count", None)
        actual_rows = getattr(output, "campplus_speaker_rows", None)
        actual_prompt_steps = getattr(output, "prompt_latent_steps", None)
        valid_slots = isinstance(actual_slots, int) and not isinstance(
            actual_slots, bool
        )
        valid_rows = isinstance(actual_rows, int) and not isinstance(actual_rows, bool)
        if (
            not valid_slots
            or not valid_rows
            or actual_slots != slots
            or actual_rows != rows
        ):
            raise RuntimeError(
                f"task {request.task} conditioning proof mismatch: "
                f"slots={actual_slots}/{slots}, CampPlus={actual_rows}/{rows}"
            )
        if (
            not isinstance(actual_prompt_steps, int)
            or isinstance(actual_prompt_steps, bool)
            or actual_prompt_steps < 0
        ):
            raise RuntimeError(
                f"task {request.task} returned invalid prompt latent provenance: "
                f"{actual_prompt_steps!r}"
            )
        if needs_prompt_latent and actual_prompt_steps <= 0:
            raise RuntimeError(
                f"task {request.task} produced no AudioVAE prompt continuation"
            )
        if not needs_prompt_latent and actual_prompt_steps != 0:
            raise RuntimeError(
                f"task {request.task} unexpectedly used AudioVAE prompt continuation"
            )
