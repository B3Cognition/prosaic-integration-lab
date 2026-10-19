"""Synthetic parcel domain using only public installed SDK APIs; never live."""
from contextvars import ContextVar
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import sys
from threading import Thread

from .quality.allowance import private_directory, private_write
from .quality.contracts import digest
from .tool_approval import ApprovalGate
from .trajectory import Trajectory, read_report, save_report

SCENARIOS = ('ready','missing','wrong','malformed','tool-error','provider-error')
_INSPECTING = ContextVar('trajectory_inspecting',default=False)


def _deny_network(event, arguments):
    if _INSPECTING.get() and event in ('socket.connect','socket.connect_ex','socket.getaddrinfo'):
        raise AssertionError('offline inspection attempted network')


sys.addaudithook(_deny_network)


def _assess(evidence, lookup, usage, binding):
    """Independent host parcel rules over verified SDK receipts, not telemetry."""
    receipts=evidence['receipts']
    categories=[]
    if any(r['result']['token_usage'] is None for r in receipts) or not receipts:
        provider_failure=any(
            r['result'].get('metadata',{}).get('provider_error_code')=='http_error'
            and type(r['result']['metadata'].get('http_status')) is int
            and 400<=r['result']['metadata']['http_status']<=599 for r in receipts)
        status='incomplete';categories=(['provider'] if provider_failure else [])+['accounting']
    else:
        tool_error=any(e.get('event')=='tool_completed' and e.get('status')!='ok'
                       for r in receipts for e in r['events'])
        output=evidence['checkpoint']['outputs'].get('worker')
        if tool_error:categories=['tool']
        elif not lookup:categories=['evidence']
        else:
            binding_id=evidence['checkpoint']['bindings'].get('worker',{}).get('id')
            scoped=[row for row in lookup if row['invocationId']==binding_id]
            if not scoped:categories=['model_output']
            elif output != {'dispatch': scoped[0]['manifest']['releaseAuthorized'] is True}:
                categories=['model_output']
        status='failed' if categories else 'passed'
    return dict(bindingDigest=binding,status=status,categories=categories,
                evidenceDigest=digest(evidence),usage=usage)


def qualify(output, *, provider, scenario):
    with ExitStack() as resources:
        return _qualify(output,provider=provider,scenario=scenario,resources=resources)


