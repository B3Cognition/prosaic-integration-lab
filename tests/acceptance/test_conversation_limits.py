"""Bounded public admission; retained owner/deployment quotas run last."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from contextlib import contextmanager
import json
import uuid

import psycopg
import pytest

from lab_runner.conversation_faults import temporary_conversation_configuration
from lab_runner.conversation_scenarios import create,request,send
from lab_runner.native_scenarios import calls,control
from test_conversation_journey import conversation_model,history,principal


@contextmanager
def bounded_binding(lab,policy,**fixture):
    p=principal(lab,'user-0016')
    def limit(config):
        grant=config['tenants'][p['tenant_id']];old=grant['binding_version']
        bundle=deepcopy(next(bundle for bundle in config['bundles'] if bundle['version']==old))
        bundle['version']='limits-'+uuid.uuid4().hex;bundle['policy']=policy;bundle.update(fixture)
        config['bundles'].append(bundle)
        grant['binding_version']=bundle['version']
        grant['retained_versions']=list(dict.fromkeys([old,*grant.get('retained_versions',[])]))
        return config
    with temporary_conversation_configuration(lab,limit):yield p


def post(lab,p,session,message_id='overflow',message='hello',**kwargs):
    return request(lab,p,'POST','/conversations/'+session['sessionId']+'/messages',replica='b',
        json={'messageId':message_id,'message':message,'expectedRevision':session['revision'],**kwargs})


def test_utf8_user_boundary_accepts_exact_16kib_and_rejects_one_extra_byte(lab):
    p=principal(lab,'user-0015');session=create(lab,p,uuid.uuid4().hex)
    before=calls(lab);text='é'*8192
    response=post(lab,p,session,message_id='boundary',message=text)
    response.raise_for_status();completed=response.json()
    assert completed['status']=='completed' and calls(lab)==before+1
    saved=history(lab,p,session['sessionId']);assert saved[0]['content']==[{'type':'text','text':text}]
    before=calls(lab);response=post(lab,p,completed,message_id='too-large',message=text+'x')
    assert response.status_code==422 and response.json()=={'detail':{'code':'invalidMessage'}}
    assert calls(lab)==before and history(lab,p,session['sessionId'])==saved


def test_json_escaping_fits_envelope_without_changing_raw_utf8_admission(lab):
    p=principal(lab,'user-0015');session=create(lab,p,uuid.uuid4().hex);text='\x00'*16384
    wire=json.dumps({'messageId':'escaped','message':text,'expectedRevision':session['revision']}).encode()
    assert 8192<len(wire)<102400
    before=calls(lab)
    response=request(lab,p,'POST','/conversations/'+session['sessionId']+'/messages',content=wire,
        headers={'Content-Type':'application/json'})
    response.raise_for_status();assert response.json()['status']=='completed'
    assert calls(lab)==before+1 and history(lab,p,session['sessionId'])[0]['content']==[{'type':'text','text':text}]


def test_messages_envelope_ceiling_rejects_before_sdk_admission(lab):
    p=principal(lab,'user-0015');session=create(lab,p,uuid.uuid4().hex);before=calls(lab)
    response=request(lab,p,'POST','/conversations/'+session['sessionId']+'/messages',content=b'x'*102401)
    assert response.status_code==413 and calls(lab)==before
    assert history(lab,p,session['sessionId'])==[]


@pytest.mark.parametrize('policy,limit',[
    ({'max_turns':1},'maxTurns'),({'max_attempts':1},'maxAttempts'),
    ({'max_history_bytes':131071},'maxHistoryBytes'),({'max_state_bytes':65536},'maxStateBytes'),
    ({'max_total_receipt_bytes':8388607},'maxTotalReceiptBytes'),
    ({'max_provider_requests':0},'maxProviderRequests'),({'max_tool_calls':0},'maxToolCalls')],
    ids=['turns','attempts','history-reservation','snapshot-reservation','receipt-reservation','provider-reservation','tool-reservation'])
def test_session_capacity_rejection_preserves_history_revision_and_exact_replay(lab,policy,limit):
    with bounded_binding(lab,policy) as p:
        key=uuid.uuid4().hex;session=create(lab,p,key,replica='b');initial=session
        # Only B receives this temporary binding; A retains its original grant.
        assert request(lab,p,'GET','/conversations/'+session['sessionId']+'/history').status_code==403
        if limit in {'maxTurns','maxAttempts'}:
            session=send(lab,p,session,'admitted','Remember Prague',replica='b')
        before=calls(lab);saved=history(lab,p,session['sessionId'],replica='b')
        rejected=post(lab,p,session)
        assert rejected.status_code==422 and rejected.json()=={'detail':{'code':'sessionLimit','limit':limit}}
        assert calls(lab)==before and history(lab,p,session['sessionId'],replica='b')==saved
        status=request(lab,p,'GET','/conversations/'+session['sessionId'],replica='b').json()
        assert status==session
        assert create(lab,p,key,replica='b')==session
        if saved:
            replay=send(lab,p,initial,'admitted','Remember Prague',replica='b')
            assert replay==session and calls(lab)==before


def test_actual_provider_context_overflow_has_safe_code_and_zero_new_history(lab):
    with bounded_binding(lab,{'max_input_bytes':16384}) as p:
        session=create(lab,p,uuid.uuid4().hex,replica='b');before=calls(lab)
        response=post(lab,p,session,message='x'*16384)
        assert response.status_code==422 and response.json()['detail']['code']=='contextLimit'
        assert set(response.json()['detail'])<={'code','limit'}
        assert calls(lab)==before and history(lab,p,session['sessionId'],replica='b')==[]
        assert request(lab,p,'GET','/conversations/'+session['sessionId'],replica='b').json()==session


def test_complete_turn_encoding_overflow_rejects_before_provider_call(lab):
    with bounded_binding(lab,{'max_turn_bytes':1000}) as p:
        session=create(lab,p,uuid.uuid4().hex,replica='b');before=calls(lab)
        response=post(lab,p,session,message='\\'*500)
        assert response.status_code==422 and response.json()=={'detail':{'code':'contextLimit','limit':'maxTurnBytes'}}
        assert calls(lab)==before and history(lab,p,session['sessionId'],replica='b')==[]


def test_json_node_capacity_stops_new_turns_without_evicting_admitted_history(lab):
    with bounded_binding(lab,{'max_json_nodes':9000}) as p:
        initial=create(lab,p,uuid.uuid4().hex,replica='b');session=initial;admitted=None
        for index in range(4):
            message_id='node-'+str(index);response=post(lab,p,session,message_id=message_id)
            if response.status_code==422:
                assert response.json()=={'detail':{'code':'sessionLimit','limit':'maxJsonNodes'}}
                break
            response.raise_for_status();session=response.json();admitted=message_id
            assert session['status']=='completed'
        else:pytest.fail('bounded JSON node allowance admitted every tested turn')
        before=calls(lab);saved=history(lab,p,session['sessionId'],replica='b')
        rejected=post(lab,p,session,message_id='nodes-exhausted')
        assert rejected.status_code==422 and rejected.json()=={'detail':{'code':'sessionLimit','limit':'maxJsonNodes'}}
        assert calls(lab)==before and history(lab,p,session['sessionId'],replica='b')==saved
        if admitted:
            assert send(lab,p,initial,admitted,'hello',replica='b')==session
            assert calls(lab)==before


def test_json_depth_ceiling_retains_failed_user_without_partial_tool_exchange(lab):
    with bounded_binding(lab,{'max_json_depth':15}) as p:
        session=create(lab,p,uuid.uuid4().hex,replica='b');before=calls(lab)
        response=post(lab,p,session,message='find players now');response.raise_for_status()
        reply=response.json()
        assert reply['status']=='failed' and reply['failureCode']=='outputLimit'
        assert calls(lab)==before+1 and 'answer' not in reply
        saved=history(lab,p,session['sessionId'],replica='b')
        assert saved==[{'role':'user','content':[{'type':'text','text':'find players now'}],
            'turnStatus':'failed','failureCode':'outputLimit'}]
        assert request(lab,p,'POST','/conversations/'+session['sessionId']+'/recover',replica='b',json={}).json()==reply
        assert calls(lab)==before+1


def test_small_sealed_receipt_ceiling_preserves_output_and_exact_replay(lab):
    policy={'max_turn_bytes':8192,'max_assistant_bytes':256,'max_receipt_bytes':22000}
    with bounded_binding(lab,policy) as p:
        session=create(lab,p,uuid.uuid4().hex,replica='b');before=calls(lab);text='x'*6000
        response=post(lab,p,session,message=text);response.raise_for_status();completed=response.json()
        assert completed['status']=='completed' and completed['failureCode'] is None
        assert calls(lab)==before+1
        saved=history(lab,p,session['sessionId'],replica='b')
        assert saved[0]['role']=='user' and saved[0]['content']==[{'type':'text','text':text}]
        with psycopg.connect(lab['conversation']['dsn']) as connection:
            receipts=connection.execute('SELECT octet_length(document) FROM prosaic_harness_conversations.receipts '
                'WHERE namespace=%s AND session_id=%s',(lab['namespace'],session['sessionId'])).fetchall()
        assert len(receipts)==1 and 0<receipts[0][0]<=policy['max_receipt_bytes']
        assert send(lab,p,session,'overflow',text,replica='b')==completed
        assert request(lab,p,'POST','/conversations/'+session['sessionId']+'/recover',replica='b',json={}).json()==completed
        assert history(lab,p,session['sessionId'],replica='b')==saved
        assert calls(lab)==before+1


@pytest.mark.parametrize('policy,code',[
    ({'max_input_bytes':4096},'contextLimit'),
    ({'max_turn_bytes':4096,'max_assistant_bytes':256,'max_receipt_bytes':18000},'outputLimit')],
    ids=['context-after-tool','receipt-evidence-after-tool'])
def test_capacity_after_completed_lookup_retains_tool_usage_and_failed_user(lab,policy,code):
    with bounded_binding(lab,policy,fixture_lookup_padding=3000) as p:
        session=create(lab,p,uuid.uuid4().hex,replica='b');before=calls(lab)
        response=post(lab,p,session,message='find players now');response.raise_for_status();failed=response.json()
        assert failed['status']=='failed' and failed['failureCode']==code
        assert calls(lab)==before+1 and 'answer' not in failed
        saved=history(lab,p,session['sessionId'],replica='b')
        assert saved==[{'role':'user','content':[{'type':'text','text':'find players now'}],
            'turnStatus':'failed','failureCode':code}]
        usage=request(lab,p,'GET','/conversations/'+session['sessionId']+'/usage',replica='b').json()['conversation']
        assert usage['total_calls']==1 and usage['complete_calls']==1
        with psycopg.connect(lab['conversation']['dsn']) as connection:
            rows=connection.execute('SELECT document FROM prosaic_harness_conversations.receipts '
                'WHERE namespace=%s AND session_id=%s',(lab['namespace'],session['sessionId'])).fetchall()
        assert len(rows)==1
        receipt=json.loads(rows[0][0]);evidence=receipt['evidence']
        assert evidence['providerAttempts']==1 and evidence['toolAttempts']==1
        assert len(evidence['toolOutcomes'])==1 and evidence['toolOutcomes'][0]['status']=='completed'
        if 'max_receipt_bytes' in policy:assert len(rows[0][0].encode())<=policy['max_receipt_bytes']
        assert send(lab,p,session,'overflow','find players now',replica='b')==failed
        assert request(lab,p,'POST','/conversations/'+session['sessionId']+'/recover',replica='b',json={}).json()==failed
        assert history(lab,p,session['sessionId'],replica='b')==saved and calls(lab)==before+1


def test_final_assistant_overflow_retains_unsuccessful_user_and_usage_without_partial_exchange(lab):
    with bounded_binding(lab,{'max_assistant_bytes':64}) as p:
        session=create(lab,p,uuid.uuid4().hex,replica='b');control(lab,result_text='x'*256)
        before=calls(lab);response=post(lab,p,session,message='PRIVATE_OUTPUT_BOUNDARY')
        response.raise_for_status();failed=response.json()
        assert failed['status']=='failed' and failed['failureCode']=='outputLimit'
        assert 'answer' not in failed and calls(lab)==before+1
        assert history(lab,p,session['sessionId'],replica='b')==[{'role':'user',
            'content':[{'type':'text','text':'PRIVATE_OUTPUT_BOUNDARY'}],
            'turnStatus':'failed','failureCode':'outputLimit'}]
        usage=request(lab,p,'GET','/conversations/'+session['sessionId']+'/usage',replica='b').json()['conversation']
        assert usage['total_calls']==1
        assert 'PRIVATE_OUTPUT_BOUNDARY' not in json.dumps(failed)+json.dumps(usage)
        before=calls(lab)
        assert request(lab,p,'POST','/conversations/'+session['sessionId']+'/recover',replica='b',json={}).json()==failed
        assert calls(lab)==before


# These tests consume retained capacity and are deliberately the final lane cases.
def test_retained_owner_quota_counts_terminal_sessions_and_preserves_creation_replay(lab):
    p=principal(lab,'user-0014')
    with psycopg.connect(lab['app_dsn']) as connection:
        retained=connection.execute('SELECT count(*) FROM lab_chat.sessions WHERE tenant_id=%s AND actor_id=%s',
            (p['tenant_id'],p['actor_id'])).fetchone()[0]
    assert retained<16
    key=uuid.uuid4().hex;first=create(lab,p,key)
    completed=send(lab,p,first,'completed','Remember Prague')
    failed=create(lab,p,uuid.uuid4().hex);control(lab,scenario='conversation',fault='503')
    failed=send(lab,p,failed,'failed','This accepted turn fails')
    assert completed['status']=='completed' and failed['status']=='failed'
    control(lab,scenario='conversation')
    for _ in range(16-retained-2):create(lab,p,uuid.uuid4().hex)
    before=calls(lab)
    rejected=request(lab,p,'POST','/conversations',headers={'Idempotency-Key':uuid.uuid4().hex},json={})
    assert rejected.status_code==422 and rejected.json()=={'detail':{'code':'sessionLimit'}}
    assert create(lab,p,key,replica='b')==completed and calls(lab)==before
    with psycopg.connect(lab['app_dsn']) as connection:
        assert connection.execute('SELECT count(*) FROM lab_chat.sessions WHERE tenant_id=%s AND actor_id=%s',
            (p['tenant_id'],p['actor_id'])).fetchone()==(16,)


def test_atomic_retained_deployment_quota_blocks_only_new_keys_at_128(lab):
    with psycopg.connect(lab['app_dsn']) as connection:
        rows=connection.execute('SELECT tenant_id,actor_id,count(*) FROM lab_chat.sessions GROUP BY tenant_id,actor_id').fetchall()
    counts={(tenant,actor):count for tenant,actor,count in rows};total=sum(counts.values())
    assert total<128
    candidates=list(lab['principals'].values());first=None;key=None
    for p in candidates:
        while total<127 and counts.get((p['tenant_id'],p['actor_id']),0)<15:
            current_key=uuid.uuid4().hex;session=create(lab,p,current_key)
            if first is None:first=(p,session);key=current_key
            counts[p['tenant_id'],p['actor_id']]=counts.get((p['tenant_id'],p['actor_id']),0)+1;total+=1
    assert total==127 and first is not None
    racers=[p for p in candidates if counts.get((p['tenant_id'],p['actor_id']),0)<16][:2]
    assert len(racers)==2;before=calls(lab)
    def submit(index):
        return request(lab,racers[index],'POST','/conversations',replica=('a','b')[index],
            headers={'Idempotency-Key':uuid.uuid4().hex},json={})
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(submit,(0,1)))
    assert sorted(response.status_code for response in responses)==[200,422]
    assert next(response for response in responses if response.status_code==422).json()=={'detail':{'code':'sessionLimit'}}
    p,session=first;assert create(lab,p,key,replica='b')==session and calls(lab)==before
    with psycopg.connect(lab['app_dsn']) as connection:
        assert connection.execute('SELECT count(*) FROM lab_chat.sessions').fetchone()==(128,)
