"""Explicit bounded dispatch, durable reservations and zero-dispatch replay."""
from contextlib import nullcontext
import fcntl
from importlib.metadata import version
import math
import os
from pathlib import Path
import re
import time

from lab_runner.quality.allowance import BenchmarkAllowance, private_directory

from . import completeness_profile, generation
from .dataset import load_frozen
from .retrieval import ARMS, fixture_provider, prepare, validate_capture
from .storage import code_binding, decode, exclusive, read, require, sha, shape
from .workflow import initial_packet, run_answer


def fixture_settings(count,review=False):
    return dict(version=1,origin='fixture',review=review,
        limits=dict(providerRequests=count*(3 if review else 1),reportedTokens=count*(98304 if review else 32768),
                    toolCalls=1,maxSamples=count,timeoutSeconds=86400))


def _settings(path,count,review):
    require(path is not None,'live mode requires an explicit private host configuration')
    path=Path(path);require(path.is_absolute() and not path.is_symlink() and path.stat().st_mode&0o077==0,
        'private host configuration required')
    settings=read(path)
    shape(settings,('version','enabled','review','runtime','castle','limits'))
    require(type(settings['version']) is int and settings['version']==1 and settings['enabled'] is True,
            'live benchmark is disabled')
    require(type(settings['review']) is bool and settings['review']==review,'explicit review selection must match config')
    shape(settings['runtime'],('base_url','model','api_key_file'))
    shape(settings['castle'],('worker_command','palace_path','config_path'))
    shape(settings['limits'],('providerRequests','reportedTokens','timeoutSeconds'))
    for key,ceiling in [('providerRequests',100000),('reportedTokens',1000000000),('timeoutSeconds',86400)]:
        require(type(settings['limits'][key]) is int and 1<=settings['limits'][key]<=ceiling,'finite shared limits required')
    for key in ('palace_path','config_path'):
        require(type(settings['castle'][key]) is str and Path(settings['castle'][key]).is_absolute(), 'absolute Castle host paths')
    keyfile=Path(settings['runtime']['api_key_file'])
    require(keyfile.is_absolute() and keyfile.is_file() and not keyfile.is_symlink()
        and keyfile.stat().st_mode&0o077==0,'private Runtime key file required')
    return dict(version=1,origin='live',review=review,runtime=settings['runtime'],castle=settings['castle'],
        limits=dict(settings['limits'],toolCalls=1,maxSamples=count))


def _provider(settings,bundle,case):
    from prosaic_memory_castle import CastleMemoryProvider,WorkerCommand
    castle=settings['castle']
    wings=sorted({bundle['sources'][sid]['wing'] for sid in case['sourceIds']})
    return CastleMemoryProvider(WorkerCommand(tuple(castle['worker_command'])),palace_path=castle['palace_path'],
        config_path=castle['config_path'],namespace=bundle['namespace'],allowed_wings=wings,
        profile='memory-fts-v1',recency_boost=False)


def _runtime(settings):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    return RuntimeConfig(profiles={'benchmark':EndpointConfig(**settings['runtime'],max_tokens=4096,temperature=0)},
                         routes={},default_profile='benchmark')


def _identity(frozen,bundle,case,arm):
    return dict(namespace=bundle['namespace'],allowedWings=sorted({bundle['sources'][s]['wing'] for s in case['sourceIds']}),
        arm=arm,qid=case['id'],sourceRunBinding=sha(read(Path(frozen)/'freeze.json')))


def _unknown(budget,results):
    receipts=[r for result in results if result for r in result.get('evidence',{}).get('receipts',[])]
    unresolved=any(result.get('executionError') or result.get('evidence',{}).get('checkpoint',{}).get('pending') is not None
        or result.get('evidence',{}).get('recoveryStatus') in ('receiptAvailable','uncertain','pending','unresolved')
        or result.get('evidence',{}).get('checkpoint',{}).get('status') in ('running','waiting')
        for result in results if result)
    return (bool(unresolved) or not budget.usage_complete or budget.provider_requests>0 and not receipts or any(
        r.get('result',{}).get('metadata',{}).get('failure_reason') in ('incomplete_response','usage_unknown') for r in receipts))


