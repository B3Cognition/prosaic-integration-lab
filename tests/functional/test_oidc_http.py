import time
import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from prosaic_integration_lab import app as service
from prosaic_integration_lab.oidc import OidcAuthenticator
import pytest

@pytest.mark.parametrize('profile',['oidc','auth0'])
def test_http_identity_verification_and_revocation_precede_request_body(monkeypatch,profile):
    private = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    key = jwt.algorithms.RSAAlgorithm.to_jwk(private.public_key(),as_dict=True)
    key.update(kid='one',alg='RS256',use='sig')
    active = [True]
    writes = []
    def endpoint(request):
        return httpx.Response(200,json={'keys':[key]} if request.url.path == '/keys' else {'active':active[0]})
    settings = {'provider':'oidc','issuer':'https://issuer.example','audience':'service',
        'jwks_uri':'https://issuer.example/keys','subjects':{'subject':
            {'tenant_id':'trusted','actor_id':'alice','billing_account_id':'payer'}},
        'introspection':{'url':'https://issuer.example/introspect','client_id':'service','client_secret':'fixture'}}
    if profile=='auth0':
        settings['provider']='auth0'
        del settings['introspection']
    class Execution:
        def __init__(self,config,**kwargs): pass
        def ready(self): pass
        def close(self): pass
        def start_request(self,actor,key,payload):
            writes.append(actor)
            return {'run_id':'fixture'}
        async def admitted(self,function,*args): return function(*args)
    monkeypatch.setattr(service,'load_config',lambda:{'authentication':settings,'deployment_mode':'production'})
    providers=[]
    def authenticator(config):
        provider=OidcAuthenticator(settings,transport=httpx.MockTransport(endpoint))
        providers.append(provider)
        return provider
    monkeypatch.setattr(service,'make_authenticator',authenticator)
    monkeypatch.setattr(service,'Execution',Execution)
    now = int(time.time())
    token = jwt.encode({'sub':'subject','iss':settings['issuer'],'aud':'service','iat':now,'exp':now+120,
        'tenant_id':'SPOOF','billing_account_id':'SPOOF'},private,algorithm='RS256',headers={'kid':'one'})
    headers = {'Authorization':'Bearer '+token,'Idempotency-Key':'fixture'}
    with TestClient(service.create_app()) as client:
        assert client.post('/runs',json={'task':'neutral fixture'},headers=headers).status_code == 200
        assert writes[0].billing_account_id == 'payer'
        active[0] = False
        if profile=='auth0':
            # Provider logout does not revoke a cached JWT. Local binding policy does.
            assert client.post('/runs',json={'task':'neutral fixture'},headers=headers).status_code == 200
            provider=providers[0]
            principal,_,not_before=provider.subjects['subject']
            provider.subjects['subject']=(principal,True,not_before)
        denied = client.post('/runs',content='invalid JSON',headers=headers)
        assert denied.status_code == 401
        assert denied.json() == {'detail':'unauthenticated'}
        assert len(writes) == (2 if profile=='auth0' else 1)
