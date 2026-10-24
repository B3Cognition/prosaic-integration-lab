"""Host-only scripted responses. This rehearses mechanics, never model quality."""

from contextlib import contextmanager
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading

from prosaic_runtime import EndpointConfig, RuntimeConfig

from .cases import load_cases
from .contracts import digest
from .host_keys import fixture_answer, load_keys


def _dialogue(case):
    import castle_sue as engine
    text=case['sources'][0]['text'];lines=text.splitlines()
    state=engine.initial_state(case['claim'],lens='euthyphro',max_turns=14);values=[]
    kinds=dict(DEFINE='definition',DISTINGUISH='distinction',CAUSE_OR_CRITERION='criterion',DIVIDE='case-split',
        COUNTEREXAMPLE='example',FOLLOW_CONSEQUENCE='consequence',TEST_OPPOSITE='consequence',REVISE='revision')
    results=dict(DEFINE='ESTABLISHED',DISTINGUISH='ESTABLISHED',CAUSE_OR_CRITERION='ESTABLISHED',DIVIDE='ESTABLISHED',
        COUNTEREXAMPLE='NOT_FOUND',FOLLOW_CONSEQUENCE='CONSISTENT',TEST_OPPOSITE='EXCLUDED',REVISE='REVISED')
    while not state['terminal']:
        op=state['operator']
        value=dict(answer='Scripted mechanics only; substantive interpretation is unproven.',verdict='SUPPORTED',
            answer_type=kinds[op],evidence_lines=[1],claim=case['claim'] if op in ('DEFINE','REVISE') else None,
            test_result=results[op],evidence=[dict(line=1,quote=lines[0])],
            premises=[dict(statement=lines[0],kind='stated',evidence_lines=[1])],witness=None,
            open_questions=[],addresses=[],revision_reason=None)
        state,error=engine.advance(state,value,lines)
        if error:raise ValueError('invalid synthetic SUE script')
        values.append(value)
    return values


@contextmanager
def provider(values,*,usage=True):
    """Capture every actual request/response; never read credentials or use a proxy."""
    rows=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            index=len(rows)
            value=values[min(index,len(values)-1)]
            response={'id':'requirements-scripted','model':request['model'],'choices':[{'index':0,
                'message':{'role':'assistant','content':value if type(value) is str else json.dumps(value)},'finish_reason':'stop'}]}
            if usage:response['usage']={'prompt_tokens':10,'completion_tokens':5,'total_tokens':15}
            rows.append({'request':request,'response':response,'status':200})
            data=json.dumps(response).encode();self.send_response(200)
            self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)))
            self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.02),daemon=True);thread.start()
    proxies={k:v for k,v in os.environ.items() if k.lower().endswith('_proxy')}
    try:
        for key in proxies:del os.environ[key]
        os.environ['no_proxy']='*'
        yield f'http://127.0.0.1:{server.server_port}/v1',rows
    finally:
        os.environ.pop('no_proxy',None);os.environ.update(proxies)
        server.shutdown();server.server_close();thread.join(5)
        if thread.is_alive():raise RuntimeError('fixture cleanup failed')


def run_fixture_sample(case_id,strategy,output,*,scenario='pass',limits=None):
    from .execution import execute_sample
    from .evidence import implementation, write_sample
    if Path(output).exists():raise FileExistsError('sample output already exists')
    implementation()  # Admit frozen source identity before opening a fixture or dispatching.
    if scenario not in {'pass','invalid-first','wrong-final','missing-usage'}:
        raise ValueError('unknown fixture scenario')
    case=load_cases()[case_id];answer=fixture_answer(case,load_keys()[case_id])
    if scenario=='wrong-final':answer.update(assessment='NO_KNOWN_ISSUES',issues=[])
    values=([{'feedback':'Evaluate the supplied source against the public issue definitions.'}] if strategy=='critic_author'
            else _dialogue(case) if strategy=='sue' else [])+[answer]
    if scenario=='invalid-first':values.insert(0,{'bad':True})
    with provider(values,usage=scenario!='missing-usage') as (url,rows):
        config=RuntimeConfig({'fixture':EndpointConfig(url,'requirements-fixture-v1',features={'streaming':False})},
            {},'fixture',allowed_tools=frozenset())
        evidence=execute_sample(case,strategy,config=config,output=output,limits=limits)
        evidence.update(origin='scripted_requirements_fixture',scenario=scenario,scriptSha256=digest(values),wire=deepcopy(rows))
    return write_sample(output,evidence),evidence
