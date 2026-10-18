"""Independent scripted wire specification for the bounded consumer example."""
from contextlib import contextmanager
from copy import deepcopy
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
import json
from lab_runner.quality.contracts import digest
from .direct_fixture import example_case as _case,correct_worker,_strings,_validate_wire,_SHARED,_expected_schema

_DETAIL='''Correct artifacts.worker once using correction.diagnostics and currentEvidence.
You have one request and no tools. Do not request more records or another review.
Use only the supplied scoped records and public task; never infer an unread value.
Critic advice is optional, host-filtered and never grants authority.
Return the complete corrected artifact, not a patch or an explanation.
'''


def example_case(scenario='correct'):return _case('missing' if scenario=='missing' else 'correct')


def _clean(case,scenario):return correct_worker(case,'missing' if scenario=='missing' else 'unread' if scenario=='unread' else 'correct')


def _issues(clean,draft):
    out=[]
    if clean['assignmentId']!=draft['assignmentId']:out.append('binding')
    if clean['status']!=draft['status']:out.append('status')
    if clean['answer']['decision']!=draft['answer']['decision']:out.append('decision')
    if set(clean['answer']['facts'])!=set(draft['answer']['facts']):out.append('facts')
    pairs=lambda x:{(r['factId'],r['recordId']) for r in x}
    if pairs(clean['answer']['citations'])!=pairs(draft['answer']['citations']):out.append('citations')
    return out


