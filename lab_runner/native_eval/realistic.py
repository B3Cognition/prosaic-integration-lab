"""Repeated realistic-task comparison through public installed Runtime APIs."""
import hashlib
import json
import os
from pathlib import Path
import statistics
import tempfile
import time
import urllib.request

from lab_runner.live_allowance import SharedLiveAllowance
from .cases import SOURCE
from .compare import resolve_local_timeout,validate_local_config
from .live import preflight
from .provenance import require_native
from .realistic_cases import CASE_IDS,OUTPUTS,prepare,grade


def _latency(rows):
    values=[r['durationMs'] for r in rows]
    return {'median':statistics.median(values),'min':min(values),'max':max(values)} if values else None


def summary(rows):
    def group(selected,**labels):
        return {**labels,'assignments':len(selected),'successes':sum(r['passed'] for r in selected),
          'completed':sum(r['completed'] for r in selected),
          'successRate':sum(r['passed'] for r in selected)/len(selected),
          'completionRate':sum(r['completed'] for r in selected)/len(selected),
          'allLatencyMs':_latency(selected),
          'successfulLatencyMs':_latency([r for r in selected if r['passed']]),
          'failures':[{'case':r['case'],'trial':r.get('trial'),'reason':r.get('failureReason')}
                      for r in selected if not r['passed']]}
    backends=sorted({r['selector'] for r in rows})
    cases=sorted({r['case'] for r in rows})
    return {'byBackend':[group([r for r in rows if r['selector']==s],selector=s) for s in backends],
      'byTask':[group([r for r in rows if r['selector']==s and r['case']==c],selector=s,case=c)
                for c in cases for s in backends if any(r['selector']==s and r['case']==c for r in rows)]}


def _private_json(path,value):
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as target:
        json.dump(value,target,sort_keys=True,indent=2,allow_nan=False)


def plan(repetitions):
    if type(repetitions) is not int or not 1<=repetitions<=3:
        raise ValueError('realistic benchmark repetitions must be 1..3')
    return {'assignments':9*repetitions,'maximumDispatchUnits':30*repetitions,
            'maximumNativeAttempts':6*repetitions,'maximumLocalRequests':24*repetitions}


def check_local_readiness(endpoint):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    token=Path(endpoint.api_key_file).expanduser().read_text().strip()
    request=urllib.request.Request(endpoint.base_url.rstrip('/')+'/models',headers={'Authorization':'Bearer '+token})
    with urllib.request.build_opener(NoRedirect()).open(request,timeout=10) as response:
        models=json.loads(response.read(262144))
    if endpoint.model not in {m['id'] for m in models['data']}:raise ValueError('local model absent from catalogue')


def _sample(runtime,selector,case,workspace,*,trial,timeout_s,native):
    sdk=require_native();artifact=prepare(case,workspace)
    inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in workspace.iterdir()}
    digest=hashlib.sha256(json.dumps({'body':artifact.body,'inputs':inputs},sort_keys=True).encode()).hexdigest()
    row={'selector':selector,'case':case,'trial':trial,'inputSha256':digest,
      'artifactSha256':hashlib.sha256((SOURCE/artifact.id).read_bytes()).hexdigest(),
      'timeoutSeconds':timeout_s,'passed':False,'completed':False,'nativeAttempts':0,
      'providerRequests':None,'reportedTokens':None,'timings':[]}
    started=time.monotonic()
    if native:
        profile=runtime.config.profiles[selector]
        row.update(backend=profile.backend,model=profile.model,configuredEffort=profile.effort)
    else:
        profile=runtime.config.profiles[runtime.config.default_profile]
        row.update(backend='openai-compatible',model=profile.model)
    try:
        if native:
            def observe_native(event):
                kind=event.get('event')
                if not isinstance(kind,str) or kind not in {
                    'started','profile_selected','profile_skipped','profile_fallback','native_progress','completed'}:return
                safe={'event':kind,'elapsedMs':(time.monotonic()-started)*1000}
                progress=event.get('type')
                if isinstance(progress,str) and progress in {
                    'thread.started','turn.started','turn.completed','turn.failed','error',
                    'item.started','item.updated','item.completed','system','assistant','user',
                    'result','stream_event','rate_limit_event'}:safe['type']=progress
                row['timings'].append(safe)
            result=runtime.run(artifact,cwd=workspace,profile=selector,
                on_event=observe_native,
                policy=sdk.NativePolicy(permission_mode='workspace-write',timeout_s=timeout_s))
            row['nativeAttempts']=len(result.metadata.get('native_execution_v1',{}).get('attempts',[]))
        else:
            def observe(event):
                safe={k:event[k] for k in ('event','name','status','outcome','reason','http_status','duration_ms') if k in event}
                row['timings'].append({**safe,'elapsedMs':(time.monotonic()-started)*1000})
            result=runtime.run(artifact,cwd=workspace,observer=observe,
                policy=sdk.RunPolicy(allowed_tools=frozenset({'read_file','write_file','edit_file'}),
                    read_roots=(str(workspace),),write_paths=(str(workspace/OUTPUTS[case]),),
                    timeout_s=timeout_s,max_provider_requests=8,max_tool_calls=7,
                    max_tool_rounds=8,max_reported_tokens=65536))
            budget=result.metadata.get('invocation_budgets_v1',{})
            row.update(providerRequests=budget.get('provider_requests'),toolCalls=budget.get('tool_calls'))
        row['completed']=result.exit_code==0
        row.update(reportedTokens=result.token_usage,timedOut=result.timed_out,
                   recoveryRequired=bool(result.metadata.get('recovery_required',False)))
        outcome=grade(case,workspace)
        row.update(grade=outcome['checks'],passed=row['completed'] and outcome['passed'])
        row['failureReason']=(None if row['passed'] else 'contract_failed' if row['completed']
                              else result.metadata.get('failure_reason','execution_failure'))
    except Exception:
        row.update(failureReason='execution_uncertain',recoveryRequired=True,
                   nativeAttemptsStatus='unknown' if native else 'not_applicable')
    row['durationMs']=(time.monotonic()-started)*1000
    return row


