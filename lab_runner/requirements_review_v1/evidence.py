"""Host evidence joins, immutable local artifacts and zero-dispatch scoring replay."""

import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import tempfile

from . import SUITE_VERSION
from .cases import load_cases, public_task
from .contracts import ENGINE_IDENTITY, LIMITS, SDK_VERSIONS, STRATEGIES, decode, digest, encoded
from .host_keys import load_keys
from .scoring import grade

MAX_BYTES=16777216
RATE_CARD={'version':'synthetic-demo-rates-v1','inputMicrousdPerMillionTokens':2000000,
           'outputMicrousdPerMillionTokens':8000000,'meaning':'Fixture units only; no money spent or model-quality evidence.'}


def _validated_runs(evidence):
    """Restore into disposable public stores; Harness.status validates SDK seals/ledger.

    No SDK contract internals are imported, and status cannot drive a graph node.
    The retained runtime binding rebuilds the admitted workflow fingerprint.
    """
    from dataclasses import asdict
    from prosaic_harness import FileRunStore, Harness, StoreError
    from prosaic_runtime import CliSandboxConfig, EndpointConfig, RunLimits, RuntimeConfig
    from prosaic_integration_lab.sue_review.contracts import ReviewSettings
    from prosaic_integration_lab.sue_review.engine import load_engine
    from prosaic_integration_lab.sue_review.workflow import build_review_workflow
    from prosaic_integration_lab.sue_review.session import SueReviewSession
    from .execution import NAMESPACE, PRINCIPAL, _admit, _workflow, runtime_binding, sue_settings

    binding=evidence['runtimeBinding']
    config=RuntimeConfig(profiles={key:EndpointConfig(**value) for key,value in binding['profiles'].items()},
        routes=binding['routes'],default_profile=binding['default_profile'],
        allowed_tools=frozenset(binding['allowed_tools']),limits=RunLimits(**binding['limits']),
        tool_directories=tuple(binding['tool_directories']),cli_sandbox=CliSandboxConfig(
            mode=binding['cli_sandbox']['mode'],runtime_roots=tuple(binding['cli_sandbox']['runtime_roots'])))
    _admit(config)
    if runtime_binding(config)!=binding:raise ValueError('runtime binding mismatch')
    runs=evidence['runs'];strategy=evidence['strategy']
    if (strategy!='sue' and len(runs)!=1 or strategy=='sue' and len(runs) not in (1,2)
            or evidence['executionStatus']=='completed' and len(runs)!=(2 if strategy=='sue' else 1)):
        raise ValueError('strategy run inventory mismatch')
    if evidence['executionStatus']=='completed' and any(run['checkpoint']['status']!='completed' for run in runs):
        raise ValueError('completed sample has unfinished saved stages')
    workflows={};engines={}
    for index,run in enumerate(runs):
        state=run['checkpoint'];is_sue=strategy=='sue' and index==0
        expected_owner={'tenant_id':PRINCIPAL.tenant_id,'actor_id':PRINCIPAL.actor_id,
            'billing_account_id':PRINCIPAL.billing_account_id,'project_id':NAMESPACE,
            'application_id':'integration-lab-sue-review' if is_sue else 'requirements-review-eval'}
        if any(state['accounting_context'].get(k)!=v for k,v in expected_owner.items()):
            raise ValueError('trusted run owner mismatch')
        if is_sue:
            engine=load_engine(ENGINE_IDENTITY);settings=ReviewSettings.from_mapping(sue_settings(evidence['limits']))
            policy={k:v for k,v in asdict(settings).items() if k!='enabled'}
            if state['inputs']['reviewPolicy']!=policy:raise ValueError('SUE policy binding mismatch')
            workflow=build_review_workflow(config=config,settings=settings,engine=engine)
            engines[run['runId']]=engine
        else:workflow=_workflow(config,strategy,evidence['limits'])
        try:
            with tempfile.TemporaryDirectory(prefix='requirements-replay-check-') as temporary:
                with FileRunStore(Path(temporary).resolve(),namespace=NAMESPACE) as store:
                    with store.lease(run['runId']) as lease:
                        revision=store.create_run(run['runId'],state,lease)
                        if revision!=run['revision']:raise ValueError('checkpoint revision mismatch')
                        for receipt in run['receipts']:
                            if receipt is None:raise ValueError('missing retained receipt')
                            store.save_receipt(run['runId'],receipt['id'],receipt,lease)
                    Harness(workflow,store=store,run_id=run['runId']).status()
                    if is_sue:
                        expected=SueReviewSession(settings={'enabled':False},store=store,config=config,
                            principal=PRINCIPAL,namespace=NAMESPACE).report(run['runId'])
                        if evidence['strategyDiagnostic']!=expected:
                            raise ValueError('SUE diagnostic reconstruction mismatch')
        except StoreError as error:
            raise ValueError('SDK rejected saved documents') from error
        workflows[run['runId']]=workflow
    return workflows,engines


