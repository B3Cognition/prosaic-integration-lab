"""Explicit advisory consumer jobs; importing this package loads no model SDK."""

from .contracts import CastleJobError, JobSettings
from .session import CastleJobSession

__all__ = ['CastleJobError', 'JobSettings', 'CastleJobSession']
