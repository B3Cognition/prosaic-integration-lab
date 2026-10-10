"""Actual HTTP effects, SQL domain uniqueness and observable worker-loss barriers."""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import uuid

import httpx
import psycopg
import pytest

from lab_runner.native_scenarios import control,calls,effect_proposal,owned,replace_worker
from lab_runner.stack import command
from lab_runner.accounting_report import accounting_snapshot
from prosaic_integration_lab.tool_journal import PgToolJournal
from test_native_workflows import http,propose,start,approved_proposal
from test_recovery import wait_for


def domain(lab,key):
    with psycopg.connect(lab['app_dsn']) as connection:
        return connection.execute('SELECT namespace,business_key,amount FROM lab_fixture.effects WHERE business_key=%s ORDER BY namespace',(key,)).fetchall()


def effect(lab,key,*,worker='a',actor='alice'):
    return start(lab,propose(lab,effect_proposal(),actor=actor,worker=worker),entity=key,worker=worker,actor=actor)


def journal(lab):return PgToolJournal(lab['app_dsn'],identity='fixture-journal-v1')


def namespace(lab,tenant='tenant-a'):
    return next(bundle['operation_namespace'] for bundle in lab['native']['bundles'] if tenant in bundle['policies'])


@pytest.fixture(autouse=True)
def effect_model(lab):
    control(lab,scenario='native_effect')
    yield
    control(lab)


def test_completed_native_business_operation_replays_without_duplicate_domain_effect(lab):
    key=uuid.uuid4().hex
    assert effect(lab,key)['status']=='completed'
    original=domain(lab,key);assert len(original)==1 and original[0][2]==1
    replace_worker(lab)
    assert effect(lab,key,worker='b')['status']=='completed'
    assert domain(lab,key)==original


def test_same_business_key_has_distinct_trusted_tenant_namespaces(lab):
    key=uuid.uuid4().hex;settings=copy.deepcopy(lab['native']);expanded=copy.deepcopy(settings)
    expanded['tenants']['tenant-b']['tools']=['fixture_apply']
    next(bundle for bundle in expanded['bundles'] if 'tenant-b' in bundle['policies'])['policies']['tenant-b']['tools']=['fixture_apply']
    try:
        replace_worker(lab,native=expanded)
        assert effect(lab,key)['status']=='completed'
        assert effect(lab,key,worker='b',actor='carol')['status']=='completed'
        rows=domain(lab,key)
        assert len(rows)==2 and {row[0] for row in rows}=={namespace(lab),namespace(lab,'tenant-b')}
    finally:replace_worker(lab,native=settings)


def crash(lab,proposal,entity,*,barrier,control_settings):
    control(lab,**control_settings)
    response=httpx.get(lab['model']+'/stats',timeout=5);response.raise_for_status()
    initial=response.json();key=uuid.uuid4().hex
    def observed():
        result=httpx.get(lab['model']+'/stats',timeout=5);result.raise_for_status();value=result.json()
        return value['calls']>initial['calls'] if barrier=='calls' else value['accepted_events']>initial['accepted_events'] if barrier=='accepted_events' else value['barriers'][barrier]>initial['barriers'][barrier]
    def submit():
        try:return start(lab,proposal,entity=entity,key=key)
        except httpx.HTTPError:return None
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(submit)
        try:
            wait_for(observed,timeout=10)
            with psycopg.connect(lab['app_dsn']) as connection:
                run_id=connection.execute('SELECT run_id FROM lab_app.runs WHERE idempotency_key=%s',(key,)).fetchone()[0]
            manifest=owned(lab);command(manifest['engine'],'kill',manifest['replica_ids']['a'])
        finally:control(lab,scenario=control_settings.get('scenario','native'))
        future.result(timeout=10)
    replace_worker(lab,'a')
    return run_id


def recover(lab,run_id,**extra):
    def attempt():
        run=http(lab,'GET','/runs/'+run_id,worker='b')
        result=httpx.post(lab['b']+'/runs/'+run_id+'/resume',
            headers=__import__('test_approval').headers(lab),json={'expected_revision':run['revision'],**extra},timeout=20)
        if result.status_code==409:
            assert result.json()['detail']=='run_busy';return None
        assert result.status_code==200;return result.json()
    return wait_for(attempt,timeout=40)


