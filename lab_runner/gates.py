"""Required acceptance receipts and safe publication summaries."""
import re
import hashlib
from pathlib import Path

COUNTS = {'audit':82,'identity':19,'ingress':5}

def validate(item,mode,postgres_major,*,candidate=False,manifest_sha=None):
    if not isinstance(item,dict): raise ValueError('invalid acceptance receipt')
    if (mode not in COUNTS or item.get('mode') != mode or
        item.get('passed') is not True or item.get('cleanup') != 'verified' or
        type(item.get('test_returncode')) is not int or item['test_returncode'] != 0 or type(item.get('test_count')) is not int or
        item['test_count'] != COUNTS[mode] or type(item.get('skipped')) is not int or item['skipped'] != 0 or
        item.get('failed_tests') != [] or 'error' in item or
        item.get('host_architecture') not in {'arm64','aarch64','x86_64','AMD64'}):
        raise ValueError('required acceptance receipt did not pass')
    images = item.get('images',{})
    if not isinstance(images,dict): raise ValueError('invalid image provenance')
    if (not re.fullmatch(r'sha256:[0-9a-f]{64}',images.get('consumer','')) or
        not re.fullmatch(r'postgres:'+str(postgres_major)+r'@sha256:[0-9a-f]{64}',images.get('postgres',''))):
        raise ValueError('required image provenance missing')
    expected = 'candidate' if candidate else 'released'
    if item.get('dependency_mode') != expected:
        raise ValueError('dependency provenance differs from required lane')
    released_sha = hashlib.sha256((Path(__file__).resolve().parents[1]/'dependencies/releases.json').read_bytes()).hexdigest()
    if item.get('released_manifest_sha256') != released_sha or item.get('payload_audit') != 'verified':
        raise ValueError('installed payload provenance missing')
    if candidate and (not isinstance(manifest_sha,str) or not re.fullmatch('[0-9a-f]{64}',manifest_sha) or
        item.get('candidate_manifest_sha256') != manifest_sha):
        raise ValueError('candidate manifest provenance missing')

def export(item):
    # Only known scalars survive; arbitrary errors/failure names/paths never do.
    if not isinstance(item,dict): item = {}
    result = {'passed':item.get('passed') is True and 'error' not in item and
        item.get('cleanup') == 'verified' and item.get('failed_tests') == [] and item.get('skipped') == 0 and
        type(item.get('test_count')) is int and item['test_count'] > 0 and
        type(item.get('test_returncode')) is int and item['test_returncode'] == 0 and item.get('payload_audit') == 'verified'}
    for key,choices in {'mode':set(COUNTS),'cleanup':{'verified','failed','pending'},
        'dependency_mode':{'released','candidate'},'host_architecture':{'arm64','aarch64','x86_64','AMD64'}}.items():
        value = item.get(key)
        result[key] = value if isinstance(value,str) and value in choices else 'unknown'
    for key in ('test_count','skipped','test_returncode'):
        value = item.get(key)
        result[key] = value if type(value) is int and 0 <= value <= 100000 else None
    result['failed_count'] = len(item.get('failed_tests',[])) if isinstance(item.get('failed_tests'),list) else None
    result['payload_audit'] = 'verified' if item.get('payload_audit') == 'verified' else 'unverified'
    owner = item.get('owner')
    if isinstance(owner,str) and re.fullmatch('[0-9a-f]{32}',owner): result['owner'] = owner
    diagnostic=item.get('engine_diagnostic')
    if isinstance(diagnostic,dict):
        operation=diagnostic.get('operation')
        category=diagnostic.get('category')
        code=diagnostic.get('return_code')
        operations={'info','pull','run','create','start','stop','kill','exec','inspect','logs','ps','rm','unknown'}
        operations|={base+'_'+verb for base in ('network','volume','image') for verb in ('create','inspect','rm','ls')}
        if (operation in operations and category in {'command_timeout','rate_limited','image_missing',
            'engine_unavailable','network_timeout','permission_denied','engine_failed'} and
            (code is None or type(code) is int and -128 <= code <= 255) and diagnostic.get('outcome')=='unknown'):
            result['engine_diagnostic']={'operation':operation,'return_code':code,'category':category,'outcome':'unknown'}
    for key in ('released_manifest_sha256','candidate_manifest_sha256'):
        value = item.get(key)
        if isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value): result[key] = value
    images = item.get('images',{})
    if not isinstance(images,dict): images = {}
    result['images'] = {key:value for key,value in images.items() if key in {'consumer','postgres','keycloak','ingress'}
        and isinstance(value,str) and re.fullmatch(r'(?:[a-z0-9./:-]+@)?sha256:[0-9a-f]{64}',value)}
    return result
