from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from prosaic_integration_lab.identity import Principal


def test_released_sdk_cannot_silently_start_conversation():
    from prosaic_integration_lab.conversation_execution import require_conversation_sdk
    import prosaic_runtime
    if 'conversation_turn_v1' not in prosaic_runtime.ProsaicRuntime.capabilities:
        with pytest.raises(ValueError,match='conversation capability unavailable'):
            require_conversation_sdk()
    else:
        require_conversation_sdk()


def test_current_grant_is_checked_before_replay_and_owner_lookup():
    from prosaic_integration_lab.conversation_execution import current_grant
    host=SimpleNamespace(config={'conversation':{'tenants':{'one':{'enabled':True,
        'binding_version':'v1','retained_versions':['v0'],'actors':['alice']}}}})
    alice=Principal('one','alice','payer')
    assert current_grant(host,alice,'v0')['binding_version']=='v1'
    for principal in (Principal('one','bob','payer'),Principal('two','alice','payer')):
        with pytest.raises(HTTPException) as error:current_grant(host,principal)
        assert error.value.status_code==403
    host.config['conversation']['tenants']['one']['enabled']=False
    with pytest.raises(HTTPException):current_grant(host,alice,'v0')


def test_unknown_retained_version_is_not_authorized():
    from prosaic_integration_lab.conversation_execution import current_grant
    host=SimpleNamespace(config={'conversation':{'tenants':{'one':{
        'enabled':True,'binding_version':'v1'}}}})
    with pytest.raises(HTTPException):current_grant(host,Principal('one','alice','payer'),'v0')


def test_fixture_phase_observer_sends_only_public_static_event_name(monkeypatch):
    from prosaic_integration_lab.conversation_execution import phase_observer
    import httpx
    requests=[]
    class Response:
        def raise_for_status(self):pass
    def post(url,**kwargs):requests.append((url,kwargs));return Response()
    monkeypatch.setattr(httpx,'post',post)
    callback=phase_observer({'fixture_events_url':'http://owned.invalid/events'})
    callback({'event':'receiptSaved','source':'PRIVATE_SOURCE','scope':'PRIVATE_SCOPE'})
    callback({'event':'text_delta','text':'PRIVATE_TEXT'})
    assert requests==[('http://owned.invalid/events/receiptSaved',{'timeout':35})]
    assert 'PRIVATE' not in str(requests)


@pytest.mark.parametrize('settings',[None,{}, {'dsn':'private','bundles':[],'tenants':{}},
    {'dsn':'private','bundles':[{}],'tenants':{},'endpoint':'client-selected'}])
def test_invalid_conversation_configuration_is_pure_before_legacy_storage(settings):
    from prosaic_integration_lab.execution import Execution
    with pytest.raises(ValueError,match='conversation configuration'):
        Execution({'conversation':settings})


def test_revoked_create_replay_never_reaches_registry():
    from prosaic_integration_lab.conversation_execution import ConversationExecution
    execution=object.__new__(ConversationExecution)
    execution.host=SimpleNamespace(config={'conversation':{'tenants':{'one':{
        'enabled':False,'binding_version':'v1'}}}})
    class Registry:
        def creation(self,*args):pytest.fail('replay read before current authorization')
    execution.registry=Registry()
    with pytest.raises(HTTPException) as error:
        execution.create_request(Principal('one','alice','payer'),'original')
    assert error.value.status_code==403


def test_conversation_pool_closes_even_when_workflow_store_close_fails():
    from prosaic_integration_lab.execution import Execution
    events=[]
    execution=object.__new__(Execution)
    execution.operations=SimpleNamespace(close=lambda:events.append('writes'))
    execution.reads=SimpleNamespace(close=lambda:events.append('reads'))
    def failed():events.append('workflow');raise RuntimeError('closed transport')
    execution.store=SimpleNamespace(close=failed)
    execution.conversation=SimpleNamespace(close=lambda:events.append('conversation'))
    with pytest.raises(RuntimeError):execution.close()
    assert events==['writes','reads','workflow','conversation']
