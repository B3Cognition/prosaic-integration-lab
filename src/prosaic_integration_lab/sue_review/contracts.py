"""Bounded immutable host policy and deterministic JSON identities."""

from dataclasses import dataclass, fields
import hashlib
import json
import re


class ReviewError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def encoded(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise ReviewError('invalid_json') from None


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def text_digest(text):
    try:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    except (AttributeError, UnicodeError):
        raise ReviewError('invalid_text') from None


def _shape(value, depth=0, count=None):
    count = [0] if count is None else count
    count[0] += 1
    if depth > 64 or count[0] > 65536:
        raise ReviewError('json_limit')
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ReviewError('invalid_json')
            _shape(item, depth+1, count)
    elif type(value) is list:
        for item in value:
            _shape(item, depth+1, count)
    elif value is not None and type(value) not in (str, bool, int, float):
        raise ReviewError('invalid_json')


def own(value, maximum=131072):
    _shape(value)
    data = encoded(value)
    if len(data) > maximum:
        raise ReviewError('input_limit')
    return json.loads(data)


def decode(raw, maximum=16384):
    if type(raw) is not str:
        raise ReviewError('invalid_json')
    try:
        if len(raw.encode('utf-8')) > maximum:
            raise ReviewError('output_limit')
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise ReviewError('duplicate_json_key')
                result[key] = value
            return result
        def invalid(_):
            raise ReviewError('invalid_json')
        return own(json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid), maximum)
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        if isinstance(error, ReviewError):
            raise
        raise ReviewError('invalid_json') from None


def reference(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', value) is not None


@dataclass(frozen=True)
class ReviewSettings:
    enabled: bool = False
    lifetime_s: int = 86400
    max_turns: int = 14
    max_calls: int = 28
    max_tokens: int = 65536
    timeout_s: int = 60
    engine_identity: str | None = None

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ReviewError('invalid_review_settings')
        for name, ceiling in (('lifetime_s',604800),('max_turns',14),('max_calls',28),('max_tokens',65536),('timeout_s',60)):
            number = getattr(self, name)
            if type(number) is not int or not 1 <= number <= ceiling:
                raise ReviewError('invalid_review_limit')
        if self.engine_identity is not None and (type(self.engine_identity) is not str or re.fullmatch('[0-9a-f]{64}',self.engine_identity) is None):
            raise ReviewError('invalid_engine_identity')

    @classmethod
    def from_mapping(cls, value):
        if value is None:
            return cls()
        if type(value) is not dict or type(value.get('enabled')) is not bool:
            raise ReviewError('invalid_review_settings')
        if not value['enabled'] and set(value) != {'enabled'}:
            raise ReviewError('disabled_review_settings')
        if set(value) - {f.name for f in fields(cls)}:
            raise ReviewError('invalid_review_settings')
        return cls(**value)
