"""Tiny synthetic, deterministic tasks; never execute model-written Python."""
import json
from pathlib import Path
import stat

CASE_IDS = ('facts', 'repair')
REPAIRED = 'def add(a, b):\n    return a + b\n'
INVENTORY = json.dumps({'counts': [3, 4, 5], 'blockingIssue': True})
SOURCE = Path(__file__).resolve().parent / 'data'


def prepare_case(case_id, workspace):
    from prosaic_runtime import ProsaicArtifact
    from prosaic import parse_artifact
    workspace = Path(workspace)
    if case_id == 'facts':
        (workspace / 'inventory.json').write_text(INVENTORY)
    elif case_id == 'repair':
        (workspace / 'calculator.py').write_text('def add(a, b):\n    return a - b\n')
    else:
        raise ValueError('unknown native benchmark case')
    artifact_id = 'subagents/' + case_id + '.md'
    parsed = parse_artifact((SOURCE / artifact_id).read_text())
    return ProsaicArtifact.from_inspection({'id': artifact_id, 'type': 'subagent', **parsed})


def _json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate response field')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=pairs)


def grade(case_id, workspace, stdout):
    try:
        root = Path(workspace)
        expected = 'inventory.json' if case_id == 'facts' else 'calculator.py'
        if {path.name for path in root.iterdir()} != {expected}:
            return False
        source = root / expected
        if source.is_symlink() or not stat.S_ISREG(source.stat().st_mode) or source.stat().st_size > 256:
            return False
        if case_id == 'facts':
            if source.read_bytes() != INVENTORY.encode():
                return False
            # Reject booleans masquerading as integer answers.
            answer = _json(stdout)
            return (type(answer) is dict and set(answer) == {'total', 'decision'}
                    and type(answer['total']) is int and answer['total'] == 12
                    and answer['decision'] == 'BLOCK')
        if case_id == 'repair':
            path = root / 'calculator.py'
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > 256:
                return False
            return path.read_bytes() == REPAIRED.encode()
        raise ValueError('unknown native benchmark case')
    except (OSError, ValueError, TypeError, RecursionError):
        return False