def _qualify(output, *, provider, scenario, resources):
    from prosaic_runtime import (CustomTool, EndpointConfig, ExecutionBudget, InvocationScope,
        ProsaicArtifact, ProsaicRuntime, RuntimeConfig, TokenCounterDescriptor, TokenCounterRegistration)
    from prosaic_runtime.accounting import MemoryRecorder
    from prosaic_harness import (Harness, FileRunStore, WorkflowFactory, WorkflowCatalog,
        WorkflowBindings, WorkflowPolicy, Validator)
    if provider not in ('openai','anthropic') or scenario not in SCENARIOS:
        raise ValueError('closed synthetic trajectory lane required')
    root=private_directory(Path(output))
    if any(root.iterdir()):raise ValueError('fresh synthetic directory required')
    run_id='1'*32
    binding=digest(dict(domain='parcel-v1',provider=provider,scenario=scenario))
    trace=Trajectory(run_id,binding_digest=binding,key=secrets.token_bytes(32))
    requests=[];errors=[];lookup=[]
    manifest=dict(releaseAuthorized=scenario!='missing',privateNote='PRIVATE-MANIFEST')
    def read_manifest(arguments,context):
        if scenario=='tool-error':raise RuntimeError('PRIVATE-HANDLER-ERROR')
        lookup.append(dict(invocationId=context.scope.invocation_id,manifest=manifest))
        private_write(root/'lookup.json',lookup)
        return manifest
    tool=CustomTool('read_manifest','Read the current granted parcel manifest.',
        dict(type='object',properties={},additionalProperties=False),read_manifest,'parcel-v1',with_context=True)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            try:
                size=int(self.headers.get('Content-Length','0'))
                assert 0<size<=262144
                native=json.loads(self.rfile.read(size));requests.append(1)
                assert len(requests)<=4 and native['model']=='trace-fixture'
                assert native.get('max_tokens',native.get('max_completion_tokens'))==512
                tools=native.get('tools',[])
                assert len(tools)==1
                assert (tools[0]['name'] if provider=='anthropic' else tools[0]['function']['name'])=='read_manifest'
                if scenario=='provider-error':
                    raw=json.dumps({'error':{'type':'synthetic_error','message':'PRIVATE-PROVIDER'}}).encode()
                    status=500
                else:
                    first=len(requests)==1
                    answer='PRIVATE-INVALID-JSON' if scenario=='malformed' else json.dumps({
                        'dispatch':False if scenario=='wrong' else manifest['releaseAuthorized']})
                    if provider=='anthropic':
                        content=[dict(type='tool_use',id='call',name='read_manifest',input={})] if first else [dict(type='text',text=answer)]
                        response=dict(id='synthetic',type='message',role='assistant',model=native['model'],content=content,
                            stop_reason='tool_use' if first else 'end_turn',usage=dict(input_tokens=100,output_tokens=50))
                    else:
                        message=dict(role='assistant',content=None,tool_calls=[dict(id='call',type='function',
                            function=dict(name='read_manifest',arguments='{}'))]) if first else dict(role='assistant',content=answer)
                        response=dict(id='synthetic',model=native['model'],choices=[dict(index=0,message=message,
                            finish_reason='tool_calls' if first else 'stop')],
                            usage=dict(prompt_tokens=100,completion_tokens=50,total_tokens=150))
                    raw=json.dumps(response).encode();status=200
                self.send_response(status);self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
            except Exception as exc:
                errors.append(type(exc).__name__);self.send_error(400)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    resources.callback(server.server_close)
    thread=Thread(target=server.serve_forever,daemon=True)
    def stop_server():
        if thread.is_alive():
            server.shutdown();thread.join(timeout=3)
        server.server_close()
        assert not thread.is_alive()
    ep=EndpointConfig(f'http://127.0.0.1:{server.server_port}/v1','trace-fixture',
        provider='anthropic' if provider=='anthropic' else 'openai-compatible',max_tokens=512,features={'streaming':False})
    config=RuntimeConfig({'fixture':ep},{},'fixture',allowed_tools=frozenset({'read_manifest'}))
    counter=TokenCounterRegistration(TokenCounterDescriptor(identity='parcel-synthetic',provider=ep.provider,
        model=ep.model,framing_revision='anthropic-messages-v1' if provider=='anthropic' else 'openai-chat-v1',
        context_capacity_tokens=32768,implementation_version='synthetic-v1',tokenizer_assets_digest='a'*64,
        template_assets_digest='b'*64,counting_kind='exact',guarantee='Synthetic units only; never live qualification.'),
        type('SyntheticCounter',(),{'count_tokens':lambda self,native:100})())
    budget=ExecutionBudget(timeout_s=600,max_provider_requests=4,max_tool_calls=2,max_reported_tokens=8192,token_counter=counter)
    recorder=MemoryRecorder(provider_id=ep.provider)
    runtime=ProsaicRuntime(config,custom_tools={'read_manifest':tool},accounting=recorder)
    agent=ProsaicArtifact('parcel-worker','subagent',dict(name='parcel-worker',description='Synthetic parcel decision',tools=['read_manifest']),
        'Read the current manifest once. Return only JSON {"dispatch": true or false}. '
        'Dispatch requires current releaseAuthorized=true. Missing authority means hold. {{args}}')
    def validate(value,context):
        rows=[r for r in lookup if r['invocationId']==context.bindings['worker']['id']]
        return [] if rows and value=={'dispatch':rows[0]['manifest']['releaseAuthorized']} else ['manifestMismatch']
    schema=dict(type='object',properties=dict(dispatch=dict(type='boolean')),required=['dispatch'],additionalProperties=False)
    definition=dict(version=1,start='worker',limits=dict(max_calls=1,max_visits=1,max_tokens=8192,
        timeout_s=600,max_run_s=600),steps={
        'worker':dict(kind='agent',agent='parcel',schema='decision',tools=['read_manifest'],require_tools=['read_manifest'],max_attempts=1,next='check'),
        'check':dict(kind='check',**{'from':'worker'},validators=['manifest'],**{'pass':'done','fail':'review'}),
        'review':dict(kind='pause',question='Inspect current manifest.',choices={'stop':'stopped'},requires=['worker']),
        'done':dict(kind='finish',requires=['worker']),'stopped':dict(kind='finish',outcome='rejected')})
    workflow=WorkflowFactory(catalog=WorkflowCatalog(agents={'parcel':agent},schemas={'decision':schema}),
        bindings=WorkflowBindings(config=config,custom_tools={'read_manifest':tool},validators={'manifest':Validator('parcel-v1',validate)},
                                  operation_namespace='parcel-domain'),
        policy=WorkflowPolicy(allowed_agents=['parcel'],allowed_schemas=['decision'],allowed_tools=['read_manifest'],
            allowed_validators=['manifest'],allow_agent_composition=True,max_calls=1,max_visits=1,max_attempts=1,
            timeout_s=600,max_run_s=600,max_tokens=8192,max_provider_requests_per_invocation=4,
            max_tool_calls_per_invocation=2)).build(definition)
    store=FileRunStore(root/'store',namespace='parcel-trajectory');store.initialize()
    resources.callback(store.close)
    harness=Harness(workflow,store=store,run_id=run_id,runtime=runtime,accounting=recorder,observer=trace.observe)
    thread.start();resources.callback(stop_server)
    try:
        try:
            with budget.activate():harness.run({'parcel':'parcel-internal'})
        finally:
            stop_server()
        evidence=harness.recovery_evidence()
        private_write(root/'evidence.json',evidence)
        tokens=[r['result']['token_usage'] for r in evidence['receipts']]
        usage=dict(providerRequests=len(recorder.intents),toolCalls=budget.tool_calls,
                   reportedTokens=sum(tokens) if tokens and all(t is not None for t in tokens) else None)
        assessment=_assess(evidence,lookup,usage,binding)
        trace.annotate('worker',kind='evidence',status='verified' if lookup and lookup[0]['manifest']['releaseAuthorized'] else 'missing',
                       evidence_digest=digest(lookup))
        trace.annotate('worker',kind='validation',status=assessment['status'],evidence_digest=digest(evidence))
        approval=None
        gate=ApprovalGate(root/'approval.json',identity=binding,tools={'dispatch_parcel':'v1'},approvers=['host-operator'])
        if assessment['status']=='passed' and evidence['checkpoint']['outputs']['worker']['dispatch']:
            gate.propose('dispatch',tool_name='dispatch_parcel',arguments={'dispatch':True},
                scope=InvocationScope(lookup[0]['invocationId'],run_id=run_id,step_id='worker',operation_namespace='parcel-domain'),
                evidence_digest=digest(evidence))
            approval=gate.inspect('dispatch')['state']
            trace.annotate('worker',kind='approval',status=approval,evidence_digest=digest(gate.inspect('dispatch')))
        before=len(requests)
        token=_INSPECTING.set(True)
        try:
            restored=Harness(workflow,store=store,run_id=run_id,runtime=runtime)
            assert restored.recovery_evidence()==evidence
            if approval:assert gate.inspect('dispatch')['state']=='pending'
            trace.annotate('worker',kind='recovery',status='inspected',evidence_digest=digest(evidence))
            report=trace.report(assessment);save_report(root/'trajectory.json',report)
            assert read_report(root/'trajectory.json',binding_digest=binding)==report
        finally:_INSPECTING.reset(token)
        assert len(requests)==before==usage['providerRequests']==budget.provider_requests and not errors
        proof=dict(report=report,providerRequests=budget.provider_requests,toolCalls=budget.tool_calls,
            lookupEffects=len(lookup),networkDeniedRecovery=True,approvalState=approval,liveRequests=0)
        private_write(root/'proof.json',proof)
        return proof
    finally:store.close()


def replay(root):
    """Read saved safe reports only; provider access is explicitly denied."""
    token=_INSPECTING.set(True)
    try:
        root=Path(root)
        for provider in ('openai','anthropic'):
            for scenario in SCENARIOS:
                binding=digest(dict(domain='parcel-v1',provider=provider,scenario=scenario))
                read_report(root/(provider+'-'+scenario)/'trajectory.json',binding_digest=binding)
        return 12
    finally:_INSPECTING.reset(token)
