"""Reasoning controls through public, installed Prosaic SDKs."""
import json
from importlib.metadata import version
from pathlib import Path

EFFORTS = ('none', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')
DATA = Path(__file__).parent / 'data'


def require_sdk():
    from packaging.version import Version
    import prosaic_runtime as sdk
    if not Version('0.9.12') <= Version(version('b3-prosaic-runtime')) < Version('0.10'):
        raise ValueError('reasoning lane requires installed Runtime 0.9.12..<0.10')
    if 'site-packages' not in Path(sdk.__file__).resolve().parts:
        raise ValueError('reasoning lane requires installed SDK wheels')
    return sdk


def load_artifact(effort):
    from prosaic import parse_artifact
    from prosaic_runtime import ProsaicArtifact
    if effort not in EFFORTS:
        raise ValueError('unknown neutral effort')
    identifier = f'subagents/{effort}.md'
    parsed = parse_artifact((DATA / identifier).read_text())
    return ProsaicArtifact.from_inspection({'id': identifier, 'type': 'subagent', **parsed})


def grade(text):
    """Strict JSON admission and answer correctness remain separate measurements."""
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('duplicate answer field')
            value[key] = item
        return value
    stripped = text.strip()
    candidate = stripped
    if stripped.startswith('```json\n') and stripped.endswith('\n```'):
        candidate = stripped[8:-4].strip()
    try:
        value = json.loads(candidate, object_pairs_hook=pairs)
    except (ValueError, TypeError, RecursionError):
        return False, False
    shape = type(value) is dict and set(value) == {'answer'} and type(value['answer']) is int
    return bool(shape and candidate == stripped), bool(shape and value['answer'] == 423)


def run_fixtures(*, provenance=None):
    from .fixtures import run
    return run(provenance=provenance)


def run_live(**options):
    from .live import run
    return run(**options)
