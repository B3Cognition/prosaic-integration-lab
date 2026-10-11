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
