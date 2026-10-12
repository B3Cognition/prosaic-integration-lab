"""Hostile conversation inputs against installed HTTP/owned PostgreSQL bindings."""
from copy import deepcopy
import uuid

import httpx
import psycopg
import pytest

from lab_runner.conversation_faults import temporary_conversation_configuration
from lab_runner.conversation_scenarios import create,request,send
from lab_runner.native_scenarios import calls,control
from test_conversation_journey import conversation_model,history,principal


@pytest.fixture(scope='module')
def owned_session(lab):
    owner=principal(lab,'user-0004');key=uuid.uuid4().hex
    return owner,key,create(lab,owner,key)


def body(session,**changes):
    return {'messageId':'security-message','message':'hello',
        'expectedRevision':session['revision'],**changes}


def counters(lab,sid):
    result=httpx.get(lab['model']+'/stats',timeout=5);result.raise_for_status()
    stats=result.json()
    with psycopg.connect(lab['app_dsn']) as connection:
        effects=connection.execute('SELECT namespace,business_key,amount FROM lab_fixture.effects '
            'WHERE business_key LIKE %s ORDER BY namespace,business_key',(sid+':%',)).fetchall()
        journal=connection.execute('SELECT operation_namespace,operation_key,state,outcome '
            'FROM lab_app.tool_operations WHERE operation_key LIKE %s ORDER BY operation_namespace,operation_key',
            (sid+':%',)).fetchall()
    return stats,effects,journal


def test_missing_or_unknown_auth_cannot_access_any_conversation_operation(lab,owned_session):
    _,_,session=owned_session;path='/conversations/'+session['sessionId'];before=calls(lab)
    operations=[('GET',path,None),('GET',path+'/history',None),('GET',path+'/usage',None),
        ('POST',path+'/messages',body(session)),('POST',path+'/recover',{}),
        ('POST',path+'/retry',{'expectedRevision':session['revision'],'acknowledgeEffectRisk':True}),
        ('POST','/conversations',{})]
    for headers in ({},{'Authorization':'Bearer unknown-fixture-token'}):
        for method,url,payload in operations:
            response=httpx.request(method,lab['b']+url,headers=headers,json=payload,timeout=10)
            assert response.status_code==401 and response.json()=={'detail':'unauthenticated'}
    assert calls(lab)==before


@pytest.mark.parametrize('actor',['bob','carol'],ids=['same-tenant','other-tenant'])
def test_nonowner_cannot_read_history_usage_send_recover_or_retry(lab,owned_session,actor):
    _,_,session=owned_session;p=principal(lab,actor);path='/conversations/'+session['sessionId']
    before=calls(lab)
    operations=[('GET',path,None),('GET',path+'/history',None),('GET',path+'/usage',None),
        ('POST',path+'/messages',body(session)),('POST',path+'/recover',{}),
        ('POST',path+'/retry',{'expectedRevision':session['revision'],'acknowledgeEffectRisk':True})]
    for method,url,payload in operations:
        response=request(lab,p,method,url,replica='b',json=payload)
        assert response.status_code==404 and response.json()=={'detail':'not_found'}
    assert calls(lab)==before


@pytest.mark.parametrize('field',['tenant','actor','billingAccount','namespace','base_dir','role',
    'history','messages','model','model_tier','config','tools','workflow','bindingVersion','inputData'])
def test_message_body_cannot_introduce_authority_or_execution_configuration(lab,owned_session,field):
    p,_,session=owned_session;before=calls(lab)
    response=request(lab,p,'POST','/conversations/'+session['sessionId']+'/messages',
        json=body(session,**{field:'PRIVATE_UNTRUSTED_AUTHORITY'}))
    assert response.status_code==422 and response.json()=={'detail':'invalid_request'}
    assert calls(lab)==before and history(lab,p,session['sessionId'])==[]


def test_create_body_and_duplicate_creation_key_header_are_closed(lab,owned_session):
    p,_,_=owned_session;before=calls(lab)
    for supplied in ({'base_dir':'PRIVATE_PATH'},{'actor':'bob'},{'tools':['fixture_apply_b']}):
        response=request(lab,p,'POST','/conversations',headers={'Idempotency-Key':uuid.uuid4().hex},json=supplied)
        assert response.status_code==422 and response.json()=={'detail':'invalid_request'}
    token=next(token for token,value in lab['principals'].items() if value==p)
    response=httpx.post(lab['a']+'/conversations',headers=[('Authorization','Bearer '+token),
        ('Idempotency-Key','first'),('Idempotency-Key','second')],json={},timeout=10)
    assert response.status_code==422 and calls(lab)==before


@pytest.mark.parametrize('raw',[
    b'{"messageId":"one","messageId":"two","message":"hello","expectedRevision":"x"}',
    b'{"messageId":"one","message":"hello","expectedRevision":NaN}',
    b'["untrusted","history"]',b'{"message":"\xff"}',
    b'{"messageId":"one","message":"\\ud800","expectedRevision":"x"}'],
    ids=['duplicate-field','nonfinite','array','invalid-utf8','unpaired-surrogate'])
