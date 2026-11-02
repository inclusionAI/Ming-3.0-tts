"""Shared text preparation for the dense and Tiny inference APIs."""

from frontend.text_segment_cut import cut_text_by_semantic_length
from frontend.toolkit import add_period, normalize_text_kit, preprosess_text
from tts_tasks import preserve_multilingual_text


def prepare_text(text, *, task, language, normalizer=None):
    """Clean markup, optionally normalize entities, then finish punctuation."""
    text = preprosess_text(text).strip()
    preserve = (preserve_multilingual_text(language)
                or str(task).strip().upper() == "DIALECT")
    if normalizer is not None and not preserve:
        language = {"zh": "zh", "zh-cn": "zh", "chinese": "zh",
                    "en": "en", "english": "en"}.get(str(language).strip().lower())
        text = normalize_text_kit(normalizer(text, language))
    if not preserve:
        text = add_period(text)
    return text


def split_text(text, max_length=24):
    """Group whole clauses at punctuation; never force a cut inside a clause."""
    if not isinstance(max_length, int) or isinstance(max_length, bool) or max_length < 1:
        raise ValueError("max_length must be a positive integer")
    fragments = [fragment for fragment in
                 cut_text_by_semantic_length(text, max_length)["fragments"]
                 if fragment.strip()]
    if not fragments or not any(ch.isalnum() for part in fragments for ch in part):
        raise ValueError(f"text produced no synthesizable fragments: {text!r}")
    return fragments
