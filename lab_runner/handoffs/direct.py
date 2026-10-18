"""Opt-in direct worker/critic graphs through installed public SDK APIs."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit
import time
from jsonschema import Draft202012Validator
from lab_runner.quality.contracts import decode,encode,digest,identifier
from lab_runner.quality.allowance import private_directory,private_write
from .contracts import LIMITS,request_for,assignment
from .direct_contracts import output_schemas,instructions,expected_worker,worker_issues,expected_review,same_review
from .execution import _collect


def materials(case,config,output,sample_id,*,mode='handoff',draft=None,record_ids=None):
    from prosaic_runtime import ProsaicArtifact,CustomTool,ProsaicRuntime,RuntimeAdapter
    from prosaic_harness import WorkflowFactory,WorkflowCatalog,WorkflowBindings,WorkflowPolicy,Validator
    identifier(sample_id)
    if mode not in ('handoff','worker','critic'):raise ValueError('invalid direct mode')
    request=request_for(case);binding=assignment(request);snapshot=deepcopy(case['records'])
    if config.profiles[config.default_profile].max_tokens!=512:raise ValueError('unchanged output cap required')
    if mode=='critic':
        if not Draft202012Validator(output_schemas()['worker']).is_valid(draft):raise ValueError('invalid controlled draft')
        ids=sorted(snapshot) if record_ids is None else record_ids
        if (type(ids) is not list or not 1<=len(ids)<=16
                or any(type(k) is not str or k not in snapshot for k in ids)
                or len(set(ids))!=len(ids)):raise ValueError('invalid controlled evidence')
        ids=list(ids);draft=deepcopy(draft)
    elif draft is not None or record_ids is not None:raise ValueError('controls require critic mode')
    else:ids=None
    request=request|dict(assignment=binding)
    if mode=='critic':request['reviewDraft']=draft
    output=private_directory(Path(output));path=output/(sample_id+'-journal.json')
    journal=decode(path.read_bytes()) if path.exists() else []
    config=replace(config,routes={'handoff':config.default_profile},allowed_tools=frozenset({'lookup_records'}),tool_directories=())
    def lookup(args,context):
        rows=[deepcopy(snapshot[k]) for k in args['recordIds']]
        journal.append(dict(sampleId=sample_id,assignmentId=binding['assignmentId'],
            invocationId=context.scope.invocation_id,recordIds=args['recordIds'],recordsSha256=digest(rows)))
        private_write(path,journal)
        return rows
    tool=CustomTool('lookup_records','Read current granted source records.',
        dict(type='object',properties={'recordIds':dict(type='array',minItems=1,maxItems=16,
            uniqueItems=True,items={'enum':sorted(snapshot)})},required=['recordIds'],additionalProperties=False),
        lookup,'direct-handoff-lookup-v2',with_context=True,max_argument_bytes=2048,max_result_bytes=8192)
    def fetched(invocation):
        rows=[]
        for entry in journal:
            if entry['invocationId']!=invocation:continue
            values=[snapshot[k] for k in entry['recordIds']]
            if (entry['sampleId']!=sample_id or entry['assignmentId']!=binding['assignmentId'] or
                    digest(values)!=entry['recordsSha256']):raise ValueError('foreign or changed lookup evidence')
            rows.extend(values)
        if not rows:raise ValueError('worker lookup evidence missing')
        return deepcopy(rows)
    def source(context):
        return [deepcopy(snapshot[k]) for k in ids] if mode=='critic' else fetched(context.bindings['worker']['id'])
    def check_binding(value,context):
        return [] if value['assignmentId']==binding['assignmentId'] else ['resultBindingMismatch']
    def check_gate(value,context):
        clean=expected_worker(request_for(case),source(context))
        worker=draft if mode=='critic' else context.artifacts['worker']
        if mode!='worker' and not same_review(expected_review(clean,worker),value):return ['criticIncorrect']
        if worker_issues(clean,worker):return ['workerIncorrect']
        return [] if clean['status']=='ready' else ['evidenceRequiresHumanReview']
    def project(artifact,arguments,*,execute,**options):
        if artifact.id=='direct-critic':
            data=decode(arguments)
            rows=[deepcopy(snapshot[k]) for k in ids] if mode=='critic' else fetched(data['artifact_bindings']['worker']['id'])
            data['currentEvidence']=dict(assignmentId=binding['assignmentId'],
                origin='hostControl' if mode=='critic' else 'workerLookup',records=rows)
            return execute(encode(data).decode())
        return execute(arguments)
    version='direct-v2-'+digest(dict(request=request,snapshot=snapshot,mode=mode,ids=ids))
    validators={'binding':Validator(version,check_binding),'gate':Validator(version,check_gate)}
    roles=['worker','critic'] if mode=='handoff' else [mode]
    agents={r:ProsaicArtifact('direct-'+r,'subagent',dict(name='direct-'+r,description='Direct evidence '+r,
        model_tier='handoff',tools=['lookup_records'] if r=='worker' else []),instructions(r,binding)) for r in roles}
    steps={}
    for role in roles:
        steps[role]=dict(kind='agent',agent=role,schema=role,tools=['lookup_records'] if role=='worker' else [],
            max_attempts=1,next='critic' if role=='worker' and mode=='handoff' else 'gate')
        if role=='worker':steps[role].update(require_tools=['lookup_records'],validators=['binding'])
        if role=='critic' and mode=='handoff':steps[role]['inputs']=['worker']
    last=roles[-1]
    steps.update({'gate':dict(kind='check',**{'from':last},validators=['gate'],**{'pass':'done','fail':'human-review'}),
        'human-review':dict(kind='pause',question='Current evidence or review requires human inspection.',choices={'stop':'stopped'},requires=[last]),
        'done':dict(kind='finish',requires=roles),'stopped':dict(kind='finish',outcome='rejected')})
    definition=dict(version=1,start=roles[0],limits=dict(max_calls=len(roles),max_visits=1,max_tokens=8192,
        timeout_s=600,max_run_s=600),steps=steps)
    policy=WorkflowPolicy(allowed_agents=roles,allowed_schemas=roles,allowed_tools=['lookup_records'],
        allowed_validators=list(validators),allowed_model_tiers=['handoff'],allow_agent_composition=True,
        max_calls=len(roles),max_visits=1,max_attempts=1,timeout_s=600,max_run_s=600,max_tokens=8192,
        max_provider_requests_per_invocation=2,max_tool_calls_per_invocation=1)
    adapter=RuntimeAdapter(ProsaicRuntime(config,custom_tools={'lookup_records':tool}),version,project,max_attempts=1)
    workflow=WorkflowFactory(catalog=WorkflowCatalog(agents=agents,schemas={r:output_schemas()[r] for r in roles}),
        bindings=WorkflowBindings(config=config,custom_tools={'lookup_records':tool},validators=validators,runtime_adapter=adapter),policy=policy).build(definition)
    return workflow,request,journal


def execute_case(case,*,config,output,sample_id,mode='handoff',draft=None,record_ids=None,token_counter=None):
    from prosaic_runtime import ExecutionBudget,TokenCounterRegistration,TokenCounterDescriptor
    from prosaic_harness import Harness,FileRunStore
    from lab_runner.quality.token_admission import admit_live_counters
    from lab_runner.memory_policy.trace import TraceRecorder
    ep=config.profiles[config.default_profile]
    if token_counter is None:
        url=urlsplit(ep.base_url)
        if (ep.model!='direct-handoff-fixture' or url.scheme!='http' or url.hostname!='127.0.0.1'
                or url.username or url.password):
            raise ValueError('qualified matching counter required outside synthetic loopback')
        class Synthetic:
            def count_tokens(self,native):return 100
        token_counter=TokenCounterRegistration(TokenCounterDescriptor(identity='direct-synthetic',provider=ep.provider,
            model=ep.model,framing_revision='anthropic-messages-v1' if ep.provider=='anthropic' else 'openai-chat-v1',
            context_capacity_tokens=32768,implementation_version='synthetic-v2',tokenizer_assets_digest='a'*64,
            template_assets_digest='b'*64,counting_kind='exact',guarantee='Synthetic units only; no live qualification.'),Synthetic())
    reg=admit_live_counters({config.default_profile:token_counter},config,[config.default_profile])[config.default_profile]
    workflow,request,journal=materials(case,config,output,sample_id,mode=mode,draft=draft,record_ids=record_ids)
    path=Path(output)/(sample_id+'-context-trace.json');trace=TraceRecorder(path,provider_id=ep.provider)
    proposals=[]
    class Measured:
        def count_tokens(self,native):
            bound=reg.counter.count_tokens(native);proposals.append(dict(inputBound=bound,nativeSha256=digest(native)))
            trace.proposals(proposals);return bound
    budget=ExecutionBudget(timeout_s=600,max_provider_requests=4,max_tool_calls=2,max_reported_tokens=8192,
        token_counter=TokenCounterRegistration(reg.descriptor,Measured()))
    store=FileRunStore(Path(output)/'store',namespace='direct-handoffs');store.initialize();began=time.monotonic()
    try:
        h=Harness(workflow,store=store,run_id=digest(dict(sampleId=sample_id))[:32],on_event=trace.event,accounting=trace)
        with budget.activate():h.run(request)
        result=_collect(h,journal);trace.finish(result['receipts'])
        result.update(version=2,sampleId=sample_id,mode=mode,control=mode=='critic',hostAssignment=request['assignment'],
            controlledDraft=deepcopy(draft),controlledRecordIds=record_ids,
            elapsedSeconds=time.monotonic()-began,counterDescriptor=reg.descriptor.to_dict(),
            contextTrace=dict(fileName=path.name,sha256=digest(decode(path.read_bytes()))))
        return result
    finally:store.close()


def recover_case(case,*,config,output,sample_id,mode='handoff',draft=None,record_ids=None):
    """Read verified saved state only. Never drive any graph node on recovery."""
    from prosaic_harness import Harness,FileRunStore
    workflow,request,journal=materials(case,config,output,sample_id,mode=mode,draft=draft,record_ids=record_ids)
    store=FileRunStore(Path(output)/'store',namespace='direct-handoffs');store.initialize()
    try:
        h=Harness(workflow,store=store,run_id=digest(dict(sampleId=sample_id))[:32]);h.status()
        result=_collect(h,journal)
        result.update(version=2,sampleId=sample_id,mode=mode,control=mode=='critic',hostAssignment=request['assignment'],
                      controlledDraft=deepcopy(draft),controlledRecordIds=record_ids)
        return result
    finally:store.close()
