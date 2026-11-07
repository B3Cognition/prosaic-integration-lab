"""New public SDK family admission must retain old, immutable qualification."""
import hashlib
import json
from pathlib import Path

import pytest
from lab_runner.gates import COUNTS, required_modes, supports_conversation, supports_context_assembly, supports_consumer_blueprints

ROOT = Path(__file__).resolve().parents[2]
VERSIONS = {'b3-prosaic': '0.5.0', 'b3-prosaic-runtime': '0.9.16',
    'b3-prosaic-harness': '0.9.11', 'b3-prosaic-runtime-postgres': '0.3.0',
    'b3-prosaic-harness-postgres': '0.4.1'}


def manifest(changes=None):
    return {'artifacts': [{'distribution': k, 'version': v} for k, v in (VERSIONS | (changes or {})).items()]}


@pytest.mark.parametrize('gate', [supports_conversation, supports_context_assembly, supports_consumer_blueprints])
def test_complete_header_validator_train_preserves_every_acceptance_lane(gate):
    assert gate(manifest())
    assert required_modes(candidate=False, manifest=manifest()) == tuple(COUNTS)


@pytest.mark.parametrize('changes', [{'b3-prosaic-runtime': '0.9.14'},
    {'b3-prosaic-harness': '0.9.10'}, {'b3-prosaic-runtime': '0.9.17'},
    {'b3-prosaic': '0.5.1'}, {'b3-prosaic-harness-postgres': '0.4.0'}])
def test_partial_or_unqualified_next_family_is_refused(changes):
    with pytest.raises(ValueError, match='unsupported or incoherent'):
        supports_conversation(manifest(changes))


@pytest.mark.parametrize('path,digest', [
    ('dependencies/releases-pre-cerebro-2026-11-07.json', '8801f698db7bee4680dc9c934dce4010138680d6a0f7e380f53c0b0ac826ecd7'),
    ('dependencies/releases-reasoning-pre-cerebro-2026-11-07.json', '8801f698db7bee4680dc9c934dce4010138680d6a0f7e380f53c0b0ac826ecd7'),
    ('lab_runner/quality/data/sdk-provenance-pre-cerebro.json', '32de46a1cb1de506285ce044960f5300d432f9e33d9e2bd3c4a9ab4c15c5dcd8'),
    ('lab_runner/memory/data/development-freeze-pre-cerebro.json', 'b0b5e6dd477196c12494a5abf5f94d2867e778195298c227d7b03fcaa2d93e94'),
    ('lab_runner/memory/data/evaluation-freeze-pre-cerebro.json', '019374249b83f585dee1a05ee1abc6ff189e5fb940a4a7de6b20a542cab456a4'),
])
def test_previous_release_snapshots_keep_their_exact_bytes(path, digest):
    assert (ROOT / path).is_file(), 'previous release must be archived before advancement'
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


def test_old_and_new_profiles_resolve_to_distinct_verified_manifests():
    from lab_runner.quality.sdk_provenance import qualified_sdk
    names = ('b3-prosaic', 'b3-prosaic-runtime', 'b3-prosaic-harness')
    new = qualified_sdk({k: VERSIONS[k] for k in names})
    old = qualified_sdk({'b3-prosaic': '0.5.0', 'b3-prosaic-runtime': '0.9.14', 'b3-prosaic-harness': '0.9.10'})
    assert old['manifestDigest'] == '8801f698db7bee4680dc9c934dce4010138680d6a0f7e380f53c0b0ac826ecd7'
    assert old == json.loads((ROOT / 'lab_runner/quality/data/sdk-provenance-pre-cerebro.json').read_bytes())
    active = ROOT / 'dependencies/releases.json'
    assert new['manifestDigest'] == hashlib.sha256(active.read_bytes()).hexdigest() != old['manifestDigest']
    expected = {item['distribution']: item for item in new['artifacts']}
    assert expected['b3-prosaic-runtime']['sha256'] == 'd2c569a1bfe233497518519f79f673023f8238ab25e053006b1e781d726db1af'
    assert expected['b3-prosaic-harness']['sha256'] == '2d9482cae429bd04587c0d58f111906019de9f068834f04727088815c70ca62f'
