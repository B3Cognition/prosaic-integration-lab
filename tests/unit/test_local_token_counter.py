from copy import deepcopy
import hashlib
import json
import pytest


class Tokenizer:
    def __init__(self):self.seen=[]
    def apply_chat_template(self,messages,**kwargs):
        self.seen.append((deepcopy(messages),deepcopy(kwargs)))
        return json.dumps(dict(messages=messages,kwargs=kwargs),ensure_ascii=False)
    def encode(self,text,*,add_special_tokens):
        assert add_special_tokens is True
        return list(text.encode('utf-8'))


def request():
    return dict(model='synthetic',messages=[dict(role='user',content='Hello 世界 🧪')],max_tokens=512,stream=False)


def counter(tokenizer=None,variants=None):
    from lab_runner.quality.local_token_counter import LocalChatCounter
    return LocalChatCounter(tokenizer or Tokenizer(),model='synthetic',variants=variants or [
        dict(templateKwargs={},schemaDescriptions=False),dict(templateKwargs={'preserve_thinking':True},schemaDescriptions=True)])


def test_counts_maximum_declared_framing_and_owns_inputs():
    tokenizer=Tokenizer();c=counter(tokenizer);native=request();before=deepcopy(native)
    amount=c.count_tokens(native)
    assert len(tokenizer.seen)==2 and native==before
    assert amount==max(len(json.dumps(dict(messages=m,kwargs=k),ensure_ascii=False).encode()) for m,k in tokenizer.seen)


def test_tool_arguments_and_schema_variants_are_structural_not_numeric_padding():
    tokenizer=Tokenizer();native=request()
    native['tools']=[dict(type='function',function=dict(name='echo',description='Echo',parameters=dict(
        type='object',properties={'word':dict(type='string')},required=['word'],additionalProperties=False)))]
    native['messages'] += [dict(role='assistant',content=None,tool_calls=[dict(id='c',type='function',
        function=dict(name='echo',arguments='{"word":"é"}'))]),dict(role='tool',tool_call_id='c',content='é')]
    before=deepcopy(native);counter(tokenizer).count_tokens(native)
    assert native==before
    assert tokenizer.seen[0][0][1]['tool_calls'][0]['function']['arguments']=={'word':'é'}
    assert tokenizer.seen[0][0][1]['content']==''
    assert 'description' not in tokenizer.seen[0][1]['tools'][0]['function']['parameters']['properties']['word']
    assert tokenizer.seen[1][1]['tools'][0]['function']['parameters']['properties']['word']['description']==''


@pytest.mark.parametrize('modify',[
    lambda r:r.update(model='other'),lambda r:r.update(images=['secret']),
    lambda r:r.update(response_format={'type':'json_object'}),lambda r:r.update(chat_template_kwargs={'unexpected':True}),
    lambda r:r['messages'][0].update(content=[{'type':'image_url','image_url':{'url':'x'}}]),
    lambda r:r['messages'][0].update(role='developer'),lambda r:r['messages'][0].update(unknown='x'),
    lambda r:r.update(tools=[{'type':'browser'}]),lambda r:r.update(tool_choice='none'),
    lambda r:r['messages'].append(dict(role='system',content='mid-system')),
    lambda r:r['messages'].append(dict(role='user',content='consecutive')),
    lambda r:r['messages'].append(dict(role='assistant',content='answer',reasoning_content='Detailed reasoning. '*100)),
])
def test_unsupported_request_fails_without_rendering(modify):
    native=request();modify(native);tokenizer=Tokenizer()
    with pytest.raises(ValueError):counter(tokenizer).count_tokens(native)
    assert tokenizer.seen==[]


def test_bad_tool_argument_does_not_turn_into_empty_object():
    native=request();native['messages'].append(dict(role='assistant',content=None,tool_calls=[
        dict(id='c',type='function',function=dict(name='echo',arguments='[]'))]))
    with pytest.raises(ValueError):counter().count_tokens(native)


def test_template_failure_has_no_fallback_or_offset():
    class Broken(Tokenizer):
        def apply_chat_template(self,*args,**kw):raise RuntimeError('unsupported')
    with pytest.raises(ValueError):counter(Broken()).count_tokens(request())


def test_asset_manifest_rejects_drift_and_symlinks(tmp_path):
    from lab_runner.quality.local_token_counter import verify_assets
    p=tmp_path/'tokenizer.json';p.write_text('{}');manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest()}
    verify_assets(tmp_path,manifest)
    p.write_text('{"changed":true}')
    with pytest.raises(ValueError):verify_assets(tmp_path,manifest)
    p.unlink();p.symlink_to(tmp_path/'other')
    with pytest.raises(ValueError):verify_assets(tmp_path,manifest)