def _sample_id(case_id,arm):
    # Dataset IDs may contain dots; the existing allowance deliberately cannot.
    base=case_id if re.fullmatch(r'[A-Za-z0-9_-]+',case_id) else 's-'+sha(case_id.encode())
    return base+'-'+arm


def _store_row(output,row,manifest):
    exclusive(output/row['path'],row)
    files=[dict(path=p.relative_to(output).as_posix(),sha256=sha(p.read_bytes()))
        for p in sorted((output/'samples'/row['id']).rglob('*')) if p.is_file() and not p.name.endswith('.lock')]
    exclusive(output/(row['path']+'.seal'),dict(runSha256=sha(manifest),outcomeSha256=sha(row),files=files))


def _check_saved_row(output,row,item,manifest,sample):
    require(all(row.get(k)==v for k,v in item.items()) and row.get('path')==f"outcomes/{item['id']}.json",
            'saved outcome identity mismatch')
    seal=read(output/(row['path']+'.seal'));shape(seal,('runSha256','outcomeSha256','files'))
    require(seal['runSha256']==sha(manifest) and seal['outcomeSha256']==sha(row),'saved outcome immediate seal mismatch')
    current=[dict(path=p.relative_to(output).as_posix(),sha256=sha(p.read_bytes()))
        for p in sorted((output/'samples'/row['id']).rglob('*')) if p.is_file() and not p.name.endswith('.lock')]
    require(current==seal['files'],'saved raw evidence changed before resume')
    if row['status']=='blocked':require(sample is None,'blocked outcome has a reservation');return
    require(sample is not None,'outcome reservation missing')
    if sample['state'] in ('known','overrun'):
        require(sample['evidenceDigest']==sha(row),'saved outcome allowance digest mismatch')
        require(sample['actual']=={k:row['usage'][k] for k in ('providerRequests','reportedTokens','toolCalls')},
                'outcome/allowance accounting mismatch')
    else:
        require(sample['state'] in ('unknown','pending') and sample['actual'] is None and sample['evidenceDigest'] is None
            and row['status']==('usage_unknown' if sample['state']=='unknown' else 'unresolved'), 'unresolved reservation mismatch')
    if row['status']=='completed':
        require((row.get('base') or {}).get('candidate') is not None and (not manifest['settings']['review']
            or (row.get('review') or {}).get('candidate') is not None),'completed outcome requires accepted candidates')


