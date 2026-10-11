"""HTTP-only host protocol doubles; installed SDK acceptance is a separate lane."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    import prosaic_integration_lab.app as module
    calls=[]
    class Chat:
        def create_request(self,principal,key):
            calls.append(('create',principal,key));return {'sessionId':'a'*32,'revision':'v1'}
        def send_request(self,principal,session_id,**kwargs):
            calls.append(('send',principal,kwargs));return {'status':'completed'}
        def status_request(self,*args):return {'status':'ready'}
        def history_request(self,*args):return {'messages':[]}
        def usage_request(self,*args):return {'conversation':{}}
        def recover_request(self,*args):return {'status':'ready'}
        def retry_request(self,*args,**kwargs):calls.append(('retry',kwargs));return {'status':'failed'}
    class Host:
        def __init__(self,*args,**kwargs):self.conversation=Chat();self.native=None
        def ready(self):pass
        def close(self):pass
        async def admitted(self,function,*args,**kwargs):return function(*args,**kwargs)
        def read(self,function,*args):return function(*args)
    monkeypatch.setattr(module,'load_config',lambda:{'principals':{'token':{
        'tenant_id':'one','actor_id':'alice','billing_account_id':'payer'}},'conversation':{}})
    monkeypatch.setattr(module,'Execution',Host)
    with TestClient(module.create_app()) as http:
        http.headers['Authorization']='Bearer token'
        yield http,calls


def body(**overrides):
    return {'messageId':'m1','message':'hello','expectedRevision':'v1',**overrides}


def test_closed_creation_and_trusted_identity(client):
    http,calls=client
    assert http.post('/conversations',json={},headers={'Idempotency-Key':'create-1'}).status_code==200
    assert calls[0][1].actor_id=='alice'
    assert http.post('/conversations',json={'actor':'bob'},headers={'Idempotency-Key':'create-2'}).status_code==422
    assert len(calls)==1


@pytest.mark.parametrize('field',['actor','tenant','billingAccount','tools','history','config','role'])
def test_messages_reject_client_authority_before_host(client,field):
    http,calls=client
    assert http.post('/conversations/'+'a'*32+'/messages',json=body(**{field:'untrusted'})).status_code==422
    assert calls==[]


def test_duplicate_keys_rejected_before_host(client):
    http,calls=client
    raw='{"messageId":"m1","message":"first","message":"second","expectedRevision":"v1"}'
    assert http.post('/conversations/'+'a'*32+'/messages',content=raw).status_code==422
    assert calls==[]


def test_valid_message_uses_closed_camel_case_host_contract(client):
    http,calls=client
    response=http.post('/conversations/'+'a'*32+'/messages',json=body(interactionRef='current'))
    assert response.status_code==200
    assert calls[0][2]=={'message_id':'m1','message':'hello','expected_revision':'v1','interaction_ref':'current'}


def test_retry_requires_explicit_literal_true(client):
    http,calls=client
    path='/conversations/'+'a'*32+'/retry'
    for value in (False,1,'true',None):
        assert http.post(path,json={'expectedRevision':'v1','acknowledgeEffectRisk':value}).status_code==422
    assert calls==[]
    assert http.post(path,json={'expectedRevision':'v1','acknowledgeEffectRisk':True}).status_code==200


def test_only_exact_messages_path_receives_larger_envelope(client):
    http,calls=client
    message='界'*5400
    assert http.post('/conversations/'+'a'*32+'/messages',json=body(message=message)).status_code==200
    assert http.post('/conversations/'+'a'*32+'/messages',content=b'x'*102401).status_code==413
    assert http.post('/runs',content=b'x'*8193).status_code==413
    assert http.post('/conversations/'+'a'*32+'/messages/extra',content=b'x'*8193).status_code==413


def test_unauthenticated_requests_never_reach_host(client):
    http,calls=client
    assert http.post('/conversations',json={},headers={'Authorization':'Bearer invalid','Idempotency-Key':'one'}).status_code==401
    assert calls==[]
