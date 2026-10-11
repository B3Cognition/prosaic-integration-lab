"""Pure admission for the fixed local/hosted conversation conformance schedule."""
import ipaddress
import json
from pathlib import Path
from urllib.parse import urlsplit

from prosaic_runtime import RuntimeConfig


SCHEDULE=(('balanced','ordinary',2),('balanced','ordinary',2),
    ('strong','ordinary',2),('strong','ordinary',2),
    ('balanced','selection',1),('balanced','confirmation',3))
MAXIMUM_REQUESTS=sum(row[2] for row in SCHEDULE)


def _object(items):
    value={}
    for key,item in items:
        if key in value:raise ValueError('invalid conversation configuration')
        value[key]=item
    return value


def preflight(path,*,live_local=False,live_hosted=False,max_calls=12):
    if type(live_local) is not bool or type(live_hosted) is not bool or live_local and live_hosted:
        raise ValueError('select only one live mode')
    if type(max_calls) is not int or not 1<=max_calls<=12:
        raise ValueError('invalid live allowance')
    if max_calls<MAXIMUM_REQUESTS:
        raise ValueError('complete conversation schedule requires twelve requests')
    mode='local' if live_local else 'hosted' if live_hosted else 'preflight'
    try:
        path=Path(path)
        if path.stat().st_size>65536:raise ValueError('invalid conversation configuration')
        document=json.loads(path.read_text(),object_pairs_hook=_object)
        if (type(document) is not dict or set(document)!={'runtime_config','allowance_file'} or
                any(type(value) is not str or not value for value in document.values())):
            raise ValueError('invalid conversation configuration')
        config_path=Path(document['runtime_config']).expanduser()
        if not config_path.is_absolute():config_path=path.resolve().parent/config_path
        config=RuntimeConfig.load(config_path)
        allowance=Path(document['allowance_file']).expanduser()
        if not allowance.is_absolute() or allowance.is_symlink():
            raise ValueError('invalid conversation configuration')
    except (OSError,TypeError,UnicodeError,RecursionError,ValueError):
        raise ValueError('invalid conversation configuration') from None
    if not {'balanced','strong'}<=config.routes.keys() or config.allowed_tools or config.tool_directories:
        raise ValueError('conversation conformance requires explicit tiers and host-only tools')
    selected={tier:config.profiles[config.routes[tier]] for tier in ('balanced','strong')}
    if selected['balanced'].model==selected['strong'].model:
        raise ValueError('balanced and strong must select distinct approved models')
    for profile in selected.values():
        url=urlsplit(profile.base_url)
        try:loopback=ipaddress.ip_address(url.hostname).is_loopback
        except ValueError:loopback=False
        if (type(profile.max_tokens) is not int or not 1<=profile.max_tokens<=512 or
                profile.features.get('streaming') is not False or
                profile.provider not in {'openai-compatible','anthropic'} or
                (profile.api_key_env is None)==(profile.api_key_file is None)):
            raise ValueError('conversation conformance requires bounded secret-managed profiles')
        if mode=='local' and (not loopback or profile.provider!='openai-compatible' or
                profile.api_key_env is not None or 'qwen' not in profile.model.lower()):
            raise ValueError('local conformance requires literal loopback approved Qwen profiles')
        if mode=='hosted' and (url.scheme!='https' or loopback or url.hostname in {'localhost','localhost.localdomain'}):
            raise ValueError('hosted conformance requires approved HTTPS profiles')
    return {'mode':mode,'runtime_config':config,'allowance_file':allowance,
        'maximum_requests':MAXIMUM_REQUESTS,'schedule':SCHEDULE}


def public_preflight(plan):
    return {'event':'conversation_conformance','mode':plan['mode'],'preflight':True,
        'live_executed':False,'dispatches':0,'maximum_requests':plan['maximum_requests'],
        'tiers':['balanced','strong']}
