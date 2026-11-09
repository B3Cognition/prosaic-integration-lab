"""Only the complete sent-effort train is admitted; older evidence remains immutable."""
import hashlib
from pathlib import Path
import pytest
from lab_runner.gates import supports_conversation,supports_context_assembly,supports_consumer_blueprints
from lab_runner.blueprints import copy_blueprint
VERSIONS={'b3-prosaic':'0.5.0','b3-prosaic-runtime':'0.9.18','b3-prosaic-harness':'0.9.12','b3-prosaic-runtime-postgres':'0.3.0','b3-prosaic-harness-postgres':'0.4.1'}
def manifest(changes=None):return {'artifacts':[{'distribution':k,'version':v} for k,v in (VERSIONS|(changes or {})).items()]}
@pytest.mark.parametrize('gate',[supports_conversation,supports_context_assembly,supports_consumer_blueprints])
def test_complete_sent_effort_train_is_admitted(gate):assert gate(manifest())
@pytest.mark.parametrize('changes',[{'b3-prosaic-runtime':'0.9.19'},{'b3-prosaic-harness':'0.9.11'},{'b3-prosaic-harness':'0.9.13'},{'b3-prosaic-runtime-postgres':'0.3.1'},{'b3-prosaic':'0.5.1'}])
def test_partial_sent_effort_train_is_refused(changes):
    with pytest.raises(ValueError,match='unsupported or incoherent'):supports_conversation(manifest(changes))
def test_sent_effort_blueprint_copy_is_no_call_and_nonoverwriting(tmp_path):
    project=copy_blueprint('sent-effort',tmp_path/'effort')
    assert (project/'host.py').is_file() and '127.0.0.1:9' in (project/'runtime.yml').read_text()
    assert '--live' in (project/'README.md').read_text()
    with pytest.raises(FileExistsError):copy_blueprint('sent-effort',project)

@pytest.mark.parametrize("path,sha",[('dependencies/releases-pre-sent-effort-2026-11-08.json', '8b5e032fcd703c19caf9b3dc068441b1376b38b4193b9da4a14f131df62b5c45'), ('dependencies/releases-reasoning-pre-sent-effort-2026-11-08.json', '8b5e032fcd703c19caf9b3dc068441b1376b38b4193b9da4a14f131df62b5c45'), ('lab_runner/quality/data/sdk-provenance-pre-sent-effort.json', '30e4fd90489f7e099e20910b49937409e80f58ebe70fc0b0fdc2e846df954fe3'), ('lab_runner/memory/data/development-freeze-pre-sent-effort.json', 'bd6a4317087e64ae37d28fa553b01a06c5e786b1c4a721f5153565f4a0396f28'), ('lab_runner/memory/data/evaluation-freeze-pre-sent-effort.json', 'e7c6ec72102960e6fd1fbed4aa724db1080c96d0d040d2b44eb796ed57533f63')])
def test_pre_sent_effort_snapshots_are_immutable(path,sha):
    assert hashlib.sha256((Path(__file__).resolve().parents[2]/path).read_bytes()).hexdigest()==sha


def test_previous_accounting_metadata_profile_remains_registered():
    import json
    from lab_runner.quality.suite import resource
    from lab_runner.quality.sdk_provenance import qualified_sdk
    saved=json.loads(resource('sdk-provenance-pre-sent-effort.json'))
    assert saved['manifestDigest']=='8b5e032fcd703c19caf9b3dc068441b1376b38b4193b9da4a14f131df62b5c45'
    assert qualified_sdk({'b3-prosaic':'0.5.0','b3-prosaic-runtime':'0.9.17','b3-prosaic-harness':'0.9.12'})==saved


def test_historical_sent_effort_profile_requires_actual_public_runtime_pin():
    import json
    from lab_runner.quality.sdk_provenance import qualified_sdk
    root=Path(__file__).resolve().parents[2];active=root/'dependencies/releases-pre-context-packs-2026-11-09.json'
    selected=qualified_sdk({name:VERSIONS[name] for name in ('b3-prosaic','b3-prosaic-runtime','b3-prosaic-harness')})
    assert selected['manifestDigest']==hashlib.sha256(active.read_bytes()).hexdigest()
    current=json.loads(active.read_bytes())['artifacts'];runtime=next(a for a in current if a['distribution']=='b3-prosaic-runtime')
    assert runtime['version']=='0.9.18' and runtime['filename']=='b3_prosaic_runtime-0.9.18-py3-none-any.whl'
    assert runtime['url'].startswith('https://files.pythonhosted.org/packages/')
    assert runtime['source_commit']=='d440d8664e0f307e01c62706976e485993b2e0a2' and runtime['sha256']=='c106f0581c3a8492fd400818d8963aeb903fbc34a3c71148faf9b78385d1ab54'
    previous=json.loads((root/'dependencies/releases-pre-sent-effort-2026-11-08.json').read_bytes())['artifacts']
    assert [a for a in current if a['distribution']!='b3-prosaic-runtime']==[a for a in previous if a['distribution']!='b3-prosaic-runtime']


def test_sent_effort_freeze_advances_only_current_provenance():
    import json
    from lab_runner.memory.freeze import verify
    from lab_runner.memory.suite import load_suite
    from lab_runner.quality.contracts import digest
    root=Path(__file__).resolve().parents[2]/'lab_runner/memory/data'
    old=json.loads((root/'development-freeze-pre-sent-effort.json').read_text());old_eval=json.loads((root/'evaluation-freeze-pre-sent-effort.json').read_text())
    dev=json.loads((root/'development-freeze-pre-context-packs.json').read_text());evaluation=json.loads((root/'evaluation-freeze-pre-context-packs.json').read_text())
    assert evaluation['suiteDigest']==old_eval['suiteDigest']
    assert evaluation['developmentFreezeDigest']==digest(dev)!=digest(old)
    assert set(dev['implementation'])==set(old['implementation'])
    assert {k for k in dev['implementation'] if dev['implementation'][k]!=old['implementation'][k]}=={'freeze.py'}
    added={'data/sdk-provenance-pre-sent-effort.json'}
    assert set(dev['qualityDependencies'])==set(old['qualityDependencies'])|added
    assert {k for k in dev['qualityDependencies'] if dev['qualityDependencies'][k]!=old['qualityDependencies'].get(k)}==added|{'sdk_provenance.py','suite.py','data/sdk-provenance-public.json'}
    assert {k:v for k,v in dev.items() if k not in ('implementation','qualityDependencies')}=={k:v for k,v in old.items() if k not in ('implementation','qualityDependencies')}
    frozen=load_suite()
    with pytest.raises(ValueError,match='development freeze drift'):verify(frozen,dev,evaluation)
    with pytest.raises(ValueError,match='development freeze drift'):verify(frozen,old,old_eval)
