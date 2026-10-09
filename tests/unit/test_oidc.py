import asyncio
import time
from types import SimpleNamespace
import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from prosaic_integration_lab.oidc import OidcAuthenticator, IdentityUnavailable
from prosaic_integration_lab.identity import make_authenticator
from prosaic_integration_lab import oidc

@pytest.fixture
def issuer():
    private = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    public = jwt.algorithms.RSAAlgorithm.to_jwk(private.public_key(),as_dict=True)
    public.update(kid='key-1',use='sig',alg='RS256')
    settings = {'provider':'oidc','issuer':'https://issuer.example/realm','audience':'service',
        'jwks_uri':'https://issuer.example/keys',
        'subjects':{'subject-1':{'tenant_id':'trusted','actor_id':'alice','billing_account_id':'payer'}},
        'introspection':{'url':'https://issuer.example/introspect','client_id':'service','client_secret':'fixture'}}
    state = {'keys':[public],'active':True,'requests':[]}
    def endpoint(request):
        state['requests'].append(request.url.path)
        return httpx.Response(200,json={'keys':state['keys']} if request.url.path == '/keys' else {'active':state['active']})
    def token(**overrides):
        now = int(time.time())
        claims = {'sub':'subject-1','iss':settings['issuer'],'aud':'service','iat':now,'exp':now+120,
            'tenant_id':'SPOOF','billing_account_id':'SPOOF',**overrides}
        return 'Bearer '+jwt.encode(claims,private,algorithm='RS256',headers={'kid':'key-1'})
    return settings,state,endpoint,token,private

def test_verified_subject_uses_only_server_bindings_and_online_activity(issuer):
    settings,state,endpoint,token,_ = issuer
    async def run():
        async with OidcAuthenticator(settings,transport=httpx.MockTransport(endpoint)) as provider:
            actor = await provider.authenticate(token())
            assert (actor.tenant_id,actor.actor_id,actor.billing_account_id) == ('trusted','alice','payer')
            state['active'] = False
            with pytest.raises(ValueError): await provider.authenticate(token())
    asyncio.run(run())
    assert state['requests'] == ['/keys','/introspect','/introspect']

@pytest.mark.parametrize('claim,value',[('iss','https://wrong.example'),('aud','wrong'),
    ('exp',1),('iat',4102444800),('sub','unknown'),('exp',None)])
def test_invalid_claims_never_reach_introspection(issuer,claim,value):
    settings,state,endpoint,token,_ = issuer
    async def run():
        async with OidcAuthenticator(settings,transport=httpx.MockTransport(endpoint)) as provider:
            with pytest.raises(ValueError): await provider.authenticate(token(**{claim:value}))
    asyncio.run(run())
    assert '/introspect' not in state['requests']

def test_unknown_kid_fetches_are_bounded_and_header_url_is_ignored(issuer):
    settings,state,endpoint,token,private = issuer
    async def run():
        async with OidcAuthenticator(settings,transport=httpx.MockTransport(endpoint)) as provider:
            await provider.authenticate(token())
            for index in range(20):
                value = jwt.encode({'sub':'subject-1'},private,algorithm='RS256',
                    headers={'kid':str(index),'jku':'https://untrusted.example/private'})
                with pytest.raises(ValueError): await provider.authenticate('Bearer '+value)
    asyncio.run(run())
    assert state['requests'].count('/keys') == 1

def test_provider_failure_is_sanitized_and_never_accepts(issuer):
    settings,_,_,token,_ = issuer
    def failed(request): raise httpx.ConnectError('PRIVATE credential-bearing diagnostic')
    async def run():
        async with OidcAuthenticator(settings,transport=httpx.MockTransport(failed)) as provider:
            with pytest.raises(IdentityUnavailable) as error: await provider.authenticate(token())
            assert 'PRIVATE' not in str(error.value)
    asyncio.run(run())

@pytest.mark.parametrize('settings',[{}, {'provider':'fixture'},
    {'provider':'oidc','issuer':'http://issuer.example','audience':'service','jwks_uri':'http://issuer.example/keys'}])
def test_production_configuration_fails_closed(settings):
    with pytest.raises(ValueError):
        make_authenticator({'deployment_mode':'production','authentication':settings,'principals':{}})

