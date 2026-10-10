"""Bounded synthetic qualification; aggregate completion is insufficient evidence."""
import hashlib
import json
import math
import re

BOUNDS = {
    'duration_s':(1,3600), 'arrivals_per_second':(0,100), 'concurrency':(1,64),
    'users':(1,1000), 'maximum_calls':(1,10000), 'maximum_records':(1,10000),
    'maximum_report_bytes':(1024,262144), 'window_s':(1,3600), 'p95_target_s':(0,3600),
    'maximum_rejection_ratio':(0,1), 'minimum_tenant_completion_ratio':(0,1),
    'provider_latency_s':(0,5), 'tool_latency_s':(0,5), 'maximum_rpo_s':(0,3600),
    'maximum_rto_s':(0,3600)}
INTEGERS={'concurrency','users','maximum_calls','maximum_records','maximum_report_bytes'}

def number(value,low,high,*,integer=False):
    return (type(value) in ({int} if integer else {int,float}) and
        math.isfinite(value) and low<=value<=high)

def validate_profile(data):
    if (type(data) is not dict or set(data)!={'version','suite',*BOUNDS} or
        type(data['version']) is not int or data['version']!=1 or
        type(data['suite']) is not str or not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',data['suite'])):
        raise ValueError('invalid qualification profile')
    for key,(low,high) in BOUNDS.items():
        if not number(data[key],low,high,integer=key in INTEGERS):
            raise ValueError('invalid qualification bound')
    if (data['arrivals_per_second']<=0 or data['p95_target_s']<=0 or
        data['window_s']>data['duration_s'] or
        math.ceil(data['duration_s']*data['arrivals_per_second'])>10000):
        raise ValueError('unbounded qualification arrivals or windows')
    return dict(data)

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),
        ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def receipt(profile,**fields):
    result={'version':1,'suite':profile['suite'],'profile_sha256':digest(profile),**fields}
    if len(json.dumps(result,allow_nan=False).encode())>profile['maximum_report_bytes']:
        return {'version':1,'suite':profile['suite'],'profile_sha256':digest(profile),
            'qualified':False,'qualification':'not_qualified','reason':'report_limit'}
    return result

def evaluate(profile,observations):
    profile=validate_profile(profile)
    if type(observations) is not dict:raise ValueError('invalid observations')
    if observations.get('suite')!=profile['suite'] or observations.get('profile_sha256')!=digest(profile):
        return receipt(profile,qualified=False,qualification='not_qualified',reason='evidence_identity_mismatch',
            correctness_passed=False,fairness_passed=False,fixture_passed=False)
    counts={key:observations.get(key) for key in ('offered','accepted','completed','errors','rejected',
        'approval_deferred','client_shed','independent_model_calls','ledger_calls','unknown_usage',
        'starved_windows','read_failures','read_samples','window_samples','tool_samples','allowance_rejected')}
    complete=all(number(value,0,10000,integer=True) for value in counts.values())
    if not complete:
        return receipt(profile,qualified=False,qualification='not_qualified',reason='missing_evidence',
            correctness_passed=False,fairness_passed=False,fixture_passed=False)
    latency=observations.get('latencies_s',[])
    tools=observations.get('tool_latencies_s',[])
    tenants=observations.get('tenant_counts',{})
    if (type(latency) is not list or len(latency)>10000 or type(tools) is not list or len(tools)>10000 or
        any(not number(v,0,30) for v in tools) or
        any(not number(v,0,7200) for v in latency) or type(tenants) is not dict or len(tenants)>1000):
        raise ValueError('invalid bounded observations')
    tenant_ratios={}
    for label,values in tenants.items():
        if (type(label) is not str or len(label.encode())>1024 or type(values) is not dict or
            set(values)!={'offered','completed'} or
            any(not number(v,0,10000,integer=True) for v in values.values()) or
            values['completed']>values['offered']):raise ValueError('invalid tenant observations')
        tenant_ratios[hashlib.sha256(label.encode()).hexdigest()]=(
            values['completed']/values['offered'] if values['offered'] else None)
    c=counts
    consistency=(c['completed']+c['approval_deferred']==c['accepted'] and
        c['accepted']+c['rejected']+c['client_shed']<=c['offered'] and
        sum(v['offered'] for v in tenants.values())==c['offered'] and
        sum(v['completed'] for v in tenants.values())==c['completed'])
    reconciled=c['independent_model_calls']==c['ledger_calls']==c['accepted'] and c['unknown_usage']==0
    correctness=c['errors']==0 and reconciled and consistency
    fairness=(len(tenant_ratios)==profile['users'] and all(v is not None and v>=profile['minimum_tenant_completion_ratio']
        for v in tenant_ratios.values()) and c['starved_windows']==0 and c['window_samples']>0)
    ordered=sorted(latency);p95=ordered[math.ceil(.95*len(ordered))-1] if ordered else None
    rejection=(c['rejected']+c['client_shed'])/c['offered'] if c['offered'] else None
    growth={key:observations.get(key) for key in ('records_before','records_after','bytes_before','bytes_after')}
    growth_ok=(all(number(v,0,2**63-1,integer=True) for v in growth.values()) and
        growth['records_after']>=growth['records_before'] and growth['bytes_after']>=growth['bytes_before'] and
        growth['records_after']<=profile['maximum_records'])
    tools=sorted(tools);tool_p95=tools[math.ceil(.95*len(tools))-1] if tools else None
    elapsed=observations.get('elapsed_s')
    coverage=(number(elapsed,0,7200) and elapsed>0 and
        (observations.get('stop_bound')!='duration' or
            (elapsed>=profile['duration_s'] and c['window_samples']>=math.floor(profile['duration_s']/profile['window_s']) and
             c['offered']==math.ceil(profile['duration_s']*profile['arrivals_per_second']))))
    qualified=(correctness and fairness and growth_ok and
        coverage and
        0<c['offered']<=math.ceil(profile['duration_s']*profile['arrivals_per_second']) and
        c['independent_model_calls']<=profile['maximum_calls'] and len(latency)==c['completed'] and
        len(tools)==c['tool_samples'] and p95 is not None and
        p95<=profile['p95_target_s'] and rejection<=profile['maximum_rejection_ratio'] and
        c['read_samples']>0 and c['read_failures']==0 and c['tool_samples']>0 and
        observations.get('stop_bound') in {'duration','calls','records'})
    return receipt(profile,qualified=qualified,qualification='qualified' if qualified else 'not_qualified',
        fixture_passed=correctness,correctness_passed=correctness,fairness_passed=fairness,
        accounting_reconciled=reconciled,p95_seconds=p95,rejection_ratio=rejection,tool_latency_p95_s=tool_p95,
        tenant_completion_ratios=tenant_ratios,counts=counts,growth=growth,
        elapsed_s=elapsed if number(elapsed,0,7200) else None,
        stop_bound=observations.get('stop_bound') if observations.get('stop_bound') in {'duration','calls','records'} else 'unknown')