def run_realistic(*,native_config,local_config,selectors,output,provenance,
                  live=False,repetitions=3,timeout_s=60,local_timeout_s=180):
    if live is not True:raise ValueError('explicit live opt-in required')
    experiment=plan(repetitions)
    local_timeout_s=resolve_local_timeout(local_timeout_s,default=180)
    if local_timeout_s!=180:raise ValueError('realistic suite fixes local timeout at 180 seconds')
    if len(selectors)!=2 or len(set(selectors))!=2 or 'local' in selectors:
        raise ValueError('select two distinct native profiles; local is reserved')
    readiness=preflight(config_path=native_config,selectors=selectors,repetitions=1,maximum=4,timeout_s=timeout_s)
    if not readiness['passed']:raise ValueError('native version preflight failed')
    sdk=require_native();config=sdk.NativeRuntimeConfig.load(native_config)
    if any(s not in config.profiles for s in selectors) or {config.profiles[s].backend for s in selectors}!={'claude-code','codex-cli'}:
        raise ValueError('select one direct Claude and one direct Codex profile')
    local=sdk.RuntimeConfig.load(local_config);validate_local_config(local)
    endpoint=local.profiles[local.default_profile]
    # Refuse redirects, as Runtime does; never forward managed credentials.
    check_local_readiness(endpoint)
    root=Path(output).resolve();root.mkdir(mode=0o700)
    rows_dir=root/'samples';rows_dir.mkdir(mode=0o700)
    outputs=root/'private-outputs';outputs.mkdir(mode=0o700)
    allowance=SharedLiveAllowance(root/'allowance.json',max_calls=experiment['maximumDispatchUnits'],ceiling=90)
    _private_json(root/'plan.json',{'suiteVersion':'realistic-runtime-v1',**experiment,
      'repetitions':repetitions,'cases':list(CASE_IDS),'nativeTimeoutSeconds':timeout_s,
      'localTimeoutSeconds':local_timeout_s,'localLimits':{'providerRequests':8,'toolCalls':7,'reportedTokens':65536},
      'provenance':provenance,'preflight':readiness})
    native_runtime=sdk.NativeRuntime(config);local_runtime=sdk.ProsaicRuntime(local)
    rows=[];order=tuple(selectors)+('local',)
    for repeat in range(repetitions):
        cases=CASE_IDS[repeat:]+CASE_IDS[:repeat]
        backends=order[repeat:]+order[:repeat]
        for case in cases:
            for selector in backends:
                native=selector!='local'
                reservation=allowance.reserve(maximum_requests=1 if native else 8)
                with tempfile.TemporaryDirectory(prefix='workspace-',dir=root) as temporary:
                    workspace=Path(temporary)
                    row=_sample(native_runtime if native else local_runtime,selector,case,workspace,
                        trial=repeat+1,timeout_s=timeout_s if native else local_timeout_s,native=native)
                    observed=(None if row.get('nativeAttemptsStatus')=='unknown' else row['nativeAttempts']) if native else row.get('providerRequests')
                    allowance.finish(reservation,actual_requests=observed)
                    target=workspace/OUTPUTS[case]
                    if target.is_file() and not target.is_symlink() and target.stat().st_size<=32768:
                        body=target.read_bytes()
                        row['outputSha256']=hashlib.sha256(body).hexdigest()
                        path=outputs/f'{repeat+1}-{case}-{selector}-{OUTPUTS[case]}'
                        with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as saved:saved.write(body)
                row['sequence']=len(rows)+1
                rows.append(row)
                _private_json(rows_dir/f'{row["sequence"]:02d}.json',row)
                print(json.dumps({'event':'realistic_sample',**{k:row.get(k) for k in ('sequence','trial','case','selector','passed','completed','durationMs','failureReason','providerRequests')}}),flush=True)
    for case in CASE_IDS:
        if len({(r['artifactSha256'],r['inputSha256']) for r in rows if r['case']==case})!=1:
            raise ValueError('benchmark inputs changed during experiment')
    report={'suiteVersion':'realistic-runtime-v1','origin':'live_repeated_realistic_tasks',
      'passed':all(r['passed'] for r in rows),'sampleCount':len(rows),'repetitions':repetitions,
      'sameInputsAcrossBackendsAndTrials':True,'modelQualityQualified':False,
      'grading':'structured factual contracts, SQL behavior and workspace integrity; prose quality ungraded',
      'nativeTimeoutSeconds':timeout_s,'localTimeoutSeconds':local_timeout_s,
      'samples':rows,**summary(rows),'allowance':allowance.status(),
      'allowanceUnit':'native_cli_attempt_or_local_provider_request','providerRequests':None,
      'cleanup':'verified','provenance':provenance,
      'limitations':['Different system prompts/tools and deadlines.','Native internal provider calls opaque.',
         'Three trials per task; no statistical model ranking.','No warmup; cache/load and host conditions may differ.']}
    _private_json(root/'report.json',report)
    return report
