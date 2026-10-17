"""Paired scheduling, immutable reservations and no-inference replay."""
from contextlib import ExitStack
from dataclasses import asdict
from importlib.resources import files
from pathlib import Path
import time
from lab_runner.quality.allowance import BenchmarkAllowance,private_directory,private_write
from lab_runner.quality.contracts import decode,digest,integer,sha,identifier
from lab_runner.quality.runner import fingerprint,provenance
from lab_runner.quality.suite import resource
from .corpus import Corpus
from .execution import execute_case,recover_case,freeze,LIMITS,PROSE
from .suite import load_suite,validate_bundle
from .reporting import public_result,unknown_result,summarize
from .contracts import answer_schema
from .evidence import validate_format,TYPED_GUIDANCE


def schedule(bundle,profiles):
    if not 1<=len(profiles)<=2 or len(set(profiles))!=len(profiles):raise ValueError('invalid memory profiles')
    rows=[]
    for slot,profile in enumerate(profiles):
        sha(profile)
        for index,case in enumerate(bundle['cases']):
            arms=('disabled','enabled') if index%2==0 else ('enabled','disabled')
            for arm in arms:
                sample=f"{case['caseId']}-p{slot+1}-{arm}";identifier(sample)
                rows.append(dict(sampleId=sample,caseId=case['caseId'],profileFingerprint=profile,arm=arm))
    return rows


def identity(bundle,*,evidence_format='raw'):
    validate_format(evidence_format)
    corpus=Corpus(bundle['corpus'],bundle['historicalSources'])
    sdk=decode(resource('sdk-provenance.json'));installed=provenance()
    qualified={a['distribution']:a['version'] for a in sdk['artifacts']}
    if any(qualified.get(k)!=v for k,v in installed.items()):raise ValueError('unqualified memory SDK')
    source={p.name:p.read_text(encoding='utf-8') for p in files(__package__).iterdir() if p.name.endswith('.py')}
    source['data/evidence-summary.schema.json']=files(__package__).joinpath('data/evidence-summary.schema.json').read_text(encoding='utf-8')
    quality={n:files('lab_runner.quality').joinpath(n).read_text(encoding='utf-8') for n in
             ('checks.py','execution.py','scoring.py','contracts.py','allowance.py','runner.py','suite.py')}
    return dict(suiteId=bundle['suiteId'],suiteDigest=digest(bundle['cases']),
        corpusDigest=digest({c['caseId']:corpus.tenant_digest(c['tenantId']) for c in bundle['cases']}),
        implementationDigest=digest(dict(memory=source,quality=quality)),evidenceFormat=evidence_format,
        proseDigest=digest(PROSE+(TYPED_GUIDANCE if evidence_format=='typed' else '')),
        schemaDigest=digest({c['caseId']:answer_schema(c) for c in bundle['cases']}),policyDigest=digest(LIMITS),
        sdkManifestDigest=sdk['manifestDigest'],sdkVersions=installed)


def preflight(bundle=None,*,evidence_format='raw'):
    bundle=validate_bundle(load_suite() if bundle is None else bundle)
    return summarize(schedule(bundle,[digest('unexecuted-a'),digest('unexecuted-b')]),[],
                     identity=identity(bundle,evidence_format=evidence_format),origin='unexecuted')


def live_settings(path):
    from prosaic_runtime import RuntimeConfig
    path=Path(path);data=decode(path.read_bytes(),65536)
    if set(data)!={'version','runtimeConfig','profiles','allowanceFile','limits','caseLimits'} or type(data['version']) is not int or data['version']!=1:
        raise ValueError('invalid memory live config')
    if data['caseLimits']!=LIMITS:raise ValueError('changed memory case caps')
    aliases=data['profiles']
    if type(aliases) is not list or len(aliases)!=2 or len(set(aliases))!=2:raise ValueError('two memory profiles required')
    runtime_path=Path(data['runtimeConfig']).expanduser()
    if not runtime_path.is_absolute():runtime_path=path.resolve().parent/runtime_path
    config=RuntimeConfig.load(runtime_path)
    if config.allowed_tools or config.tool_directories:raise ValueError('host-only memory tools required')
    for alias in aliases:
        if alias not in config.profiles:raise ValueError('unknown memory profile')
        p=config.profiles[alias]
        if p.max_tokens is None or p.max_tokens>4096 or p.api_key_env is None and p.api_key_file is None:
            raise ValueError('bounded secret-managed memory profile required')
    allowance=Path(data['allowanceFile']).expanduser()
    if not allowance.is_absolute():raise ValueError('absolute memory allowance required')
    return data,config,allowance


