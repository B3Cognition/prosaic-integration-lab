"""Explicit qualified trains remain reproducible without accepting mixtures."""
import hashlib
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]


def test_archived_public_train_remains_selectable_after_active_release_advances(monkeypatch):
    from lab_runner.quality import sdk_provenance
    original=sdk_provenance.resource
    active=json.loads(original('sdk-provenance-public.json'))
    next(a for a in active['artifacts'] if a['distribution']=='b3-prosaic-runtime')['version']='0.9.8'
    active['manifestDigest']='f'*64
    monkeypatch.setattr(sdk_provenance,'resource',lambda name:
        json.dumps(active).encode() if name=='sdk-provenance-public.json' else original(name))
    installed={'b3-prosaic':'0.4.1','b3-prosaic-runtime':'0.9.7','b3-prosaic-harness':'0.9.4'}
    archived=sdk_provenance.qualified_sdk(installed)
    assert archived==json.loads(original('sdk-provenance-pre-unified.json'))
    assert archived['manifestDigest']==hashlib.sha256((ROOT/'dependencies/releases-pre-unified-2026-10-24.json').read_bytes()).hexdigest()


@pytest.mark.parametrize('runtime,manifest',[
    ('0.9.7','releases-pre-unified-2026-10-24.json'),('0.9.8','releases.json'),
    ('0.9.8+diagnostics.1','response-diagnostics-candidate.json')])
def test_qualified_public_and_private_trains_keep_distinct_manifest_bindings(runtime,manifest):
    from lab_runner.quality.sdk_provenance import qualified_sdk
    installed={'b3-prosaic':'0.4.1','b3-prosaic-runtime':runtime,'b3-prosaic-harness':'0.9.4'}
    profile=qualified_sdk(installed)
    assert profile['manifestDigest']==hashlib.sha256((ROOT/'dependencies'/manifest).read_bytes()).hexdigest()
    assert {a['distribution']:a['version'] for a in profile['artifacts'] if a['distribution'] in installed}==installed


@pytest.mark.parametrize('change',[{'b3-prosaic-runtime':'0.9.6'},
    {'b3-prosaic-harness':'0.9.0'},{'b3-prosaic-runtime':'0.9.9'},
    {'b3-prosaic':'0.4.2'},{'unexpected':'0.1'}])
def test_unqualified_sdk_mixtures_fail_closed(change):
    from lab_runner.quality.sdk_provenance import qualified_sdk
    installed={'b3-prosaic':'0.4.1','b3-prosaic-runtime':'0.9.7','b3-prosaic-harness':'0.9.4'}|change
    with pytest.raises(ValueError):qualified_sdk(installed)


def test_public_blueprint_train_admits_context_but_rejects_mixed_harness():
    from lab_runner.gates import supports_consumer_blueprints,supports_context_assembly
    data=json.loads((ROOT/'dependencies/continuation-candidate.json').read_bytes())
    assert supports_consumer_blueprints(data) and supports_context_assembly(data)
    next(a for a in data['artifacts'] if a['distribution']=='b3-prosaic-harness')['version']='0.9.0'
    with pytest.raises(ValueError):supports_context_assembly(data)
