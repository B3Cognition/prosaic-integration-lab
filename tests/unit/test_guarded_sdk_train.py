"""Only the complete released guarded SDK family may enter ordinary Lab gates."""
import pytest

from lab_runner.gates import (
    COUNTS, required_modes, supports_consumer_blueprints,
    supports_context_assembly, supports_conversation,
)


VERSIONS = {
    'b3-prosaic': '0.5.0',
    'b3-prosaic-runtime': '0.9.14',
    'b3-prosaic-runtime-postgres': '0.3.0',
    'b3-prosaic-harness': '0.9.9',
    'b3-prosaic-harness-postgres': '0.4.1',
}


def manifest(changes=None):
    versions = VERSIONS | (changes or {})
    return {'artifacts': [
        {'distribution': name, 'version': version}
        for name, version in versions.items()
    ]}


def test_released_guarded_train_retains_every_existing_required_lane():
    train = manifest()
    assert supports_conversation(train)
    assert supports_context_assembly(train)
    assert supports_consumer_blueprints(train)
    assert required_modes(candidate=False, manifest=train) == tuple(COUNTS)


@pytest.mark.parametrize('changes', [
    {'b3-prosaic-runtime': '0.9.13'},
    {'b3-prosaic-harness': '0.9.8'},
])
@pytest.mark.parametrize('gate', [
    supports_conversation, supports_context_assembly, supports_consumer_blueprints,
])
def test_partial_guarded_sdk_upgrade_is_refused(changes, gate):
    with pytest.raises(ValueError, match='unsupported or incoherent'):
        gate(manifest(changes))


def test_prior_core050_profile_survives_the_guarded_release(monkeypatch):
    import hashlib
    import json
    from pathlib import Path
    from lab_runner.quality import sdk_provenance

    root = Path(__file__).resolve().parents[2]
    original = sdk_provenance.resource
    advanced = json.loads(original('sdk-provenance-public.json'))
    for item in advanced['artifacts']:
        if item['distribution'] in VERSIONS:
            item['version'] = VERSIONS[item['distribution']]
    advanced['manifestDigest'] = 'f' * 64
    monkeypatch.setattr(sdk_provenance, 'resource', lambda name:
        json.dumps(advanced) if name == 'sdk-provenance-public.json' else original(name))

    prior = {'b3-prosaic': '0.5.0', 'b3-prosaic-runtime': '0.9.13',
             'b3-prosaic-harness': '0.9.8'}
    profile = sdk_provenance.qualified_sdk(prior)
    assert profile == json.loads(original('sdk-provenance-pre-guarded.json'))
    archived = root / 'dependencies/releases-pre-guarded-2026-11-06.json'
    assert profile['manifestDigest'] == hashlib.sha256(archived.read_bytes()).hexdigest()
