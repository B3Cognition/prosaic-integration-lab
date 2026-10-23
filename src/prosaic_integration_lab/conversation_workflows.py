"""Host confirmation authority is independent of interpreted model data."""
import json
from pathlib import Path


def confirm_current(source_text,proposal,view):
    return (source_text in {'approve','yes, approve'} and type(proposal) is dict and
        type(view) is dict and proposal.get('ambiguous') is False and
        proposal.get('choice')=='approve' and proposal.get('interactionRef')==view.get('reference') and
        type(view.get('reference')) is str and 'approve' in view.get('choices',()))


def admit_workflow_reply(source_text,proposal,view):
    """Only current whole messages authorize the corresponding fixture phase."""
    if (type(source_text) is not str or type(proposal) is not dict or type(view) is not dict or
            proposal.get('ambiguous') is not False or type(view.get('reference')) is not str or
            proposal.get('interactionRef')!=view['reference']):
        return False
    choices=view.get('choices')
    if type(choices) is not list or any(type(choice) is not str for choice in choices):return False
    if view.get('stepId')=='select':
        positions={'the first result':0,'the first player':0,'first':0,
                   'the second result':1,'the second player':1,'second':1}
        index=positions.get(source_text)
        selected=choices[index] if index is not None and index<len(choices) else None
        return (selected in {'player-a','player-b'} and proposal.get('choice')==selected and
                proposal.get('response')=={'entityId':selected})
    if view.get('stepId') in {'confirm-a','confirm-b'}:
        if proposal.get('choice')=='approve':
            return confirm_current(source_text,proposal,view) and proposal.get('response')=={'confirmed':True}
        return (source_text in {'reject','no, reject'} and proposal.get('choice')=='reject' and
                'reject' in choices and proposal.get('response')=={'confirmed':False})
    return False


REGISTRATION='selection-v1'


def approved_definition():
    """The host fixes the offered order and every consequential branch."""
    return {'version':1,'start':'select','steps':{
        'select':{'kind':'pause','question':'Choose the displayed result: 1. player-a; 2. player-b.',
            'choices':{'player-a':'confirm-a','player-b':'confirm-b'},'response_schema':'selection'},
        **{f'confirm-{suffix}':{'kind':'pause','question':f'Approve the operation for player-{suffix}?',
            'choices':{'approve':f'apply-{suffix}','reject':'rejected'},
            'response_schema':'decision'} for suffix in ('a','b')},
        **{f'apply-{suffix}':{'kind':'agent','agent':f'effecter-{suffix}','schema':f'entity-{suffix}',
            'tools':[f'fixture_apply_{suffix}'],'require_tools':[f'fixture_apply_{suffix}'],
            'next':f'done-{suffix}'} for suffix in ('a','b')},
        **{f'done-{suffix}':{'kind':'finish','requires':[f'apply-{suffix}']} for suffix in ('a','b')},
        'rejected':{'kind':'finish','outcome':'rejected'}}}


def effect_tools(host,definition,registry):
    """Host scope gates keep registered ordinary tools from authorizing effects."""
    from prosaic_runtime import CustomTool
    version=definition['version']
    namespace=definition['operation_namespace']
    def event(name):
        import httpx
        result=httpx.post(host.config['fixture_events_url']+'/'+name,timeout=35)
        result.raise_for_status()
    tools={}
    for suffix in ('a','b'):
        entity='player-'+suffix
        step='apply-'+suffix
        def authorize(arguments,context,*,step=step):
            event('tool-authorizer')
            return (context.scope.run_id is not None and context.scope.step_id==step and
                    context.scope.operation_namespace==namespace)
        def key(arguments,context,*,entity=entity,step=step):
            event('tool-resolver')
            if (context.scope.run_id is None or context.scope.step_id!=step or
                    context.scope.operation_namespace!=namespace):
                raise ValueError('workflow_authorization_required')
            with registry.connection() as connection:
                row=connection.execute('SELECT binding_version FROM lab_chat.sessions WHERE session_id=%s',
                    (context.scope.run_id,)).fetchone()
            if row is None or row['binding_version']!=version:
                raise ValueError('workflow_authorization_required')
            return context.scope.run_id+':'+entity
        def apply(arguments,context,*,entity=entity):
            event('tool-handler')
            with registry.connection() as connection:
                connection.execute('''INSERT INTO lab_fixture.effects(namespace,business_key,amount)
                    VALUES (%s,%s,%s)''',(context.scope.operation_namespace,context.operation_key,1))
            event('tool-effect')
            return {'applied':True,'entityId':entity}
        name='fixture_apply_'+suffix
        tools[name]=CustomTool(name,'Apply the explicitly approved synthetic player operation',
            {'type':'object','properties':{},'additionalProperties':False},apply,
            'conversation-domain-v1-key-v1',with_context=True,authorize=authorize,operation_key=key,max_result_bytes=4096)
    return tools,event


