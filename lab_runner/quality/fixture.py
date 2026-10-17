"""Owned bounded scripted HTTP provider; never used by the live runner."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import re
import threading
from .suite import load_suite
from .execution import CASE_LIMITS


@contextmanager
def fixture_provider(*,scenario='correct'):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    if scenario not in {'correct','wrong','simulated','missing_usage','invalid_json','wrong_record','repair_once','permuted',
                        'public_check_once','correct_draft','stale_attempt','partial_critic_once','stubborn_review'}:
        raise ValueError('unknown quality fixture')
    class Provider:
        requests=0
        payloads=[]
        final_count=0
        case_limits=dict(CASE_LIMITS)
    provider=Provider();cases={c['caseId']:c for c in load_suite()['cases']}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            if self.path!='/v1/chat/completions':self.send_error(404);return
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=196608:self.send_error(413);return
            request=json.loads(self.rfile.read(size));provider.requests+=1
            if provider.requests>256:self.send_error(429);return
            provider.payloads.append(request)
            text=json.dumps(request['messages'])
            found=re.search(r'caseId\\?"\s*:\s*\\?"([a-z]+-0[12])',text)
            if not found:self.send_error(400);return
            case=cases[found.group(1)]
            critic='supplied flawed draft' in text or 'correctionTarget' in text
            tool_done=any(m['role']=='tool' for m in request['messages'])
            if not tool_done and scenario!='simulated':
                ids=case['requiredRecords'] if scenario!='wrong_record' else ['not-a-record']
                if scenario=='stale_attempt' and provider.final_count:ids=ids[:1]
                message={'role':'assistant','content':None,'tool_calls':[{'id':'lookup-1','type':'function',
                    'function':{'name':'lookup_records','arguments':json.dumps({'recordIds':ids})}}]}
                finish='tool_calls'
            else:
                provider.final_count+=1
                answer={'approved':False,'issues':['decision','facts','citations']} if critic else case['expected']
                if critic and (scenario=='correct_draft' or scenario=='public_check_once' and provider.final_count==1):
                    answer={'approved':True,'issues':[]}
                if critic and scenario=='partial_critic_once' and provider.final_count==1:
                    answer={'approved':False,'issues':['decision']}
                if critic and scenario=='stubborn_review':answer={'approved':True,'issues':[]}
                if not critic and scenario in {'public_check_once','stale_attempt'} and provider.final_count==1:
                    answer={**answer,'decision':'reject' if answer['decision']=='approve' else 'approve'}
                if scenario=='permuted' and not critic:
                    answer={**answer,'facts':list(reversed(answer['facts'])),'citations':list(reversed(answer['citations']))}
                if scenario=='wrong':answer={**case['expected'],'decision':'reject' if case['expected']['decision']=='approve' else 'approve'}
                content=json.dumps(answer)
                if scenario=='invalid_json' or scenario=='repair_once' and provider.final_count==1:content='not JSON'
                message={'role':'assistant','content':content};finish='stop'
            response={'id':'fixture-response','object':'chat.completion','model':request['model'],
                'choices':[{'index':0,'message':message,'finish_reason':finish}]}
            if scenario!='missing_usage':response['usage']={'prompt_tokens':100,'completion_tokens':50,'total_tokens':150}
            raw=json.dumps(response).encode();self.send_response(200)
            self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
            self.end_headers();self.wfile.write(raw)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    provider.config=RuntimeConfig({'fixture':EndpointConfig(
        'http://127.0.0.1:'+str(server.server_port)+'/v1','quality-fixture',max_tokens=512,
        features={'streaming':False})},{},'fixture')
    try:yield provider
    finally:server.shutdown();server.server_close();thread.join(timeout=2)