@pytest.mark.parametrize('barrier,effects,state',[('tool-claimed',0,'uncertain'),
    ('tool-effect',1,'uncertain'),('tool-committed',1,'replay')])
def test_worker_loss_claim_effect_commit_never_infers_redispatch(lab,barrier,effects,state):
    key=uuid.uuid4().hex;proposal=propose(lab,effect_proposal())
    run_id=crash(lab,proposal,key,barrier=barrier,
                 control_settings={'scenario':'native_effect','effect_gate':barrier})
    assert len(domain(lab,key))==effects
    with psycopg.connect(lab['app_dsn']) as connection:
        signature=connection.execute('SELECT signature FROM lab_app.tool_operations WHERE operation_namespace=%s AND operation_key=%s',
            (namespace(lab),key)).fetchone()[0]
    claim=journal(lab).claim(namespace(lab),key,signature)
    assert claim.state==state and claim.claim_token is None
    # Fresh invocation with the same trusted business key replays completion or
    # fails uncertain. It never runs the handler again, independent of lease age.
    result=effect(lab,key,worker='b')
    assert result['status']==('completed' if state=='replay' else 'blocked')
    assert len(domain(lab,key))==effects
    assert recover(lab,run_id)['status']=='blocked'


def test_concurrent_native_claims_execute_only_one_domain_handler(lab):
    key=uuid.uuid4().hex
    stats=httpx.get(lab['model']+'/stats',timeout=5);stats.raise_for_status()
    entered=stats.json()['barriers']['tool-handler']
    proposals=[propose(lab,effect_proposal()) for _ in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(lambda item:start(lab,item[1],entity=key,worker=item[0]),zip(('a','b'),proposals)))
    assert sum(outcome['status']=='completed' for outcome in outcomes)>=1
    assert len(domain(lab,key))==1
    stats=httpx.get(lab['model']+'/stats',timeout=5);stats.raise_for_status()
    assert stats.json()['barriers']['tool-handler']==entered+1

@pytest.mark.parametrize('budget,scenario,reason',[('tools','native_effect_batch','tool_call_limit'),
    ('provider','native_effect','provider_request_limit')])
def test_native_invocation_cap_blocks_next_dispatch_and_retains_real_sql_evidence(lab,budget,scenario,reason):
    settings=copy.deepcopy(lab['native']);key=uuid.uuid4().hex
    try:
        if budget=='provider':
            limited=copy.deepcopy(settings)
            for bundle in limited['bundles']:bundle['fixture_provider_request_limit']=1
            replace_worker(lab,native=limited)
        control(lab,scenario=scenario)
        before=calls(lab)
        stats=httpx.get(lab['model']+'/stats',timeout=5);stats.raise_for_status()
        barriers=stats.json()['barriers']
        run=effect(lab,key,worker='b')
        assert run['status']=='blocked' and calls(lab)==before+1
        stats=httpx.get(lab['model']+'/stats',timeout=5);stats.raise_for_status()
        assert stats.json()['barriers']['tool-handler']==barriers['tool-handler']+1
        assert stats.json()['barriers']['tool-claimed']==barriers['tool-claimed']+1
        assert stats.json()['barriers']['tool-committed']==barriers['tool-committed']+1
        assert domain(lab,key)==[(namespace(lab),key,1)]
        with psycopg.connect(lab['app_dsn']) as connection:
            assert connection.execute('SELECT state,outcome FROM lab_app.tool_operations WHERE operation_namespace=%s AND operation_key=%s',
                (namespace(lab),key)).fetchall()==[('completed',{'status':'ok','result':{'applied':True}})]
        with psycopg.connect(lab['harness_dsn']) as connection:
            receipts=connection.execute('SELECT document FROM prosaic_harness.receipts WHERE run_id=%s',(run['run_id'],)).fetchall()
        assert len(receipts)==1
        result=json.loads(receipts[0][0])['result']
        assert result['exit_code']!=0 and result['metadata']['failure_reason']==reason
        assert result['metadata']['invocation_budgets_v1']['tool_calls']==1
        assert result['metadata']['invocation_budgets_v1']['provider_requests']==1
        assert result['token_usage']==125
        original=http(lab,'GET','/runs/'+run['run_id']+'/usage',worker='b')
        assert original['total_calls']==1 and original['complete_calls']==1 and original['unresolved_calls']==0
        replace_worker(lab)
        assert http(lab,'GET','/runs/'+run['run_id'],worker='b')['status']=='blocked'
        assert accounting_snapshot(http(lab,'GET','/runs/'+run['run_id']+'/usage',worker='b'))==accounting_snapshot(original)
        assert calls(lab)==before+1
    finally:
        if budget=='provider':replace_worker(lab,native=settings)


