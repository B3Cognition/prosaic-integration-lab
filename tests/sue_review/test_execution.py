from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import threading
import uuid

import pytest
from prosaic_harness import FileRunStore
from prosaic_runtime import EndpointConfig, RuntimeConfig
from prosaic_integration_lab.identity import Principal

SOURCE = 'Only administrators may export data.\r\nConsent must be current.\r\n'
CLAIM = 'Administrators export with current consent.'
TYPES = dict(DEFINE='definition',DISTINGUISH='distinction',CAUSE_OR_CRITERION='criterion',DIVIDE='case-split',COUNTEREXAMPLE='example',FOLLOW_CONSEQUENCE='consequence',TEST_OPPOSITE='consequence',REVISE='revision')
RESULTS = dict(DEFINE='ESTABLISHED',DISTINGUISH='ESTABLISHED',CAUSE_OR_CRITERION='ESTABLISHED',DIVIDE='ESTABLISHED',COUNTEREXAMPLE='NOT_FOUND',FOLLOW_CONSEQUENCE='CONSISTENT',TEST_OPPOSITE='EXCLUDED',REVISE='REVISED')


def answer(op):
    return dict(answer='An attributed interpretation requiring review.',verdict='SUPPORTED',answer_type=TYPES[op],evidence_lines=[1],claim=CLAIM if op in ('DEFINE','REVISE') else None,test_result=RESULTS[op],evidence=[{'line':1,'quote':SOURCE.splitlines()[0]}],premises=[{'statement':SOURCE.splitlines()[0],'kind':'stated','evidence_lines':[1]}],witness=None,open_questions=[],addresses=[],revision_reason=None)


def script(lens='euthyphro',max_turns=14):
    import castle_sue as engine
    state = engine.initial_state(CLAIM,lens=lens,max_turns=max_turns)
    values=[]
    while not state['terminal']:
        value = answer(state['operator'])
        values.append(value)
        state,error = engine.advance(state,value,SOURCE.splitlines())
        assert error is None
    return values,state


@contextmanager
def fixture(values, usage=True):
    requests=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            value=values[min(len(requests)-1,len(values)-1)]
            result={'id':'sue-fixture','model':'sue-fixture','choices':[{'index':0,'message':{'role':'assistant','content':value if type(value) is str else json.dumps(value)},'finish_reason':'stop'}]}
            if usage: result['usage']={'prompt_tokens':10,'completion_tokens':5,'total_tokens':15}
            data=json.dumps(result).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try: yield f'http://127.0.0.1:{server.server_port}/v1',requests
    finally:
        server.shutdown();server.server_close();thread.join(5)
        assert not thread.is_alive()


def session(store,url,settings=None,owner=None,**kw):
    assert importlib.util.find_spec('prosaic_integration_lab.sue_review.session') is not None,'SUE session is not implemented'
    from prosaic_integration_lab.sue_review.session import SueReviewSession
    config=RuntimeConfig({'fixture':EndpointConfig(url,'sue-fixture',features={'streaming':False})},{},'fixture',allowed_tools=frozenset())
    return SueReviewSession(settings={'enabled':True,**(settings or {})},store=store,config=config,principal=owner or Principal('tenant','alice','payer'),namespace='sue-test',**kw)


@pytest.mark.parametrize('lens',['euthyphro','meno','parmenides','cratylus','theaetetus','sophist','gorgias','republic','philebus'])
def test_real_wire_review_preserves_engine_state_and_zero_call_start(tmp_path,lens):
    values,expected=script(lens)
    with fixture(values) as (url,requests), FileRunStore(tmp_path/'runs',namespace='sue-test') as store:
        flow=session(store,url)
        run=uuid.uuid4().hex
        waiting=flow.start(run,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}],lens=lens)
        assert waiting['status']=='waiting' and requests==[]
        result=flow.resume(run,expected_revision=waiting['revision'],choice='continue')
        assert result['status']=='completed' and result['terminal']==expected['terminal']
        report=flow.report(run)
        assert report['coverage']==__import__('castle_sue').coverage(expected)
        assert report['acceptedTurns']==len(values) and len(requests)==len(values)
        assert all(not r.get('tools') for r in requests)
        assert report['advisory'] is True
        assert flow.resume(run,expected_revision=result['revision'])==result
        assert len(requests)==len(values)


def test_invalid_answer_retry_keeps_rejected_receipt(tmp_path):
    values,state=script(max_turns=1)
    with fixture(['{"bad":true}',*values]) as (url,requests), FileRunStore(tmp_path/'runs',namespace='sue-test') as store:
        flow=session(store,url)
        run=uuid.uuid4().hex
        waiting=flow.start(run,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}],max_turns=1)
        result=flow.resume(run,expected_revision=waiting['revision'],choice='continue')
        assert result['terminal']=='BOUNDED_STOP' and len(requests)==2
        saved=store.load_run(run).state
        assert len(saved['invocations'])==2 and len(saved['outputs'])==1
        assert flow.report(run)['acceptedTurns']==1


def test_identity_idempotency_disabled_resume_and_frozen_sources(tmp_path):
    values,_=script(max_turns=1)
    sources=[{'sourceId':'spec','text':SOURCE,'revision':'r1'}]
    with fixture(values) as (url,requests), FileRunStore(tmp_path/'runs',namespace='sue-test') as store:
        flow=session(store,url)
        run=uuid.uuid4().hex
        waiting=flow.start(run,seed=CLAIM,sources=sources,max_turns=1)
        assert flow.start(run,seed=CLAIM,sources=sources,max_turns=1)==waiting
        sources[0]['revision']='r2'
        with pytest.raises(ValueError,match='conflict'):flow.start(run,seed=CLAIM,sources=sources,max_turns=1)
        foreign=session(store,url,owner=Principal('tenant','bob','payer'))
        with pytest.raises(PermissionError):foreign.status(run)
        disabled=session(store,url,settings={'enabled':False})
        assert disabled.status(run)==waiting
        with pytest.raises(ValueError,match='disabled'):disabled.resume(run,expected_revision=waiting['revision'],choice='continue')
        assert requests==[]
        result=flow.resume(run,expected_revision=waiting['revision'],choice='reject')
        assert result['status']=='rejected' and requests==[]
