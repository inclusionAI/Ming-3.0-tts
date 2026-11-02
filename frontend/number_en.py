# Copyright (c) Ant Group. All rights reserved.
"""Compatibility entry point for the shared English text normalizer."""
from functools import lru_cache


@lru_cache(maxsize=1)
def _normalizer():
    # Keep Pynini optional until normalization is requested.
    from .talker_tn.talker_tn import TalkerTN
    return TalkerTN()


def normalize_numbers(text):
    return _normalizer().normalize(text, language='en')
