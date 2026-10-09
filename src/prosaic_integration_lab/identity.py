from dataclasses import dataclass

@dataclass(frozen=True)
class Principal:
    tenant_id: str
    actor_id: str
    billing_account_id: str

def authenticate(header, mapping):
    if not header or not header.startswith('Bearer ') or header[7:] not in mapping:
        raise ValueError('unauthenticated')
    return Principal(**mapping[header[7:]])

class FixtureAuthenticator:
    def __init__(self,mapping): self.mapping = mapping
    async def authenticate(self,header): return authenticate(header,self.mapping)
    async def close(self): pass

def make_authenticator(config):
    mode = config.get('deployment_mode','lab')
    if mode not in {'lab','production'}: raise ValueError('invalid deployment mode')
    settings = config.get('authentication',{'provider':'fixture'})
    if not isinstance(settings,dict): raise ValueError('invalid authentication configuration')
    provider = settings.get('provider')
    if provider == 'fixture':
        if mode != 'lab' or set(settings) != {'provider'}: raise ValueError('fixture authentication is lab-only')
        return FixtureAuthenticator(config['principals'])
    if provider in {'oidc','auth0'}:
        if mode == 'production' and config.get('principals'): raise ValueError('fixture identities are lab-only')
        from .oidc import OidcAuthenticator
        return OidcAuthenticator(settings,deployment_mode=mode)
    raise ValueError('invalid authentication provider')