def test_stale_fence_cannot_overwrite_original_committed_native_result(lab):
    key=uuid.uuid4().hex
    assert effect(lab,key)['status']=='completed'
    with pytest.raises(ValueError,match='tool_claim_conflict'):
        journal(lab).commit(namespace(lab),key,'stale-token',{'status':'ok','result':{'applied':False}})
    assert domain(lab,key)[0][2]==1


@pytest.mark.parametrize('changed',['arguments','version'])
def test_changed_operation_signature_conflicts_without_mutating_effect_evidence(lab,changed):
    key=uuid.uuid4().hex
    assert effect(lab,key)['status']=='completed'
    with psycopg.connect(lab['app_dsn']) as connection:
        original=connection.execute('SELECT signature,state,outcome FROM lab_app.tool_operations WHERE operation_key=%s',(key,)).fetchall()
    settings=copy.deepcopy(lab['native'])
    try:
        if changed=='arguments':control(lab,scenario='native_effect',effect_amount=2)
        else:
            expanded=copy.deepcopy(settings)
            for bundle in expanded['bundles']:
                bundle['version']='synthetic-v2';bundle['fixture_effect_version']='v2'
            for tenant in expanded['tenants'].values():tenant['bundle_version']='synthetic-v2'
            replace_worker(lab,native=expanded)
        assert effect(lab,key,worker='b')['status']=='blocked'
        assert domain(lab,key)[0][2]==1
        with psycopg.connect(lab['app_dsn']) as connection:
            assert connection.execute('SELECT signature,state,outcome FROM lab_app.tool_operations WHERE operation_key=%s',(key,)).fetchall()==original
    finally:
        if changed=='version':replace_worker(lab,native=settings)


def test_native_saved_receipt_adoption_durable_usage_and_no_duplicate_provider(lab):
    before=calls(lab);proposal=propose(lab,approved_proposal())
    run_id=crash(lab,proposal,uuid.uuid4().hex,barrier='accepted_events',
        control_settings={'scenario':'native','accepted_gate':True})
    run=recover(lab,run_id)
    assert run['status']=='waiting' and calls(lab)==before+2
    usage=http(lab,'GET','/runs/'+run_id+'/usage',worker='b')
    assert usage['total_calls']==2 and usage['complete_calls']==2
    replace_worker(lab)
    assert accounting_snapshot(http(lab,'GET','/runs/'+run_id+'/usage',worker='b'))==accounting_snapshot(usage)
    assert calls(lab)==before+2


def test_native_interrupted_provider_requires_consent_and_preserves_unknown_usage(lab):
    before=calls(lab);proposal=propose(lab,approved_proposal())
    run_id=crash(lab,proposal,uuid.uuid4().hex,barrier='calls',
        control_settings={'scenario':'native','blocked':True})
    blocked=recover(lab,run_id)
    assert blocked['status']=='blocked' and blocked['recovery_status']=='retry_consent_required'
    blocked=recover(lab,run_id,retry_interrupted=True)
    assert blocked['status']=='blocked' and blocked['recovery_status']=='usage_reconciliation_required'
    assert calls(lab)==before+1
    usage=http(lab,'GET','/runs/'+run_id+'/usage',worker='b')
    assert usage['unresolved_calls']==1 and usage['fully_costed'] is False
