import json
from types import SimpleNamespace

import pytest


def test_session_sql_partition_keeps_app_recorder_and_workflow_routes(tmp_path,monkeypatch):
    import lab_runner.conversation_faults as faults
    secret=tmp_path/'service.json'
    original={'harness_dsn':'workflow-direct','accounting_dsn':'recorder-direct','app_dsn':'app-direct',
        'conversation':{'dsn':'session-direct','bundles':['retained'],'tenants':{'a':'grant'}}}
    secret.write_text(json.dumps(original))
    events=[]
    stack=SimpleNamespace(secrets=tmp_path,engine='owned-engine',manifest={'runtime_config_job':'owned-config-job'})
    proxy=SimpleNamespace(harness_dsn=lambda dsn:'session-relay',control=lambda blocked:events.append(('control',blocked)))
    monkeypatch.setattr(faults,'owned_stack',lambda lab:stack)
    monkeypatch.setattr(faults,'start_proxy',lambda lab:proxy)
    monkeypatch.setattr(faults,'replace_worker',lambda lab,name,**kwargs:events.append(('worker',name,kwargs)))
    monkeypatch.setattr(faults,'command',lambda *args:events.append(('command',args)))
    with faults.partition_session_worker_a({}) as selected:
        assert selected is proxy
        assert json.loads(secret.read_text())==original
    assert events[0]==('worker','a',{'config_patch':{'conversation':{
        **original['conversation'],'dsn':'session-relay'}}})
    assert events[-1]==('control',False)


def test_owned_worker_kill_targets_verified_exact_id(monkeypatch):
    import lab_runner.conversation_faults as faults
    stack=SimpleNamespace(engine='engine',manifest={'replica_ids':{'a':'exact-owned-a','b':'other-owned-b'},
        'resources':[{'kind':'container','id':'exact-owned-a'},{'kind':'container','id':'other-owned-b'}]})
    seen=[]
    monkeypatch.setattr(faults,'owned_stack',lambda lab:stack)
    monkeypatch.setattr(faults,'command',lambda *args:seen.append(args))
    faults.kill_worker({},'a')
    assert seen==[('engine','kill','exact-owned-a')]
    with pytest.raises(ValueError):faults.kill_worker({},'foreign')


def test_worker_id_outside_recorded_owned_inventory_is_never_killed(monkeypatch):
    import lab_runner.conversation_faults as faults
    stack=SimpleNamespace(engine='engine',manifest={'replica_ids':{'a':'foreign-a'},'resources':[]})
    monkeypatch.setattr(faults,'owned_stack',lambda lab:stack)
    monkeypatch.setattr(faults,'command',lambda *args:pytest.fail('unrecorded target reached engine'))
    with pytest.raises(ValueError):faults.kill_worker({},'a')


def test_temporary_conversation_config_restores_exact_private_delivery_and_worker(tmp_path,monkeypatch):
    import lab_runner.conversation_faults as faults
    source=tmp_path/'service.json'
    original={'conversation':{'dsn':'container-private','bundles':[{'version':'v1'}],'tenants':{}},
        'harness_dsn':'private-workflow'}
    raw=json.dumps(original,indent=3)+'\n';source.write_text(raw);source.chmod(0o600)
    events=[]
    stack=SimpleNamespace(secrets=tmp_path)
    monkeypatch.setattr(faults,'owned_stack',lambda lab:stack)
    def replaced(lab,name,**kwargs):
        events.append((name,kwargs))
        document=json.loads(source.read_text());document.update(kwargs['config_patch'])
        source.write_text(json.dumps(document));source.chmod(0o600)
    monkeypatch.setattr(faults,'replace_worker',replaced)
    def transform(settings):
        settings['bundles'][0]['version']='v2';return settings
    with pytest.raises(RuntimeError):
        with faults.temporary_conversation_configuration({},transform) as changed:
            assert changed['dsn']=='container-private' and changed['bundles'][0]['version']=='v2'
            raise RuntimeError('fixture case failed')
    assert source.read_text()==raw and source.stat().st_mode&0o777==0o600
    assert len(events)==2 and all(name=='b' for name,_ in events)
    assert events[-1][1]=={'config_patch':{'conversation':original['conversation']}}


def test_failed_worker_loss_case_still_restores_owned_replica(monkeypatch):
    import lab_runner.conversation_faults as faults
    restored=[]
    monkeypatch.setattr(faults,'replace_worker',lambda lab,name:restored.append(name))
    with pytest.raises(RuntimeError):
        with faults.restore_workers_after_loss({},'a'):
            raise RuntimeError('recovery assertion failed')
    assert restored==['a']
