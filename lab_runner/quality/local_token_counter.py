"""Local text/tool counters from frozen tokenizer assets and explicit framing.

No model IDs, serving-engine imports, learned offsets, remote code or weights.
Qualification belongs to the host and is specific to each serving contract.
"""
from copy import deepcopy
import hashlib
from importlib.metadata import version
from pathlib import Path
from .contracts import decode,encode,integer,sha,digest

LIBRARIES={'transformers':'5.17.0','tokenizers':'0.23.2','jinja2':'3.1.6'}
ASSET_NAMES={'tokenizer.json','tokenizer_config.json','chat_template.jinja','special_tokens_map.json',
             'added_tokens.json','config.json'}
REQUEST_KEYS={'model','messages','tools','tool_choice','max_tokens','stream','stream_options',
              'temperature','top_p','seed','stop','presence_penalty','frequency_penalty'}
MESSAGE_KEYS={'role','content','name','tool_calls','tool_call_id'}
SCHEMA_KEYS={'type','properties','items','enum','required','additionalProperties','minItems','maxItems','uniqueItems','description'}


def _admit_schema(value):
    if type(value) is bool:return
    if type(value) is not dict or set(value)-SCHEMA_KEYS:raise ValueError('unqualified schema vocabulary')
    for key,child in value.items():
        if key=='properties':
            if type(child) is not dict:raise ValueError('invalid schema properties')
            for schema in child.values():_admit_schema(schema)
        elif key in {'items','additionalProperties'}:_admit_schema(child)


def verify_assets(directory,manifest):
    directory=Path(directory)
    if (not directory.is_absolute() or any(p.is_symlink() for p in (directory,*directory.parents)) or
            type(manifest) is not dict or not manifest or set(manifest)-ASSET_NAMES):
        raise ValueError('invalid tokenizer assets')
    for name,expected in manifest.items():
        sha(expected);path=directory/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size>67108864:
            raise ValueError('invalid tokenizer asset')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('tokenizer asset drift')


def _descriptions(schema):
    """One explicit JSON Schema rendering variant; the original stays intact."""
    if type(schema) is not dict:return deepcopy(schema)
    result=deepcopy(schema)
    for key,value in result.items():
        if key=='properties' and type(value) is dict:
            result[key]={name:_schema(child) for name,child in value.items()}
        elif key in {'items','additionalProperties','contains','propertyNames','not','if','then','else'}:
            result[key]=_schema(value)
        elif key in {'oneOf','anyOf','allOf','prefixItems'} and type(value) is list:
            result[key]=[_schema(child) for child in value]
    return result


def _schema(value):
    result=_descriptions(value)
    if type(result) is dict:
        description=result.get('description','')
        if type(description) is not str:raise ValueError('non-text schema description')
        result['description']=description
    return result


