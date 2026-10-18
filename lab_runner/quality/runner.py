"""Sequential scheduling, provenance and reconciliation around benchmark SDK calls."""
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
import math
import time
from .contracts import decode,digest,integer,sha
from .allowance import BenchmarkAllowance,private_directory,private_write
from .execution import CASE_LIMITS,workflow_definition,workflow_policy
from .checks import checks_digest
from .sdk_provenance import qualified_sdk
from .suite import load_suite,resource,agent_prose,AGENT_NAMES
from .reporting import public_result,summarize,estimate_cost,unknown_result


def provenance():
    names=('b3-prosaic','b3-prosaic-runtime','b3-prosaic-harness')
    return {name:version(name) for name in names}


def identity(suite,limits):
    installed=provenance()
    qualified=qualified_sdk(installed)
    return dict(suiteId=suite['suiteId'],scorerVersion='evidence-score-v1',suiteDigest=digest(suite),
        proseDigest=digest({k:agent_prose(k) for k in AGENT_NAMES}),
        toolDigest=digest({'version':'lookup-v1','maximumRecords':4}),policyDigest=digest(limits),
        sdkVersions=installed,sdkManifestDigest=qualified['manifestDigest'],
        workflowDigest=digest(dict(definitions={k:workflow_definition(k,limits) for k in ('ordinary','repair')},
                                  policy=workflow_policy(limits),publicChecks=checks_digest())),
        schemaDigest=digest({k:decode(resource(k+'.schema.json')) for k in ('answer','review')}),
        scorerDigest=digest({'source':files(__package__).joinpath('scoring.py').read_text(encoding='utf-8')}))


def fingerprint(profile):
    # Credentials and secret-file references are excluded even from the identity.
    return digest({key:getattr(profile,key) for key in (
        'provider','base_url','model','max_tokens','temperature','features','max_response_bytes')})


def schedule(suite,profiles,repetitions):
    integer(repetitions,1,10)
    if not 1<=len(profiles)<=4:raise ValueError('invalid benchmark profile count')
    return [dict(sampleId=f"{case['caseId']}-p{slot+1}-r{rep}",caseId=case['caseId'],
                 profileFingerprint=sha(fp),repetition=rep)
            for slot,fp in enumerate(profiles) for rep in range(1,repetitions+1) for case in suite['cases']]


def preflight(repetitions=1):
    suite=load_suite()
    rows=schedule(suite,[digest({'profile':'unexecuted'})],repetitions)
    return summarize(rows,[],identity=identity(suite,CASE_LIMITS),origin='unexecuted',recovery=[])


def live_settings(path):
    from prosaic_runtime import RuntimeConfig
    path=Path(path)
    if path.stat().st_size>65536:raise ValueError('benchmark config limit')
    data=decode(path.read_bytes(),65536)
    if set(data)-{'version','runtimeConfig','profiles','allowanceFile','limits','caseLimits','rateCard'} or not {
        'version','runtimeConfig','profiles','allowanceFile','limits','caseLimits'}<=set(data) or type(data['version']) is not int or data['version']!=1:
        raise ValueError('invalid benchmark config')
    if type(data['profiles']) is not list or not 1<=len(data['profiles'])<=4 or len(set(data['profiles']))!=len(data['profiles']):
        raise ValueError('invalid benchmark profiles')
    if type(data['caseLimits']) is not dict or set(data['caseLimits'])!=set(CASE_LIMITS):raise ValueError('invalid case caps')
    for key,val in data['caseLimits'].items():integer(val,1,1_000_000)
    if data['caseLimits']['providerRequests']<8 or data['caseLimits']['toolCalls']<4:
        raise ValueError('case allowance too small')
    runtime_path=Path(data['runtimeConfig']).expanduser()
    if not runtime_path.is_absolute():runtime_path=path.resolve().parent/runtime_path
    config=RuntimeConfig.load(runtime_path)
    if config.allowed_tools or config.tool_directories:raise ValueError('benchmark requires host-only tools')
    for alias in data['profiles']:
        if alias not in config.profiles:raise ValueError('unapproved benchmark profile')
        endpoint=config.profiles[alias]
        if endpoint.max_tokens is None or endpoint.max_tokens>4096 or endpoint.api_key_env is None and endpoint.api_key_file is None:
            raise ValueError('bounded secret-managed benchmark profile required')
    allowance=Path(data['allowanceFile']).expanduser()
    if not allowance.is_absolute():raise ValueError('absolute benchmark allowance required')
    if data.get('rateCard') is not None:
        estimate_cost(dict(inputTokens=None,outputTokens=None,counts={'reportedTokens':None}),data['rateCard'])
    return data,config,allowance


