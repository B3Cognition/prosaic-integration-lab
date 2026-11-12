"""The current lane uses released SDK bytes; historical candidates remain reproducible."""

import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
CORE_COMMIT = '67b3807281ed0cdfd345fff84c56b236ec82cfb1'
HISTORICAL_RUNTIME_COMMIT = '498ffc78c6b215bc425847c8fbc645c20e9b2d05'
HISTORICAL_HARNESS_COMMIT = '5b3f0f2e2899b29c4f2b457875af2cb522140c03'
QUALIFICATION = 'local-offline-candidate; not a published release'


def artifacts(name):
    return {item['distribution']: item for item in json.loads((ROOT / name).read_text())['artifacts']}


def test_current_manifest_pins_the_exact_released_guarded_train():
    from lab_runner.rule_admission import MANIFEST

    assert MANIFEST == 'dependencies/releases.json'
    released = artifacts(MANIFEST)
    assert {(name, item['version'], item['source_commit'], item['sha256'])
            for name, item in released.items()} == {
        ('b3-prosaic', '0.5.0', CORE_COMMIT,
         'e858a853595746c6930fbe062e84bd8ece1a366aa3b126f2fe11bfb7cb2ceb81'),
        ('b3-prosaic-runtime', '0.9.23', '48c10ac9aeb18bd06f53015df0624b35d5254646',
         '5caab59f6d0ffd14299ee0840dd5f9b58b4e4f4a1b724ff6e3e2fa1699f08fd8'),
        ('b3-prosaic-harness', '0.9.17', '5cf6b08e3f181bfb368b24afbe1eadf9911b4504',
         'c65c932798cc7e52e7e9659e43e72cc5f2e48feee9b889b5593e80e9e241c0fb'),
        ('b3-prosaic-runtime-postgres', '0.3.0', 'a59621c5f30d766d1217b37df777d3876075dc34',
         '5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca'),
        ('b3-prosaic-harness-postgres', '0.4.5', '5cf6b08e3f181bfb368b24afbe1eadf9911b4504',
         '6a64d3276850582fbf24d6a6698d83bd0adb861bd9189f096733a3f1d28b03cc'),
    }
    for item in released.values():
        assert 'qualification' not in item
        url = urlsplit(item['url'])
        assert url.scheme == 'https' and url.netloc == 'files.pythonhosted.org'
        assert not url.query and not url.fragment and url.path.endswith('/' + item['filename'])
        assert item['filename'] == item['distribution'].replace('-', '_') + '-' + item['version'] + '-py3-none-any.whl'
    assert released == artifacts('dependencies/releases-reasoning.json')


def test_historical_manifest_retains_the_exact_candidate_bytes():
    candidate = artifacts('dependencies/rule-admission-candidate.json')
    published = artifacts('dependencies/releases-reasoning-pre-core050-2026-11-05.json')
    core, runtime = candidate['b3-prosaic'], candidate['b3-prosaic-runtime']
    assert (core['source_commit'], runtime['source_commit']) == (CORE_COMMIT, HISTORICAL_RUNTIME_COMMIT)
    harness = candidate['b3-prosaic-harness']
    assert harness['source_commit'] == HISTORICAL_HARNESS_COMMIT
    assert runtime['qualification'] == harness['qualification'] == QUALIFICATION
    assert 'qualification' not in core and core['version'] == '0.5.0' and 'url' in core
    assert 'url' not in runtime and 'url' not in harness
    assert core['filename'] != published['b3-prosaic']['filename']
    assert core['sha256'] != published['b3-prosaic']['sha256']
    for name in ('b3-prosaic-runtime-postgres', 'b3-prosaic-harness-postgres'):
        assert candidate[name] == published[name]


def test_installed_sdks_match_the_released_wheels():
    from prosaic_integration_lab.dependencies import cache_directory
    from prosaic_integration_lab.sdk_audit import audit

    manifest = ROOT / 'dependencies/releases.json'
    audit(manifest, cache_directory(manifest, ROOT / '.cache/wheels'))


def test_a_core_without_parse_rules_is_refused(tmp_path):
    """A Core without rule parsing must stop the lane, not run it unenforced."""
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


def test_require_sdk_accepts_the_installed_release():
    from lab_runner.rule_admission import require_sdk

    sdk = require_sdk()
    assert 'rule_admission_v1' in sdk.ProsaicRuntime.capabilities


def test_candidate_builder_selects_exactly_runtime_and_harness():
    sys.path.insert(0, str(ROOT / 'scripts'))
    try:
        from build_rule_admission_candidates import candidates
    finally:
        sys.path.remove(str(ROOT / 'scripts'))
    selected = candidates(ROOT / 'dependencies/rule-admission-candidate.json')
    assert {item['source_repository']: item['source_commit'] for item in selected} == {
        'B3Cognition/prosaic-runtime': HISTORICAL_RUNTIME_COMMIT,
        'B3Cognition/prosaic-harness': HISTORICAL_HARNESS_COMMIT,
    }
