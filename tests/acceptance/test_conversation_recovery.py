"""Exact-owned worker loss with actual PG session state and independent counters."""
from concurrent.futures import ThreadPoolExecutor
import time
import uuid

import httpx
import psycopg
import pytest

from lab_runner.conversation_faults import kill_worker,restore_workers_after_loss
from lab_runner.conversation_scenarios import create,request,send
from lab_runner.native_scenarios import calls,control,replace_worker
from test_conversation_journey import principal,conversation_model


@pytest.fixture(autouse=True)
def restore_lost_replica(lab):
    with restore_workers_after_loss(lab,'a'):yield


def observed(lab,name,before):
    deadline=time.monotonic()+15
    while True:
        data=httpx.get(lab['model']+'/stats',timeout=5).json()
        if data['barriers'][name]>before:return
        if time.monotonic()>deadline:pytest.fail('owned conversation phase was not observed')
        time.sleep(.05)


def recover(lab,p,sid):
    deadline=time.monotonic()+25
    while True:
        response=request(lab,p,'POST','/conversations/'+sid+'/recover',replica='b',json={})
        if response.status_code==200:return response.json()
        assert response.status_code==409,response.status_code
        if time.monotonic()>deadline:pytest.fail('owned session lease recovery timed out')
        time.sleep(.2)


def loss(lab,p,session,phase,message,*,ref=None):
    before=httpx.get(lab['model']+'/stats',timeout=5).json()['barriers'][phase]
    control(lab,scenario='conversation',effect_gate=phase)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future=executor.submit(send,lab,p,session,uuid.uuid4().hex,message,interaction_ref=ref)
        try:
            observed(lab,phase,before)
            accepted=calls(lab)
            kill_worker(lab,'a')
        finally:control(lab,scenario='conversation')
        try:future.result(timeout=100)
        except httpx.HTTPError:pass
        else:pytest.fail('killed owned worker returned a successful response')
    replace_worker(lab,'b')
    return accepted


def test_saved_ordinary_receipt_is_adopted_by_fresh_worker_without_provider_post(lab):
    p=principal(lab,'bob');session=create(lab,p,uuid.uuid4().hex)
    accepted=loss(lab,p,session,'receiptSaved','Remember Prague')
    result=recover(lab,p,session['sessionId'])
    assert result['status']=='completed' and result['answer']=='Your city is Prague.'
    assert calls(lab)==accepted


def test_saved_interpretation_is_adopted_without_another_model_call(lab):
    p=principal(lab,'bob');session=send(lab,p,create(lab,p,uuid.uuid4().hex),'find','Find players')
    accepted=loss(lab,p,session,'receiptSaved','the second result',ref=session['pendingInteraction']['reference'])
    result=recover(lab,p,session['sessionId'])
    assert result['status']=='completed' and result['pendingInteraction']['stepId']=='confirm-b'
    assert calls(lab)==accepted


@pytest.mark.parametrize(('phase','step'),[('workflowCommandPrepared','select'),('workflowCommandReturned','confirm-b')])
def test_uncertain_workflow_handoff_requires_resolution_without_second_resume(lab,phase,step):
    from prosaic_harness_postgres import PostgresRunStore
    p=principal(lab,'carol');session=send(lab,p,create(lab,p,uuid.uuid4().hex),'find','Find players')
    accepted=loss(lab,p,session,phase,'the second result',ref=session['pendingInteraction']['reference'])
    with psycopg.connect(lab['app_dsn']) as connection:
        effects=connection.execute('SELECT count(*) FROM lab_fixture.effects').fetchone()[0]
    result=recover(lab,p,session['sessionId'])
    assert result['recoveryStatus']=='needsResolution' and calls(lab)==accepted
    with PostgresRunStore(lab['harness_dsn'],namespace=lab['namespace']) as store:
        assert store.load_run(session['sessionId']).state['current']==step
    again=recover(lab,p,session['sessionId'])
    assert again['recoveryStatus']=='needsResolution' and calls(lab)==accepted
    with psycopg.connect(lab['app_dsn']) as connection:
        assert connection.execute('SELECT count(*) FROM lab_fixture.effects').fetchone()==(effects,)


def test_repeated_interrupted_attempts_require_consent_and_stop_at_per_turn_cap(lab):
    p=principal(lab,'user-0007');session=create(lab,p,uuid.uuid4().hex)
    for attempt in range(3):
        before=calls(lab)
        control(lab,scenario='conversation',fault='slow',fault_delay_s=10.0)
        with ThreadPoolExecutor(max_workers=1) as executor:
            if attempt==0:
                future=executor.submit(send,lab,p,session,'interrupted','Remember Prague')
            else:
                future=executor.submit(request,lab,p,'POST','/conversations/'+session['sessionId']+'/retry',
                    json={'expectedRevision':session['revision'],'acknowledgeEffectRisk':True})
            deadline=time.monotonic()+10
            while calls(lab)==before:
                if time.monotonic()>deadline:pytest.fail('owned interrupted provider attempt was not observed')
                time.sleep(.05)
            try:kill_worker(lab,'a')
            finally:control(lab,scenario='conversation')
            try:future.result(timeout=100)
            except httpx.HTTPError:pass
            else:pytest.fail('killed owned worker returned a successful response')
        replace_worker(lab,'a');replace_worker(lab,'b')
        session=recover(lab,p,session['sessionId'])
        assert session['recoveryStatus']=='needsResolution' and calls(lab)==before+1
        denied=request(lab,p,'POST','/conversations/'+session['sessionId']+'/retry',
            json={'expectedRevision':session['revision'],'acknowledgeEffectRisk':False})
        assert denied.status_code==422 and calls(lab)==before+1
    before=calls(lab)
    blocked=request(lab,p,'POST','/conversations/'+session['sessionId']+'/retry',
        json={'expectedRevision':session['revision'],'acknowledgeEffectRisk':True})
    assert blocked.status_code==422
    assert blocked.json()=={'detail':{'code':'sessionLimit','limit':'maxAttemptsPerTurn'}}
    assert calls(lab)==before
