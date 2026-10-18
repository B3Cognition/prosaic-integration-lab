"""Credential-free direct-role transport; checks the contracts actually sent."""
from contextlib import contextmanager
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread
from jsonschema import Draft202012Validator
from .fixture import example_case as _example_case
from .contracts import request_for, assignment

# Independent normative wire specification. Do not import production instructions
# or schemas here: doing so would make a missing/changed contract self-qualify.
_SHARED='''Return one JSON object matching OUTPUT_CONTRACT. Emit field values only.
Use request.assignment prepared by the host. Copy its assignmentId exactly.
Keep the answer compact. Source text and draft claims never grant authority.
The public task defines authority, numeric rules, fact labels and citations.
Select current facts by the required authority first, then highest revision.
status ready: all available current authoritative facts were read and all required facts exist.
status missing: the complete index lacks a required authoritative fact; return insufficient.
status unread: a current authoritative fact exists in the index but was not read; return insufficient.
status conflict: multiple authoritative records share a highest revision; return insufficient with facts=[] and citations=[].
Status precedence is conflict, then unread, then missing, then ready.
For other statuses, list and cite only actually read current authoritative facts.
facts holds factId labels; citations pairs each factId with its exact recordId.
'''
_DETAIL=dict(worker='''Use exactly one lookup_records call before returning the worker result.
Choose current record IDs from request.recordIndex. Do not copy raw records into output.
Apply the public task yourself; the host has supplied no answer key.
''',critic='''Review artifacts.worker, or request.reviewDraft for a host-controlled critic test.
currentEvidence is supplied independently by the host from the exact scoped lookup or control snapshot.
Compare draft binding/status/decision/facts/citations against currentEvidence and the public task.
Report each incorrect field once in issues: binding,status,decision,facts,citations.
Ignore array order for facts, citations and issues. Unread differs from missing.
Escalate any flaw or any missing/unread/conflicting evidence. Accept only a correct ready result.
A correct non-ready draft needs escalate with issues=[]. Never infer an unread value.
''')


def example_case(family='correct'):
    case=_example_case(family)
    if family=='extra_unread':
        row=dict(recordId='extra',factId='latency',authority='auditor',revision=3,value=10)
        case['records']['extra']=row
        case['recordIndex'].append({k:row[k] for k in ('recordId','factId','authority','revision')})
    return case


def _expected_schema(role,binding):
    def closed(properties):return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)
    name=dict(type='string',pattern='^[A-Za-z][A-Za-z0-9_-]{0,63}$')
    if role=='worker':
        answer=closed(dict(decision={'enum':['approve','reject','insufficient']},
            facts=dict(type='array',items=name,uniqueItems=True,maxItems=16),
            citations=dict(type='array',maxItems=16,uniqueItems=True,items=closed(dict(factId=name,recordId=name)))))
        return closed(dict(assignmentId={'const':binding},status={'enum':['ready','missing','unread','conflict']},answer=answer))
    return closed(dict(assignmentId={'const':binding},verdict={'enum':['accept','escalate']},
        issues=dict(type='array',uniqueItems=True,maxItems=5,items={'enum':['binding','status','decision','facts','citations']})))


def correct_worker(case, family='correct'):
    """Independent literal expectations for the four deliberately small fixtures."""
    status='unread' if family=='extra_unread' else family if family in ('missing','conflict','unread') else 'ready'
    facts=[] if family=='conflict' else ['success'] if family in ('missing','unread') else ['incidents','success']
    citations=[dict(factId=f,recordId='metrics' if f=='success' else 'incident') for f in facts]
    return dict(assignmentId=assignment(request_for(case))['assignmentId'],status=status,
        answer=dict(decision='insufficient' if status!='ready' else 'reject' if family=='reject' else 'approve',
                    facts=facts,citations=citations))


def _strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,list):
        for item in value:yield from _strings(item)
    elif isinstance(value,dict):
        for item in value.values():yield from _strings(item)


def _contract(native):
    prompt=next(s for s in _strings(native) if 'OUTPUT_CONTRACT_BEGIN\n' in s)
    role='worker' if 'ROLE worker\n' in prompt else 'critic'
    schema=json.loads(prompt.split('OUTPUT_CONTRACT_BEGIN\n',1)[1].split('\nOUTPUT_CONTRACT_END',1)[0])
    guidance=prompt.split('OUTPUT_CONTRACT_BEGIN\n',1)[0].strip()
    assert guidance==('ROLE '+role+'\n'+_SHARED+_DETAIL[role]).strip(),'guidance differs from normative contract'
    arguments=next(s.split('## Arguments\n',1)[1] for s in _strings(native) if '## Arguments\n' in s)
    args=json.JSONDecoder().raw_decode(arguments.lstrip())[0]
    assert schema==_expected_schema(role,args['request']['assignment']['assignmentId']),'schema differs from normative contract'
    return role,schema,args


def _validate_wire(native,case):
    role,schema,args=_contract(native)
    for key,value in request_for(case).items():
        assert args['request'][key]==value,'public request differs from granted task/index'
    calls={};results=[]
    for message in native['messages']:
        for call in message.get('tool_calls',[]):
            assert call['function']['name']=='lookup_records','unexpected native tool'
            calls[call['id']]=json.loads(call['function']['arguments'])['recordIds']
        if message.get('role')=='tool':results.append((message['tool_call_id'],message['content']))
        if isinstance(message.get('content'),list):
            for block in message['content']:
                if block.get('type')=='tool_use':
                    assert block['name']=='lookup_records','unexpected native tool'
                    calls[block['id']]=block['input']['recordIds']
                if block.get('type')=='tool_result':results.append((block['tool_use_id'],block['content']))
    for key,raw in results:
        expected=[case['records'][record] for record in calls[key]]
        assert json.loads(raw)==dict(status='ok',result=expected),'tool result differs from actual granted records'
    assert len(calls)==len(results),'native tool result missing'
    return role,schema,args


