"""Exact-owned worker loss with actual PG session state and independent counters."""
from concurrent.futures import ThreadPoolExecutor
import time
import uuid

import httpx
import psycopg
import pytest

from lab_runner.conversation_faults import kill_worker,restore_workers_after_loss,partition_session_worker_a
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


def effect_evidence(lab,sid):
    key=sid+':player-b'
    with psycopg.connect(lab['app_dsn']) as connection:
        domain=connection.execute('SELECT namespace,business_key,amount FROM lab_fixture.effects '
            'WHERE business_key=%s ORDER BY namespace',(key,)).fetchall()
        journal=connection.execute('SELECT operation_namespace,operation_key,signature,claim_token,state,outcome '
            'FROM lab_app.tool_operations WHERE operation_key=%s ORDER BY operation_namespace',(key,)).fetchall()
    return domain,journal


@pytest.mark.parametrize('phase,effects',[
    ('workflowCommandPrepared',0),('workflowCommandReturned',1)],ids=['before-approved-effect','after-committed-effect'])
def test_approval_handoff_loss_preserves_effect_journal_without_resume(lab,phase,effects):
    from prosaic_harness_postgres import PostgresRunStore
    p=principal(lab,'user-0008')
    session=send(lab,p,create(lab,p,uuid.uuid4().hex),'find','Find players')
    session=send(lab,p,session,'second','the second result',interaction_ref=session['pendingInteraction']['reference'])
    accepted=loss(lab,p,session,phase,'approve',ref=session['pendingInteraction']['reference'])
    original=effect_evidence(lab,session['sessionId'])
    assert len(original[0])==effects and len(original[1])==effects
    if effects:assert original[1][0][4]=='completed'
    with PostgresRunStore(lab['harness_dsn'],namespace=lab['namespace']) as store:
        run=store.load_run(session['sessionId'])
        assert run.state['status']==('completed' if effects else 'waiting')
    for _ in range(2):
        result=recover(lab,p,session['sessionId'])
        assert result['recoveryStatus']=='needsResolution' and calls(lab)==accepted
        assert effect_evidence(lab,session['sessionId'])==original
        with PostgresRunStore(lab['harness_dsn'],namespace=lab['namespace']) as store:
            assert store.load_run(session['sessionId']).revision==run.revision


def test_two_workers_admit_one_duplicate_and_one_competing_revision(lab):
    p=principal(lab,'user-0009');session=create(lab,p,uuid.uuid4().hex)
    for names in (('duplicate','duplicate'),('left','right')):
        before=calls(lab)
        def submit(worker,message_id):
            return request(lab,p,'POST','/conversations/'+session['sessionId']+'/messages',replica=worker,
                json={'messageId':message_id,'message':'Remember Prague','expectedRevision':session['revision']})
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures=[executor.submit(submit,worker,message_id) for worker,message_id in zip(('a','b'),names)]
            replies=[future.result(timeout=100) for future in futures]
        assert any(reply.status_code==200 for reply in replies)
        assert all(reply.status_code in {200,409} for reply in replies)
        assert calls(lab)==before+1
        current=request(lab,p,'GET','/conversations/'+session['sessionId'],replica='b').json()
        assert current['turnSequence']==(1 if names[0]=='duplicate' else 2)
        if names[0]==names[1]:
            assert send(lab,p,session,names[0],'Remember Prague',replica='b')==current
            assert calls(lab)==before+1
        else:assert sum(reply.status_code==200 for reply in replies)==1
        session=current


def test_live_session_partition_takeover_fences_late_worker_and_adopts_receipt(lab):
    from test_conversation_journey import history
    p=principal(lab,'user-0010');session=create(lab,p,uuid.uuid4().hex)
    def durable():
        with psycopg.connect(lab['conversation']['dsn']) as connection:
            state=connection.execute('SELECT revision,document FROM prosaic_harness_conversations.sessions '
                'WHERE namespace=%s AND session_id=%s',(lab['namespace'],session['sessionId'])).fetchall()
            receipts=connection.execute('SELECT invocation_id,sha256,document FROM prosaic_harness_conversations.receipts '
                'WHERE namespace=%s AND session_id=%s ORDER BY invocation_id',
                (lab['namespace'],session['sessionId'])).fetchall()
        return state,receipts
    with partition_session_worker_a(lab) as proxy:
        before=httpx.get(lab['model']+'/stats',timeout=5).json()['barriers']['receiptSaved']
        control(lab,scenario='conversation',effect_gate='receiptSaved')
        with ThreadPoolExecutor(max_workers=1) as executor:
            future=executor.submit(request,lab,p,'POST','/conversations/'+session['sessionId']+'/messages',
                json={'messageId':'partitioned','message':'Remember Prague','expectedRevision':session['revision']})
            try:
                observed(lab,'receiptSaved',before);accepted=calls(lab)
                partition=proxy.control(True)
                assert partition['blocked'] is True and partition['active']==0
                replace_worker(lab,'b')
                independent=create(lab,p,uuid.uuid4().hex,replica='b')
                assert independent['status']=='ready' and calls(lab)==accepted
                separate=request(lab,p,'GET','/conversations/'+independent['sessionId'],replica='b')
                assert separate.status_code==200 and separate.json()==independent
                assert history(lab,p,independent['sessionId'],replica='b')==[]
                assert calls(lab)==accepted
                adopted=recover(lab,p,session['sessionId'])
                assert adopted['status']=='completed' and adopted['answer']=='Your city is Prague.'
                assert calls(lab)==accepted
                committed=durable()
                assert len(committed[0])==1 and len(committed[1])==1
            finally:
                control(lab,scenario='conversation')
                proxy.control(False)
            late=future.result(timeout=100)
            assert late.status_code in {409,503}
        assert request(lab,p,'GET','/conversations/'+session['sessionId'],replica='b').json()==adopted
        assert len(history(lab,p,session['sessionId'],replica='b'))==2 and calls(lab)==accepted
        assert durable()==committed
        assert recover(lab,p,session['sessionId'])==adopted and calls(lab)==accepted
        assert durable()==committed