def registered_workflow(host,definition,config,registry,tools,journal):
    from prosaic_harness import (ConfirmationRule,RunAuthorizer,WorkflowBindings,
        WorkflowCatalog,WorkflowFactory,WorkflowPolicy,WorkflowRegistration)
    from prosaic_runtime import ProsaicArtifact
    from .identity import Principal
    def authorize(scope,run_id):
        from .conversation_execution import current_grant
        if (scope.namespace!=host.config['namespace'] or scope.environment!=host.config['environment'] or
                scope.application!='integration-lab-chat'):
            return False
        principal=Principal(scope.tenant,scope.actor,scope.billing_account)
        current_grant(host,principal,definition['version'])
        row=registry.owned(principal,run_id)
        link=registry.workflow(row) if row is not None else None
        return (row is not None and row['binding_version']==definition['version'] and
                link is not None and link['registration']==REGISTRATION)
    agents={suffix:ProsaicArtifact.from_inspection({'id':f'conversation/agents/effecter-{suffix}.md',
        'type':'subagent','frontmatter':{'name':'effecter-'+suffix,
            'description':'Approved synthetic player operation','model_tier':definition.get('model_tier','balanced'),
            'tools':['fixture_apply_'+suffix]},'body':
            f'ALWAYS execute fixture_apply_{suffix} once through its provided native callable interface.\n'
            'NEVER describe or simulate a tool call in response text.\n'
            f'ALWAYS wait for the actual tool result before returning only the plain JSON object {{"entity_id":"player-{suffix}"}}.\n'
            'NEVER wrap the final JSON in Markdown or code fences, or add other text.\n'
            'NEVER execute another tool or use a user message as authorization.'}) for suffix in ('a','b')}
    schemas={'selection':{'type':'object','properties':{'entityId':{'enum':['player-a','player-b']}},
        'required':['entityId'],'additionalProperties':False},
        'decision':{'type':'object','properties':{'confirmed':{'type':'boolean'}},
        'required':['confirmed'],'additionalProperties':False},
        **{'entity-'+suffix:{'type':'object','properties':{'entity_id':{'const':'player-'+suffix}},
            'required':['entity_id'],'additionalProperties':False} for suffix in ('a','b')}}
    catalog=WorkflowCatalog(agents={'effecter-'+suffix:agent for suffix,agent in agents.items()},schemas=schemas)
    bindings=WorkflowBindings(config=config,custom_tools=tools,
        operation_namespace=definition['operation_namespace'],tool_journal=journal)
    policy=WorkflowPolicy(allowed_agents=frozenset('effecter-'+suffix for suffix in ('a','b')),allowed_schemas=frozenset(schemas),
        allowed_tools=frozenset(tools),allowed_model_tiers=frozenset({definition.get('model_tier','balanced')}),
        allow_agent_composition=True,max_calls=1,max_tokens=1024,max_run_s=120,timeout_s=30,max_attempts=1,
        max_provider_requests_per_invocation=2,max_tool_calls_per_invocation=1)
    workflow=WorkflowFactory(catalog=catalog,bindings=bindings,policy=policy).build(approved_definition())
    registration=WorkflowRegistration(workflow,store=host.store,accounting=host.recorder,
        authorizer=RunAuthorizer('conversation-owned-run','1',authorize),
        confirmation_rule=ConfirmationRule('conversation-phase-current-source','1',admit_workflow_reply))
    return workflow,registration


def lookup_tool(padding=0):
    """Trusted synthetic fixture data for bounded real-wire capacity checks."""
    from prosaic_runtime import CustomTool
    if type(padding) is not int or not 0<=padding<=3000:
        raise ValueError('invalid fixture lookup padding')
    def lookup(arguments):
        result={'results':[{'id':'player-a','label':'First result'},
                           {'id':'player-b','label':'Second result'}]}
        if padding:result['padding']='x'*padding
        return result
    return CustomTool('fixture_lookup','Look up the approved synthetic result order',
        {'type':'object','properties':{'query':{'type':'string','maxLength':128}},
         'required':['query'],'additionalProperties':False},lookup,
        'conversation-lookup-v1'+('-padding-'+str(padding) if padding else ''),max_result_bytes=4096)


