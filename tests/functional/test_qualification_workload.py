"""Run the real arrival scheduler against bounded external I/O substitutes."""
import json
import threading
import httpx
import pytest

@pytest.mark.parametrize('calls,records,expected_stop,rate,expected_count',[(2,10,'calls',100,2),
    (10,1,'records',100,1),(10,10,'duration',2,2)])
def test_arrivals_stop_at_first_call_or_record_bound_and_keep_tenant_actor_identity(monkeypatch,calls,records,expected_stop,rate,expected_count):
    from lab_runner import load_profile
    from pathlib import Path
    profile=json.loads(Path('configs/qualification.synthetic.json').read_text())
    profile.update(duration_s=1,window_s=1,arrivals_per_second=rate,concurrency=2,users=2,
        maximum_calls=calls,maximum_records=records)
    state={'rows':0,'calls':0,'controls':[],'runs':{},'tool_samples':0};lock=threading.Lock()
    class Cursor:
        def __init__(self,value):self.value=value
        def fetchone(self):return (self.value,)
    class Connection:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def execute(self,query):return Cursor(state['rows'] if 'count' in query else 1000)
    class Recorder:
        def __init__(self,*args,**kwargs):pass
        def report(self,**kwargs):return {'total_calls':state['calls'],'unresolved_calls':0}
    import psycopg
    monkeypatch.setattr(psycopg,'connect',lambda *a,**k:Connection())
    monkeypatch.setattr(load_profile,'PostgresRecorder',Recorder)
    def service(request):
        path=request.url.path
        if path=='/control':
            state['controls'].append(json.loads(request.content));return httpx.Response(200,json={})
        if path=='/stats':return httpx.Response(200,json={k:state[k] for k in ('calls','tool_samples')}|{'allowance_rejected':0})
        if path=='/operation':state['tool_samples']+=1;return httpx.Response(200,json={'seconds':0})
        token=request.headers.get('Authorization')
        if path=='/runs':
            with lock:
                state['rows']+=1;state['calls']+=1;run_id=str(state['rows'])
                state['runs'][run_id]=token
            return httpx.Response(200,json={'run_id':run_id,'revision':'v1','status':'waiting'})
        run_id=path.split('/')[2]
        if token!=state['runs'][run_id]:return httpx.Response(404,json={})
        if path.endswith('/usage'):
            return httpx.Response(200,json={'total_calls':1,'complete_calls':1,'unresolved_calls':0,
                'fully_costed':True,'billing_eligible':False})
        return httpx.Response(200,json={'run_id':run_id,'revision':'v2',
            'status':'completed' if request.method=='POST' else 'waiting'})
    real_client=httpx.Client
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:real_client(transport=httpx.MockTransport(service),**kwargs))
    config={'model':'http://127.0.0.1:1','a':'http://127.0.0.1:2','b':'http://127.0.0.1:3',
        'migration_dsn':'unused','accounting_dsn':'unused','namespace':'fixture','environment':'sandbox',
        'principals':{'a':{'tenant_id':'tenant-a','actor_id':'same'},'b':{'tenant_id':'tenant-b','actor_id':'same'}}}
    result=load_profile.run_qualification(config,profile,None)
    assert result['stop_bound']==expected_stop
    assert result['independent_model_calls']==expected_count
    assert result['records_after']==expected_count
    assert len(result['tenant_counts'])==2
    assert result['accepted']==result['completed']==result['ledger_calls']
    assert result['tool_samples']==result['completed']
    assert result['read_failures']==0 and result['read_samples']==result['completed']
    assert state['controls'][-1]=={'preserve_allowance':True}  # Timing resets without removing the dispatch ceiling.
    if expected_stop=='duration':assert result['window_samples']==1
