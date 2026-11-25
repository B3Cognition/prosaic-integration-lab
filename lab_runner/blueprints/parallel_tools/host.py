"""Trusted application declarations; Runtime owns scheduling and validation."""
import prosaic_runtime as runtime
import prosaic_harness as harness


def build_host(*,base_url,provider,lookup,max_concurrency=2,authorize=lambda a,c:True,operation_key=None,require_citations=False,evidence_allowed=lambda use:True):
    def read(arguments,context):
        value=lookup(arguments,context)
        if isinstance(value,(runtime.ToolFailure,runtime.ToolResultV1)):return value
        return runtime.ToolResultV1(data={'count':value},evidence=(runtime.EvidenceDraftV1('graph-'+arguments['component'],'r1','PRIVATE-LOCATOR','/count','Dependents'),))
    tool=runtime.CustomTool('lookup','Read component dependents',{'type':'object','required':['component'],'properties':{'component':{'type':'string','maxLength':128}},'additionalProperties':False},read,'1',max_result_bytes=8192,with_context=True,parallel_read=True,authorize=authorize,operation_key=operation_key,result_contract=runtime.ToolResultContractV1('1'),event_policy=runtime.ToolEventPolicyV1('1',{'count':runtime.ToolDisplayFieldV1('result','/count')}))
    config=runtime.RuntimeConfig({'api':runtime.EndpointConfig(base_url,'synthetic',provider=provider,features={'streaming':False})},{},'api',frozenset({'lookup'}))
    agent=runtime.ProsaicArtifact('analyst','subagent',{'name':'analyst','description':'Read service evidence','tools':['lookup']},'Answer using granted tools and cite sources when required.')
    contracts=harness.ToolContracts('parallel-host','1',evidence_authorizer=runtime.EvidenceAuthorizerV1('sources','1',evidence_allowed),display_authorizer=runtime.ToolDisplayAuthorizerV1('viewer','1',lambda use:True),citations=runtime.CitationPolicyV1('required') if require_citations else None)
    return harness.ConversationBindings(agent,version='parallel-1',config=config,policy=harness.ConversationPolicy(),custom_tools={'lookup':tool},tool_contracts=contracts,operation_namespace='parallel-graph',run_policy=runtime.RunPolicy(allowed_tools=frozenset({'lookup'}),max_provider_requests=3,max_tool_calls=8,parallel_tools=runtime.ParallelToolPolicyV1(max_concurrency=max_concurrency)))


def forward_event(event,send):
    if event.get('event')=='tool_execution_settled' and 'parallelToolV1' in event:send(event)
    elif event.get('event') in {'tool_started','tool_completed'} and 'toolEventV1' in event:send(event)
