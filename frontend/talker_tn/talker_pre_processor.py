# Copyright (c) Ant Group. All rights reserved.
import re
import unicodedata

from frontend.toolkit import normalize_text_kit, preprosess_text


class TalkerPreProcessor:
    """Remove presentation markup without deleting speech or numeric entities."""

    _width = str.maketrans({chr(i): chr(i - 0xFEE0) for i in range(0xFF01, 0xFF5F)})
    # Match the historical Chinese-space cleanup while preserving Latin word
    # boundaries, including accented letters, and spaces around numeric entities.
    _chinese_space = re.compile(
        r'(?<=[^A-Za-z0-9.\u00c0-\u024f]) +(?=[^A-Za-z0-9.\u00c0-\u024f])')

    def __call__(self, text):
        text = unicodedata.normalize('NFC', text).translate(self._width)
        text = text.replace('\u3000', ' ').replace('−', '-')
        text = preprosess_text(text)
        # Newlines are language boundaries in mixed speech. Collapse their
        # whitespace only after each clause has passed through the right TN.
        return '\n'.join(self._chinese_space.sub('', normalize_text_kit(line))
                         for line in text.splitlines())