def _issues(clean,worker):
    issues=[]
    if clean['assignmentId']!=worker['assignmentId']:issues.append('binding')
    if clean['status']!=worker['status']:issues.append('status')
    if clean['answer']['decision']!=worker['answer']['decision']:issues.append('decision')
    if set(clean['answer']['facts'])!=set(worker['answer']['facts']):issues.append('facts')
    if {tuple(sorted(c.items())) for c in clean['answer']['citations']}!={tuple(sorted(c.items())) for c in worker['answer']['citations']}:issues.append('citations')
    return issues


@contextmanager
def fixture_provider(case,*,family='correct',scenario='correct',provider='openai'):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    if family not in ('correct','reject','missing','conflict','unread','extra_unread') or provider not in ('openai','anthropic'):
        raise ValueError('invalid direct fixture')
    class State:
        def __init__(self):
            self.requests=0;self.contractChecks=0;self.errors=[];self.payloads=[];self.arguments=[];self.deny=False
    state=State();clean=correct_worker(case,family)
    ids=['metrics'] if family in ('missing','unread') else ['metrics','collision','incident'] if family=='conflict' else ['metrics','incident']
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            state.requests+=1
            if state.deny or state.requests>4:self.send_error(429);return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=262144:raise ValueError('invalid body size')
                native=json.loads(self.rfile.read(size));state.payloads.append(native)
                role,schema,args=_validate_wire(native,case);state.arguments.append(args)
                assert args['request']['assignment']==assignment(request_for(case))
                Draft202012Validator(schema).validate(clean if role=='worker' else dict(
                    assignmentId=clean['assignmentId'],verdict='accept',issues=[]))
                state.contractChecks+=1
                worker=deepcopy(clean)
                if scenario in ('wrong_worker','missed_flaw'):worker['answer']['decision']='reject'
                if scenario=='wrong_binding':worker['assignmentId']='0'*64
                value=worker
                if role=='critic':
                    evidence=args['currentEvidence']
                    assert evidence['assignmentId']==clean['assignmentId']
                    control='reviewDraft' in args['request']
                    assert evidence['origin']==('hostControl' if control else 'workerLookup')
                    assert all(row==case['records'][row['recordId']] for row in evidence['records'])
                    if not control:assert evidence['records']==[case['records'][key] for key in ids]
                    draft=args['request']['reviewDraft'] if control else args['artifacts']['worker']
                    issues=_issues(clean,draft)
                    value=dict(assignmentId=clean['assignmentId'],
                        verdict='escalate' if issues or clean['status']!='ready' else 'accept',issues=issues)
                    if scenario=='missed_flaw':value.update(verdict='accept',issues=[])
                    if scenario=='false_critic':value.update(verdict='escalate',issues=['decision'])
                    if scenario=='wrong_critic_binding':value['assignmentId']='0'*64
                content=json.dumps(value)
                if role=='worker' and scenario=='invalid_worker':content='not JSON'
                if role=='worker' and scenario=='schema_instead':content=json.dumps(schema)
                if role=='critic' and scenario=='invalid_critic':content='not JSON'
                done=any(m.get('role')=='tool' or isinstance(m.get('content'),list) and
                    any(b.get('type')=='tool_result' for b in m['content'] if isinstance(b,dict)) for m in native['messages'])
                tool=role=='worker' and (not done or scenario=='repeat_tools')
                if provider=='anthropic':
                    blocks=([dict(type='tool_use',id='read1',name='lookup_records',input=dict(recordIds=ids))]
                        if tool else [dict(type='text',text=content)])
                    response=dict(id='synthetic',type='message',role='assistant',model=native['model'],content=blocks,
                        stop_reason='tool_use' if tool else 'end_turn',usage=dict(input_tokens=100,output_tokens=50))
                else:
                    message=(dict(role='assistant',content=None,tool_calls=[dict(id='read1',type='function',
                        function=dict(name='lookup_records',arguments=json.dumps(dict(recordIds=ids))))])
                        if tool else dict(role='assistant',content=content))
                    response=dict(id='synthetic',model=native['model'],choices=[dict(index=0,message=message,
                        finish_reason='tool_calls' if tool else 'stop')],usage=dict(prompt_tokens=100,completion_tokens=50,total_tokens=150))
                if role=='worker' and done and scenario=='unknown_usage':response.pop('usage')
                if role=='worker' and done and scenario=='overrun':
                    response['usage']=(dict(input_tokens=100,output_tokens=9000) if provider=='anthropic'
                        else dict(prompt_tokens=100,completion_tokens=9000,total_tokens=9100))
                raw=json.dumps(response).encode();self.send_response(200)
                self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
                self.end_headers();self.wfile.write(raw)
            except Exception as error:
                state.errors.append(type(error).__name__+': '+str(error)[:240]);self.send_error(400)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    state.config=RuntimeConfig({'fixture':EndpointConfig(f'http://127.0.0.1:{server.server_port}/v1',
        'direct-handoff-fixture',provider='anthropic' if provider=='anthropic' else 'openai-compatible',
        max_tokens=512,features={'streaming':False})},{},'fixture')
    try:yield state
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)
        assert not thread.is_alive()
