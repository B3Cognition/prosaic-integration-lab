"""Host confirmation authority is independent of interpreted model data."""
import json
from pathlib import Path


def confirm_current(source_text,proposal,view):
    return (source_text in {'approve','yes, approve'} and type(proposal) is dict and
        type(view) is dict and proposal.get('ambiguous') is False and
        proposal.get('choice')=='approve' and proposal.get('interactionRef')==view.get('reference') and
        type(view.get('reference')) is str and 'approve' in view.get('choices',()))


def build_bindings(host,definition):
    """Read approved fixture instructions and seal one host-chosen model profile."""
    from prosaic_harness import ConversationBindings,ConversationPolicy
    from prosaic_runtime import CustomTool,EndpointConfig,ProsaicArtifact,RunPolicy,RuntimeConfig
    from .conversation_registry import reference
    if (type(definition) is not dict or set(definition)-{'version','model_url','model','model_tier',
            'assets','policy'} or not {'version','model_url'}<=set(definition)):
        raise ValueError('invalid conversation bundle')
    version=reference(definition['version'])
    directory=Path(definition.get('assets',Path(host.config['assets'])/'conversation'))
    tier=definition.get('model_tier','balanced')
    if tier not in {'balanced','strong'}:raise ValueError('invalid conversation tier')
    tools={'fixture_lookup':CustomTool('fixture_lookup','Look up the approved synthetic result order',
        {'type':'object','properties':{'query':{'type':'string','maxLength':128}},
         'required':['query'],'additionalProperties':False},
        lambda arguments:{'results':[{'id':'player-a','label':'First result'},
                                    {'id':'player-b','label':'Second result'}]},
        'conversation-lookup-v1',max_result_bytes=4096)}
    def artifact(name,requested):
        return ProsaicArtifact.from_inspection({'id':f'conversation/agents/{name}.md','type':'subagent',
            'frontmatter':{'name':name,'description':f'Synthetic conversation {name}',
                'model_tier':tier,'tools':requested},'body':(directory/'agents'/f'{name}.md').read_text()})
    config=RuntimeConfig({'conversation':EndpointConfig(definition['model_url'],
        definition.get('model','test-model'),features={'streaming':False})},
        {tier:'conversation'},'conversation',allowed_tools=frozenset(tools))
    policy=ConversationPolicy(**definition.get('policy',{}))
    return ConversationBindings(artifact('assistant',list(tools)),version=version,config=config,
        policy=policy,run_policy=RunPolicy(allowed_tools=frozenset(tools),timeout_s=30,
            max_tool_rounds=2,max_provider_requests=2,max_tool_calls=1,max_input_bytes=policy.max_input_bytes),
        custom_tools=tools,interpreter=artifact('interpreter',[]),
        interpretation_schema=json.loads((directory/'schemas'/'interpretation.json').read_text()))
