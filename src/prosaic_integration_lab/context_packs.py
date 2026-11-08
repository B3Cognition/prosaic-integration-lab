"""Trusted synthetic consumer scenarios; all execution belongs to installed SDKs.

No HTTP client may choose these bindings, principals or captured records.
Application lookup completeness is normalized explicitly before composition.
"""
import json
from pathlib import Path
import uuid


def require_context_pack_sdk():
    import prosaic_harness as harness
    import prosaic_harness_postgres as postgres
    from prosaic_runtime import ProsaicRuntime
    required={'guard_input_views_v1','frozen_turn_inputs_v1','context_input_variants_v1'}
    if (not required <= ProsaicRuntime.capabilities or
            any(not hasattr(harness,name) for name in ('ContextPacker','ContextPackBindings','ContextPackReader')) or
            not hasattr(postgres,'PostgresSessionStore')):
        raise ValueError('installed context-pack SDK capability unavailable')


def scenario(kind, *, outcome='complete', allow_partial=False, conflict=False, reader=False,
             namespace='context-pack-lab', authorize=None):
    from prosaic_harness import (ContextPackSpec,ContextSlot,ContextPackBindings,ContextScope,
        ContextAuthorizer,InputSource,ContextPacker,ContextSnapshot,ContextSource)
    from prosaic_harness.context_packs import capture_sources
    require_context_pack_sdk()
    if kind not in {'markdown-review','service-impact'}: raise ValueError('unknown fixture scenario')
    alias='document' if kind=='markdown-review' else 'lookup'
    records={'task':'Identify supported changes with citations','private':'UNDECLARED-819'}
    records[alias]=('# Release requirements\nREQUIREMENTS-214: preserve evidence.' if kind=='markdown-review' else
        {'service':'csb-frontend','dependents':['dashboard','release-email'],'domainComplete':outcome=='complete',
         'observations':[{'revision':'revision-a','dependency':'kafka','enabled':True}] +
         ([{'revision':'revision-b','dependency':'kafka','enabled':False}] if conflict else [])})
    spec=ContextPackSpec('impact','1',[ContextSlot('task',required=True),ContextSlot(alias,
        required=not reader,availability='discoverable' if reader else 'inline',allow_partial=allow_partial)],task_source='task')
    bindings=ContextPackBindings(specs={'impact':spec},sources={'task':InputSource('/task'),alias:InputSource('/'+alias)},
        scope=ContextScope(namespace,'sandbox','context-pack-lab','tenant-a','actor-a'),
        authorizer=ContextAuthorizer('fixture-access','1',authorize or (lambda use:True)))
    if outcome=='unavailable': records.pop(alias)
    snapshot=capture_sources(spec,{'request':records},{},bindings)
    if outcome=='partial':
        sources=[ContextSource(source.alias,source.source_identity,source.revision,
            'partial' if source.alias==alias else source.outcome,ranked_item_ids=source.ranked_item_ids)
            for source in snapshot.sources]
        snapshot=ContextSnapshot.from_items(list(snapshot.items),sources=sources,scope_binding=bindings.scope)
    return bindings,ContextPacker().compose(spec,snapshot)


def conversation(bindings,store,url, *, reader=None):
    import prosaic_runtime as runtime
    from prosaic_harness import Conversation,ConversationBindings,ConversationPolicy,ConversationScope
    tools={'read_context_item':reader.as_tool()} if reader else {}
    artifact=runtime.ProsaicArtifact('analyst','subagent',{'name':'analyst','description':'Synthetic evidence review','tools':list(tools)},
        'ALWAYS cite supplied evidence and acknowledge incomplete or conflicting observations. NEVER invent facts.')
    config=runtime.RuntimeConfig({'local':runtime.EndpointConfig(url,'synthetic-context-packs',max_tokens=256,
        features={'streaming':False})},{},'local',frozenset(tools))
    binding=ConversationBindings(artifact,version='lab-context-pack-1',config=config,policy=ConversationPolicy(),
        custom_tools=tools,context_packs=bindings,run_policy=runtime.RunPolicy(allowed_tools=frozenset(tools),
            max_provider_requests=2 if reader else 1,max_tool_calls=1 if reader else 0))
    scope=ConversationScope(bindings.scope.namespace,'sandbox','context-pack-lab','tenant-a','actor-a')
    return Conversation(binding,store=store,scope=scope)


