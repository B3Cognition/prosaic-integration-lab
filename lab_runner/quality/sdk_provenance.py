"""Closed packaged qualification profiles; never infer support from a version range."""
from .contracts import decode
from .suite import resource


def qualified_sdk(installed):
    names={'b3-prosaic','b3-prosaic-runtime','b3-prosaic-harness'}
    if set(installed)==names:
        for name in ('sdk-provenance-public.json','sdk-provenance-pre-unified.json','sdk-provenance.json'):
            profile=decode(resource(name))
            expected={a['distribution']:a['version'] for a in profile['artifacts'] if a['distribution'] in names}
            if expected==installed:return profile
    raise ValueError('unqualified SDK versions')