def run(config,profile,events):
    profile=validate_profile(profile)  # Every ceiling is checked before a client/recorder opens.
    verify_config(config)
    from .load_profile import run as load
    observations=load(config,profile['users'],profile['duration_s'],profile['arrivals_per_second'],
        profile['concurrency'],events,p95_target=profile['p95_target_s'],
        max_rejection=profile['maximum_rejection_ratio'],qualification_profile=profile)
    return evaluate(profile,observations)

def verify_config(config):
    """The only execution target is an exact, independently inspected owned fixture."""
    from pathlib import Path
    from .manifest import validate_resource
    from .stack import ROOT,command
    from .staging_qualification import private_bytes
    if type(config) is not dict or not config.get('fixture_manifest'):
        raise ValueError('owned fixture configuration required')
    path=Path(config['fixture_manifest'])
    manifest=json.loads(path.read_text())
    if (type(manifest.get('owner')) is not str or not re.fullmatch('[0-9a-f]{32}',manifest['owner']) or
        path.resolve()!=ROOT/'.lab'/manifest['owner']/'ownership.json' or manifest.get('engine') not in {'docker','podman'}):
        raise ValueError('owned fixture manifest required')
    host=json.loads(private_bytes(path.parent/'secrets'/'host.json'))
    for key in ('migration_dsn','accounting_dsn','harness_dsn','app_dsn','namespace','environment','principals'):
        if key not in host or config.get(key)!=host[key]:raise ValueError('private fixture configuration mismatch')
    if manifest.get('payload_audit')!='verified':raise ValueError('verified fixture required')
    if not any(r.get('kind')=='container' and r.get('id')==manifest.get('database_id') for r in manifest.get('resources',[])):
        raise ValueError('owned database required')
    for name in ('model','a','b'):
        if config.get(name)!=manifest.get('endpoints',{}).get(name):raise ValueError('fixture endpoint mismatch')
        from urllib.parse import urlsplit
        parts=urlsplit(config[name])
        if parts.scheme!='http' or parts.hostname!='127.0.0.1':raise ValueError('loopback fixture required')
    for resource in manifest['resources']:
        if resource['kind']=='container':
            state=json.loads(command(manifest['engine'],'inspect',resource['id']))[0]
            validate_resource(state,resource['id'],manifest['owner'])
    return manifest