def test_hmac_cannot_substitute_for_rsa_key(issuer):
    settings,state,endpoint,_,_ = issuer
    async def run():
        async with OidcAuthenticator(settings,transport=httpx.MockTransport(endpoint)) as provider:
            forged = jwt.encode({'sub':'subject-1'},'fixture-only-key'*4,algorithm='HS256',headers={'kid':'key-1'})
            with pytest.raises(ValueError): await provider.authenticate('Bearer '+forged)
    asyncio.run(run())
    assert state['requests'] == []

def test_keyset_can_contain_unrelated_encryption_or_signature_algorithms(issuer):
    settings,state,endpoint,token,_ = issuer
    state['keys'].append({'kid':'unrelated','kty':'RSA','use':'enc','alg':'RSA-OAEP'})
    async def run():
        async with OidcAuthenticator(settings,transport=httpx.MockTransport(endpoint)) as provider:
            assert (await provider.authenticate(token())).actor_id == 'alice'
    asyncio.run(run())

def test_key_rotation_refreshes_after_cooldown_and_removed_keys_expire(issuer,monkeypatch):
    settings,state,endpoint,token,_ = issuer
    clock = [0]
    monkeypatch.setattr(oidc,'time',SimpleNamespace(monotonic=lambda:clock[0]))
    second = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    public = jwt.algorithms.RSAAlgorithm.to_jwk(second.public_key(),as_dict=True)
    public.update(kid='key-2',alg='RS256',use='sig')
    now = int(time.time())
    replacement = 'Bearer '+jwt.encode({'sub':'subject-1','iss':settings['issuer'],'aud':'service',
        'iat':now,'exp':now+120},second,algorithm='RS256',headers={'kid':'key-2'})
    async def run():
        async with OidcAuthenticator(settings,transport=httpx.MockTransport(endpoint)) as provider:
            await provider.authenticate(token())
            state['keys'].append(public)
            clock[0] = 6
            assert (await provider.authenticate(replacement)).actor_id == 'alice'
            state['keys'] = [public]
            clock[0] = 67
            with pytest.raises(ValueError): await provider.authenticate(token())
            assert (await provider.authenticate(replacement)).actor_id == 'alice'
    asyncio.run(run())
    assert state['requests'].count('/keys') == 3

def test_duplicate_key_identifiers_fail_closed(issuer):
    settings,state,endpoint,token,_ = issuer
    state['keys'].append(dict(state['keys'][0]))
    async def run():
        async with OidcAuthenticator(settings,transport=httpx.MockTransport(endpoint)) as provider:
            with pytest.raises(IdentityUnavailable): await provider.authenticate(token())
    asyncio.run(run())
    assert '/introspect' not in state['requests']

def test_keyset_response_has_a_size_limit(issuer):
    settings,_,_,token,_ = issuer
    async def run():
        async with OidcAuthenticator(settings,transport=httpx.MockTransport(
            lambda request:httpx.Response(200,content=b'x'*65537))) as provider:
            with pytest.raises(IdentityUnavailable): await provider.authenticate(token())
    asyncio.run(run())

def test_whole_authentication_deadline_includes_key_lookup_and_introspection(issuer):
    settings,_,endpoint,token,_ = issuer
    settings['request_timeout'] = .03
    async def delayed(request):
        await asyncio.sleep(.02)
        return endpoint(request)
    async def run():
        async with OidcAuthenticator(settings,transport=httpx.MockTransport(delayed)) as provider:
            with pytest.raises(IdentityUnavailable): await provider.authenticate(token())
    asyncio.run(run())

def test_expired_key_cache_never_accepts_during_refresh_outage(issuer,monkeypatch):
    settings,_,endpoint,token,_ = issuer
    clock,failed = [0],[False]
    monkeypatch.setattr(oidc,'time',SimpleNamespace(monotonic=lambda:clock[0]))
    def upstream(request):
        if failed[0]: raise httpx.ConnectError('PRIVATE')
        return endpoint(request)
    async def run():
        async with OidcAuthenticator(settings,transport=httpx.MockTransport(upstream)) as provider:
            await provider.authenticate(token())
            clock[0],failed[0] = 61,True
            with pytest.raises(IdentityUnavailable): await provider.authenticate(token())
    asyncio.run(run())
