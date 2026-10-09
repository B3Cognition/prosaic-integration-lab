from fastapi.testclient import TestClient
from prosaic_integration_lab import app as service

def test_bad_json_without_auth_is_rejected_before_validation(monkeypatch):
    class Execution:
        def __init__(self,config): pass
        def ready(self): pass
        def close(self): pass
    monkeypatch.setattr(service,'Execution',Execution)
    monkeypatch.setattr(service,'load_config',lambda:{'principals':{}})
    with TestClient(service.create_app()) as client:
        response = client.post('/runs',content='invalid json',headers={'Content-Type':'application/json'})
        assert response.status_code == 401
        assert response.json() == {'detail':'unauthenticated'}

def test_unexpected_route_exception_does_not_escape_to_server_logger(monkeypatch,caplog):
    class Execution:
        def __init__(self,config): pass
        def ready(self): pass
        def close(self): pass
        def start_request(self,*args): raise RuntimeError('PRIVATE_ROUTE_DIAGNOSTIC')
        async def admitted(self,function,*args): return function(*args)
    mapping = {'token':{'tenant_id':'a','actor_id':'alice','billing_account_id':'payer'}}
    monkeypatch.setattr(service,'Execution',Execution)
    monkeypatch.setattr(service,'load_config',lambda:{'principals':mapping})
    with TestClient(service.create_app()) as client:
        response = client.post('/runs',json={'task':'neutral fixture'},
            headers={'Authorization':'Bearer token','Idempotency-Key':'fixture'})
        assert response.status_code == 503
        assert response.json() == {'detail':'service_unavailable'}
    assert 'PRIVATE_ROUTE_DIAGNOSTIC' not in caplog.text
