"""Frozen wall-clock profiles, independent of generation or token grants."""
from dataclasses import dataclass

from .storage import require

LEGACY='bounded-60s-v1'
LONG='bounded-120s-v1'
PROFILES=(LEGACY,LONG)
DEFAULT_ELAPSED=object()


@dataclass(frozen=True)
class Limits:
    call: int
    answer: int
    review: int
    sample: int


def limits(profile):
    require(type(profile) is str and profile in PROFILES,'unknown execution profile')
    return Limits(60,120,120,300) if profile==LEGACY else Limits(120,150,270,450)


def stage_seconds(value,profile,role):
    bounds=limits(profile)
    require(role in ('answer','review'),'unknown execution stage')
    maximum=getattr(bounds,role)
    if value is DEFAULT_ELAPSED:return maximum
    require(type(value) is int and 1<=value<=maximum,'bounded stage lifetime required')
    return value


def binding_version(version,profile):
    limits(profile)
    return version if profile==LEGACY else version+'-'+profile
