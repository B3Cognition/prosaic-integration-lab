from types import SimpleNamespace
from fastapi.testclient import TestClient
from prosaic_integration_lab import app as service
from prosaic_integration_lab.views import public_run

def test_http_owner_sees_plain_json_review_without_private_operator_state(monkeypatch):
    class Execution:
        def __init__(self,config,**kwargs): self.metadata = SimpleNamespace(owned=self.owned)
        def ready(self): pass
        def close(self): pass
        def owned(self,actor,run_id): return {'run_id':run_id} if actor.actor_id == 'alice' else None
        def read(self,function): return function()
        def status(self,reservation):
            return public_run(reservation['run_id'],{'status':'waiting','current':'approval',
                'choices':['approve','reject'],'outputs':{'author':{'result':'<script>fixture</script>'}},
                'inputs':{'task':'PRIVATE'},'history':['PRIVATE']},'reviewed-revision',workflow='synthetic')
    mapping = {actor:{'tenant_id':'a','actor_id':actor,'billing_account_id':'payer'} for actor in ('alice','bob')}
    monkeypatch.setattr(service,'load_config',lambda:{'principals':mapping})
    monkeypatch.setattr(service,'Execution',Execution)
    with TestClient(service.create_app()) as client:
        owner = client.get('/runs/fixture',headers={'Authorization':'Bearer alice'})
        assert owner.status_code == 200
        assert owner.headers['content-type'] == 'application/json'
        assert owner.json()['review']['revision'] == 'reviewed-revision'
        assert owner.json()['review']['result']['result'] == '<script>fixture</script>'
        assert 'PRIVATE' not in owner.text
        assert client.get('/runs/fixture',headers={'Authorization':'Bearer bob'}).status_code == 404
