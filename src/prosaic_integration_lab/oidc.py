"""Bounded standard OIDC verification; authorization remains server-side."""
import asyncio
import json
import math
import ssl
import time
from urllib.parse import urlsplit
import httpx
import jwt
from .identity import Principal

class IdentityUnavailable(RuntimeError):
    def __init__(self): super().__init__('identity_unavailable')


class OidcAuthenticator:
    def __init__(self,settings,*,deployment_mode='production',transport=None):
        if not isinstance(settings,dict) or settings.get('provider') not in {'oidc','auth0'}:
            raise ValueError('invalid OIDC provider')
        offline = settings['provider']=='auth0'
        required = {'provider','issuer','audience','jwks_uri','subjects'}
        if not offline: required.add('introspection')
        optional = {'ca_file','allow_insecure_http','request_timeout','jwks_ttl',
                    'refresh_cooldown','max_token_lifetime','required_scope'}
        if not isinstance(settings,dict) or not required <= set(settings) or set(settings)-required-optional:
            raise ValueError('invalid OIDC configuration')
        insecure = settings.get('allow_insecure_http',False)
        if type(insecure) is not bool or (deployment_mode != 'lab' and insecure):
            raise ValueError('invalid OIDC transport policy')
        self.settings = dict(settings)
        for key in ('issuer','jwks_uri'):
            self._url(settings[key],insecure)
        if type(settings['audience']) is not str or not 1 <= len(settings['audience']) <= 256:
            raise ValueError('invalid OIDC audience')
        self.introspection = None
        if not offline:
            intro = settings['introspection']
            if (not isinstance(intro,dict) or set(intro) != {'url','client_id','client_secret'} or
                any(type(intro[key]) is not str or not intro[key] or len(intro[key]) > 8192 for key in intro)):
                raise ValueError('invalid OIDC introspection configuration')
            self._url(intro['url'],insecure)
            self.introspection = dict(intro)
        self.timeout = settings.get('request_timeout',2)
        self.ttl = settings.get('jwks_ttl',60)
        self.cooldown = settings.get('refresh_cooldown',5)
        self.max_lifetime = settings.get('max_token_lifetime',300)
        for value,lower,upper in ((self.timeout,.01,2),(self.ttl,1,300),
                                  (self.cooldown,1,60),(self.max_lifetime,1,300 if offline else 3600)):
            if type(value) not in {float,int} or not math.isfinite(value) or not lower <= value <= upper:
                raise ValueError('invalid OIDC bounds')
        subjects = settings['subjects']
        if not isinstance(subjects,dict) or not 1 <= len(subjects) <= 10000:
            raise ValueError('invalid OIDC subject bindings')
        self.subjects = {}
        fields = {'tenant_id','actor_id','billing_account_id'}
        for subject,binding in subjects.items():
            if (type(subject) is not str or not 1 <= len(subject) <= 256 or not isinstance(binding,dict) or
                not fields <= set(binding) or set(binding)-fields-{'disabled','not_before'} or
                any(type(binding[key]) is not str or not 1 <= len(binding[key]) <= 256 for key in fields) or
                type(binding.get('disabled',False)) is not bool or
                type(binding.get('not_before',0)) is not int or binding.get('not_before',0) < 0):
                raise ValueError('invalid OIDC subject binding')
            self.subjects[subject] = (Principal(**{key:binding[key] for key in fields}),
                binding.get('disabled',False),binding.get('not_before',0))
        scope = settings.get('required_scope')
        if scope is not None and (type(scope) is not str or not scope or len(scope) > 256 or ' ' in scope):
            raise ValueError('invalid OIDC scope policy')
        verify = ssl.create_default_context(cafile=settings.get('ca_file'))
        self.client = httpx.AsyncClient(timeout=self.timeout,verify=verify,transport=transport,
            follow_redirects=False,trust_env=False,limits=httpx.Limits(max_connections=8,max_keepalive_connections=8))
        self.keys = {}
        self.fetched = float('-inf')
        self.attempted = float('-inf')
        self.lock = asyncio.Lock()

    @staticmethod
    def _url(value,insecure):
        if type(value) is not str or len(value) > 2048:
            raise ValueError('invalid OIDC URL')
        parsed = urlsplit(value)
        if (not parsed.hostname or parsed.username or parsed.password or parsed.fragment or
            parsed.scheme not in ({'https','http'} if insecure else {'https'})):
            raise ValueError('invalid OIDC URL')

    async def __aenter__(self): return self
    async def __aexit__(self,*args): await self.close()
    async def close(self): await self.client.aclose()

    async def _json(self,method,url,**kwargs):
        try:
            async with asyncio.timeout(self.timeout):
                async with self.client.stream(method,url,**kwargs) as response:
                    if response.status_code != 200: raise IdentityUnavailable()
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        if len(content)+len(chunk) > 65536: raise IdentityUnavailable()
                        content.extend(chunk)
                    data = json.loads(content)
                    if not isinstance(data,dict): raise IdentityUnavailable()
                    return data
        except (httpx.HTTPError,TimeoutError,ValueError,UnicodeError):
            raise IdentityUnavailable() from None

    async def _key(self,kid):
        now = time.monotonic()
        if kid in self.keys and now-self.fetched < self.ttl:
            return self.keys[kid]
        async with self.lock:
            now = time.monotonic()
            if kid in self.keys and now-self.fetched < self.ttl:
                return self.keys[kid]
            if now-self.attempted < self.cooldown:
                if now-self.fetched >= self.ttl: raise IdentityUnavailable()
                raise ValueError('unauthenticated')
            self.attempted = now
            data = await self._json('GET',self.settings['jwks_uri'])
            try:
                items = data['keys']
                if not isinstance(items,list) or not 1 <= len(items) <= 32: raise ValueError()
                keys = {}
                identifiers = set()
                for item in items:
                    if not isinstance(item,dict): raise ValueError()
                    identifier = item['kid']
                    if type(identifier) is not str or not 1 <= len(identifier) <= 128 or identifier in identifiers:
                        raise ValueError()
                    identifiers.add(identifier)
                    if (item.get('kty') != 'RSA' or item.get('alg','RS256') != 'RS256' or
                        item.get('use','sig') != 'sig' or item.get('key_ops',['verify']) != ['verify']):
                        continue
                    if {'d','p','q','dp','dq','qi','k'} & set(item): raise ValueError()
                    key = jwt.PyJWK.from_dict(item,algorithm='RS256').key
                    if key.key_size < 2048: raise ValueError()
                    keys[identifier] = key
                if not keys: raise ValueError()
                self.keys,self.fetched = keys,time.monotonic()
            except (KeyError,ValueError,TypeError,jwt.PyJWTError):
                raise IdentityUnavailable() from None
            if kid not in self.keys: raise ValueError('unauthenticated')
            return self.keys[kid]

    async def authenticate(self,header):
        try:
            async with asyncio.timeout(self.timeout):
                return await self._authenticate(header)
        except TimeoutError:
            raise IdentityUnavailable() from None

    async def _authenticate(self,header):
        if type(header) is not str or not header.startswith('Bearer ') or not 1 <= len(header[7:]) <= 8192:
            raise ValueError('unauthenticated')
        token = header[7:]
        try:
            unverified = jwt.get_unverified_header(token)
            kid = unverified.get('kid')
            if unverified.get('alg') != 'RS256' or type(kid) is not str or not 1 <= len(kid) <= 128:
                raise ValueError()
            key = await self._key(kid)
            claims = jwt.decode(token,key,algorithms=['RS256'],issuer=self.settings['issuer'],
                audience=self.settings['audience'],options={'require':['exp','iat','sub','iss','aud']})
            if (type(claims['exp']) is not int or type(claims['iat']) is not int or
                not 0 < claims['exp']-claims['iat'] <= self.max_lifetime):
                raise ValueError()
            actor,disabled,not_before = self.subjects[claims['sub']]
            if disabled or claims['iat'] < not_before: raise ValueError()
            required_scope = self.settings.get('required_scope')
            if required_scope and required_scope not in str(claims.get('scope','')).split(): raise ValueError()
            if self.introspection is not None:
                active = await self._json('POST',self.introspection['url'],data={'token':token,'token_type_hint':'access_token'},
                    auth=httpx.BasicAuth(self.introspection['client_id'],self.introspection['client_secret']))
                if active.get('active') is not True or active.get('sub',claims['sub']) != claims['sub']:
                    raise ValueError()
            return actor
        except (jwt.PyJWTError,ValueError,KeyError,TypeError):
            raise ValueError('unauthenticated') from None
