"""Bounded canonical data shared by benchmark resources and evidence."""
import hashlib
import json
import math
import re


def integer(value, minimum=0, maximum=2**63-1):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError('invalid benchmark count')
    return value


def identifier(value):
    if type(value) is not str or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,95}', value):
        raise ValueError('invalid benchmark identity')
    return value


def sha(value):
    if type(value) is not str or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('invalid benchmark digest')
    return value


def _bounded(value, depth=0, nodes=None):
    nodes = [0] if nodes is None else nodes
    nodes[0] += 1
    if depth > 32 or nodes[0] > 65536:
        raise ValueError('benchmark data limit')
    if isinstance(value, dict):
        if any(type(k) is not str for k in value):
            raise ValueError('invalid benchmark keys')
        for child in value.values(): _bounded(child, depth+1, nodes)
    elif isinstance(value, list):
        for child in value: _bounded(child, depth+1, nodes)
    elif value is not None and type(value) not in (str, bool, int, float):
        raise ValueError('invalid benchmark data')
    elif type(value) is float and not math.isfinite(value):
        raise ValueError('invalid benchmark number')


def encode(value, maximum=4_194_304):
    try:
        _bounded(value)
        raw = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
        if len(raw) > maximum: raise ValueError('benchmark data limit')
        return raw
    except (RecursionError, OverflowError, UnicodeError, TypeError):
        raise ValueError('invalid benchmark data') from None


def decode(raw, maximum=4_194_304):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError('duplicate benchmark key')
            result[key] = value
        return result
    try:
        if len(raw.encode('utf-8') if isinstance(raw, str) else raw) > maximum:
            raise ValueError('benchmark data limit')
        value = json.loads(raw, object_pairs_hook=pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError('invalid number')))
        encode(value, maximum)
        return value
    except (RecursionError, UnicodeError, TypeError):
        raise ValueError('invalid benchmark JSON') from None


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()