def test_malformed_json_is_rejected_without_admission_or_dispatch(lab,owned_session,raw):
    p,_,session=owned_session;before=calls(lab)
    response=request(lab,p,'POST','/conversations/'+session['sessionId']+'/messages',content=raw)
    assert response.status_code==422
    assert 'PRIVATE' not in response.text and calls(lab)==before
    assert history(lab,p,session['sessionId'])==[]


def test_interpreter_fabricated_registered_effect_call_has_zero_consequential_dispatch(lab):
    p=principal(lab,'user-0006');session=send(lab,p,create(lab,p,uuid.uuid4().hex),'find','Find players')
    pending=session['pendingInteraction'];control(lab,scenario='conversation_interpreter_tool')
    before,effects,journal=counters(lab,session['sessionId'])
    reply=send(lab,p,session,'fabricated','the second result',interaction_ref=pending['reference'])
    after,new_effects,new_journal=counters(lab,session['sessionId'])
    assert reply['status']=='failed' and reply['failureCode']=='invalidToolRequest'
    assert {key:value for key,value in reply['pendingInteraction'].items() if key!='reference'}=={
        key:value for key,value in pending.items() if key!='reference'}
    assert after['calls']==before['calls']+1
    assert after['interpreter_calls']==before['interpreter_calls']+1
    assert after['interpreter_tool_definitions']==before['interpreter_tool_definitions']==0
    for event in ('tool-authorizer','tool-resolver','tool-claimed','tool-handler','tool-effect','tool-committed'):
        assert after['barriers'][event]==before['barriers'][event]
    assert new_effects==effects==[] and new_journal==journal==[]


def test_foreign_and_replaced_interaction_references_fail_before_interpretation(lab):
    p=principal(lab,'user-0006');session=send(lab,p,create(lab,p,uuid.uuid4().hex),'find','Find players')
    old=session['pendingInteraction']['reference'];before=calls(lab)
    response=request(lab,p,'POST','/conversations/'+session['sessionId']+'/messages',
        json=body(session,messageId='foreign',message='the second result',interactionRef='f'*64))
    assert response.status_code==409 and response.json()=={'detail':{'code':'interactionStale'}}
    assert calls(lab)==before
    session=send(lab,p,session,'selected','the second result',interaction_ref=old)
    before=calls(lab)
    response=request(lab,p,'POST','/conversations/'+session['sessionId']+'/messages',
        json=body(session,messageId='replaced',message='approve',interactionRef=old))
    assert response.status_code==409 and response.json()=={'detail':{'code':'interactionStale'}}
    assert calls(lab)==before
    current=request(lab,p,'GET','/conversations/'+session['sessionId']).json()
    assert current==session


def test_current_grant_revocation_precedes_duplicate_create_message_and_reads(lab,owned_session):
    p,key,session=owned_session
    def revoke(config):
        config['tenants'][p['tenant_id']]['enabled']=False
        return config
    before=calls(lab)
    with temporary_conversation_configuration(lab,revoke):
        path='/conversations/'+session['sessionId']
        operations=[('GET',path,None),('GET',path+'/history',None),('GET',path+'/usage',None),
            ('POST',path+'/messages',body(session)),('POST',path+'/recover',{}),
            ('POST',path+'/retry',{'expectedRevision':session['revision'],'acknowledgeEffectRisk':True})]
        for method,url,payload in operations:
            response=request(lab,p,method,url,replica='b',json=payload)
            assert response.status_code==403 and response.json()=={'detail':'conversation_access_denied'}
        replay=request(lab,p,'POST','/conversations',replica='b',headers={'Idempotency-Key':key},json={})
        assert replay.status_code==403
    assert calls(lab)==before


@pytest.mark.parametrize('field',['operation_namespace','journal_identity','model'])
def test_reconstructed_host_binding_drift_cannot_read_recover_or_dispatch(lab,owned_session,field):
    p,_,session=owned_session
    def drift(config):
        version=config['tenants'][p['tenant_id']]['binding_version']
        bundle=next(bundle for bundle in config['bundles'] if bundle['version']==version)
        bundle[field]+='-drift'
        return config
    before=calls(lab)
    with temporary_conversation_configuration(lab,drift):
        path='/conversations/'+session['sessionId']
        for method,suffix,payload in [('GET','',None),('GET','/history',None),('GET','/usage',None),
                ('POST','/recover',{}),('POST','/messages',body(session))]:
            response=request(lab,p,method,path+suffix,replica='b',json=payload)
            assert response.status_code==409 and response.json()=={'detail':{'code':'bindingConflict'}}
    assert calls(lab)==before


def test_removed_retained_version_is_denied_before_old_creation_replay(lab,owned_session):
    p,key,session=owned_session
    def remove(config):
        grant=config['tenants'][p['tenant_id']];version=grant['binding_version']
        new=deepcopy(next(bundle for bundle in config['bundles'] if bundle['version']==version))
        new['version']='security-'+uuid.uuid4().hex;config['bundles'].append(new)
        grant['binding_version']=new['version'];grant['retained_versions']=[]
        return config
    before=calls(lab)
    with temporary_conversation_configuration(lab,remove):
        response=request(lab,p,'GET','/conversations/'+session['sessionId'],replica='b')
        assert response.status_code==403
        response=request(lab,p,'POST','/conversations',replica='b',headers={'Idempotency-Key':key},json={})
        assert response.status_code==403
    assert calls(lab)==before