def _sue_projection(receipt,state,workflow,engine):
    from prosaic_integration_lab.sue_review.workflow import project_answer, step_number

    arguments=receipt['arguments'];number=step_number(receipt['step'])
    prefix={f'answer-{n:02}':state['outputs'][f'answer-{n:02}'] for n in range(1,number)}
    bindings={name:state['bindings'][name] for name in prefix}
    if (arguments['request']!=state['inputs'] or arguments['artifacts']!=prefix
            or arguments['artifact_bindings']!=bindings):
        raise ValueError('SUE accepted prefix binding mismatch')
    captured=[]
    class Captured(Exception):pass
    def capture(arguments,**options):
        captured.append(arguments)
        raise Captured()
    try:
        project_answer(workflow.artifacts[receipt['step']],encoded(arguments).decode(),execute=capture,engine=engine)
    except Captured:pass
    if len(captured)!=1:raise ValueError('missing deterministic projection')
    return captured[0]


def implementation():
    root=Path(__file__).resolve().parent
    files={path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(root.glob('*.py'))}
    legacy=json.loads((root/'legacy-v10-source-lock.json').read_text())
    for name,sha in legacy['files'].items():
        if hashlib.sha256((root.parents[1]/name).read_bytes()).hexdigest()!=sha:
            raise ValueError('legacy byte binding changed')
    binding={'suiteVersion':SUITE_VERSION,'files':files,'legacySourceLockSha256':digest(legacy),
             'casesSha256':digest(load_cases()),'keysSha256':digest(load_keys()),
             'sdkVersions':SDK_VERSIONS,'sueEngineIdentity':ENGINE_IDENTITY}
    lock=root/'source-lock.json'
    if not lock.is_file() or json.loads(lock.read_text())!=binding:
        raise ValueError('requirements source binding changed')
    return binding


