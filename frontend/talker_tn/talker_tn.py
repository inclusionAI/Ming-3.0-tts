# Copyright (c) Ant Group. All rights reserved.
import os
import re

from .talker_pre_processor import TalkerPreProcessor
from .normalizer import Normalizer
from .text_rules import EntityNormalizer
from frontend.toolkit import (
    PARALINGUISTIC_TAG_RE, normalize_text_kit, protect_paralinguistic_tags,
)


class TalkerTN:
    def __init__(self):
        self.talker_pre_processor = TalkerPreProcessor()
        file_dir = os.path.dirname(os.path.realpath(__file__))
        self.re_contains_chinese = re.compile(r'[\u3400-\u9fff\U00020000-\U0003134f]')
        self.tn_zh = Normalizer(f'{file_dir}/zh_tn', ordertype='tn')
        self.tn_en = Normalizer(f'{file_dir}/en_tn', ordertype='en_tn')
        self.entities = EntityNormalizer(self.tn_zh, self.tn_en)
        self.protected_text = re.compile(
            r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|'
            r'(?<![A-Za-z0-9_.])[+-]?\.\d+|'
            r'(?<!\d)\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\d)|'
            r'(?:[A-Za-z]\.){2,}|'
            r'(?i:(?<![A-Za-z])(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc)\.)|'
            r'(?i:(?:[a-z0-9-]+\.)+[a-z]{2,})')

    def _clauses(self, text):
        """Find language boundaries without cutting numeric/technical entities."""
        protected = bytearray(len(text))
        for pattern in (self.entities.scanner, self.protected_text):
            for match in pattern.finditer(text):
                protected[match.start():match.end()] = b'\1' * len(match[0])
        start = 0
        for index, char in enumerate(text):
            if protected[index]:
                continue
            if char not in '。！？.!?;；,，:：“”"\n':
                continue
            # Decimal points and numeric ratios are not language boundaries.
            if (char in '.:' and index and index+1 < len(text)
                    and text[index-1].isdigit() and text[index+1].isdigit()):
                continue
            yield text[start:index+1]
            start = index+1
        if start < len(text):
            yield text[start:]

    def __call__(self, text, language=None):
        text = self.talker_pre_processor(text)
        if not text:
            return text
        fallback = language == 'zh' if language is not None else bool(self.re_contains_chinese.search(text))
        pieces = []
        for clause in self._clauses(text):
            lexical = PARALINGUISTIC_TAG_RE.sub('', clause)
            if self.re_contains_chinese.search(lexical):
                chinese = True
            else:
                # Unit/currency codes and technical IDs do not independently
                # turn a numeric-only clause into English.
                def language_label(match):
                    if match.lastgroup == 'serial':
                        label = self.entities.serial.fullmatch(match[0])[1]
                        if re.search(r'phone|mobile|postal|ZIP|postcode|call|contact|tel|fax', label, re.I):
                            return label
                    return ''
                ordinary = self.entities.scanner.sub(language_label, lexical)
                chinese = False if re.search(r'[A-Za-z\u00c0-\u024f]', ordinary) else fallback
            if any(c.isalnum() for c in lexical):
                fallback = chinese
            pieces.append(protect_paralinguistic_tags(
                clause, lambda part: self.entities.normalize(part, chinese)))
        return normalize_text_kit(''.join(pieces))

    def normalize(self, text, language=None):
        return self(text, language)
