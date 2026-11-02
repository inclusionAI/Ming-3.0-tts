# Copyright (c) Ant Group. All rights reserved.
"""Context-aware entities around the shipped Chinese/English FSTs.

An entity is normalized once, as a whole. Ordinary text is still handled by
the FST; rendered entities never pass through another numeric rewrite.
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata

import inflect

_DECIMAL = r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+'
_NUMBER = rf'[+-]?(?:\d+\s+\d+/\d+|\d+/\d+|(?:{_DECIMAL})(?:[eE][+-]?\d+)?)'
_BASE = rf'(?:{_NUMBER}|[A-Za-z])'
_OPERAND = rf'(?:√\s*)?{_BASE}(?:\^[+-]?\d+|[²³])?'
_OPERATOR = r'(?:>=|<=|[+*×÷=<>≠≤≥≈-])'
_EXPRESSION = rf'{_OPERAND}(?:\s*{_OPERATOR}\s*{_OPERAND})*'
_QUANTITY = rf'{_NUMBER}(?:\s*[-–—~～至到]\s*{_NUMBER})?'
_LEFT = r'(?<![A-Za-z0-9_.])'
_RIGHT = r'(?![A-Za-z0-9_]|\.\d)'
_DATE = r'(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}/\d{1,2}/\d{4})'
_TIME = r'\d{1,2}:\d{2}(?::\d{2})?'


def _alternatives(values):
    return '|'.join(re.escape(value) for value in sorted(values, key=len, reverse=True))


def _units():
    # Case matters: MW/mW, Mb/MB and Mbps/MBps are different units.
    base = {
        'm': ('米', 'meter'), 'g': ('克', 'gram'), 's': ('秒', 'second'),
        'W': ('瓦', 'watt'), 'V': ('伏特', 'volt'), 'A': ('安培', 'ampere'),
        'Hz': ('赫兹', 'hertz'), 'Pa': ('帕斯卡', 'pascal'),
        'J': ('焦耳', 'joule'), 'L': ('升', 'liter'), 'l': ('升', 'liter'),
        'mol': ('摩尔', 'mole'), 'Ω': ('欧姆', 'ohm'),
        'N': ('牛顿', 'newton'), 'F': ('法拉', 'farad'),
        'B': ('字节', 'byte'), 'b': ('比特', 'bit'),
    }
    prefixes = {'': ('', ''), 'k': ('千', 'kilo'), 'M': ('兆', 'mega'),
                'G': ('吉', 'giga'), 'T': ('太', 'tera'),
                'd': ('分', 'deci'), 'c': ('厘', 'centi'),
                'm': ('毫', 'milli'), 'μ': ('微', 'micro'),
                'µ': ('微', 'micro'), 'u': ('微', 'micro'), 'n': ('纳', 'nano'),
                'p': ('皮', 'pico'), 'f': ('飞', 'femto')}
    result = {}
    for suffix, (zh, en) in base.items():
        for prefix, (zh_prefix, en_prefix) in prefixes.items():
            result[prefix+suffix] = (zh_prefix+zh, en_prefix+en)
    result.update({
        'h': ('小时', 'hour'), 'hr': ('小时', 'hour'),
        'min': ('分钟', 'minute'), 'sec': ('秒', 'second'),
        'day': ('天', 'day'), 'days': ('天', 'day'),
        'ft': ('英尺', 'foot'), 'in': ('英寸', 'inch'),
        'lb': ('磅', 'pound'), 'lbs': ('磅', 'pound'),
        'mi': ('英里', 'mile'), 'oz': ('盎司', 'ounce'),
        '°C': ('摄氏度', 'degree Celsius'), '℃': ('摄氏度', 'degree Celsius'),
        '°F': ('华氏度', 'degree Fahrenheit'), '℉': ('华氏度', 'degree Fahrenheit'),
        'bit': ('比特', 'bit'), 'byte': ('字节', 'byte'),
        'KB': ('千字节', 'kilobyte'), 'KHz': ('千赫兹', 'kilohertz'),
        'kWh': ('千瓦时', 'kilowatt hour'), 'Wh': ('瓦时', 'watt hour'),
        'mAh': ('毫安时', 'milliampere hour'), 'Ah': ('安时', 'ampere hour'),
        'cal': ('卡路里', 'calorie'), 'kcal': ('千卡', 'kilocalorie'),
        'mmHg': ('毫米汞柱', 'millimeter of mercury'),
        'bpm': ('次每分', 'beat per minute'), 'rpm': ('转每分', 'revolution per minute'),
        'ha': ('公顷', 'hectare'), 't': ('吨', 'ton'),
        'dB': ('分贝', 'decibel'), 'rad': ('弧度', 'radian'),
        '㎡': ('平方米', 'square meter'), '㎥': ('立方米', 'cubic meter'),
    })
    for key in ['m', 'dm', 'cm', 'mm', 'km', 'ft', 'in', 'mi']:
        zh, en = result[key]
        for power, zh_power, en_power in [('2', '平方', 'square'), ('3', '立方', 'cubic')]:
            for notation in [power, '^'+power, '²' if power == '2' else '³']:
                result[key+notation] = (zh_power+zh, en_power+' '+en)
    return result


class EntityNormalizer:
    def __init__(self, zh_fst, en_fst):
        self.zh_fst, self.en_fst = zh_fst, en_fst
        self.inflect = inflect.engine()
        self.units = _units()
        cfg = json.loads(Path(__file__).with_name('talker_re.json').read_text(encoding='utf-8'))
        self.proper_nouns = {k: v for k, v in cfg['proper_noun'].items()
                             if re.search(r'[\u3400-\u9fff]', k)}
        self.currency_zh = dict(cfg['money'], **{'EUR': '欧元', 'HK$': '港元', 'US$': '美元'})
        self.currency_en = {
            '$': 'dollar', 'US$': 'dollar', 'USD': 'dollar',
            '€': 'euro', 'EUR': 'euro', '£': 'pound', '￡': 'pound', 'GBP': 'pound',
            '¥': 'yuan', '￥': 'yuan', 'CNY': 'yuan', 'RMB': 'yuan',
            'HK$': 'Hong Kong dollar', 'HKD': 'Hong Kong dollar', 'HK＄': 'Hong Kong dollar',
            'A$': 'Australian dollar', 'AUD': 'Australian dollar',
            'CAD$': 'Canadian dollar', 'CAD': 'Canadian dollar',
            'JPY': 'yen', 'J￥': 'yen', 'JP￥': 'yen', 'JPY￥': 'yen', 'JP¥': 'yen',
            'INR': 'rupee', '₹': 'rupee', 'RUB': 'ruble', '₽': 'ruble',
            'CHF': 'Swiss franc', 'SGD': 'Singapore dollar', 'KRW': 'won',
            'R$': 'Brazilian real', 'THB': 'baht', '฿': 'baht',
            'AED': 'UAE dirham', 'SAR': 'Saudi riyal', 'SEK': 'Swedish krona',
            'ARS': 'Argentine peso', 'TRY': 'Turkish lira',
        }
        self.scales = {
            '百': ('百', 'hundred'), '千': ('千', 'thousand'),
            '万': ('万', 'ten thousand'), '亿': ('亿', 'hundred million'),
            '兆': ('兆', 'trillion'),
            'thousand': ('千', 'thousand'), 'million': ('百万', 'million'),
            'billion': ('十亿', 'billion'), 'trillion': ('万亿', 'trillion'),
        }
        unit = '(?:'+_alternatives(self.units)+')'
        currency = '(?:'+_alternatives(self.currency_zh)+')'
        scale = '(?:'+_alternatives(self.scales)+')'
        # The same patterns are used by the scanner and entity parsers.
        self.money_before = re.compile(rf'([+-]?{currency})\s*({_QUANTITY})(?:\s*({scale}))?(?![A-Za-z0-9_]|\.\d)')
        self.money_after = re.compile(rf'({_QUANTITY})\s*({scale})?\s*({currency})(?![A-Za-z])')
        self.money_range = re.compile(self.money_before.pattern+r'\s*[-–—~～至到]\s*'+self.money_before.pattern)
        self.measure = re.compile(rf'({_QUANTITY})\s*({unit})(?:\s*/\s*({unit})|(ps))?(?![A-Za-z0-9_²³^])')
        labels = [k for k in cfg['serial_before'] if k not in {'AM', 'FM'}]
        labels += ['身份证号', '身份证号码', '手机号码', '电话号码', '号码',
                   '邮编', '账号', '编号', '订单号', '序列号', '尾号']
        label = '(?:'+_alternatives(labels)+r'|(?i:phone(?: number)?|telephone(?: number)?|mobile(?: number)?|ZIP(?: code)?|postal(?: code)?|postcode|call|contact|tel|fax))'
        self.serial = re.compile(rf'({label}\s*(?:(?i:is)|是|为)?\s*[:：#]?\s*)(\+?[\d(][\d ()-]*\d)'+_RIGHT)
        self.datetime = re.compile(rf'({_DATE})[T ]({_TIME})(Z|[+-]\d{{2}}:\d{{2}})?')
        patterns = [
            # Preserve URL paths and query parameters as one literal entity.
            # Leave trailing sentence punctuation outside the protected span.
            ('url', r"(?i:https?://|www\.)[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+%=,;]*[A-Za-z0-9\-_~/#\[\]@$&'()*+%=]"),
            ('formula', rf'\$\$\s*{_EXPRESSION}\s*\$\$|\$\s*{_EXPRESSION}\s*\$'),
            ('datetime', _LEFT+self.datetime.pattern+_RIGHT),
            ('date', _LEFT+_DATE+_RIGHT),
            ('year', _LEFT+rf'(?:{_DECIMAL})\s*年'),
            ('serial', r'(?<![A-Za-z0-9_])'+self.serial.pattern),
            ('proper_noun', '(?:'+_alternatives(self.proper_nouns)+')'+r'(?!\d)'),
            ('time', _LEFT+_TIME+rf'(?:\s*[-–—~～至到]\s*{_TIME})?'+r'(?![\d:])'),
            ('money_range', _LEFT+self.money_range.pattern),
            ('money_before', _LEFT+self.money_before.pattern),
            ('money_after', _LEFT+self.money_after.pattern),
            ('measure', _LEFT+self.measure.pattern),
            ('ratio', _LEFT+rf'{_QUANTITY}\s*[%‰‱]'),
            ('scientific', _LEFT+rf'[+-]?(?:{_DECIMAL})[eE][+-]?\d+'+_RIGHT),
            ('power', _LEFT+rf'(?:{_NUMBER}|[A-Za-z])(?:\^[+-]?\d+|[²³])'+_RIGHT),
            ('version', _LEFT+r'(?:[vV]\d+(?:\.\d+)+|\d+(?:\.\d+){2,})'+_RIGHT),
            ('math', _LEFT+rf'{_OPERAND}(?:\s*{_OPERATOR}\s*{_OPERAND})+'+_RIGHT),
            ('range', _LEFT+rf'{_NUMBER}\s*[-–—~～至到]\s*{_NUMBER}'+_RIGHT),
            ('programming', r'(?<![A-Za-z0-9_])(?:[Cc]\+\+|[Cc]#)(?![A-Za-z0-9_])'),
            ('ordinal', _LEFT+r'\d+(?:st|nd|rd|th)'+_RIGHT),
            ('unicode_number', r'[Ⅰ-Ⅻⅰ-ⅻ①-⑳㉑-㉟㊱-㊿⓪❶-❿⓫-⓴⓵-⓾]'),
            ('technical', r'(?<![A-Za-z0-9_])[A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)+(?![A-Za-z0-9_])'),
            ('identifier', r'(?<![A-Za-z0-9_])[A-Za-z]+\d+[A-Za-z0-9]*(?![A-Za-z0-9_])'),
            ('name', r'[\u3400-\u9fff]+(?:[·-][\u3400-\u9fff]+)+'),
            ('long_number', _LEFT+r'(?:\+\d{1,3}[ -]+)?[+-]?\d{5,}'+_RIGHT),
        ]
        # Inner parser captures must not shadow the scanner's named group.
        self.scanner = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in patterns))

    @staticmethod
    def _zh_integer(value):
        if value < 0:
            raise ValueError('integer magnitude must be nonnegative')
        if value == 0:
            return '零'
        digits, scales = '零一二三四五六七八九', ['', '万', '亿', '兆', '京', '垓']
        def block(n, leading):
            result, zero = '', False
            for power, unit in [(1000, '千'), (100, '百'), (10, '十'), (1, '')]:
                digit, n = divmod(n, power)
                if digit:
                    if zero:
                        result += '零'
                    if not (power == 10 and digit == 1 and not result and leading):
                        result += '两' if digit == 2 and power >= 100 else digits[digit]
                    result += unit
                    zero = False
                elif result and n:
                    zero = True
            return result
        groups = []
        while value:
            value, group = divmod(value, 10000)
            groups.append(group)
        if len(groups) > len(scales):
            return ''.join(digits[int(c)] for c in str(sum(g*10000**i for i,g in enumerate(groups))))
        result, zero = '', False
        for i in reversed(range(len(groups))):
            group = groups[i]
            if not group:
                zero = bool(result)
                continue
            if result and (zero or group < 1000):
                result += '零'
            result += block(group, not result)+scales[i]
            zero = False
        return result

    @lru_cache(maxsize=2048)
    def number(self, text, chinese):
        text = text.replace(',', '').strip()
        sign = ''
        if text.startswith(('-', '+')):
            if text[0] == '-':
                sign = '负' if chinese else 'negative '
            text = text[1:]
        if re.fullmatch(r'(?:\d+\s+)?\d+/\d+', text):
            if not chinese:
                return sign+self.en_fst.normalize(text)
            whole, _, fraction = text.rpartition(' ')
            numerator, denominator = fraction.split('/')
            return sign+(self._zh_integer(int(whole))+'又' if whole else '')+self._zh_integer(int(denominator))+'分之'+self._zh_integer(int(numerator))
        if re.search('[eE]', text):
            mantissa, exponent = re.split('[eE]', text)
            if chinese:
                return sign+self.number(mantissa, True)+'乘以十的'+self.number(exponent, True)+'次方'
            return sign+self.number(mantissa, False)+' times ten to the power of '+self.number(exponent, False)
        if not chinese:
            try:
                return sign+self.inflect.number_to_words(text, andword='').replace('-', ' ')
            except inflect.NumOutOfRangeError:
                # Preserve every digit of identifiers larger than the cardinal
                # vocabulary, rather than failing the whole synthesis request.
                digits = 'zero one two three four five six seven eight nine'.split()
                return sign+' '.join('point' if c == '.' else digits[int(c)] for c in text)
        integer, point, fraction = text.partition('.')
        return sign+self._zh_integer(int(integer or '0'))+('点'+''.join('零一二三四五六七八九'[int(c)] for c in fraction) if point else '')

    def quantity(self, text, chinese):
        pair = re.fullmatch(rf'({_NUMBER})\s*[-–—~～至到]\s*({_NUMBER})', text)
        if pair:
            return self.number(pair[1], chinese)+('至' if chinese else ' to ')+self.number(pair[2], chinese)
        return self.number(text, chinese)

    def _plural(self, word, quantity):
        if word.endswith('hertz') or word in {'yen', 'won', 'baht'}:
            return word
        try:
            singular = abs(Decimal(quantity.replace(',', ''))) == 1
        except InvalidOperation:
            singular = False
        if singular:
            return word
        if word.startswith('degree '):
            return 'degrees '+word[len('degree '):]
        if word.endswith(' per minute'):
            return self._plural(word[:-len(' per minute')], quantity)+' per minute'
        if word == 'millimeter of mercury':
            return 'millimeters of mercury'
        return self.inflect.plural_noun(word) or word

    def _money(self, match, chinese):
        parser = self.money_before if match.lastgroup == 'money_before' else self.money_after
        item = parser.fullmatch(match[0])
        symbol, value, scale = ((item[1], item[2], item[3]) if match.lastgroup == 'money_before'
                                else (item[3], item[1], item[2]))
        return self._money_value(symbol, value, scale, chinese, match[0])

    def _money_value(self, symbol, value, scale, chinese, original):
        if symbol.startswith(('-', '+')):
            if value.startswith(('-', '+')):
                return original  # Conflicting signs are not a valid numeric entity.
            value, symbol = symbol[0]+value, symbol[1:]
        unit = self.currency_zh[symbol] if chinese else self._plural(self.currency_en.get(symbol, symbol), '2' if scale else value)
        magnitude = self.scales[scale][0 if chinese else 1] if scale else ''
        return self.quantity(value, chinese)+(('' if chinese else ' ')+magnitude if magnitude else '')+('' if chinese else ' ')+unit

    def _measure(self, match, chinese):
        item = self.measure.fullmatch(match[0])
        value, unit, denominator = item[1], item[2], item[3]
        if item[4]:
            denominator = 's'
        zh, en = self.units[unit]
        if chinese:
            return ('每'+self.units[denominator][0] if denominator else '')+self.quantity(value, True)+zh
        return self.quantity(value, False)+' '+self._plural(en, value)+(' per '+self.units[denominator][1] if denominator else '')

    def _year(self, match, text, chinese):
        if not chinese:
            return self.en_fst.normalize(match[0])
        value = match[0][:-1].strip()
        before = text[:match.start()]
        after = text[match.end():]
        # Use only the local phrase: a duration cue in an earlier sentence
        # must not turn a later calendar year into a quantity.
        before = re.split(r'[。！？.!?;；,，:：\n]', before)[-1].rstrip()
        after = after.lstrip()
        digitwise = lambda: ''.join('零一二三四五六七八九'[int(c)] for c in value)+'年'
        if re.search(r'[,.]', value):
            return self.number(value, True)+'年'
        # A complete date or explicit era is stronger than a duration verb:
        # "经历了2000年10月的风暴" still refers to October of that year.
        if (re.match(r'\d{1,2}\s*月', after)
                or re.search(r'(?:公元前?|西元前?|西历|年份(?:是|为|为：|是：)?)\s*$', before)
                or re.match(r'(?:的)?(?:那[场次]|这[场次]|发生的|举行的|出版的|发行的|上映的)', after)
                or after.startswith('代')):
            return digitwise()
        modifiers = r'(?:了|有|达|约|近|将近|超过|不足|整整|至少|不满|不到|长达|大约|大概|差不多|已经|的|这|那|最近)'
        duration = (r'经历|历经|持续|历时|耗时|花费|花了|用时|用了|等待|等了|工作了|'
                    r'生活了|居住了|活了|存活了|经过|度过|过了|走过|跨越|穿越|'
                    r'时隔|相隔|间隔|已有|已经有|有|拥有|距今|至今已有|长达|为期|'
                    r'过去|未来|近|最近|约|大约|超过|不足|不到|至少|整整')
        if re.search(rf'(?:{duration})(?:{modifiers})*\s*$', before):
            return self.number(value, True)+'年'
        # Explicit calendar anchors take precedence over bare "前/后":
        # "在2000年后" and "2000年后" can refer to different things.
        if (re.search(r'(?:在|于|从|自|到|至|截至|直到|回到|到了|生于|建于)\s*$', before)
                or re.match(r'(?:以来|起|开始|之[前后]|初|底|末|度|发生|举行|出版|发行|上映|毕业|出生|成立)', after)):
            return digitwise()
        if (re.match(r'(?:前|后|来|间|内|以上|以下|左右|之久|有余|整|半|多)', after)
                or re.match(r'(?:的)?(?:历史(?!事件|背景|记录|记载|资料|文献|人物)|岁月|时光|光阴|时间|工龄|经验|寿命|树龄|时长)', after)):
            return self.number(value, True)+'年'
        # With no disambiguating context, retain the existing four-digit
        # calendar-year convention rather than guessing at the semantics.
        return digitwise() if len(value) == 4 else self.number(value, True)+'年'

    def _date(self, text, chinese):
        parts = re.split('[-/.]', text)
        if len(parts[0]) == 4:
            year, month, day = map(int, parts)
        else:
            month, day, year = map(int, parts)
            if month > 12:
                month, day = day, month
        try:
            date(year, month, day)
        except ValueError:
            return text
        if chinese:
            return ''.join('零一二三四五六七八九'[int(c)] for c in str(year))+'年'+self.number(str(month), True)+'月'+self.number(str(day), True)+'日'
        month_name = ['January','February','March','April','May','June','July','August','September','October','November','December'][month-1]
        ordinal = self.en_fst.normalize(self.inflect.ordinal(day))
        return month_name+' '+ordinal+', '+self.number(str(year), False)

    def _serial(self, text, chinese):
        label, digits = self.serial.fullmatch(text).groups()
        spoken_digits = ('零幺二三四五六七八九' if re.search(r'身份证|电话|手机', label)
                         else '零一二三四五六七八九') if chinese else 'zero one two three four five six seven eight nine'.split()
        values = [spoken_digits[int(c)] if c.isdigit() else ('加' if chinese else 'plus')
                  for c in digits if c.isdigit() or c == '+']
        fst = self.zh_fst if chinese else self.en_fst
        return fst.normalize(label).rstrip()+('' if chinese else ' ')+('' if chinese else ' ').join(values)

    def _datetime(self, text, chinese):
        day, clock, zone = self.datetime.fullmatch(text).groups()
        fst = self.zh_fst if chinese else self.en_fst
        value = self._date(day, chinese)+('' if chinese else ' at ')+fst.normalize(clock)
        if zone:
            value += '协调世界时' if chinese else ' UTC'
            if zone != 'Z':
                hour, minute = zone[1:].split(':')
                value += ('加' if zone[0] == '+' else '减') if chinese else (' plus ' if zone[0] == '+' else ' minus ')
                value += self.number(hour, chinese)+('小时' if chinese else ' '+self._plural('hour', hour))
                if int(minute):
                    value += ('' if chinese else ' ')+self.number(minute, chinese)+('分钟' if chinese else ' '+self._plural('minute', minute))
        return value

    def _version(self, text, chinese, context):
        prefix = text[:1] if text[:1] in 'vV' else ''
        parts = text[len(prefix):].split('.')
        if (not prefix and len(parts) == 4 and all(int(n) <= 255 for n in parts)
                and not re.search(r'(?:version|版本)\s*(?:is|为|是)?\s*$', context, re.I)):
            return ('点'.join(''.join('零幺二三四五六七八九'[int(c)] for c in n) for n in parts)
                    if chinese else ' dot '.join(self.number(n, False) for n in parts))
        return prefix+(' ' if prefix and not chinese else '')+('点' if chinese else ' point ').join(self.number(n, chinese) for n in parts)

    def _operand(self, text, chinese):
        if text.startswith('√'):
            return ('根号' if chinese else 'square root of ')+self._operand(text[1:].strip(), chinese)
        power = re.fullmatch(rf'({_BASE})(?:\^([+-]?\d+)|([²³]))', text)
        if power:
            exponent = power[2] or power[3].translate(str.maketrans({'²':'2', '³':'3'}))
            return self._operand(power[1], chinese)+('的' if chinese else ' to the power of ')+self.number(exponent, chinese)+('次方' if chinese else '')
        return self.number(text, chinese) if re.fullmatch(_NUMBER, text) else text

    def _math(self, text, chinese, *, formula=False):
        operators = {'+':'加', '-':'减', '*':'乘', '×':'乘', '÷':'除以', '=':'等于',
                     '>':'大于', '<':'小于', '>=':'大于等于', '<=':'小于等于',
                     '≠':'不等于', '≤':'小于等于', '≥':'大于等于', '≈':'约等于'} if chinese else {
                     '+':'plus', '-':'minus', '*':'times', '×':'times', '÷':'divided by', '=':'equals',
                     '>':'greater than', '<':'less than', '>=':'greater than or equal to', '<=':'less than or equal to',
                     '≠':'not equal to', '≤':'less than or equal to', '≥':'greater than or equal to', '≈':'approximately equals'}
        first = re.match(_OPERAND, text)
        tokens = [first[0]]
        offset = first.end()
        while offset < len(text):
            pair = re.match(rf'\s*({_OPERATOR})\s*({_OPERAND})', text[offset:])
            tokens.extend([pair[1], pair[2]])
            offset += pair.end()
        # A bare numeric hyphen is a range; an equation supplies subtraction context.
        if not formula and len(tokens) == 3 and tokens[1] == '-' and all(re.fullmatch(_NUMBER, t) for t in tokens[::2]):
            return self.quantity(text, chinese)
        if not formula and len(tokens) == 3 and tokens[1] == '-':
            return text  # An isolated F-5/T-800 is also a technical identifier.
        spoken = [self._operand(token, chinese) if i % 2 == 0 else operators[token]
                  for i, token in enumerate(tokens)]
        return ('' if chinese else ' ').join(spoken)

    def normalize(self, text, chinese):
        fst = self.zh_fst if chinese else self.en_fst
        def ordinary(part):
            if not part.strip():
                return part
            # Preserve meaningful symbols which the FST's word grammar cannot expand.
            symbols = {'±': '正负', '√': '根号', 'π': '派', '≠': '不等于', '≈': '约等于'} if chinese else {'±':'plus or minus', '√':'square root of', 'π':'pi', '≠':'not equal to', '≈':'approximately equals'}
            for symbol, spoken in symbols.items():
                part = part.replace(symbol, spoken if chinese else ' '+spoken+' ')
            value = fst.normalize(part)
            return (' ' if part[:1].isspace() else '')+value.strip()+(' ' if part[-1:].isspace() else '')
        pieces, offset = [], 0
        for match in self.scanner.finditer(text):
            pieces.append(ordinary(text[offset:match.start()]))
            kind, value = match.lastgroup, match[0]
            if kind == 'formula':
                value = self._math(value.strip('$').strip(), chinese, formula=True)
            elif kind == 'money_range':
                a, b, c, d, e, f = self.money_range.fullmatch(value).groups()
                value = self._money_value(a, b, c, chinese, value)+('至' if chinese else ' to ')+self._money_value(d, e, f, chinese, value)
            elif kind.startswith('money_'):
                value = self._money(match, chinese)
            elif kind == 'measure':
                value = self._measure(match, chinese)
            elif kind == 'ratio':
                quantity, symbol = value[:-1].strip(), value[-1]
                value = ({'%':'百分之', '‰':'千分之', '‱':'万分之'}[symbol]+self.quantity(quantity, True) if chinese else self.quantity(quantity, False)+' '+{'%':'percent','‰':'per thousand','‱':'per ten thousand'}[symbol])
            elif kind == 'date':
                value = self._date(value, chinese)
            elif kind == 'year':
                value = self._year(match, text, chinese)
            elif kind == 'datetime':
                value = self._datetime(value, chinese)
            elif kind == 'serial':
                value = self._serial(value, chinese)
            elif kind == 'proper_noun':
                value = self.proper_nouns[value] if chinese else fst.normalize(value)
            elif kind == 'time':
                times = re.split(r'\s*[-–—~～至到]\s*', value)
                value = ('至' if chinese else ' to ').join(fst.normalize(t) for t in times)
            elif kind in {'scientific', 'range'}:
                value = self.quantity(value, chinese)
            elif kind == 'math':
                value = self._math(value, chinese)
            elif kind == 'power':
                value = self._operand(value, chinese)
            elif kind == 'version':
                value = self._version(value, chinese, text[max(0, match.start()-20):match.start()])
            elif kind == 'programming':
                value = {'C++': 'C加加' if chinese else 'C plus plus', 'C#': 'C井号' if chinese else 'C sharp'}[value.upper()]
            elif kind == 'ordinal':
                value = self.en_fst.normalize(value)
            elif kind == 'unicode_number':
                value = self.number(str(int(unicodedata.numeric(value))), chinese)
            elif kind == 'long_number':
                context = text[max(0,match.start()-50):match.start()]
                if (re.search(r'(?:phone(?: number)?|telephone(?: number)?|mobile(?: number)?|ZIP(?: code)?|postal(?: code)?|postcode|电话|手机(?:号)?|号码|邮编|账号|编号|订单号|序列号)\s*(?:is|为|是)?\s*[:：#]?\s*$', context, re.I)
                        or re.fullmatch(r'\+\d{1,3}[ -]+\d{5,}', value)):
                    digit_names = '零幺二三四五六七八九' if re.search(r'电话|手机', context) else '零一二三四五六七八九'
                    digits = ''.join(digit_names[int(c)] if c.isdigit() else c for c in value) if chinese else ' '.join('zero one two three four five six seven eight nine'.split()[int(c)] if c.isdigit() else ('plus' if c == '+' else '') for c in value)
                    value = digits.replace('+', '加')
                else:
                    value = (fst.normalize(value) if chinese and re.fullmatch(r'1[3-9]\d{9}', value)
                             else self.number(value, chinese))
            # URLs, names and technical identifiers retain their original characters.
            pieces.append(value)
            offset = match.end()
        pieces.append(ordinary(text[offset:]))
        return ''.join(pieces)
