"""Credential-free scripted provider, imported only by explicit fixture runs."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import re
import threading


@contextmanager
def fixture_provider(cases,scenario='correct'):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    if scenario not in {'correct','wrong','missing_usage','invalid_json','repair_fact_ids','repair_source','repair_absence'}:raise ValueError('invalid memory fixture')
    by_id={c['caseId']:c for c in cases}
    class Provider:
        requests=0
        payloads=[]
    p=Provider()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            if self.path!='/v1/chat/completions':self.send_error(404);return
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=196608:self.send_error(413);return
            request=json.loads(self.rfile.read(size));p.requests+=1
            if p.requests>512:self.send_error(429);return
            p.payloads.append(request)
            text=' '.join(m['content'] for m in request['messages'] if m['role']=='user' and isinstance(m.get('content'),str))
            found=re.search(r'"caseId"\s*:\s*"([a-zA-Z0-9_-]+)"',text)
            if found is None or found[1] not in by_id:self.send_error(400);return
            case=by_id[found[1]]
            arguments=json.loads(text.rsplit('## Arguments\n',1)[1])
            retry=bool(arguments.get('validation_feedback'))
            if not any(m['role']=='tool' for m in request['messages']):
                ids=case['requiredRecords']
                if scenario=='repair_source' and not retry:
                    ids=[k for k,v in case['records'].items() if v['authority']=='observer'][:4]
                message=dict(role='assistant',content=None,tool_calls=[dict(id='memory-lookup',type='function',
                    function=dict(name='lookup_records',arguments=json.dumps({'recordIds':ids})))])
                finish='tool_calls'
            else:
                answer=case['expected']
                if scenario=='wrong':answer={**answer,'decision':'reject' if answer['decision']=='approve' else 'approve'}
                if scenario=='repair_fact_ids' and not retry:answer={**answer,'facts':case['requiredRecords']}
                if scenario=='repair_absence' and not retry:answer={**answer,'decision':'reject'}
                message=dict(role='assistant',content='not JSON' if scenario=='invalid_json' else json.dumps(answer));finish='stop'
            response=dict(id='memory-fixture-response',object='chat.completion',model=request['model'],
                          choices=[dict(index=0,message=message,finish_reason=finish)])
            if scenario!='missing_usage':response['usage']=dict(prompt_tokens=100,completion_tokens=50,total_tokens=150)
            raw=json.dumps(response).encode();self.send_response(200)
            self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
            self.end_headers();self.wfile.write(raw)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    p.config=RuntimeConfig({name:EndpointConfig('http://127.0.0.1:'+str(server.server_port)+'/v1',
        'memory-'+name,max_tokens=512,features={'streaming':False}) for name in ('fixture-a','fixture-b')},{},'fixture-a')
    try:yield p
    finally:server.shutdown();server.server_close();thread.join(timeout=2)