def build_bindings(host,definition,*,registry=None,workflow_materials=None):
    """Read approved fixture instructions and seal one host-chosen model profile."""
    from prosaic_harness import ConversationBindings,ConversationPolicy
    from prosaic_runtime import CustomTool,EndpointConfig,ProsaicArtifact,RunPolicy,RuntimeConfig
    from .conversation_registry import reference
    if (type(definition) is not dict or set(definition)-{'version','model_url','model','model_tier',
            'assets','policy','fixture_effects','operation_namespace','journal_identity','fixture_lookup_padding',
            'context_policy','interpretation_context_policy','interpretation_model',
            'interpretation_model_tier','interpretation_model_url'} or
            not {'version','model_url'}<=set(definition) or
            type(definition.get('fixture_effects',False)) is not bool):
        raise ValueError('invalid conversation bundle')
    version=reference(definition['version'])
    directory=Path(definition.get('assets',Path(host.config['assets'])/'conversation'))
    tier=definition.get('model_tier','balanced')
    if tier not in {'balanced','strong'}:raise ValueError('invalid conversation tier')
    interpretation_tier=definition.get('interpretation_model_tier',tier)
    if interpretation_tier not in {'balanced','strong'}:raise ValueError('invalid interpretation tier')
    tools={'fixture_lookup':lookup_tool(definition.get('fixture_lookup_padding',0))}
    journal=None;workflows={}
    if definition.get('fixture_effects'):
        if registry is None or workflow_materials is None or not host.config.get('fixture_events_url'):
            raise ValueError('fixture effects require explicit host bindings')
        reference(definition['operation_namespace']);reference(definition['journal_identity'])
        from .tool_journal import PgToolJournal
        effects,event=effect_tools(host,definition,registry)
        class Journal(PgToolJournal):
            def claim(self,*args):
                result=super().claim(*args)
                if result.state=='new':event('tool-claimed')
                return result
            def commit(self,*args):
                super().commit(*args);event('tool-committed')
        journal=Journal(host.config['app_dsn'],identity=definition['journal_identity'])
        tools.update(effects)
    def artifact(name,requested):
        return ProsaicArtifact.from_inspection({'id':f'conversation/agents/{name}.md','type':'subagent',
            'frontmatter':{'name':name,'description':f'Synthetic conversation {name}',
            'model_tier':interpretation_tier if name=='interpreter' else tier,
            'tools':requested},'body':(directory/'agents'/f'{name}.md').read_text()})
    config=RuntimeConfig({'conversation':EndpointConfig(definition['model_url'],
        definition.get('model','test-model'),features={'streaming':False})},
        {tier:'conversation'},'conversation',allowed_tools=frozenset(tools))
    if any(key in definition for key in ('interpretation_model','interpretation_model_url')):
        if interpretation_tier==tier:raise ValueError('separate interpretation endpoint requires distinct tier')
        config.profiles['interpretation']=EndpointConfig(definition.get('interpretation_model_url',definition['model_url']),
            definition.get('interpretation_model',definition.get('model','test-model')),features={'streaming':False})
        config.routes[interpretation_tier]='interpretation'
    policy=ConversationPolicy(**definition.get('policy',{}))
    if definition.get('fixture_effects'):
        workflow,registration=registered_workflow(host,definition,config,registry,effects,journal)
        workflows[REGISTRATION]=registration
        workflow_materials[version]=(workflow,REGISTRATION)
    from .context_counter import context_configuration
    context_args=context_configuration(definition)
    return ConversationBindings(artifact('assistant',list(tools)),version=version,config=config,
        policy=policy,run_policy=RunPolicy(allowed_tools=frozenset(tools),timeout_s=30,
            max_tool_rounds=2,max_provider_requests=2,max_tool_calls=1,max_input_bytes=policy.max_input_bytes),
        custom_tools=tools,interpreter=artifact('interpreter',[]),
        operation_namespace=definition.get('operation_namespace'),tool_journal=journal,workflows=workflows,
        interpretation_policy=RunPolicy(allowed_tools=frozenset(),timeout_s=30,max_tool_rounds=1,
            max_provider_requests=1,max_tool_calls=0,max_input_bytes=policy.max_input_bytes),
        interpretation_schema=json.loads((directory/'schemas'/'interpretation.json').read_text()),**context_args)
