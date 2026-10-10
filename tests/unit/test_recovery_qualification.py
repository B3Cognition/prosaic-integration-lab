"""Missing measurements cannot be mistaken for zero-loss restoration."""
import pytest
import hashlib
import json

def identity():
    from test_qualification import profile
    return {'suite':'synthetic-capacity-v1','profile_sha256':hashlib.sha256(json.dumps(profile(),sort_keys=True,
        separators=(',',':'),ensure_ascii=False).encode()).hexdigest()}

def test_recovery_requires_owned_stack_before_any_effect():
    from lab_runner.recovery_qualification import run
    from test_qualification import profile
    with pytest.raises(ValueError):run(object(),profile())

@pytest.mark.parametrize('patch',[{'acknowledged':[]},{'restored':[]},{'ready_at':None},{'calls_after':3},
    {'restored':[999]}])
def test_missing_or_redispatched_restore_evidence_fails(patch):
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence=dict(acknowledged=[{'sequence':1,'time':10}],restored=[1],loss_at=11,ready_at=12,
        calls_before=2,calls_after=2,owner_verified=True,revision_verified=True,
        receipt_verified=True,unknown_usage_verified=True)
    evidence.update(patch)
    evidence.update(identity())
    assert evaluate(profile(),evidence)['qualification']=='not_qualified'

def test_observed_missing_marker_rpo_is_measured():
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence=dict(acknowledged=[{'sequence':1,'time':10},{'sequence':2,'time':15}],restored=[1],
        loss_at=16,ready_at=20,calls_before=2,calls_after=2,owner_verified=True,
        revision_verified=True,receipt_verified=True,unknown_usage_verified=True)
    evidence.update(identity())
    result=evaluate(profile(),evidence)
    assert result['observed_rpo_s']==5 and result['observed_rto_s']==4
    assert result['qualification']=='not_qualified'

def test_restore_identity_mismatch_cannot_qualify():
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    assert evaluate(profile(),{'suite':'other-suite'})['reason']=='evidence_identity_mismatch'

def test_restore_refreshes_owned_port_through_readiness_and_final_restart(tmp_path,monkeypatch):
    """Engine restart may reassign the same verified container's published port."""
    import httpx
    from types import SimpleNamespace
    from lab_runner import recovery_qualification as recovery
    from lab_runner.stack import OwnedStack
    from test_qualification import profile
    stack=object.__new__(OwnedStack)
    stack.directory=tmp_path;stack.secrets=tmp_path;stack.owner='a'*32;stack.engine='fixture-engine'
    stack.manifest={'owner':stack.owner,'database_id':'db','replica_ids':{'b':'replica-b'},
        'runtime_config_job':'delivery','endpoints':{'a':'http://127.0.0.1:1001',
        'b':'http://127.0.0.1:1002','model':'http://127.0.0.1:1003'}}
    config={'migration_dsn':'dbname=lab','principals':{'owner':{},'other':{}},
        'harness_dsn':'dbname=lab','accounting_dsn':'dbname=lab','app_dsn':'dbname=lab'}
    (tmp_path/'host.json').write_text(json.dumps(config));(tmp_path/'service.json').write_text(json.dumps(config))
    monkeypatch.setattr(OwnedStack,'verify_owned',lambda self:True)
    class Connection:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def execute(self,query,*args):
            if 'SELECT count' in query:return SimpleNamespace(fetchone=lambda:(0,))
            if 'SELECT sequence' in query:return [(1,10.0),(2,11.0)]
    monkeypatch.setattr(recovery.psycopg,'connect',lambda *a,**k:Connection())
    monkeypatch.setattr(recovery.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout=b'fixture dump'))
    clock={'value':0};port={'value':1002}
    def monotonic():clock['value']+=.1;return clock['value']
    monkeypatch.setattr(recovery,'time',SimpleNamespace(monotonic=monotonic,time=lambda:10,sleep=lambda _:None))
    def command(engine,*args):
        if args==('start','replica-b'):port['value']+=1000
        return json.dumps([{'Id':'replica-b','Config':{'Labels':{'io.prosaic.lab.owner':stack.owner}},
            'NetworkSettings':{'Ports':{'8080/tcp':[{'HostIp':'127.0.0.1','HostPort':str(port['value'])}]}}}])
    monkeypatch.setattr(recovery,'command',command)
    seen=[];states=[]
    def service(request):
        seen.append(str(request.url));path=request.url.path
        if path=='/control':return httpx.Response(200,json={})
        if path=='/stats':return httpx.Response(200,json={'calls':2})
        if path=='/runs':
            state={'status':'waiting','run_id':str(len(states)),'revision':'v1','review':{},'choices':['approve']}
            states.append(state);return httpx.Response(200,json=state)
        if request.url.port!=2002:raise httpx.ConnectError('closed previous ephemeral port',request=request)
        if path=='/readyz':return httpx.Response(200,json={})
        if request.headers.get('Authorization')=='Bearer other':return httpx.Response(404,json={})
        if path.endswith('/usage'):return httpx.Response(200,json={'unresolved_calls':1,'fully_costed':False})
        return httpx.Response(200,json=states[int(path.split('/')[2])])
    real_client=httpx.Client
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:real_client(transport=httpx.MockTransport(service),**kwargs))
    result=recovery.run(stack,profile())
    assert result['qualification']=='qualified' and result['observed_rto_s']>0
    assert 'http://127.0.0.1:2002/readyz' in seen
    assert not any(':1002/' in url for url in seen)
    assert stack.manifest['endpoints']['b']=='http://127.0.0.1:3002'
    assert json.loads((tmp_path/'ownership.json').read_text())['endpoints']['b']=='http://127.0.0.1:3002'