def execute(*,output,repetitions=1,live_config=None,token_counters=None):
    from .execution import execute_case
    from .fixture import fixture_provider
    from .recovery import run_recovery_cases
    suite=load_suite();output=private_directory(output)
    live=live_config is not None
    if live:
        data,config,allowance_path=live_settings(live_config)
        aliases=data['profiles'];caps=data['caseLimits'];limits=data['limits']
        profiles=[fingerprint(config.profiles[p]) for p in aliases]
    else:
        aliases=['fixture'];caps=dict(CASE_LIMITS)
        profiles=[digest({'profile':'quality-fixture'})]
        limits=dict(providerRequests=80*repetitions,toolCalls=40*repetitions,
            reportedTokens=163840*repetitions,maxSamples=10*repetitions,timeoutSeconds=300)
        allowance_path=output/'allowance.json';data={}
    rows=schedule(suite,profiles,repetitions);ident=identity(suite,caps)
    from .token_admission import admit_live_counters
    counters=admit_live_counters(token_counters,config,aliases) if live else {}
    binding=digest(dict(identity=ident,schedule=rows,origin='live' if live else 'fixture',
        tokenAdmission={k:v.descriptor.to_dict() for k,v in counters.items()}))
    allowance=BenchmarkAllowance(allowance_path,identity=binding,limits=limits,version=2)
    maximum={k:caps[k] for k in ('providerRequests','toolCalls','reportedTokens')}
    results=[];costs=[]
    cases={c['caseId']:c for c in suite['cases']}
    for row in rows:
        sample=row['sampleId'];path=output/(sample+'.json')
        claim=allowance.sample(sample)
        if path.exists():
            e=decode(path.read_bytes())
            if e.get('benchmarkIdentity')!=binding or e.get('profileFingerprint')!=row['profileFingerprint']:
                raise ValueError('foreign benchmark evidence')
            # Completed evidence can settle a pending reservation without execution.
        else:
            if claim is not None:
                results.append(unknown_result(row));break
            try:allowance.reserve(sample,maximum)
            except ValueError:break
            remaining=math.floor(allowance.status()['deadline']-time.time())
            if remaining<1:break
            effective=caps|{'timeoutSeconds':min(caps['timeoutSeconds'],remaining)}
            try:
                if live:
                    slot=profiles.index(row['profileFingerprint'])
                    e=execute_case(cases[row['caseId']],config=config,profile=aliases[slot],output=output,
                        sample_id=sample,limits=effective,token_counter=counters[aliases[slot]])
                else:
                    with fixture_provider() as provider:
                        e=execute_case(cases[row['caseId']],config=provider.config,profile='fixture',output=output,
                            sample_id=sample,limits=effective)
                        if e['counts']['providerRequests']!=provider.requests or e['counts']['toolCalls']!=len(e['journal']):
                            raise ValueError('fixture accounting mismatch')
            except Exception:
                allowance.finish(sample,actual=None,evidence_digest=None)
                results.append(unknown_result(row));break
            e.update(benchmarkIdentity=binding,profileFingerprint=row['profileFingerprint'])
            private_write(path,e)
        actual=e['counts'] if e['counts']['reportedTokens'] is not None else None
        if claim is None or claim['state']!='unknown':
            claim=allowance.finish(sample,actual=actual,evidence_digest=digest(e) if actual is not None else None,
                violation=e.get('admissionViolation') if actual is not None else None)
        public=public_result(cases[row['caseId']],e,profile_fingerprint=row['profileFingerprint'],repetition=row['repetition'])
        public.update(reservationRetained=claim['state']=='unknown',reservationExceeded=claim['state']=='overrun')
        results.append(public);costs.append(estimate_cost(public,data.get('rateCard')))
        if claim['state'] in {'unknown','overrun'}:break
    recovery_path=output/'recovery.json'
    if live:
        recovery=[]  # Fault probes are fixture evidence, never live model quality.
    elif recovery_path.exists():recovery=decode(recovery_path.read_bytes())
    else:
        recovery=run_recovery_cases(output/'recovery');private_write(recovery_path,recovery)
    report=summarize(rows,results,identity=ident,origin='live' if live else 'fixture',recovery=recovery)
    private_write(output/'summary.json',report)
    private_write(output/'cost-estimates.json',dict(version=1,samples=[dict(sampleId=r['sampleId'],**c) for r,c in zip(results,costs)]))
    return report
