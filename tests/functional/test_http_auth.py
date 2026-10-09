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