def assess(evidence):
    if evidence['origin']!='scripted_requirements_fixture' or evidence['strategy'] not in STRATEGIES:
        raise ValueError('unsupported evidence origin or strategy')
    limits=evidence['limits']
    if set(limits)!=set(LIMITS) or any(type(v) is not int or not 1<=v<=LIMITS[k] for k,v in limits.items()):
        raise ValueError('invalid common allowance')
    case=load_cases()[evidence['caseId']]
    task=public_task(case)
    if evidence['task']!=task or evidence['taskSha256']!=digest(task):
        raise ValueError('public task binding mismatch')
    rows=evidence['wire'];usage=evidence['usage']
    if (any(type(usage.get(k)) is not int or usage[k]<0 for k in ('providerRequests','toolCalls','reportedTokens'))
            or type(usage.get('usageComplete')) is not bool
            or type(usage.get('elapsedSeconds')) not in (int,float)
            or not math.isfinite(usage['elapsedSeconds']) or usage['elapsedSeconds']<0):
        raise ValueError('invalid usage counts')
    if usage['providerRequests']!=len(rows) or usage['toolCalls']!=0 or evidence['replayAdditionalRequests']!=0:
        raise ValueError('dispatch accounting mismatch')
    workflows,engines=_validated_runs(evidence)
    offset=0;input_tokens=output_tokens=reported=0;complete=True;bound_final=None
    for run in evidence['runs']:
        state=run['checkpoint']
        if state['run_id']!=run['runId']:raise ValueError('run identity mismatch')
        if len(state['invocations'])!=len(run['receipts']):raise ValueError('attempt inventory mismatch')
        by_id={receipt['id']:receipt for receipt in run['receipts'] if receipt is not None}
        for name,binding in state['bindings'].items():
            receipt=by_id.get(binding['id'])
            if receipt is None or decode(receipt['result']['stdout'],maximum=262144)!=state['outputs'][name]:
                raise ValueError('accepted output binding mismatch')
        if 'final' in state['outputs']:bound_final=state['outputs']['final']
        if 'publicTask' in state['inputs']:
            if state['inputs']!={'publicTask':task,'strategyAdvice':evidence['strategyDiagnostic']}:
                raise ValueError('final task binding mismatch')
        else:
            if state['inputs']['seed']!=task['claim'] or state['inputs']['evidence']!=task['evidence']:
                raise ValueError('SUE source binding mismatch')
            if state['inputs']['engine']['engineIdentity']['digest']!=ENGINE_IDENTITY:
                raise ValueError('SUE engine binding unavailable')
            diagnostic=evidence['strategyDiagnostic']
            outputs=state['outputs']
            terminal=outputs[sorted(outputs)[-1]]['terminal'] if outputs else None
            if diagnostic is not None and (diagnostic['terminal']!=terminal or diagnostic['acceptedTurns']!=len(outputs)):
                raise ValueError('SUE diagnostic binding mismatch')
        for invocation,receipt in zip(state['invocations'],run['receipts'],strict=True):
            if receipt is None:raise ValueError('missing attempt receipt')
            if (receipt['id']!=invocation['id'] or receipt['step']!=invocation['step']
                    or receipt['run_id']!=run['runId']):
                raise ValueError('receipt invocation mismatch')
            result=receipt['result'];budget=result['metadata']['invocation_budgets_v1']
            count=budget['provider_requests']
            if type(count) is not int or count not in (0,1):raise ValueError('unexpected request grouping')
            if count:
                if offset>=len(rows):raise ValueError('missing wire exchange')
                row=rows[offset];offset+=1
                if row['status']!=200 or row['request']['model']!=row['response']['model']:
                    raise ValueError('invalid fixture exchange')
                messages=row['request']['messages']
                if len(messages)!=1 or messages[0]['role']!='user' or row['request'].get('tools'):
                    raise ValueError('unexpected wire prompt shape')
                content=messages[0]['content']
                if receipt['step'].startswith('answer-'):
                    _,separator,arguments=content.partition('\n\n## Arguments\n')
                    if not separator:raise ValueError('SUE prompt arguments missing')
                    projected=decode(arguments,maximum=262144)
                    expected=_sue_projection(receipt,state,workflows[run['runId']],engines[run['runId']])
                    attempts=result['metadata']['runtime_adapter_v1']['attempts']
                    if (arguments!=expected or len(attempts)!=1
                            or content!=workflows[run['runId']].artifacts[receipt['step']].body+'\n\n## Arguments\n'+expected
                            or attempts[0]['arguments_sha256']!=hashlib.sha256(arguments.encode()).hexdigest()):
                        raise ValueError('deterministic SUE wire projection mismatch')
                    lines=[line for source in task['evidence']['sources'] for line in source['text'].splitlines()]
                    if (projected['seed']!=task['claim'] or projected['sourceLines']!=[
                            {'line':n,'text':line} for n,line in enumerate(lines,1)]):
                        raise ValueError('SUE wire sources changed')
                else:
                    _,separator,arguments=content.partition('\nTask arguments:\n')
                    if (not separator or decode(arguments,maximum=262144)!=receipt['arguments']
                            or content!=workflows[run['runId']].artifacts[receipt['step']].body.replace('{{args}}',arguments)):
                        raise ValueError('wire receipt arguments mismatch')
                wire_output=row['response']['choices'][0]['message']['content']
                raw=result['metadata'].get('sueRawResponse')
                if raw is not None and raw!=wire_output:raise ValueError('SUE raw response mismatch')
                if raw is None and result['exit_code']==0 and result['stdout']!=wire_output:
                    raise ValueError('final response mismatch')
                reported_usage=row['response'].get('usage')
                if reported_usage is None:
                    complete=False
                else:
                    if (any(type(reported_usage.get(n)) is not int or reported_usage[n]<0
                            for n in ('prompt_tokens','completion_tokens','total_tokens'))
                            or reported_usage['prompt_tokens']+reported_usage['completion_tokens']!=reported_usage['total_tokens']):
                        raise ValueError('invalid usage')
                    input_tokens+=reported_usage['prompt_tokens'];output_tokens+=reported_usage['completion_tokens']
                    reported+=reported_usage['total_tokens']
                    if result['token_usage']!=reported_usage['total_tokens']:
                        raise ValueError('receipt usage mismatch')
    if offset!=len(rows) or usage['reportedTokens']!=reported or usage['usageComplete']!=complete:
        raise ValueError('unmatched attempts or usage')
    if usage['providerRequests']>evidence['limits']['calls']:
        raise ValueError('common call limit exceeded')
    final=evidence['final'];semantic=None
    if final!=bound_final:raise ValueError('final accepted output mismatch')
    if final is not None:
        semantic=grade(case,load_keys()[case['caseId']],final)
    within_limits=(usage['reportedTokens']<=limits['tokens'] and usage['elapsedSeconds']<=limits['elapsedSeconds'])
    passed=evidence['executionStatus']=='completed' and complete and within_limits and semantic is not None and semantic['passed']
    cost=(input_tokens*RATE_CARD['inputMicrousdPerMillionTokens']+output_tokens*RATE_CARD['outputMicrousdPerMillionTokens']+999999)//1000000
    return {'suiteVersion':SUITE_VERSION,'origin':evidence['origin'],'caseId':case['caseId'],
        'strategy':evidence['strategy'],'sampleId':evidence['sampleId'],'passed':bool(passed),
        'executionStatus':evidence['executionStatus'],'executionError':evidence['executionError'],
        'grade':semantic,'strategyDiagnostic':evidence['strategyDiagnostic'],
        'usage':{**usage,'estimatedSpendMicrousd':cost if complete else None,'rateCard':RATE_CARD},
        'limits':evidence['limits'],'taskSha256':evidence['taskSha256'],
        'replayAdditionalRequests':0,'meaning':'Scripted fixture mechanics only. Review quality and SUE benefit are unproven.'}


