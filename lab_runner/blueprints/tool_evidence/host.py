"""Trusted application bindings. Authenticate the principal before constructing these."""
from pathlib import Path
import prosaic_runtime as runtime
import prosaic_harness as harness

PROJECT=Path(__file__).parent


def dependents_tool(lookup,*,legacy=False):
    def execute(arguments):
        records=lookup(arguments['component'])
        if type(records) is not list or len(records)>128:raise ValueError('bounded records required')
        data={'count':len(records),'dependents':records}
        if legacy:return data
        return runtime.ToolResultV1(data=data,evidence=(runtime.EvidenceDraftV1(
            'service-graph','revision-424242','PRIVATE-LOCATOR','/dependents','Service dependents'),))
    return runtime.CustomTool('dependents','Read the granted component dependents',
        {'type':'object','required':['component'],'properties':{'component':{'type':'string','maxLength':128},
            'credential':{'type':'string','maxLength':128}},'additionalProperties':False},execute,'1',max_result_bytes=8192,
        result_contract=None if legacy else runtime.ToolResultContractV1('1',{'type':'object','required':['count','dependents'],
            'properties':{'count':{'type':'integer'},'dependents':{'type':'array','maxItems':128}},'additionalProperties':False}),
        event_policy=runtime.ToolEventPolicyV1('1',{'component':runtime.ToolDisplayFieldV1('arguments','/component'),
            'count':runtime.ToolDisplayFieldV1('result','/count')}))


def bindings(*,base_url,provider,lookup,evidence_allowed=lambda use:True,display_allowed=lambda use:True):
    tool=dependents_tool(lookup)
    contracts=harness.ToolContracts('cerebro-tools','1',evidence_authorizer=runtime.EvidenceAuthorizerV1('evidence','1',evidence_allowed),
        display_authorizer=runtime.ToolDisplayAuthorizerV1('display','1',display_allowed),citations=runtime.CitationPolicyV1('required'))
    config=runtime.RuntimeConfig({'api':runtime.EndpointConfig(base_url,'synthetic-tool-evidence',provider=provider,
        features={'streaming':False},max_tokens=256)},{},'api',frozenset({'dependents'}))
    artifact=runtime.ProsaicArtifact('analyst','subagent',{'name':'analyst','description':'Service evidence analyst','tools':['dependents']},
        'ALWAYS use captured evidence and cite exact sources. NEVER invent dependents or progress.')
    return harness.ConversationBindings(artifact,version='tool-evidence-1',config=config,policy=harness.ConversationPolicy(),
        custom_tools={'dependents':tool},tool_contracts=contracts,operation_namespace='service-graph',
        run_policy=runtime.RunPolicy(allowed_tools=frozenset({'dependents'}),max_provider_requests=2,max_tool_calls=1))


def forward_event(event,send):
    """Forward the SDK's approved event; the host chooses its SSE transport."""
    if event.get('event') in {'tool_started','tool_completed'} and 'toolEventV1' in event:
        send(event)
