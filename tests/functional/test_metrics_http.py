import re
from types import SimpleNamespace
from fastapi.testclient import TestClient
from prosaic_integration_lab import app as service

def test_operator_metrics_are_separate_from_user_auth_and_logs_are_curated(monkeypatch,caplog):
    from prosaic_integration_lab.observability import logger
    monkeypatch.setattr(logger,'handlers',[caplog.handler])
    class Execution:
        def __init__(self,config,**kwargs):
            self.config={'namespace':'scope','environment':'sandbox'}
            self.metadata=SimpleNamespace(phase_counts=lambda *args:{'starting':2})
        def ready(self): pass
        def close(self): pass
        def read(self,function,*args): return function(*args)
        async def inspected(self,function,*args): return function(*args)
    monkeypatch.setattr(service,'Execution',Execution)
    monkeypatch.setattr(service,'load_config',lambda:{'principals':{},'metrics_token':'a'*64})
    with TestClient(service.create_app()) as client:
        assert client.get('/metrics',headers={'Authorization':'Bearer PRIVATE'}).status_code==401
        assert client.get('/metrics').status_code==401
        response=client.get('/metrics',headers={'Authorization':'Bearer '+'a'*64})
        assert response.status_code==200
        assert 'lab_reservation_phase{phase="starting"} 2' in response.text
        assert client.post('/metrics',headers={'Authorization':'Bearer '+'a'*64},content='PRIVATE').status_code==405
        rejected=client.post('/runs',content='PRIVATE',headers={'X-Request-ID':'PRIVATE'})
        assert rejected.status_code==401
        assert re.fullmatch('[0-9a-f]{32}',rejected.headers['x-request-id'])
    assert 'PRIVATE' not in caplog.text

def test_metrics_disabled_by_default(monkeypatch):
    class Execution:
        def __init__(self,config,**kwargs): pass
        def ready(self): pass
        def close(self): pass
    monkeypatch.setattr(service,'Execution',Execution)
    monkeypatch.setattr(service,'load_config',lambda:{'principals':{}})
    with TestClient(service.create_app()) as client:
        assert client.get('/metrics').status_code==404