def markdown_workflow(root: Path, url: str, store):
    """Two nodes use the same Markdown agent with different evidence selections."""
    import yaml
    from prosaic_harness import Workflow,Harness,ContextPackBindings,ContextScope,ContextAuthorizer,InputSource,EvidenceSource,ArtifactSource
    (root/'.prosaic/subagents').mkdir(parents=True)
    (root/'.prosaic/subagents/reviewer.md').write_text('---\nname: reviewer\ndescription: Review selected evidence\n---\n'
        'ALWAYS cite supplied evidence and return JSON. NEVER invent facts.\n')
    (root/'requirements.md').write_text('# Requirements\nREQUIREMENTS-214: preserve provenance.')
    (root/'constraints.md').write_text('# Constraints\nCONSTRAINTS-317: protect private records.')
    (root/'result.json').write_text('{"type":"object"}')
    (root/'runtime.yml').write_text(yaml.safe_dump({'default_profile':'local','profiles':{'local':{
        'base_url':url,'model':'synthetic-context-packs','max_tokens':256,'features':{'streaming':False}}}}))
    sources={'task':InputSource('/task'),'requirements':EvidenceSource('requirements.md'),
        'constraints':EvidenceSource('constraints.md'),'candidate':ArtifactSource('build')}
    packs={name:{'version':'1','taskSource':'task','slots':[{'source':alias,'required':True} for alias in aliases]}
        for name,aliases in [('implementation',['task','requirements','constraints']),('review',['task','requirements','candidate'])]}
    graph={'version':1,'source':'.prosaic','runtime':'runtime.yml','evidence':['requirements.md','constraints.md'],
        'contextPacks':packs,'agentContextPacks':{'subagents/reviewer.md':'implementation'},'start':'build',
        'limits':{'timeout_s':15,'max_provider_requests_per_invocation':1,'max_tool_calls_per_invocation':0},
        'steps':{'build':{'kind':'agent','agent':'subagents/reviewer.md','schema':'result.json','next':'review'},
            'review':{'kind':'agent','agent':'subagents/reviewer.md','schema':'result.json','contextPack':'review','inputs':['build'],'next':'done'},
            'done':{'kind':'finish','requires':['review']}}}
    path=root/'workflow.yml';path.write_text(yaml.safe_dump(graph))
    bindings=ContextPackBindings(specs={},sources=sources,scope=ContextScope(store.namespace,'sandbox','context-pack-lab','tenant-a','actor-a'),
        authorizer=ContextAuthorizer('fixture-access','1',lambda use:True))
    workflow=Workflow.load(path,context_packs=bindings)
    return Harness(workflow,store=store,run_id=uuid.uuid4().hex)


def service_workflow(url,store):
    """Explicit producer read followed by selected accepted-record evidence."""
    import prosaic_runtime as runtime
    from prosaic_harness import (WorkflowFactory,WorkflowCatalog,WorkflowBindings,WorkflowPolicy,Harness,
        ContextPackSpec,ContextSlot,ContextPackBindings,ContextScope,ContextAuthorizer,InputSource,ArtifactSource)
    calls=[]
    def lookup(arguments):
        calls.append(arguments)
        return {'service':'csb-frontend','dependents':['release-email','dashboard'],'complete':True}
    tool=runtime.CustomTool('lookup_dependents','Read the granted service record',
        {'type':'object','additionalProperties':False},lookup,'1')
    agent=runtime.ProsaicArtifact('analyst','subagent',{'name':'analyst','description':'Impact analyst'},
        'ALWAYS use the accepted lookup and cite evidence. NEVER invent facts.')
    config=runtime.RuntimeConfig({'local':runtime.EndpointConfig(url,'synthetic-context-packs',max_tokens=256,
        features={'streaming':False})},{},'local',frozenset({'lookup_dependents'}))
    spec=ContextPackSpec('impact','1',[ContextSlot('task',required=True),ContextSlot('lookup',required=True)],task_source='task')
    packs=ContextPackBindings(specs={'impact':spec},sources={'task':InputSource('/task'),'lookup':ArtifactSource('lookup')},
        scope=ContextScope(store.namespace,'sandbox','context-pack-lab','tenant-a','actor-a'),
        authorizer=ContextAuthorizer('fixture-access','1',lambda use:True),agent_defaults={'analyst':'impact'})
    factory=WorkflowFactory(catalog=WorkflowCatalog(agents={'analyst':agent},schemas={'result':{'type':'object'}}),
        bindings=WorkflowBindings(config=config,custom_tools={'lookup_dependents':tool},context_packs=packs),
        policy=WorkflowPolicy(allowed_agents={'analyst'},allowed_schemas={'result'},allowed_tools={'lookup_dependents'},
            allowed_direct_tools={'lookup_dependents'},max_provider_requests_per_invocation=1,max_tool_calls_per_invocation=1))
    workflow=factory.build({'version':1,'start':'lookup','steps':{
        'lookup':{'kind':'tool','tool':'lookup_dependents','arguments':{},'schema':'result','next':'review'},
        'review':{'kind':'agent','agent':'analyst','schema':'result','inputs':['lookup'],'next':'done'},
        'done':{'kind':'finish','requires':['review']}}})
    return Harness(workflow,store=store,run_id=uuid.uuid4().hex),calls
