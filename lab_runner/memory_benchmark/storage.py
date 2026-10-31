"""Bounded canonical private evidence files; no inference or source discovery."""
import hashlib
import json
import os
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(',', ':')).encode('utf-8')


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else encoded(value)).hexdigest()


def decode(raw, maximum=16_777_216):
    require(type(raw) is bytes and len(raw) <= maximum, 'JSON byte limit')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
            parse_constant=lambda _: require(False, 'nonfinite JSON'))
        encoded(value)
        return value
    except (UnicodeError, TypeError, RecursionError) as error:
        raise ValueError('invalid finite Unicode JSON') from error


def read(path, maximum=16_777_216):
    path = Path(path)
    require(not path.is_symlink() and path.is_file() and path.stat().st_size <= maximum,
            'bounded regular file required')
    with path.open('rb') as stream:
        return decode(stream.read(maximum+1), maximum)


def exclusive(path, value):
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink denied')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(encoded(value)); stream.flush(); os.fsync(stream.fileno())


def identifier(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}', value), 'invalid identifier')
    return value


def shape(value, keys):
    require(type(value) is dict and set(value) == set(keys), 'invalid closed object')


def code_binding():
    root = Path(__file__).parent
    return {p.name: sha(p.read_bytes()) for p in sorted(root.glob('*.py'))}
