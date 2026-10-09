from types import SimpleNamespace
from fastapi import HTTPException
from fastapi.testclient import TestClient
from prosaic_integration_lab import app as service


def test_saturated_http_start_never_calls_reservation_boundary(monkeypatch):
    writes = []
    class Execution:
        def __init__(self, config):
            self.fingerprint = 'fixture'
            self.metadata = SimpleNamespace(reserve=self.reserve)
        def ready(self): pass
        def close(self): pass
        def reserve(self,*args,**kwargs):
            writes.append('reserved')
            return {'phase':'reserved'}
        def start(self,*args): raise AssertionError('execution must not run')
        def start_request(self,*args): raise AssertionError('reservation must not run')
        async def admitted(self,*args): raise HTTPException(503,'capacity_exhausted')
    config = {'principals':{'token':{'tenant_id':'a','actor_id':'alice','billing_account_id':'payer'}},
              'namespace':'fixture','environment':'sandbox'}
    monkeypatch.setattr(service,'load_config',lambda:config)
    monkeypatch.setattr(service,'Execution',Execution)
    with TestClient(service.create_app()) as client:
        for index in range(3):
            response = client.post('/runs',json={'task':'neutral fixture'},
                headers={'Authorization':'Bearer token','Idempotency-Key':str(index)})
            assert response.status_code == 503
    assert writes == []