def test_reserved_template_kwargs_cannot_replace_owned_messages_or_tools():
    for key in ('messages','tools','tokenize','add_generation_prompt','continue_final_message'):
        with pytest.raises(ValueError):counter(variants=[dict(templateKwargs={key:True},schemaDescriptions=False)])


def test_unqualified_schema_vocabulary_is_closed():
    native=request();native['tools']=[dict(type='function',function=dict(name='echo',description='Echo',
        parameters={'$ref':'unqualified.json'}))]
    with pytest.raises(ValueError):counter().count_tokens(native)


def test_structured_enum_data_is_outside_schema_normalization_domain():
    native=request();native['tools']=[dict(type='function',function=dict(name='echo',description='Echo',
        parameters=dict(type='object',properties={'x':dict(enum=[{'properties':{'x':{'type':'string'}}}])})))]
    with pytest.raises(ValueError):counter().count_tokens(native)


def test_registration_binds_source_libraries_assets_and_framing(monkeypatch,tmp_path):
    import lab_runner.quality.local_token_counter as module
    monkeypatch.setattr(module,'load_local_counter',lambda *a,**kw:counter())
    assets={'tokenizer.json':'a'*64,'tokenizer_config.json':'b'*64}
    variants=[dict(templateKwargs={},schemaDescriptions=False)]
    a=module.register_local_counter(tmp_path,assets=assets,model='synthetic',variants=variants,capacity=8192)
    b=module.register_local_counter(tmp_path,assets=assets,model='synthetic',variants=[
        dict(templateKwargs={'preserve_thinking':True},schemaDescriptions=False)],capacity=8192)
    assert a.descriptor.counting_kind=='conservativeUpperBound'
    assert a.descriptor.tokenizer_assets_digest==b.descriptor.tokenizer_assets_digest
    assert a.descriptor.template_assets_digest!=b.descriptor.template_assets_digest
    assert a.descriptor.identity!=b.descriptor.identity
    assert a.descriptor.implementation_version.startswith('local-hf-v1-')
    assert 'qualification' in a.descriptor.guarantee


def test_qualified_native_constraints_and_conditional_suffix_are_bound():
    from lab_runner.quality.local_token_counter import LocalChatCounter
    tokenizer=Tokenizer();variants=[dict(templateKwargs={},schemaDescriptions=False),
        dict(templateKwargs={},schemaDescriptions=False,whenExtension='response_format',systemSuffix='Only valid JSON.')]
    c=LocalChatCounter(tokenizer,model='synthetic',variants=variants,
        extensions={'response_format':{'type':'json_object'},'structured_outputs':{'regex':'literal'}})
    native=request();c.count_tokens(native)
    assert len(tokenizer.seen)==1
    tokenizer.seen.clear();native['response_format']={'type':'json_object'};before=deepcopy(native)
    c.count_tokens(native)
    assert len(tokenizer.seen)==2 and native==before
    assert tokenizer.seen[1][0][0]==dict(role='system',content='Only valid JSON.')
    native['response_format']={'type':'json_schema'}
    with pytest.raises(ValueError):c.count_tokens(native)


def test_extension_declarations_cannot_admit_media_or_unconditional_hidden_input():
    from lab_runner.quality.local_token_counter import LocalChatCounter
    with pytest.raises(ValueError):LocalChatCounter(Tokenizer(),model='synthetic',
        variants=[dict(templateKwargs={},schemaDescriptions=False)],extensions={'images':[]})
    with pytest.raises(ValueError):LocalChatCounter(Tokenizer(),model='synthetic',
        variants=[dict(templateKwargs={},schemaDescriptions=False,systemSuffix='unbound')])


def test_trailing_tool_finalization_system_requires_explicit_system_framing():
    from lab_runner.quality.local_token_counter import LocalChatCounter
    tokenizer=Tokenizer();native=request()
    native['messages'] += [dict(role='assistant',content='lookup'),dict(role='tool',content='data',tool_call_id='c'),
                           dict(role='system',content='Now finalize.')]
    with pytest.raises(ValueError):counter().count_tokens(native)
    variants=[dict(templateKwargs={},schemaDescriptions=False,systemHandling=mode) for mode in ('verbatim','consolidate')]
    LocalChatCounter(tokenizer,model='synthetic',variants=variants).count_tokens(native)
    assert tokenizer.seen[0][0][-1]['role']=='system'
    assert tokenizer.seen[1][0][0]==dict(role='system',content='Now finalize.')
    assert [m['role'] for m in tokenizer.seen[1][0]]==['system','user','assistant','tool']