def write_sample(output,evidence):
    output=Path(output)
    evidence['implementationSha256']=digest(implementation())
    raw=encoded(evidence)
    if len(raw)>MAX_BYTES:raise ValueError('sample evidence limit')
    # Retain attempted wire data even if an internal evidence join rejects it.
    # The existing directory remains closed to redispatch after partial failure.
    with (output/'evidence.json').open('xb') as handle:handle.write(raw)
    report=assess(evidence)
    data={'evidence.json':raw,'report.json':encoded(report)}
    if len(data['report.json'])>MAX_BYTES:raise ValueError('sample report limit')
    with (output/'report.json').open('xb') as handle:handle.write(data['report.json'])
    lock={'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in data.items()},
          'implementationSha256':evidence['implementationSha256']}
    with (output/'sample-lock.json').open('xb') as handle:handle.write(encoded(lock))
    return report


def read_sample(output):
    output=Path(output)
    lock=decode((output/'sample-lock.json').read_text(),maximum=65536)
    if set(lock['files'])!={'evidence.json','report.json'} or lock['implementationSha256']!=digest(implementation()):
        raise ValueError('source lock mismatch')
    values={}
    for name,sha in lock['files'].items():
        raw=(output/name).read_bytes()
        if len(raw)>MAX_BYTES or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('saved artifact changed')
        values[name]=decode(raw.decode('utf-8'),maximum=MAX_BYTES)
    evidence=values['evidence.json']
    if evidence['implementationSha256']!=lock['implementationSha256']:
        raise ValueError('implementation identity mismatch')
    names=('b3-prosaic','b3-prosaic-runtime','b3-prosaic-harness')
    if set(evidence['sdkVersions'])!=set(names) or evidence['sdkVersions']!={name:version(name) for name in names}:
        raise ValueError('SDK binding unavailable')
    report=assess(evidence)
    if report!=values['report.json']:raise ValueError('report mismatch')
    return report
