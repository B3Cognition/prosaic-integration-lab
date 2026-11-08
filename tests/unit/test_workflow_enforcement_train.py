"""Exact V2 SDK train and immutable pre-upgrade selection."""
import hashlib
import json
from pathlib import Path

import pytest
from lab_runner.gates import supports_conversation, supports_context_assembly, supports_consumer_blueprints

ROOT=Path(__file__).resolve().parents[2]
VERSIONS={'b3-prosaic':'0.5.0','b3-prosaic-runtime':'0.9.16','b3-prosaic-harness':'0.9.12',
    'b3-prosaic-runtime-postgres':'0.3.0','b3-prosaic-harness-postgres':'0.4.1'}


def manifest(changes=None):
    return {'artifacts':[{'distribution':k,'version':v} for k,v in (VERSIONS | (changes or {})).items()]}


@pytest.mark.parametrize('gate',[supports_conversation,supports_context_assembly,supports_consumer_blueprints])
def test_complete_workflow_enforcement_train_keeps_all_required_lanes(gate):
    assert gate(manifest())


@pytest.mark.parametrize('changes',[{'b3-prosaic-runtime':'0.9.15'},{'b3-prosaic-runtime':'0.9.18'},
    {'b3-prosaic':'0.5.1'},{'b3-prosaic-harness-postgres':'0.4.0'},{'b3-prosaic-harness':'0.9.13'}])
def test_partial_unqualified_workflow_train_refuses(changes):
    with pytest.raises(ValueError,match='unsupported or incoherent'):supports_conversation(manifest(changes))


@pytest.mark.parametrize('path,sha',[
    ('dependencies/releases-pre-workflow-enforcement-2026-11-07.json','1acd2563d84c8dce6fe4a6e610ea82ee52760c60d58c1c6b7b296d8f8534dc5c'),
    ('dependencies/releases-reasoning-pre-workflow-enforcement-2026-11-07.json','1acd2563d84c8dce6fe4a6e610ea82ee52760c60d58c1c6b7b296d8f8534dc5c'),
    ('lab_runner/quality/data/sdk-provenance-pre-workflow-enforcement.json','bda7c1adecce35419525d5f56cb5b406e588c3384917b7f3f1e8a3ec135e82ab'),
    ('lab_runner/memory/data/development-freeze-pre-workflow-enforcement.json','f017e9653029f7a63fc363bcc130671cce02beb902dd5d02d5cbe1115e5a9844'),
    ('lab_runner/memory/data/evaluation-freeze-pre-workflow-enforcement.json','2656283b2cd3f60164dfc0825f8c40acddc22af3571e90b1c1deec36ac16c3ac'),
])
def test_lab098_snapshots_keep_exact_original_bytes(path,sha):
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha


def test_previous_profile_resource_is_registered_and_selectable():
    from lab_runner.quality.suite import resource
    from lab_runner.quality.sdk_provenance import qualified_sdk
    previous=json.loads(resource('sdk-provenance-pre-workflow-enforcement.json'))
    assert previous['manifestDigest']=='1acd2563d84c8dce6fe4a6e610ea82ee52760c60d58c1c6b7b296d8f8534dc5c'
    assert qualified_sdk({'b3-prosaic':'0.5.0','b3-prosaic-runtime':'0.9.16','b3-prosaic-harness':'0.9.11'})==previous


def test_current_workflow_profile_pins_verified_release_and_keeps_previous_profile_distinct():
    from lab_runner.quality.sdk_provenance import qualified_sdk
    selected=qualified_sdk({name:VERSIONS[name] for name in ('b3-prosaic','b3-prosaic-runtime','b3-prosaic-harness')})
    active=ROOT/'dependencies/releases-pre-accounting-metadata-2026-11-08.json'
    assert selected['manifestDigest']==hashlib.sha256(active.read_bytes()).hexdigest()
    assert selected['manifestDigest']!='1acd2563d84c8dce6fe4a6e610ea82ee52760c60d58c1c6b7b296d8f8534dc5c'
    harness=next(item for item in selected['artifacts'] if item['distribution']=='b3-prosaic-harness')
    assert harness=={'distribution':'b3-prosaic-harness','version':'0.9.12',
        'sha256':'fb07797c3e42ab2e7e8f0a727b7bd25229e9b223cf15309716f10ff9d1f1147b'}


def test_workflow_freeze_keeps_benchmark_inputs_and_binds_only_new_provenance():
    from lab_runner.memory.freeze import verify
    from lab_runner.memory.suite import load_suite
    from lab_runner.quality.contracts import digest
    root=ROOT/'lab_runner/memory/data'
    old=json.loads((root/'development-freeze-pre-workflow-enforcement.json').read_text())
    old_eval=json.loads((root/'evaluation-freeze-pre-workflow-enforcement.json').read_text())
    dev=json.loads((root/'development-freeze-pre-accounting-metadata.json').read_text())
    evaluation=json.loads((root/'evaluation-freeze-pre-accounting-metadata.json').read_text())
    assert evaluation['suiteDigest']==old_eval['suiteDigest']
    assert evaluation['developmentFreezeDigest']==digest(dev)!=digest(old)
    assert set(dev['implementation'])==set(old['implementation'])
    assert {k for k in dev['implementation'] if dev['implementation'][k]!=old['implementation'][k]}=={'freeze.py'}
    added={'data/sdk-provenance-pre-workflow-enforcement.json'}
    assert set(dev['qualityDependencies'])==set(old['qualityDependencies'])|added
    assert {k for k in dev['qualityDependencies'] if dev['qualityDependencies'][k]!=old['qualityDependencies'].get(k)}==added|{'sdk_provenance.py','suite.py','data/sdk-provenance-public.json'}
    assert {k:v for k,v in dev.items() if k not in ('implementation','qualityDependencies')}=={k:v for k,v in old.items() if k not in ('implementation','qualityDependencies')}
    frozen=load_suite()
    with pytest.raises(ValueError,match='development freeze drift'):verify(frozen,dev,evaluation)
    with pytest.raises(ValueError,match='development freeze drift'):verify(frozen,old,old_eval)
