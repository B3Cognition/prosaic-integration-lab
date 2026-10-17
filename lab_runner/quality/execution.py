"""Run benchmark workflows through public installed Runtime/Harness contracts."""
from copy import deepcopy
from dataclasses import replace
import time
from .contracts import decode, digest, encode, identifier
from .allowance import private_directory, private_write
from .suite import public_case, resource, agent_prose, AGENT_NAMES
from .checks import assess_evidence, compare_fields, parse_task, checks_digest

CASE_LIMITS = dict(providerRequests=8,toolCalls=4,reportedTokens=16384,timeoutSeconds=30)


def project_correction_arguments(artifact_id,arguments):
    """Reduce only a host-target correction's context; never rewrite its result."""
    if artifact_id!='quality-review-corrector':return arguments
    data=decode(arguments)
    feedback=data.get('validation_feedback')
    if not isinstance(feedback,str) or not feedback.startswith('publicCheck '):return arguments
    value=decode(feedback.removeprefix('publicCheck '))
    if 'target' not in value or value.get('missingRecords') or value.get('error'):return arguments
    from jsonschema import Draft202012Validator,ValidationError
    target=value['target']
    try:Draft202012Validator(decode(resource('review.schema.json'))).validate(target)
    except ValidationError as exc:raise ValueError('invalid public review target') from exc
    if target['approved']!= (not target['issues']):raise ValueError('inconsistent public review target')
    request=data['request']
    return encode(dict(caseId=request['caseId'],correctionTarget=target,
                       recordIndex=request['recordIndex'])).decode('utf-8')


def workflow_definition(kind,limits):
    def step(agent,next_,**extra):
        return dict(kind='agent',agent=agent,schema='review' if agent in {'critic','review-corrector'} else 'answer',
            tools=['lookup_records'],require_tools=['lookup_records'],max_attempts=2,next=next_,**extra)
    steps={'answer':step('reviewer','done',validators=['answer']),'done':{'kind':'finish'}}
    if kind=='repair':
        steps={'critic':step('critic','critic-check')|{'max_attempts':1},
            'critic-check':dict(kind='check',**{'from':'critic'},validators=['review'],
                               **{'pass':'author','fail':'review-correction'}),
            'review-correction':step('review-corrector','author',inputs=['critic'],validators=['review'])|{'max_attempts':1},
            'author':step('author','done',inputs=['critic'],optional_inputs=['review-correction'],validators=['answer']),
            'done':{'kind':'finish'}}
    return dict(version=1,start='critic' if kind=='repair' else 'answer',
        limits=dict(max_calls=4,max_visits=2,timeout_s=limits['timeoutSeconds'],
                    max_tokens=limits['reportedTokens'],max_run_s=limits['timeoutSeconds']),steps=steps)


