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
