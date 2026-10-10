"""Catch aggregate success masking starvation and unbounded/absent evidence."""
import json
import hashlib
from pathlib import Path
import pytest

def profile():
    return json.loads(Path('configs/qualification.synthetic.json').read_text())

def observations():
    return dict(offered=22,accepted=22,completed=20,errors=0,rejected=0,
        approval_deferred=2,client_shed=0,latencies_s=[.1]*20,
        independent_model_calls=22,ledger_calls=22,unknown_usage=0,
        tenant_counts={'a':{'offered':20,'completed':20},'b':{'offered':2,'completed':0}},
        starved_windows=1,read_failures=0,read_samples=2,window_samples=2,
        records_before=0,records_after=22,bytes_before=100,bytes_after=1000,
        stop_bound='duration',elapsed_s=20,tool_samples=22,tool_latencies_s=[0]*22,allowance_rejected=0,
        suite='synthetic-capacity-v1',profile_sha256=hashlib.sha256(json.dumps(profile(),sort_keys=True,
            separators=(',',':'),ensure_ascii=False).encode()).hexdigest())

@pytest.mark.parametrize('starved_windows',[0,1])
def test_aggregate_success_does_not_hide_tenant_starvation(starved_windows):
    from lab_runner.qualification import evaluate
    configuration=profile();configuration.update(users=2,duration_s=22)
    data=observations();data.update(starved_windows=starved_windows,elapsed_s=22)
    data['profile_sha256']=hashlib.sha256(json.dumps(configuration,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    result=evaluate(configuration,data)
    assert result['correctness_passed'] is True
    assert result['fairness_passed'] is False
    assert result['qualified'] is False

@pytest.mark.parametrize('key,value', [('duration_s',float('nan')),('duration_s',True),
    ('duration_s',3601),pytest.param('duration_s',10**1000,id='huge-integral-duration'),
    ('arrivals_per_second',-1),('concurrency',65),
    ('maximum_calls',0),('maximum_records',10001),('maximum_report_bytes',262145),
    ('provider_latency_s',6),('window_s',0),('extra',1)])
def test_profile_rejects_unbounded_values(key,value):
    from lab_runner.qualification import validate_profile
    data=profile();data[key]=value
    with pytest.raises(ValueError): validate_profile(data)

@pytest.mark.parametrize('patch', [dict(offered=0),dict(latencies_s=[]),dict(unknown_usage=1),
    dict(independent_model_calls=23),dict(read_samples=0),dict(window_samples=0),dict(tool_samples=0),
    dict(tool_latencies_s=[]),dict(suite='wrong-suite'),dict(profile_sha256='f'*64)])
def test_absent_or_inconsistent_evidence_never_qualifies(patch):
    from lab_runner.qualification import evaluate
    data=observations();data.update(patch)
    assert evaluate(profile(),data)['qualified'] is False

def test_matching_complete_fair_observations_qualify():
    from lab_runner.qualification import evaluate
    configuration=profile();configuration['users']=2
    data=observations();data.update(offered=20,accepted=20,completed=20,approval_deferred=0,
        independent_model_calls=20,ledger_calls=20,starved_windows=0,
        tenant_counts={'a':{'offered':10,'completed':10},'b':{'offered':10,'completed':10}},
        tool_samples=20,tool_latencies_s=[0]*20)
    data['profile_sha256']=hashlib.sha256(json.dumps(configuration,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    result=evaluate(configuration,data)
    assert result['qualification']=='qualified'
    assert result['tool_latency_p95_s']==0

@pytest.mark.parametrize('patch',[{'window_samples':1},{'elapsed_s':0},{'tenant_counts':{'a':{'offered':20,'completed':20}}}])
def test_partial_duration_or_identity_coverage_cannot_qualify(patch):
    from lab_runner.qualification import evaluate
    configuration=profile();configuration['users']=2
    data=observations();data.update(offered=20,accepted=20,completed=20,approval_deferred=0,
        independent_model_calls=20,ledger_calls=20,starved_windows=0,
        tenant_counts={'a':{'offered':10,'completed':10},'b':{'offered':10,'completed':10}},
        tool_samples=20,tool_latencies_s=[0]*20)
    data['profile_sha256']=hashlib.sha256(json.dumps(configuration,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    data.update(patch)
    assert evaluate(configuration,data)['qualified'] is False

def test_wrong_profile_cannot_relabel_success():
    from lab_runner.qualification import evaluate
    data=observations();data.update(profile_sha256='a'*64)
    assert evaluate(profile(),data)['reason']=='evidence_identity_mismatch'

def test_unclassified_arrivals_cannot_pass_accounting_correctness():
    from lab_runner.qualification import evaluate
    data=observations();data.update(accepted=21,completed=19,independent_model_calls=21,ledger_calls=21,
        latencies_s=[.1]*19)
    data['tenant_counts']['a']['completed']=19
    assert evaluate(profile(),data)['correctness_passed'] is False

def test_report_hashes_hostile_labels_and_bounds_maximum_observations():
    from lab_runner.qualification import evaluate
    data=observations();data['tenant_counts']={'secret\n<script>':{'offered':22,'completed':20}}
    data['latencies_s']=[.1]*10000
    result=evaluate(profile(),data)
    assert 'secret' not in json.dumps(result)
    assert len(json.dumps(result).encode())<=262144
    data['latencies_s'].append(.1)
    with pytest.raises(ValueError):evaluate(profile(),data)

def test_overload_correctness_does_not_imply_qualification():
    from lab_runner.qualification import evaluate
    data=observations();data.update(offered=24,rejected=2)
    data['tenant_counts']['b']['offered']=4
    result=evaluate(profile(),data)
    assert result['correctness_passed'] is True
    assert result['qualification']=='not_qualified'

def test_synthetic_allowance_is_atomic_and_latency_control_validated():
    from concurrent.futures import ThreadPoolExecutor
    from fastapi.testclient import TestClient
    from lab_runner.model import app
    with TestClient(app) as client:
        assert client.post('/control',json={'maximum_calls':3,'provider_latency_s':0}).status_code==200
        before=client.get('/stats').json()['calls']
        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses=list(pool.map(lambda _:client.post('/v1/chat/completions').status_code,range(20)))
        assert statuses.count(200)==3 and statuses.count(429)==17
        stats=client.get('/stats').json()
        assert stats['calls']-before==3 and stats['allowance_rejected']==17
        assert client.post('/control',json={'preserve_allowance':True}).status_code==200
        assert client.post('/v1/chat/completions').status_code==429
        assert client.post('/control',json={'provider_latency_s':True}).status_code==422
        assert client.post('/control',json={'provider_latency_s':6}).status_code==422
        assert client.post('/operation',json={'latency_s':0}).status_code==200
        client.post('/control',json={}).raise_for_status()

def test_qualification_rejects_nonowned_config_before_network(monkeypatch):
    import httpx
    from lab_runner.qualification import run
    monkeypatch.setattr(httpx,'Client',lambda *a,**k:(_ for _ in ()).throw(AssertionError('network')))
    with pytest.raises(ValueError):run({'model':'https://paid.example'},profile(),None)

def test_owned_endpoints_cannot_authorize_a_foreign_database(monkeypatch):
    from lab_runner.stack import OwnedStack
    from lab_runner.qualification import verify_config
    import lab_runner.stack as stack_module
    import shutil
    owned=OwnedStack()
    try:
        endpoints={'model':'http://127.0.0.1:1','a':'http://127.0.0.1:2','b':'http://127.0.0.1:3'}
        owned.manifest.update(payload_audit='verified',endpoints=endpoints,
            resources=[{'kind':'container','id':'fixture'}],database_id='fixture')
        owned._save()
        host={'migration_dsn':'owned','app_dsn':'owned','harness_dsn':'owned','accounting_dsn':'owned',
            'principals':{},'namespace':'fixture','environment':'sandbox',
            'fixture_manifest':str(owned.directory/'ownership.json')}
        owned._secret('host.json',json.dumps(host))
        corrupted={**host,**endpoints,'migration_dsn':'shared-private-database'}
        monkeypatch.setattr(stack_module,'command',lambda *a,**k:(_ for _ in ()).throw(AssertionError('engine before validation')))
        with pytest.raises(ValueError):verify_config(corrupted)
    finally:shutil.rmtree(owned.directory)