def workflow_policy(limits):
    return dict(allowed_agents=list(AGENT_NAMES),allowed_schemas=['answer','review'],
        allowed_tools=['lookup_records'],allowed_validators=['answer','review'],allowed_model_tiers=['quality'],
        allow_agent_composition=True,max_calls=4,max_visits=2,max_attempts=2,
        timeout_s=limits['timeoutSeconds'],max_run_s=limits['timeoutSeconds'],max_tokens=limits['reportedTokens'],
        max_provider_requests_per_invocation=limits['providerRequests']//4,
        max_tool_calls_per_invocation=limits['toolCalls']//4)


def materials(case, config, profile, sample_id, limits, *, journal_path=None):
    from prosaic_harness import WorkflowFactory,WorkflowCatalog,WorkflowBindings,WorkflowPolicy,Validator
    from prosaic_runtime import CustomTool,ProsaicArtifact,ProsaicRuntime,RuntimeAdapter
    identifier(sample_id)
    if profile not in config.profiles: raise ValueError('unapproved benchmark profile')
    config=replace(config,default_profile=profile,routes={'quality':profile},
                   allowed_tools=frozenset({'lookup_records'}),tool_directories=())
    request=public_case(case)
    parse_task(request['task'])
    journal=decode(journal_path.read_bytes()) if journal_path is not None and journal_path.exists() else []
    active={};started={};current={}
    def on_event(event):
        if event.get('event')=='started':
            started[event['attempt_id']]=time.monotonic()
            current['invocationId']=event['attempt_id']
        if event.get('event')=='completed' and event['attempt_id'] in started:
            on_event.timings[event['attempt_id']]=time.monotonic()-started[event['attempt_id']]
        if event.get('event')=='tool_started':active[event['attempt_id']]=event['call_id']
    on_event.timings={}
    def lookup(arguments,context):
        ids=arguments['recordIds']
        rows=[deepcopy(case['records'][key]) for key in ids]
        row=dict(sampleId=sample_id,invocationId=context.scope.invocation_id,
            callIndex=context.call_index,callId=active.get(context.scope.invocation_id),
            signature=digest(dict(tool_name='lookup_records',tool_version='lookup-v1',arguments=arguments)),
            toolVersion='lookup-v1',recordIds=ids,recordsSha256=digest(rows),status='ok')
        journal.append(row)
        if journal_path is not None:private_write(journal_path,journal)
        return rows
    schema=dict(type='object',properties={'recordIds':dict(type='array',minItems=1,maxItems=4,
        uniqueItems=True,items={'enum':sorted(case['records'])})},required=['recordIds'],additionalProperties=False)
    tool=CustomTool('lookup_records','Read synthetic dossier records by their public record IDs',
                    schema,lookup,'lookup-v1',with_context=True,max_argument_bytes=1024,max_result_bytes=8192)
    agents={name:ProsaicArtifact('quality-'+name,'subagent',dict(name='quality-'+name,
        description='Review synthetic evidence',model_tier='quality',tools=['lookup_records']),agent_prose(name))
        for name in AGENT_NAMES}
    def public_check(output,context):
        # Harness has already verified successful required tool execution in this
        # receipt. Bind feedback to that attempt, never a prior agent's evidence.
        invocation=current.get('invocationId',journal[-1]['invocationId'] if journal else None)
        fetched=[]
        for row in journal:
            if row['invocationId']!=invocation:continue
            if row['sampleId']!=sample_id:raise ValueError('foreign lookup journal')
            records=[deepcopy(case['records'][key]) for key in row['recordIds']]
            if digest(records)!=row['recordsSha256']:raise ValueError('changed fetched evidence')
            fetched.extend(records)
        if not fetched:return ['publicCheck '+encode({'error':'noCurrentEvidence'}).decode('utf-8')]
        try:assessment=assess_evidence(request,fetched)
        except (ValueError,KeyError,TypeError):
            return ['publicCheck '+encode({'error':'unsupportedEvidence'}).decode('utf-8')]
        if assessment['missingRecords']:
            feedback={'error':'fetchCurrentRecordsBeforeDeciding','missingRecords':assessment['missingRecords']}
        elif context.step in {'critic','review-correction'}:
            issues=compare_fields(assessment['answer'],request['draft'])
            review=dict(approved=not issues,issues=issues)
            if output['approved']==review['approved'] and set(output['issues'])==set(issues):return []
            fields=[]
            if output['approved']!=review['approved']:fields.append('approved')
            if set(output['issues'])!=set(issues):fields.append('issues')
            feedback={'target':review,'fields':fields,'draftIssues':issues}
        else:
            issues=compare_fields(assessment['answer'],output)
            if not issues:return []
            feedback={'target':assessment['answer'],'fields':issues,'missingFacts':assessment['missingFacts']}
        return ['publicCheck '+encode(feedback).decode('utf-8')]
    version='quality-public-checks-v1-'+digest(dict(source=checks_digest(),request=request))
    validators={name:Validator(version,public_check) for name in ('answer','review')}
    def invoke(artifact,arguments,*,execute,**options):
        return execute(project_correction_arguments(artifact.id,arguments))
    adapter=RuntimeAdapter(ProsaicRuntime(config,custom_tools={'lookup_records':tool}),
        'quality-review-projection-v1-'+checks_digest(),invoke,max_attempts=1)
    definition=workflow_definition(case['kind'],limits)
    factory=WorkflowFactory(catalog=WorkflowCatalog(agents=agents,schemas={
        'answer':decode(resource('answer.schema.json')),'review':decode(resource('review.schema.json'))}),
        bindings=WorkflowBindings(config=config,custom_tools={'lookup_records':tool},validators=validators,
                                  runtime_adapter=adapter),
        policy=WorkflowPolicy(**workflow_policy(limits)))
    return factory.build(definition),journal,on_event


def extract(case,sample_id,harness,journal,elapsed,*,timings=None):
    evidence=harness.recovery_evidence()
    receipts=evidence['receipts'];state=evidence['checkpoint']
    answer=state['outputs'].get('author' if case['kind']=='repair' else 'answer')
    counts=dict(providerRequests=0,toolCalls=0,reportedTokens=0)
    input_tokens=output_tokens=0
    for receipt in receipts:
        result=receipt['result'];info=result['metadata'].get('invocation_budgets_v1',{})
        counts['providerRequests']+=info.get('provider_requests',0)
        counts['toolCalls']+=info.get('tool_calls',0)
        if result['token_usage'] is None:counts['reportedTokens']=None
        elif counts['reportedTokens'] is not None:counts['reportedTokens']+=result['token_usage']
        usage=result['metadata'].get('token_usage_details',{})
        if type(usage.get('prompt_tokens')) is not int:input_tokens=None
        elif input_tokens is not None:input_tokens+=usage['prompt_tokens']
        if type(usage.get('completion_tokens')) is not int:output_tokens=None
        elif output_tokens is not None:output_tokens+=usage['completion_tokens']
    if state['pending'] is not None:
        counts['reportedTokens']=None
    failures=[e for e in state['history'] if e['event']=='validation_failed']
    retried={r['id'] for i,r in enumerate(receipts) if any(n['step']==r['step'] for n in receipts[i+1:])}
    semantic=lambda e:e.get('message')=='answerIncorrect' or e.get('message','').startswith('publicCheck ')
    schema_repairs=sum(e['attempt_id'] in retried and not semantic(e) for e in failures)
    task_repairs=sum(e['attempt_id'] in retried and semantic(e) for e in failures)
    task_repairs+=sum(e['event']=='check_failed' and e.get('message','').startswith('publicCheck ')
        for e in state['history']) if any(r['step']=='review-correction' for r in receipts) else 0
    critic=state['outputs'].get('review-correction')
    if critic is None and any(e['event']=='check_passed' and e['step']=='critic-check' for e in state['history']):
        critic=state['outputs'].get('critic')
    result=dict(version=1,sampleId=sample_id,caseId=case['caseId'],answer=answer,
        journal=deepcopy(journal),receipts=receipts,receiptDigests=[digest(r) for r in receipts],
        completed=state['status']=='completed',counts=counts,elapsedSeconds=elapsed,
        inputTokens=input_tokens,outputTokens=output_tokens,
        schemaRepairs=schema_repairs,taskRepairs=task_repairs,
        firstPass=case['kind']=='ordinary' and not failures and state['status']=='completed',
        criticDetected=bool(critic and critic['approved'] is False and 'decision' in critic['issues']),
        reason=state['reason'],workflowDigest=digest(harness.workflow.definition),
        attempts=[dict(invocationId=r['id'],step=r['step'],exitCode=r['result']['exit_code'],
                        reportedTokens=r['result']['token_usage'],elapsedSeconds=(timings or {}).get(r['id'])) for r in receipts])
    return result


def execute_case(case,*,config,profile,output,sample_id,limits):
    from prosaic_harness import Harness,FileRunStore
    output=private_directory(output)
    workflow,journal,on_event=materials(case,config,profile,sample_id,limits,
                                      journal_path=output/(sample_id+'-journal.json'))
    store=FileRunStore(output/'store',namespace='agent-quality');store.initialize()
    run_id=digest({'sampleId':sample_id})[:32]
    harness=Harness(workflow,store=store,run_id=run_id,on_event=on_event)
    began=time.monotonic()
    try:
        harness.run(public_case(case))
        result=extract(case,sample_id,harness,journal,time.monotonic()-began,timings=on_event.timings)
        private_write(output/(sample_id+'-execution.json'),result)
        return result
    finally:store.close()