def execute(*,output,bundle=None,fixture=False,live_config=None,fixture_scenario='correct',recover_only=False,evidence_format='raw'):
    if fixture==(live_config is not None):raise ValueError('select explicit memory execution mode')
    if not fixture and fixture_scenario!='correct':raise ValueError('fixture scenario in live mode')
    bundle=validate_bundle(load_suite() if bundle is None else bundle);out=private_directory(output)
    corpus=Corpus(bundle['corpus'],bundle['historicalSources']);ident=identity(bundle,evidence_format=evidence_format)
    aliases=['fixture-a','fixture-b'];config=None
    if fixture:
        profiles=[digest('memory-'+name) for name in aliases]
        count=len(bundle['cases'])*4
        limits=dict(providerRequests=count*4,toolCalls=count*2,reportedTokens=count*8192,maxSamples=count,timeoutSeconds=28800)
        allowance_path=out/'allowance.json'
    else:
        data,config,allowance_path=live_settings(live_config);aliases=data['profiles'];limits=data['limits']
        profiles=[fingerprint(config.profiles[p]) for p in aliases]
    rows=schedule(bundle,profiles);origin='fixture' if fixture else 'live'
    binding=digest(dict(identity=ident,schedule=rows,origin=origin))
    allowance=BenchmarkAllowance(allowance_path,identity=binding,limits=limits)
    maximum={k:LIMITS[k] for k in ('providerRequests','toolCalls','reportedTokens')}
    cases={c['caseId']:c for c in bundle['cases']};results=[];observed=dict(providerRequests=0,toolCalls=0)
    with ExitStack() as stack:
        provider=None
        for row in rows:
            case=cases[row['caseId']];sample=row['sampleId'];path=out/(sample+'.json');claim=allowance.sample(sample)
            available=[ep['episodeId'] for ep in bundle['corpus']['episodes'] if ep['tenantId']==case['tenantId'] and ep['observedAt']<=case['asOf']]
            profile=aliases[profiles.index(row['profileFingerprint'])]
            preparation_path=out/(sample+'-prepared.json')
            observation_path=out/(sample+'-fixture-observed.json')
            def adopt_receipt():
                nonlocal config
                if fixture:
                    from prosaic_runtime import RuntimeConfig
                    if not (out/'fixture-runtime.yml').exists():return None
                    config=RuntimeConfig.load(out/'fixture-runtime.yml')
                if config is None:return None
                recovered=recover_case(case,corpus=corpus,arm=row['arm'],config=config,profile=profile,
                    output=out,sample_id=sample,limits=LIMITS,evidence_format=evidence_format)
                if recovered is None:return None
                if fixture:
                    if not observation_path.exists():return None
                    independent=decode(observation_path.read_bytes())
                    if set(independent)!=set(observed):raise ValueError('invalid fixture observation')
                    for key in observed:
                        integer(independent[key],0,LIMITS[key])
                        if independent[key]!=recovered['counts'][key]:raise ValueError('fixture native count mismatch')
                    recovered['fixtureObserved']=independent
                recovered.update(benchmarkIdentity=binding,profileFingerprint=row['profileFingerprint'],
                    reservationRetained=claim is not None and claim['state']=='unknown' or recovered['counts']['reportedTokens'] is None)
                private_write(path,recovered)
                return recovered
            def interrupted():
                preparation=None
                if fixture and observation_path.exists():
                    independent=decode(observation_path.read_bytes())
                    if set(independent)!=set(observed):raise ValueError('invalid fixture observation')
                    for key in observed:
                        integer(independent[key],0,LIMITS[key]);observed[key]+=independent[key]
                if preparation_path.exists():
                    freeze(case,corpus,row['arm'],preparation_path,evidence_format=evidence_format)
                    preparation=decode(preparation_path.read_bytes())
                return unknown_result(row,case,preparation,available)
            if path.exists():
                e=decode(path.read_bytes())
                if claim is None or e.get('benchmarkIdentity')!=binding or e.get('profileFingerprint')!=row['profileFingerprint'] or e['prepared']['arm']!=row['arm']:
                    raise ValueError('foreign memory evidence')
            else:
                if claim is not None:
                    e=None
                    if claim['state'] in {'pending','unknown'}:
                        try:e=adopt_receipt()
                        except Exception:e=None
                        if e is None and claim['state']=='pending':allowance.finish(sample,actual=None,evidence_digest=None)
                    if e is None:results.append(interrupted());break
                elif recover_only:break
                else:
                    e=None
                if e is not None:
                    actual=e['counts'] if e['counts']['reportedTokens'] is not None else None
                    if claim['state']!='unknown':allowance.finish(sample,actual=actual,evidence_digest=digest(e) if actual is not None else None)
                    if fixture:
                        for key in observed:observed[key]+=e['fixtureObserved'][key]
                    results.append(public_result(case,e,row,available))
                    if actual is None or claim['state']=='unknown':break
                    continue
                if allowance.status()['deadline']-time.time()<LIMITS['timeoutSeconds']:break
                try:allowance.reserve(sample,maximum)
                except ValueError:break
                try:
                    if fixture and provider is None:
                        from .fixture import fixture_provider
                        provider=stack.enter_context(fixture_provider(bundle['cases'],fixture_scenario));config=provider.config
                        private_write(out/'fixture-runtime.yml',dict(profiles={k:asdict(v) for k,v in config.profiles.items()},
                            routes=config.routes,default_profile=config.default_profile,allowed_tools=[],
                            limits=asdict(config.limits),tool_directories=[],cli_sandbox=dict(mode='off',runtime_roots=[])))
                    before=provider.requests if provider is not None else None
                    try:
                        e=execute_case(case,corpus=corpus,arm=row['arm'],config=config,profile=profile,
                                       output=out,sample_id=sample,limits=LIMITS,evidence_format=evidence_format)
                    finally:
                        if fixture:
                            journal_path=out/(sample+'-journal.json')
                            journal=decode(journal_path.read_bytes()) if journal_path.exists() else []
                            private_write(observation_path,dict(providerRequests=provider.requests-before,toolCalls=len(journal)))
                    if fixture:
                        independent=decode(observation_path.read_bytes())
                        if any(independent[k]!=e['counts'][k] for k in independent):raise ValueError('fixture native count mismatch')
                        e['fixtureObserved']=independent
                    e.update(benchmarkIdentity=binding,profileFingerprint=row['profileFingerprint'],
                        reservationRetained=e['counts']['reportedTokens'] is None)
                    private_write(path,e)
                except Exception:
                    try:e=adopt_receipt()
                    except Exception:e=None
                    if e is None:
                        allowance.finish(sample,actual=None,evidence_digest=None);results.append(interrupted());break
            actual=e['counts'] if e['counts']['reportedTokens'] is not None else None
            if claim is None or claim['state']!='unknown':
                allowance.finish(sample,actual=actual,evidence_digest=digest(e) if actual is not None else None)
            if fixture:
                for key in observed:observed[key]+=e['fixtureObserved'][key]
            results.append(public_result(case,e,row,available))
            if actual is None or claim is not None and claim['state']=='unknown':break
    report=summarize(rows,results,identity=ident,origin=origin,fixture_counts=observed if fixture else None)
    private_write(out/'summary.json',report)
    return report
