"""Lazy versioned public lightweight engine, independent of Castle memory."""

from .contracts import ReviewError


def load_engine(expected_identity=None):
    try:
        import castle_sue
    except ImportError:
        raise ReviewError('engine_unavailable') from None
    try:
        capabilities = castle_sue.capabilities()
    except (OSError, ValueError, KeyError, TypeError):
        raise ReviewError('engine_identity_mismatch') from None
    if capabilities.get('apiVersion') != 1 or capabilities.get('schemaVersion') != 2 or capabilities.get('policyVersion') != '2026-09-24':
        raise ReviewError('engine_identity_mismatch')
    if expected_identity is not None and capabilities['engineIdentity']['digest'] != expected_identity:
        raise ReviewError('engine_identity_mismatch')
    return castle_sue
