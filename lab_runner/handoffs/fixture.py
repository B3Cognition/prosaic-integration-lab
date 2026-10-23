"""Credential-free bounded scripted transport. Never used for live inference."""
from contextlib import contextmanager
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread
from .contracts import request_for, assignment, target, review_target

SCENARIOS=('correct','reject','missing','conflict','unread','wrong_worker','missed_flaw',
           'false_critic','wrong_assignment','wrong_binding','invalid_json','unknown_usage',
           'forged_evidence','repeat_tools','overrun')


def example_case(scenario='correct'):
    from lab_runner.quality.suite import load_suite
    case=deepcopy(load_suite()['cases'][0])
    case={k:case[k] for k in ('caseId','task','recordIndex','records')}
    if scenario=='reject':case['records']['metrics']['value']=70
    if scenario=='missing':
        case['records'].pop('incident')
        case['recordIndex']=[r for r in case['recordIndex'] if r['recordId']!='incident']
    if scenario=='conflict':
        row=case['records']['metrics']|dict(recordId='collision',value=10)
        case['records']['collision']=row
        case['recordIndex'].append({k:row[k] for k in ('recordId','factId','authority','revision')})
    return case


@contextmanager
def fixture_provider(case, *, scenario='correct', provider='openai'):
    from prosaic_runtime import EndpointConfig, RuntimeConfig
    if scenario not in SCENARIOS or provider not in ('openai','anthropic'):raise ValueError('invalid fixture')
    class State:
        requests=0
        deny=False
        payloads=[]
    state=State()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            state.requests+=1
            if state.deny or state.requests>4:self.send_error(429);return
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=262144:self.send_error(413);return
            native=json.loads(self.rfile.read(size));state.payloads.append(native)
            text=json.dumps(native)
            role='planner' if 'ROLE planner' in text else 'worker' if 'ROLE worker' in text else 'critic'
            request=request_for(case)
            ids=sorted(case['records']) if scenario!='unread' else ['metrics']
            clean=target(request,[case['records'][key] for key in ids])
            worker=deepcopy(clean)
            if scenario in ('wrong_worker','missed_flaw'):worker['answer']['decision']='reject'
            if scenario=='wrong_binding':worker['assignmentId']='0'*64
            if scenario=='forged_evidence':worker['evidence'][0]['value']=999
            value=assignment(request) if role=='planner' else worker if role=='worker' else review_target(clean,worker)
            if role=='planner' and scenario=='wrong_assignment':value['caseId']='foreign'
            if role=='critic' and scenario=='missed_flaw':value=dict(assignmentId=clean['assignmentId'],verdict='accept',issues=[])
            if role=='critic' and scenario=='false_critic':value=dict(assignmentId=clean['assignmentId'],verdict='escalate',issues=['decision'])
            content=json.dumps(value)
            if role=='worker' and scenario=='invalid_json':content='not JSON'
            done=any(m.get('role')=='tool' or isinstance(m.get('content'),list) and
                any(b.get('type')=='tool_result' for b in m['content'] if isinstance(b,dict)) for m in native['messages'])
            tool=role=='worker' and (not done or scenario=='repeat_tools')
            if provider=='anthropic':
                blocks=([dict(type='tool_use',id='read1',name='lookup_records',input=dict(recordIds=ids))]
                    if tool else [dict(type='text',text=content)])
                response=dict(id='synthetic',type='message',role='assistant',model=native['model'],
                    content=blocks,stop_reason='tool_use' if tool else 'end_turn',usage=dict(input_tokens=100,output_tokens=50))
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
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    state.config=RuntimeConfig({'fixture':EndpointConfig(f'http://127.0.0.1:{server.server_port}/v1',
        'typed-handoff-fixture',provider='anthropic' if provider=='anthropic' else 'openai-compatible',
        max_tokens=512,features={'streaming':False})},{},'fixture')
    try:yield state
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)
        assert not thread.is_alive()
