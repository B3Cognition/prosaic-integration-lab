"""Private, opt-in deployment observations; synthetic fixtures cannot substitute."""
import json
import os
from pathlib import Path
import stat
import time
from urllib.parse import urlsplit

from .qualification import digest,number

CASES={'rotation','outage','backend_isolation','drain'}

def private_bytes(path,maximum=65536):
    """Read an owned regular private file without following a final symlink."""
    descriptor=os.open(Path(path),os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:
            raise ValueError('private input permissions required')
        if info.st_size>maximum:raise ValueError('private input size limit')
        with os.fdopen(descriptor,'rb',closefd=False) as source:
            data=source.read(maximum+1)
        if len(data)>maximum:raise ValueError('private input size limit')
        return data
    finally:os.close(descriptor)

def load_private_config(path):
    return json.loads(private_bytes(path))

def validate(config):
    required={'version','suite','origin','approved_origins','token_file','ca_file','signing_key_file',
        'issuer','audience','maximum_token_lifetime_s','maximum_calls','duration_s','maximum_report_bytes','cases'}
    if type(config) is not dict or set(config)!=required or type(config['version']) is not int or config['version']!=1:
        raise ValueError('missing deployment inputs')
    if config['suite']!='deployment-staging-v1':raise ValueError('invalid staging suite')
    origins=config['approved_origins']
    if type(origins) is not list or not 1<=len(origins)<=8 or len(set(origins))!=len(origins):raise ValueError('invalid origins')
    for origin in origins:
        if type(origin) is not str or len(origin)>2048:raise ValueError('invalid origins')
        parts=urlsplit(origin)
        if (parts.scheme!='https' or not parts.hostname or parts.username or parts.password or
            parts.path not in {'','/'} or parts.query or parts.fragment or origin.endswith('/')):
            raise ValueError('exact HTTPS origin required')
        _=parts.port
    if config['origin'] not in origins:raise ValueError('unapproved origin')
    for key,low,high in [('maximum_token_lifetime_s',1,3600),('maximum_calls',1,10000),
            ('duration_s',1,3600),('maximum_report_bytes',1024,262144)]:
        if not number(config[key],low,high,integer=True):raise ValueError('invalid staging ceiling')
    for key in ('issuer','audience'):
        if type(config[key]) is not str or not 1<=len(config[key])<=2048:raise ValueError('invalid token expectation')
    cases=config['cases']
    if type(cases) is not dict or set(cases)!=CASES:raise ValueError('missing staging cases')
    for item in cases.values():
        if (type(item) is not dict or set(item)!={'passed','evidence_sha256','observed_at'} or
            type(item['passed']) is not bool or type(item['evidence_sha256']) is not str or
            len(item['evidence_sha256'])!=64 or any(c not in '0123456789abcdef' for c in item['evidence_sha256']) or
            not number(item['observed_at'],time.time()-3600,time.time()+5)):
            raise ValueError('invalid staging observation')
    token=private_bytes(config['token_file']).decode().strip()
    ca=private_bytes(config['ca_file'])
    key=private_bytes(config['signing_key_file'])
    import jwt
    claims=jwt.decode(token,key,algorithms=['RS256'],issuer=config['issuer'],audience=config['audience'],
        options={'require':['exp','iat','iss','aud']})
    if (not number(claims['iat'],0,time.time()+5) or not number(claims['exp'],0,time.time()+3600) or
        not 0<claims['exp']-claims['iat']<=config['maximum_token_lifetime_s']):
        raise ValueError('token lifetime mismatch')
    return token,ca

def run(config,*,enabled=False):
    result={'version':1,'suite':'deployment-staging-v1','fixture_passed':False,'qualified':False,
            'qualification':'not_qualified'}
    if not enabled:return {**result,'reason':'staging_disabled'}
    if config is None:return {**result,'reason':'missing_deployment_inputs'}
    try:
        token,ca=validate(config)
    except Exception:
        return {**result,'reason':'missing_deployment_inputs'}
    result['configuration_sha256']=digest(config)
    # CA bytes are read/validated before constructing the client. No token acquisition or paid dispatch.
    import ssl
    import httpx
    try:
        context=ssl.create_default_context(cadata=ca.decode())
        began=time.monotonic()
        with httpx.Client(verify=context,timeout=min(10,config['duration_s']),follow_redirects=False) as client:
            response=client.get(config['origin']+'/readyz',headers={'Authorization':'Bearer '+token})
        if 300<=response.status_code<400:return {**result,'reason':'redirect_rejected'}
        passed=(response.status_code==200 and time.monotonic()-began<=config['duration_s'] and
            all(item['passed'] for item in config['cases'].values()))
        result.update(qualified=passed,qualification='qualified' if passed else 'not_qualified',
            reason='operator_observations_verified' if passed else 'deployment_cases_failed',
            calls=1,case_evidence={name:item['evidence_sha256'] for name,item in config['cases'].items()})
    except Exception:result['reason']='deployment_probe_failed'
    if len(json.dumps(result).encode())>config['maximum_report_bytes']:
        return {key:value for key,value in {**result,'qualified':False,'qualification':'not_qualified',
            'reason':'report_limit'}.items() if key!='case_evidence'}
    return result
