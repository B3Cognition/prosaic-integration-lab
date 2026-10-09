import httpx
from prosaic_runtime_postgres import PostgresRecorder
from test_approval import headers,start
from test_accounting import count
from test_recovery import crash_during,resume_after_lease

def test_http_consumed_budget_blocks_resume_and_identity_override_without_new_dispatch(lab):
    before = count(lab)
    httpx.post(lab['model']+'/control',json={'scenario':'large_usage'},timeout=5).raise_for_status()
    try:
        run = start(lab,workflow='synthetic').json()
    finally:
        httpx.post(lab['model']+'/control',json={'scenario':'normal'},timeout=5).raise_for_status()
    assert run['status'] == 'blocked' and run['recovery_status'] == 'budget_exhausted'
    assert count(lab) == before+1
    for replica in ('a','b'):
        response = httpx.post(lab[replica]+'/runs/'+run['run_id']+'/resume',headers=headers(lab),
            json={'expected_revision':run['revision'],'retry_interrupted':True},timeout=10)
        assert response.status_code == 200
        assert response.json()['recovery_status'] == 'budget_exhausted'
    spoofed = httpx.post(lab['b']+'/runs/'+run['run_id']+'/resume',headers=headers(lab),
        json={'expected_revision':run['revision'],'retry_interrupted':True,'billing_account_id':'SPOOF'},timeout=10)
    assert spoofed.status_code == 422
    assert count(lab) == before+1

def test_http_missing_receipt_unknown_usage_budget_cannot_be_bypassed_by_explicit_retry(lab):
    before = count(lab)
    run_id = crash_during(lab,{'blocked':True},lambda:count(lab) == before+1)
    recovered = resume_after_lease(lab,run_id)
    assert recovered['recovery_status'] == 'retry_consent_required'
    response = httpx.post(lab['b']+'/runs/'+run_id+'/resume',headers=headers(lab),
        json={'expected_revision':recovered['revision'],'retry_interrupted':True},timeout=10)
    assert response.status_code == 200
    blocked = response.json()
    assert blocked['status'] == 'blocked' and blocked['recovery_status'] == 'usage_reconciliation_required'
    repeated = httpx.post(lab['a']+'/runs/'+run_id+'/resume',headers=headers(lab),
        json={'expected_revision':blocked['revision'],'retry_interrupted':True},timeout=10)
    assert repeated.status_code == 200
    assert repeated.json()['recovery_status'] == 'usage_reconciliation_required'
    recorder = PostgresRecorder(lab['accounting_dsn'],namespace=lab['namespace'],environment=lab['environment'])
    calls = recorder.calls(run_id=run_id)
    assert len(calls) == 1
    context = calls[0]['intent']['context']
    assert (context['tenant_id'],context['actor_id'],context['billing_account_id']) == ('tenant-a','alice','account-a')
    usage = recorder.report(run_id=run_id)
    assert usage['unresolved_calls'] == 1 and usage['estimated_amounts'] == {}
    assert usage['billing_eligible'] is False
    assert count(lab) == before+1