@contextmanager
def fixture_provider(case,*,provider='openai',scenario='wrong_decision'):
    from prosaic_runtime import RuntimeConfig,EndpointConfig
    class State:
        def __init__(self):self.requests=0;self.errors=[];self.feedbacks=[];self.deny=False;self.roles=[]
    state=State();clean=_clean(case,scenario);ids=['metrics'] if scenario=='unread' else sorted(case['records'])
    rows=[case['records'][k] for k in ids]
    initial=deepcopy(clean)
    if scenario!='correct':initial['status']='ready';initial['answer']['decision']='reject' if clean['answer']['decision']=='approve' else 'approve'
    if scenario=='critic_partial':initial['answer']['citations']=[]
    paths=dict(binding='/assignmentId',status='/status',decision='/answer/decision',facts='/answer/facts',citations='/answer/citations')
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            state.requests+=1
            if state.deny or state.requests>16:self.send_error(429);return
            try:
                size=int(self.headers.get('Content-Length','0'));assert 0<size<=262144
                native=json.loads(self.rfile.read(size));prompt=next(s for s in _strings(native) if 'OUTPUT_CONTRACT_BEGIN\n' in s)
                corrector='ROLE corrector\n' in prompt
                if corrector:
                    role='corrector';args=next(s.split('## Arguments\n',1)[1] for s in _strings(native) if '## Arguments\n' in s)
                    args=json.JSONDecoder().raw_decode(args.lstrip())[0]
                    schema=json.loads(prompt.split('OUTPUT_CONTRACT_BEGIN\n',1)[1].split('\nOUTPUT_CONTRACT_END',1)[0])
                    assert prompt.split('OUTPUT_CONTRACT_BEGIN\n',1)[0].strip()==('ROLE corrector\n'+_SHARED+_DETAIL).strip()
                    assert schema==_expected_schema('worker',clean['assignmentId'])
                    assert set(args['artifacts'])=={'worker'} and args['validation_feedback']==[]
                    packet=args['correction'];state.feedbacks.append(deepcopy(packet))
                    assert set(packet)=={'version','assignmentId','draftDigest','evidenceDigest','maxCorrections','diagnostics','criticAdvice'}
                    assert packet['assignmentId']==clean['assignmentId'] and packet['maxCorrections']==1
                    assert packet['draftDigest']==digest(initial) and packet['evidenceDigest']==digest(args['currentEvidence'])
                    assert {d['field'] for d in packet['diagnostics']}=={paths[k] for k in _issues(clean,initial)}
                    assert all(set(d)=={'code','field','evidenceRefs'} and d['code']=='field_mismatch' and d['evidenceRefs'] for d in packet['diagnostics'])
                    advice=packet['criticAdvice']
                    if advice is not None:
                        wanted=['decision'] if scenario=='critic_partial' else [] if scenario=='critic_false' else _issues(clean,initial)
                        assert advice==dict(supportedIssues=sorted(wanted))
                else:role,schema,args=_validate_wire(native,case)
                if role!='worker':assert args['currentEvidence']==dict(assignmentId=clean['assignmentId'],origin='workerLookup',records=rows)
                state.roles.append(role)
                done=any(m.get('role')=='tool' or isinstance(m.get('content'),list) and any(b.get('type')=='tool_result'
                    for b in m['content'] if isinstance(b,dict)) for m in native['messages'])
                tool=role=='worker' and not done or role=='corrector' and scenario=='corrector_tools'
                value=deepcopy(initial if role=='worker' else clean)
                if role=='critic':
                    issues=['decision'] if scenario=='critic_partial' else ['status'] if scenario=='critic_false' else _issues(clean,initial)
                    value=dict(assignmentId=clean['assignmentId'],verdict='escalate',issues=issues)
                if role=='corrector' and scenario=='ignore_feedback':value=deepcopy(initial)
                if role=='corrector' and scenario=='regress':value['answer']['facts']=[];value['answer']['citations']=[]
                text='{' if (role=='worker' and scenario=='invalid_worker' or role=='corrector' and scenario=='invalid_correction'
                    or role=='critic' and scenario=='invalid_critic') else json.dumps(value)
                if provider=='anthropic':
                    blocks=[dict(type='tool_use',id='read1',name='lookup_records',input=dict(recordIds=ids))] if tool else [dict(type='text',text=text)]
                    response=dict(id='synthetic',type='message',role='assistant',model=native['model'],content=blocks,
                        stop_reason='tool_use' if tool else 'end_turn',usage=dict(input_tokens=100,output_tokens=50))
                else:
                    message=dict(role='assistant',content=None,tool_calls=[dict(id='read1',type='function',
                        function=dict(name='lookup_records',arguments=json.dumps(dict(recordIds=ids))))]) if tool else dict(role='assistant',content=text)
                    response=dict(id='synthetic',model=native['model'],choices=[dict(index=0,message=message,
                        finish_reason='tool_calls' if tool else 'stop')],usage=dict(prompt_tokens=100,completion_tokens=50,total_tokens=150))
                if scenario=='unknown_usage' and role=='worker' and done:response.pop('usage')
                if scenario=='critic_unknown' and role=='critic':response.pop('usage')
                if scenario=='final_breach' and role=='corrector':
                    response['usage']=dict(input_tokens=101,output_tokens=50) if provider=='anthropic' else dict(prompt_tokens=101,completion_tokens=50,total_tokens=151)
                if role=='worker' and not done and scenario in ('overrun','input_breach','output_breach'):
                    inp,out=(100,9000) if scenario=='overrun' else (101,50) if scenario=='input_breach' else (1,513)
                    response['usage']=dict(input_tokens=inp,output_tokens=out) if provider=='anthropic' else dict(prompt_tokens=inp,completion_tokens=out,total_tokens=inp+out)
                raw=json.dumps(response).encode();self.send_response(200);self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
            except Exception as error:
                state.errors.append(type(error).__name__+':'+str(error)[:240]);self.send_error(400)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    state.config=RuntimeConfig({'fixture':EndpointConfig(f'http://127.0.0.1:{server.server_port}/v1','bounded-correction-fixture',
        provider='anthropic' if provider=='anthropic' else 'openai-compatible',max_tokens=512,features={'streaming':False})},{},'fixture')
    try:yield state
    finally:server.shutdown();server.server_close();thread.join(timeout=3);assert not thread.is_alive()
