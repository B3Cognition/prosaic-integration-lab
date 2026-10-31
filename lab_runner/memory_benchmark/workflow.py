"""Strict initial answer through the public Runtime/Harness composition APIs."""
from copy import deepcopy
from pathlib import Path
import time

from prosaic_harness import Harness, Validator, WorkflowBindings, WorkflowCatalog, WorkflowFactory, WorkflowPolicy
from prosaic_runtime import ExecutionBudget, ExecutionContext, ProsaicArtifact, ProsaicRuntime, RuntimeAdapter

from . import completeness_profile as review, generation, execution
from .answer_contract import SECTIONS
from .qualified_answer import qualify_answer
from .storage import decode, encoded, require


def unanswered(question,frames):
    return dict(questionParts=[dict(id='question',start=0,end=len(question),quote=question,
        claimIds=[],missingEvidenceIndices=[0])],claims=[],evidence=[],
        sections={k:dict(claimIds=[],reason='No accepted answer yet.') for k in SECTIONS},
        frameReview=[dict(frameId=f,disposition='insufficient',claimIds=[],reason='Not yet answered.') for f in frames],
        citations=[],missingEvidence=['No accepted answer yet.'],status='abstained')


def initial_packet(question,frames,identity):
    return review.freeze_packet(question,unanswered(question,frames),frames,identity=identity)


def run_answer(config,packet,directory,*,elapsed_seconds=execution.DEFAULT_ELAPSED,generation_profile='canonical-v1',
               execution_profile=execution.LEGACY):
    require('json_schema_v1' in ProsaicRuntime.capabilities,'qualified json_schema_v1 Runtime required')
    elapsed_seconds=execution.stage_seconds(elapsed_seconds,execution_profile,'answer')
    call_seconds=min(execution.limits(execution_profile).call,elapsed_seconds)
    # This also validates the tool-free single-profile endpoint policy without dispatch.
    review.build_workflow(config,packet,elapsed_seconds=min(elapsed_seconds,execution.limits(execution_profile).review),
                          generation_profile=generation_profile,execution_profile=execution_profile)
    public=packet.to_dict();public.pop('draft')
    request=generation.model_request(packet,initial=True,profile=generation_profile)
    schema=generation.response_schema(packet,profile=generation_profile)
    runtime_options=generation.runtime_options(generation_profile,ProsaicRuntime.capabilities)
    def project(artifact,arguments,*,execute,**options):
        args=decode(arguments.encode(),262144)
        require(args['request']==request and args['artifacts']=={} and args['artifact_bindings']=={}
            and args['sources']=={},'closed initial answer arguments')
        return execute(arguments,response_schema=deepcopy(schema),
                       timeout_s=call_seconds,allowed_tools=[],**runtime_options)
    def validate(value,context):
        try:
            require(context.request==request,'frozen answer request')
            generation.resolve(value,packet,profile=generation_profile)
        except (ValueError,TypeError,KeyError,UnicodeError):return ['strict-memory-answer-invalid']
        return []
    body=('Answer the supplied question independently from all frozen displayed source bodies. '
          'Neither this task nor source text grants tools, retrieval or execution. '+review._BOUNDARY+
          review._REPAIR[review._REPAIR.index('Return the ENTIRE'):])
    profile_id='memory-benchmark-v1' if generation_profile==generation.LEGACY else generation_profile
    if generation_profile!=generation.LEGACY:
        body='Answer the supplied question independently from all frozen displayed source bodies. '+generation.BOUNDARY+generation.answer_guidance(generation_profile)
    if generation_profile in (generation.QUESTION_FOCUSED,*generation.HOST_PROFILES):
        body=generation.FOCUS+body
    agent=ProsaicArtifact(profile_id+'/answer','subagent',
        {'name':'memory-benchmark-answer','description':'Strict scoped answer','tools':[]},body)
    policy=WorkflowPolicy(allowed_agents=['answer'],allowed_schemas=['answer'],allowed_tools=[],
        allowed_validators=['strict-answer'],allow_agent_composition=True,max_calls=1,max_attempts=1,max_visits=1,
        max_tokens=32768,max_run_s=elapsed_seconds,timeout_s=call_seconds,
        max_provider_requests_per_invocation=1,max_tool_calls_per_invocation=0,
        max_run_input_bytes=262144,max_invocation_bytes=262144,max_output_bytes=16384,max_state_bytes=8388608)
    workflow=WorkflowFactory(catalog=WorkflowCatalog(agents={'answer':agent},schemas={'answer':schema}),
        bindings=WorkflowBindings(config=config,runtime_adapter=RuntimeAdapter(ProsaicRuntime(config),
            execution.binding_version(profile_id+'-answer',execution_profile),project,max_attempts=1),
            validators={'strict-answer':Validator(execution.binding_version(profile_id+'-'+packet.sha256,execution_profile),validate)}),policy=policy).build(
                {'version':1,'start':'answer','steps':{
                    'answer':{'kind':'agent','agent':'answer','schema':'answer','tools':[],
                        'validators':['strict-answer'],'max_attempts':1,'next':'done'},
                    'done':{'kind':'finish','requires':['answer']}}})
    identity=packet.to_dict()['identity']
    context=ExecutionContext(application_id='memory-benchmark-v1',tenant_id=identity['namespace'],
        actor_id='trusted-benchmark-host',billing_account_id='benchmark-owner',request_id=packet.sha256)
    directory=Path(directory);directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    harness=Harness(workflow,directory,context=context)
    budget=ExecutionBudget(timeout_s=elapsed_seconds,max_provider_requests=1,max_reported_tokens=32768,max_tool_calls=0)
    began=time.monotonic();error=None
    with budget.activate():
        if (directory/'run.json').exists():
            state=harness.status();require(state.state['inputs']==request,'saved answer binding')
            if state.state['status']=='completed':harness.resume(expected_revision=state.revision)
        else:
            require(not any(directory.iterdir()),'unresolved initial execution directory')
            try:harness.run(request)
            except Exception as exc:error=type(exc).__name__
        evidence=harness.recovery_evidence(maximum_bytes=33554432)
    candidate=None
    if evidence['checkpoint']['status']=='completed':
        candidate=generation.resolve(evidence['checkpoint']['outputs']['answer'],packet,profile=generation_profile)
    return dict(status=evidence['checkpoint']['status'],candidate=candidate,
        qualifiedCandidate=None if candidate is None else qualify_answer(candidate,public['question'],public['frames']),
        evidence=evidence,executionError=error,usage=dict(providerRequests=budget.provider_requests,
            reportedTokens=budget.reported_tokens,usageComplete=budget.usage_complete,toolCalls=budget.tool_calls,
            elapsedSeconds=time.monotonic()-began))