def _check_stage(result,packet,stage,*,generation_profile='canonical-v1'):
    if not result or result.get('candidate') is None:return
    data=packet.to_dict();evidence=result['evidence'];state=evidence['checkpoint']
    initial=stage=='base';roles=('answer',) if initial else ('critic','repair')
    expected=generation.model_request(packet,initial=initial,profile=generation_profile)
    require(state['status']=='completed' and state['inputs']==expected and set(state['outputs'])==set(roles)
        and set(state['bindings'])==set(roles),'candidate requires exact completed checkpoint')
    require(generation.resolve(state['outputs'][roles[-1]],packet,profile=generation_profile)==result['candidate'],
            'candidate differs from accepted checkpoint')
    receipts={r['id']:r for r in evidence['receipts']}
    require(len(receipts)==len(evidence['receipts']) and set(receipts)=={r['id'] for r in state['invocations']},
            'candidate receipt denominator')
    for role in roles:
        binding=state['bindings'][role];receipt=receipts[binding['id']]
        require(receipt['run_id']==evidence['runId'] and receipt['step']==role and receipt['result']['exit_code']==0,
                'accepted receipt identity/result mismatch')
        args=receipt['arguments'];args=decode(args.encode(),262144) if isinstance(args,str) else args
        require(args['request']==expected and args['sources']=={},'receipt input mismatch')
        artifacts={} if role!='repair' else {'critic':state['outputs']['critic']}
        dependencies={} if role!='repair' else {'critic':state['bindings']['critic']}
        require(args['artifacts']==artifacts and args['artifact_bindings']==dependencies
            and binding['dependencies']==dependencies,'accepted stage dependency mismatch')
        raw=receipt['result']['stdout'].strip();fence=re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```',raw,re.S)
        value=decode((fence.group(1) if fence else raw).encode(),16384)
        require(value==state['outputs'][role],'candidate/receipt raw output mismatch')


def _summarize(manifest,rows,allowance):
    samples=[dict(id=r['id'],caseId=r['caseId'],arm=r['arm'],status=r['status'],path=r['path']) for r in rows]
    unknown=allowance['unknownSamples']+allowance['pendingSamples']
    return dict(version=1,origin=manifest['settings']['origin'],binding=sha(manifest),scheduled=len(manifest['schedule']),
        completed=sum(r['status']=='completed' for r in rows),blocked=sum(r['status']=='blocked' for r in rows),
        failed=sum(r['status'] not in ('completed','blocked') for r in rows),reviewEnabled=manifest['settings']['review'],
        acceptedReviews=sum(r.get('review',{}).get('candidate') is not None for r in rows if r.get('review')),
        providerRequests=sum(r.get('usage',{}).get('providerRequests',0) for r in rows),
        actualTokens=None if unknown else sum(r.get('usage',{}).get('reportedTokens',0) for r in rows),
        unknownSamples=allowance['unknownSamples'],pendingSamples=allowance['pendingSamples'],
        retained=allowance['retained'],semanticQuality='unmeasured',samples=samples)


def _validate_completed(frozen,output,bundle,manifest,seal):
    require(manifest['frozen']==str(Path(frozen)) and manifest['datasetSha256']==sha(bundle)
        and manifest['code']==code_binding(),'saved run input/code mismatch')
    rows=[]
    for entry in seal['outcomes']:
        require(entry['path']==f"outcomes/{entry['id']}.json",'outcome path escape')
        row=read(output/entry['path'],67108864)
        require(sha(row)==entry['sha256'] and row['id']==entry['id'],'outcome digest mismatch')
        rows.append(row)
    require([r['id'] for r in rows]==[r['id'] for r in manifest['schedule']], 'outcome denominator mismatch')
    for entry in seal['files']:
        path=output/entry['path'];require(not path.is_symlink() and path.resolve().is_relative_to(output), 'saved evidence path')
        require(path.is_file() and sha(path.read_bytes())==entry['sha256'],'saved raw evidence mismatch')
    ledger=read(output/'allowance.json')
    for row,item in zip(rows,manifest['schedule']):
        _check_saved_row(output,row,item,manifest,ledger['samples'].get(row['id']))
        if not row.get('retrieval'):continue
        case=next(c for c in bundle['cases'] if c['id']==row['caseId'])
        validate_capture(frozen,bundle,case,row['retrieval'])
        if row.get('base') is None:continue
        packet=initial_packet(case['question'],row['retrieval']['frames'],_identity(frozen,bundle,case,row['arm']))
        require(read(output/'samples'/row['id']/'inputs.json')==packet.to_dict(),'saved initial packet mismatch')
        _check_stage(row.get('base'),packet,'base',generation_profile=bundle.get('generationProfile',generation.LEGACY))
        if (row.get('base') or {}).get('candidate') is not None:
            completeness_profile.validate_candidate(row['base']['candidate'],packet)
            from .qualified_answer import qualify_answer
            require(row['base']['qualifiedCandidate']==qualify_answer(row['base']['candidate'],case['question'],row['retrieval']['frames']),
                    'base answer rendering mismatch')
        if (row.get('review') or {}).get('candidate') is not None:
            review_packet=completeness_profile.freeze_packet(case['question'],row['base']['candidate'],row['retrieval']['frames'],
                identity=_identity(frozen,bundle,case,row['arm']))
            completeness_profile.validate_candidate(row['review']['candidate'],review_packet)
            require(read(output/'samples'/row['id']/'review-inputs.json')==review_packet.to_dict(),'saved review packet mismatch')
            _check_stage(row['review'],review_packet,'review',generation_profile=bundle.get('generationProfile',generation.LEGACY))
            require(row['review']['qualifiedCandidate']==qualify_answer(row['review']['candidate'],case['question'],row['retrieval']['frames']),
                    'review answer rendering mismatch')
    return rows


def replay(frozen,output):
    """No model, provider, socket, ledger settlement or mutable output writes."""
    frozen,output=Path(frozen),Path(output);bundle=load_frozen(frozen)
    manifest=read(output/'run.json');seal=read(output/'results-seal.json')
    require(seal['runSha256']==sha(manifest),'run seal mismatch')
    rows=_validate_completed(frozen,output,bundle,manifest,seal)
    ledger=read(output/'allowance.json');require(ledger['identity']==sha(manifest),'allowance binding mismatch')
    allowance=seal['allowance']
    require(sha(ledger)==seal['allowanceSha256'],'allowance changed since sealing')
    return _summarize(manifest,rows,allowance)


def run(frozen,output,*,fixture=False,review=False,config_path=None,_fixture_server=None):
    from prosaic_runtime import ExecutionBudget,ProsaicRuntime
    require(type(fixture) is bool and type(review) is bool,'explicit modes required')
    require(_fixture_server is None or fixture,'fixture injection forbidden for live mode')
    require('json_schema_v1' in ProsaicRuntime.capabilities,'qualified json_schema_v1 Runtime required')
    frozen,output=Path(frozen),Path(output);bundle=load_frozen(frozen)
    from .generation import runtime_options, LEGACY
    runtime_options(bundle.get('generationProfile',LEGACY),ProsaicRuntime.capabilities)
    from . import execution
    execution_profile=bundle.get('executionProfile',execution.LEGACY)
    timing=execution.limits(execution_profile)
    if not fixture:require(bundle.get('castleMap') is not None,'live Castle comparison requires frozen import map')
    schedule=[]
    for i,case in enumerate(bundle['cases']):
        # strict precedes expanded to bind identical raw ranks; manual order alternates.
        arms=ARMS if i%2==0 else ('strict','expanded','manual')
        schedule.extend(dict(id=_sample_id(case['id'],arm),caseId=case['id'],arm=arm) for arm in arms)
    settings=fixture_settings(len(schedule),review) if fixture else _settings(config_path,len(schedule),review)
    manifest=dict(version=1,frozen=str(frozen),datasetSha256=sha(bundle),code=code_binding(),settings=settings,
        sdkVersions={name:version(name) for name in ('b3-prosaic','b3-prosaic-runtime','b3-prosaic-harness')},schedule=schedule)
    if (output/'run.json').exists():require(read(output/'run.json')==manifest,'saved run config mismatch')
    if (output/'results-seal.json').exists():return replay(frozen,output)
    private_directory(output)
    lock=os.open(output/'run.lock',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if not (output/'run.json').exists():
            require(set(p.name for p in output.iterdir())=={'run.lock'},'unresolved output directory')
            exclusive(output/'run.json',manifest)
        allowance=BenchmarkAllowance(output/'allowance.json',identity=sha(manifest),limits=settings['limits'],version=2)
        status=allowance.status();stop=bool(status['pendingSamples'] or status['unknownSamples'] or status['overrunSamples'])
        rows=[]
        from .fixture import FixtureServer
        server_context=(nullcontext(_fixture_server) if _fixture_server is not None else FixtureServer()) if fixture else nullcontext(None)
        with server_context as server:
            config=server.config if fixture else _runtime(settings)
            for item in schedule:
                sid=item['id'];path=f'outcomes/{sid}.json';sampledir=output/'samples'/sid
                if (output/path).exists():
                    row=read(output/path,67108864)
                    _check_saved_row(output,row,item,manifest,allowance.sample(sid))
                    rows.append(row);continue
                row=dict(item,path=path,status='blocked',base=None,review=None,retrieval=None)
                previous=allowance.sample(sid)
                if stop or previous is not None:
                    if previous is not None:row['status']='unresolved';stop=True
                    _store_row(output,row,manifest);rows.append(row);continue
                case=next(c for c in bundle['cases'] if c['id']==item['caseId']);started=time.monotonic()
                maximum=dict(providerRequests=3 if review else 1,reportedTokens=98304 if review else 32768,toolCalls=0)
                try:
                    sample_seconds=timing.sample
                    if execution_profile!=execution.LEGACY:
                        sample_seconds=min(sample_seconds,allowance.status()['deadline']-time.time())
                        require(sample_seconds>0,'shared execution deadline')
                    # Reserve before any inference; a crash from here remains pending.
                    allowance.reserve(sid,maximum)
                except ValueError:
                    stop=True;_store_row(output,row,manifest);rows.append(row);continue
                budget=ExecutionBudget(timeout_s=sample_seconds,max_provider_requests=maximum['providerRequests'],
                    max_reported_tokens=maximum['reportedTokens'],max_tool_calls=0)
                try:
                    if fixture:
                        selected_provider=fixture_provider(frozen,bundle)
                        wings={bundle['sources'][s]['wing'] for s in case['sourceIds']}
                        selected_provider.slices={r:s for r,s in selected_provider.slices.items() if s['provenance']['wing'] in wings}
                        provider_context=nullcontext(selected_provider)
                    else:provider_context=_provider(settings,bundle,case)
                    with budget.activate(),provider_context as provider:
                        search_replay=None
                        if item['arm']=='expanded':
                            strict=read(output/f"outcomes/{_sample_id(case['id'],'strict')}.json",67108864)
                            require(strict['retrieval'] is not None,'strict capture unavailable')
                            search_replay=[a['result'] for a in strict['retrieval']['audit'] if a['op']=='search']
                        retrieved=prepare(frozen,bundle,case,item['arm'],provider=provider,search_replay=search_replay)
                        validate_capture(frozen,bundle,case,retrieved)
                        row['retrieval']=retrieved
                        require(retrieved['memoryStatus'] not in ('unavailable',),'memory unavailable')
                        identity=_identity(frozen,bundle,case,item['arm']);packet=initial_packet(case['question'],retrieved['frames'],identity)
                        exclusive(sampledir/'inputs.json',packet.to_dict())
                        elapsed=math.floor(min(timing.answer,sample_seconds-(time.monotonic()-started)));require(elapsed>0,'task deadline')
                        row['base']=run_answer(config,packet,sampledir/'base',elapsed_seconds=elapsed,
                            generation_profile=bundle.get('generationProfile',generation.LEGACY),execution_profile=execution_profile)
                        if review and row['base']['candidate'] is not None and not _unknown(budget,[row['base']]):
                            candidate_packet=completeness_profile.freeze_packet(case['question'],row['base']['candidate'],retrieved['frames'],identity=identity)
                            exclusive(sampledir/'review-inputs.json',candidate_packet.to_dict())
                            elapsed=math.floor(min(timing.review,sample_seconds-(time.monotonic()-started)));require(elapsed>0,'task deadline')
                            row['review']=completeness_profile.run_review(config,candidate_packet,sampledir/'review',elapsed_seconds=elapsed,
                                generation_profile=bundle.get('generationProfile',generation.LEGACY),execution_profile=execution_profile)
                    row['status']='completed' if row['base']['candidate'] is not None and (not review or row['review'] is not None
                        and row['review']['candidate'] is not None) else 'rejected'
                except Exception as error:
                    row.update(status='failed',errorType=type(error).__name__,errorMessage=str(error)[:512]);stop=True
                row['usage']=dict(providerRequests=budget.provider_requests,reportedTokens=budget.reported_tokens,
                    toolCalls=budget.tool_calls,usageComplete=budget.usage_complete,elapsedSeconds=time.monotonic()-started)
                unknown=_unknown(budget,[row['base'],row['review']])
                if row['status']=='failed' and budget.provider_requests:unknown=True
                if unknown:
                    row['status']='usage_unknown';allowance.finish(sid,actual=None,evidence_digest=None);stop=True
                else:
                    actual={k:row['usage'][k] for k in maximum}
                    over=budget.reservation_exceeded or any(actual[k]>maximum[k] for k in actual)
                    if over:stop=True;row['status']='overrun'
                    allowance.finish(sid,actual=actual,evidence_digest=sha(row),
                        violation='token_reservation_exceeded' if over else None)
                _store_row(output,row,manifest);rows.append(row)
        files=[dict(path=p.relative_to(output).as_posix(),sha256=sha(p.read_bytes())) for p in sorted(output.rglob('*'))
               if p.is_file() and p.name not in ('run.lock','allowance.json.lock')]
        exclusive(output/'results-seal.json',dict(runSha256=sha(manifest),
            outcomes=[dict(id=r['id'],path=r['path'],sha256=sha(r)) for r in rows],files=files,
            allowance=allowance.status(),allowanceSha256=sha(read(output/'allowance.json'))))
        return replay(frozen,output)
    finally:os.close(lock)