class LocalChatCounter:
    def __init__(self,tokenizer,*,model,variants,asset_check=None):
        variants=decode(encode(variants,65536),65536)
        if type(model) is not str or not model or type(variants) is not list or not 1<=len(variants)<=8:
            raise ValueError('invalid counter framing')
        for variant in variants:
            if (type(variant) is not dict or set(variant)!={'templateKwargs','schemaDescriptions'} or
                    type(variant['schemaDescriptions']) is not bool or type(variant['templateKwargs']) is not dict or
                    set(variant['templateKwargs'])-{'enable_thinking','preserve_thinking','reasoning_effort'}):
                raise ValueError('invalid counter framing')
            for key,value in variant['templateKwargs'].items():
                if key=='reasoning_effort':
                    if type(value) is not str or len(value)>32:raise ValueError('invalid reasoning framing')
                elif type(value) is not bool:raise ValueError('invalid thinking framing')
        self._tokenizer,self._model,self._variants=tokenizer,model,variants
        self._asset_check=asset_check

    def count_tokens(self,request):
        try:
            native=decode(encode(request,196608),196608)
            if type(native) is not dict or set(native)-REQUEST_KEYS or native.get('model')!=self._model:
                raise ValueError('unsupported native request')
            messages=native.get('messages')
            if type(messages) is not list or not 1<=len(messages)<=256:raise ValueError('unsupported messages')
            previous=None
            for index,message in enumerate(messages):
                if (type(message) is not dict or set(message)-MESSAGE_KEYS or
                        message.get('role') not in {'system','user','assistant','tool'}):raise ValueError('unsupported message')
                role=message['role']
                if (role=='system' and index!=0) or (role==previous and role!='tool'):
                    raise ValueError('unqualified role consolidation')
                previous=role
                content=message.get('content')
                if content is None and message.get('role')=='assistant' and message.get('tool_calls'):message['content']=''
                elif type(content) is not str:raise ValueError('text-only counter')
                if 'tool_calls' in message:
                    if message['role']!='assistant' or type(message['tool_calls']) is not list:raise ValueError('invalid tool calls')
                    for call in message['tool_calls']:
                        if type(call) is not dict or set(call)-{'id','type','function'} or call.get('type','function')!='function':raise ValueError('unsupported call')
                        function=call.get('function')
                        if type(function) is not dict or set(function)!={'name','arguments'}:raise ValueError('invalid call function')
                        arguments=function['arguments']
                        if type(arguments) is str:arguments=decode(arguments.encode(),8192)
                        if type(arguments) is not dict:raise ValueError('tool arguments must be an object')
                        function['arguments']=arguments
                        call.pop('type',None)
            tools=native.get('tools')
            if tools is not None:
                if type(tools) is not list or not 1<=len(tools)<=64:raise ValueError('invalid tool list')
                for tool in tools:
                    if type(tool) is not dict or set(tool)!={'type','function'} or tool['type']!='function':raise ValueError('unsupported tool')
                    function=tool['function']
                    if (type(function) is not dict or set(function)!={'name','description','parameters'} or
                            type(function['name']) is not str or type(function['description']) is not str or
                            type(function['parameters']) is not dict):raise ValueError('unsupported tool definition')
                    _admit_schema(function['parameters'])
            choice=native.get('tool_choice','auto')
            if choice not in ('auto','required'):
                if (type(choice) is not dict or set(choice)!={'type','function'} or choice['type']!='function' or
                        type(choice['function']) is not dict or set(choice['function'])!={'name'} or
                        not any(t['function']['name']==choice['function']['name'] for t in tools or [])):
                    raise ValueError('unsupported tool choice')
            if self._asset_check is not None:self._asset_check()
            totals=[]
            for variant in self._variants:
                framed_tools=deepcopy(tools)
                if framed_tools and variant['schemaDescriptions']:
                    for tool in framed_tools:tool['function']['parameters']=_descriptions(tool['function']['parameters'])
                kwargs=dict(tokenize=False,add_generation_prompt=True,**variant['templateKwargs'])
                if framed_tools:kwargs['tools']=framed_tools
                rendered=self._tokenizer.apply_chat_template(deepcopy(messages),**kwargs)
                if type(rendered) is not str:raise ValueError('unsupported template output')
                totals.append(len(self._tokenizer.encode(rendered,add_special_tokens=True)))
            if self._asset_check is not None:self._asset_check()
            return integer(max(totals))
        except Exception:
            raise ValueError('local token counter cannot admit request') from None


def load_local_counter(directory,*,assets,model,variants):
    """Load tokenizer data only; caller constructs the public SDK registration."""
    verify_assets(directory,assets)
    if not {'tokenizer.json','tokenizer_config.json'}<=set(assets):raise ValueError('missing tokenizer assets')
    directory=Path(directory)
    if {p.name for p in directory.iterdir()}!=set(assets):raise ValueError('unmanifested tokenizer assets')
    if any(version(name)!=expected for name,expected in LIBRARIES.items()):raise ValueError('unqualified tokenizer libraries')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(str(directory),local_files_only=True,trust_remote_code=False)
    return LocalChatCounter(tokenizer,model=model,variants=variants,
        asset_check=lambda:verify_assets(directory,assets))


def register_local_counter(directory,*,assets,model,variants,capacity):
    """Bind public SDK provenance; serving qualification is a host responsibility."""
    from prosaic_runtime import TokenCounterDescriptor,TokenCounterRegistration
    counter=load_local_counter(directory,assets=assets,model=model,variants=variants)
    implementation=digest(dict(sourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),libraries=LIBRARIES))
    tokenizer_digest=digest(assets)
    framing_digest=digest(dict(assets=assets,variants=variants,implementation=implementation))
    descriptor=TokenCounterDescriptor(identity='local-hf-'+digest(dict(model=model,framing=framing_digest)),
        provider='openai-compatible',model=model,framing_revision='openai-chat-v1',
        context_capacity_tokens=integer(capacity,1),implementation_version='local-hf-v1-'+implementation,
        tokenizer_assets_digest=tokenizer_digest,template_assets_digest=framing_digest,
        counting_kind='conservativeUpperBound',guarantee='Maximum over explicit frozen HF text/tool framing variants. '
        'Requires host qualification against the serving profile and unchanged assets/settings. '
        'Media, historical reasoning, mid-system/consecutive user roles, unknown schema/request fields are rejected. '
        'No arbitrary-server or billing guarantee; no measured offsets or model weights.')
    return TokenCounterRegistration(descriptor,counter)
