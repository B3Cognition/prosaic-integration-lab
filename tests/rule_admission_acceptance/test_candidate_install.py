"""The lane runs only on the exact candidate SDK bytes, never the published Core 0.4.1."""

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CORE_COMMIT = '9d5a02f87469da373ba35e1e599b456b45459cd2'
RUNTIME_COMMIT = '65ba15d7e93ee058e22bececdb2e528cef2a474a'
QUALIFICATION = 'local-offline-candidate; not a published release'


def artifacts(name):
    return {item['distribution']: item for item in json.loads((ROOT / name).read_text())['artifacts']}


def test_manifest_pins_exact_commits_and_differs_from_the_published_core():
    candidate = artifacts('dependencies/rule-admission-candidate.json')
    published = artifacts('dependencies/releases-reasoning.json')
    core, runtime = candidate['b3-prosaic'], candidate['b3-prosaic-runtime']
    assert (core['source_commit'], runtime['source_commit']) == (CORE_COMMIT, RUNTIME_COMMIT)
    assert core['qualification'] == runtime['qualification'] == QUALIFICATION
    assert 'url' not in core and 'url' not in runtime
    # Same version and filename as the release that lacks parse_rules: only the bytes tell them apart.
    assert core['filename'] == published['b3-prosaic']['filename']
    assert core['sha256'] != published['b3-prosaic']['sha256']
    for name in ('b3-prosaic-runtime-postgres', 'b3-prosaic-harness', 'b3-prosaic-harness-postgres'):
        assert candidate[name] == published[name]


def test_installed_sdks_match_the_candidate_wheels():
    from prosaic_integration_lab.dependencies import cache_directory
    from prosaic_integration_lab.sdk_audit import audit

    manifest = ROOT / 'dependencies/rule-admission-candidate.json'
    audit(manifest, cache_directory(manifest, ROOT / '.cache/wheels'))


def test_a_core_without_parse_rules_is_refused(tmp_path):
    """A published Core 0.4.1 shadowing the candidate must stop the lane, not run it unenforced."""
    shadow = tmp_path / 'shadow' / 'prosaic'
    shadow.mkdir(parents=True)
    (shadow / '__init__.py').write_text('def inspect_artifact(*args, **kwargs):\n    raise AssertionError\n')
    code = (
        'import sys; sys.path.insert(0, sys.argv[1]); sys.path.insert(1, sys.argv[2])\n'
        'from lab_runner.rule_admission import require_sdk\n'
        'require_sdk()\n'
    )
    completed = subprocess.run(
        [sys.executable, '-I', '-c', code, str(shadow.parent), str(ROOT)],
        capture_output=True,
        text=True,
        timeout=60,
        env={key: value for key, value in os.environ.items() if key != 'PYTHONPATH'},
    )
    assert completed.returncode != 0
    assert 'parse_rules' in completed.stderr


def test_require_sdk_accepts_the_installed_candidate():
    from lab_runner.rule_admission import require_sdk

    sdk = require_sdk()
    assert 'rule_admission_v1' in sdk.ProsaicRuntime.capabilities


def test_candidate_builder_selects_exactly_core_and_runtime():
    sys.path.insert(0, str(ROOT / 'scripts'))
    try:
        from build_rule_admission_candidates import candidates
    finally:
        sys.path.remove(str(ROOT / 'scripts'))
    selected = candidates(ROOT / 'dependencies/rule-admission-candidate.json')
    assert {item['source_repository']: item['source_commit'] for item in selected} == {
        'B3Cognition/prosaic': CORE_COMMIT,
        'B3Cognition/prosaic-runtime': RUNTIME_COMMIT,
    }
