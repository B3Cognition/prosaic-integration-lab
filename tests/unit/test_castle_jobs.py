"""Optional jobs use installed SDKs and a credential-free loopback fixture."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import uuid

import pytest

from prosaic_integration_lab.castle_jobs import CastleJobError, CastleJobSession, JobSettings
from prosaic_integration_lab.castle_jobs.contracts import freeze_candidates, interpret
from prosaic_integration_lab.identity import Principal


def candidates():
    return [{'sourceId': f's{i}', 'text': f'Original evidence {i}. 🙂\r\n',
             'revision': 'r1', 'reference': f'fixture://s{i}'} for i in range(4)]


def request(kind='judge'):
    return {'kind': kind, 'candidates': candidates(), 'query': 'evidence', 'top_n': 2}


@contextmanager
def responder(raw, *, usage=True, status=200):
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            body = {'id': 'castle-fixture', 'model': 'castle-fixture', 'choices': [
                {'index': 0, 'message': {'role': 'assistant', 'content': raw}, 'finish_reason': 'stop'}]}
            if usage:
                body['usage'] = {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15}
            encoded = json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1', calls
    finally:
        server.shutdown()
        server.server_close()
        worker.join(5)
        assert not worker.is_alive()


def session(tmp_path, url, *, settings=None, store=None, principal=None, namespace='jobs'):
    from prosaic_harness import FileRunStore
    from prosaic_runtime import EndpointConfig, RuntimeConfig
    from prosaic_runtime.accounting import MemoryRecorder
    config = RuntimeConfig({'fixture': EndpointConfig(url, 'castle-fixture', features={'streaming': False})},
                           {}, 'fixture', allowed_tools=frozenset())
    recorder = MemoryRecorder(namespace=namespace)
    return CastleJobSession(settings or {'enabled': True}, store or FileRunStore(tmp_path/'runs', namespace=namespace),
        config, principal or Principal('tenant', 'alice', 'payer'), namespace, accounting=recorder), recorder


@pytest.mark.parametrize('raw', [
    '{"ranked_indices":[0]}', '{"ranked_indices":[0,0]}', '{"ranked_indices":[0,2]}',
    '{"ranked_indices":[true,false]}', '{"ranked_indices":[0.0,1]}',
    '{"ranked_indices":[1,0,2]}', '{"ranked_indices":[-1,0]}',
    '{"ranked_indices":[1,0],"other":1}', '{"ranked_indices":[1,0],"ranked_indices":[0,1]}',
    '{"ranked_indices":[NaN,1]}', 'not JSON',
])
def test_invalid_complete_permutations_fallback_preserves_all_candidates(raw):
    frozen = freeze_candidates(candidates())
    result = interpret({'kind':'judge', 'candidates': frozen, 'topN':2}, raw)
    assert result['rankedSourceIds'] == ['s0', 's1', 's2', 's3']
    assert result['audit']['fallback'] is True and result['audit']['reason']


def test_full_permutation_changes_only_top_n_and_preserves_tail():
    result = interpret({'kind':'judge','candidates':freeze_candidates(candidates()),'topN':2},
                       '{"ranked_indices":[1,0]}')
    assert result['rankedSourceIds'] == ['s1','s0','s2','s3']
    assert result['audit']['fallback'] is False


def test_disabled_zero_imports_and_model_calls():
    import os
    from pathlib import Path
    import subprocess
    import sys
    code = '''
import importlib.abc,sys
class Deny(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'cognitive_castle','castle_sue','prosaic_runtime','prosaic_harness'}:raise AssertionError(name)
sys.meta_path.insert(0,Deny())
from prosaic_integration_lab.castle_jobs import CastleJobSession,CastleJobError
from prosaic_integration_lab.identity import Principal
s=CastleJobSession(None,None,None,Principal('tenant','alice','payer'),'jobs')
try:s.start('a'*32,kind='judge',candidates=[])
except CastleJobError as e:assert str(e)=='castle_jobs_disabled'
else:raise AssertionError('disabled admitted')
'''
    result = subprocess.run([sys.executable,'-c',code],env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[2]/'src')},capture_output=True,text=True)
    assert result.returncode == 0, result.stderr


def test_start_freezes_exact_source_owner_and_usage_resume_never_redispatches(tmp_path):
    from prosaic_harness import RevisionConflict
    with responder('{"ranked_indices":[1,0]}') as (url, calls):
        flow, recorder = session(tmp_path, url)
        run = uuid.uuid4().hex
        data = request()
        waiting = flow.start(run, **data)
        assert waiting['status'] == 'waiting' and calls == []
        data['candidates'][0]['text'] = 'Changed after admission'
        with pytest.raises(CastleJobError, match='job_request_conflict'):
            flow.start(run, **data)
        with pytest.raises(RevisionConflict):
            flow.resume(run, expected_revision='0'*64, choice='continue')
        wrong, _ = session(tmp_path,url,principal=Principal('tenant','bob','payer'))
        with pytest.raises(PermissionError):
            wrong.resume(run,expected_revision=waiting['revision'],choice='continue')
        assert calls == []
        done = flow.resume(run, expected_revision=waiting['revision'],choice='continue')
        assert done['status'] == 'completed' and len(calls) == 1
        assert 'Changed after admission' not in json.dumps(calls)
        report = flow.report(run)
        assert report['rankedSourceIds'] == ['s1','s0','s2','s3']
        assert report['advisory'] is True and report['usageComplete'] is True and report['reportedTokens'] == 15
        assert flow.store.load_run(run).state['inputs']['candidates'][0]['text'] == candidates()[0]['text']
        intent = next(iter(recorder.intents.values()))
        assert {k:intent['context'][k] for k in ('tenant_id','actor_id','billing_account_id','project_id','application_id')} == {
            'tenant_id':'tenant','actor_id':'alice','billing_account_id':'payer','project_id':'jobs','application_id':'integration-lab-castle-jobs'}
        flow.resume(run,expected_revision=done['revision'])
        with pytest.raises(RevisionConflict):
            flow.resume(run,expected_revision=waiting['revision'],choice='continue')
        assert len(calls) == 1 and len(recorder.intents) == 1
        assert 'rawResponse' not in json.dumps(report) and 'accounting_context' not in json.dumps(report)


@pytest.mark.parametrize('raw,usage,status', [('bad JSON',True,200),('{"ranked_indices":[1,0]}',False,200),('error',True,503)])
def test_malformed_failed_and_unknown_judge_are_audited_without_retry(tmp_path,raw,usage,status):
    with responder(raw,usage=usage,status=status) as (url,calls):
        flow, _ = session(tmp_path,url)
        run = uuid.uuid4().hex
        waiting=flow.start(run,**request())
        done=flow.resume(run,expected_revision=waiting['revision'],choice='continue')
        report=flow.report(run)
        assert report['rankedSourceIds'] == ['s0','s1','s2','s3'] and report['audit']['fallback']
        assert report['audit']['reason'] and len(calls)==1
        flow.resume(run,expected_revision=done['revision'])
        assert len(calls)==1


@pytest.mark.parametrize('save_first',[False,True])
def test_interruption_recovers_only_saved_receipt_without_redispatch(tmp_path,save_first):
    from prosaic_harness import FileRunStore
    class LostProcess(BaseException): pass
    base=FileRunStore(tmp_path/'runs',namespace='jobs')
    class InterruptedStore:
        def __getattr__(self,name):return getattr(base,name)
        def save_receipt(self,*args,**kwargs):
            if save_first:base.save_receipt(*args,**kwargs)
            raise LostProcess()
    with responder('{"ranked_indices":[1,0]}') as (url,calls):
        flow,recorder=session(tmp_path,url,store=InterruptedStore())
        run=uuid.uuid4().hex
        waiting=flow.start(run,**request())
        with pytest.raises(LostProcess):flow.resume(run,expected_revision=waiting['revision'],choice='continue')
        recovered,_=session(tmp_path,url,store=base)
        recovered.accounting=recorder
        current=recovered.status(run)
        done=recovered.resume(run,expected_revision=current['revision'])
        assert done['status']==('completed' if save_first else 'blocked')
        report=recovered.report(run)
        assert report['audit']['fallback'] is (not save_first)
        assert len(calls)==1
        recovered.resume(run,expected_revision=done['revision'])
        assert len(calls)==1


def test_entity_and_origin_outputs_remain_separate_advisory_records(tmp_path):
    entity={'classifications':[{'name':'Evidence','label':'TOPIC','reason':'A theme.'}]}
    with responder(json.dumps(entity)) as (url,calls):
        flow,_=session(tmp_path,url)
        run=uuid.uuid4().hex
        data={'kind':'entity_refinement','candidates':candidates(),
              'entities':[{'name':'Evidence','currentType':'uncertain','contexts':[
                  {'sourceId':'s0','line':1,'quote':'Original evidence 0.'}]}]}
        waiting=flow.start(run,**data)
        flow.resume(run,expected_revision=waiting['revision'],choice='continue')
        report=flow.report(run)
        assert report['result']==entity and report['advisory'] is True and len(calls)==1
        assert data['candidates']==candidates()
    origin={'is_ai_dialogue_corpus':True,'confidence':0.7,'primary_platform':'fixture',
            'user_name':'Alice','agent_persona_names':['Alice','Echo'],'evidence':['Explicit dialogue.']}
    with responder(json.dumps(origin)) as (url,calls):
        flow,_=session(tmp_path,url)
        run=uuid.uuid4().hex
        waiting=flow.start(run,kind='corpus_origin',candidates=candidates())
        flow.resume(run,expected_revision=waiting['revision'],choice='continue')
        report=flow.report(run)
        assert report['result']['agent_persona_names']==['Echo'] and report['advisory']


@pytest.mark.parametrize('override',[{'confidence':True},{'confidence':1.1},{'confidence':float('nan')},
                                    {'confidence':10**1000}, {'is_ai_dialogue_corpus':'false'},{'agent_persona_names':[1]}])
def test_origin_rejects_untyped_or_nonfinite_values(override):
    output={'is_ai_dialogue_corpus':True,'confidence':0.5,'primary_platform':None,'user_name':None,
            'agent_persona_names':[],'evidence':[]}
    output.update(override)
    report=interpret({'kind':'corpus_origin','candidates':freeze_candidates(candidates())},json.dumps(output))
    assert report['result'] is None and report['audit']['reason']


def test_source_hash_and_entity_context_drift_fail_admission(tmp_path):
    docs=candidates()
    docs[0]['textSha256']='0'*64
    with pytest.raises(CastleJobError):freeze_candidates(docs)
    flow,_=session(tmp_path,'http://127.0.0.1:1/v1')
    with pytest.raises(CastleJobError):
        flow.start(uuid.uuid4().hex,kind='entity_refinement',candidates=candidates(),entities=[
            {'name':'Evidence','currentType':'uncertain','contexts':[{'sourceId':'s0','line':1,'quote':'Invented quote'}]}])


@pytest.mark.parametrize('settings',[{'enabled':1},{'enabled':True,'max_tokens':True},
                                    {'enabled':True,'timeout_s':61},{'enabled':True,'unknown':1}])
def test_settings_are_strict(settings):
    with pytest.raises(CastleJobError):JobSettings.from_mapping(settings)


@pytest.mark.parametrize('change', [
    {'currentType':[]}, {'contexts':[{'sourceId':[], 'line':1, 'quote':'Original'}]},
])
def test_invalid_entity_input_uses_bounded_error_contract(tmp_path, change):
    flow,_=session(tmp_path,'http://127.0.0.1:1/v1')
    entity={'name':'Evidence','currentType':'uncertain','contexts':[]}
    entity.update(change)
    with pytest.raises(CastleJobError):
        flow.start(uuid.uuid4().hex,kind='entity_refinement',candidates=candidates(),entities=[entity])


def test_report_links_failure_receipt_and_rejects_changed_runtime(tmp_path):
    from dataclasses import replace
    with responder('bad JSON') as (url,calls):
        flow,_=session(tmp_path,url)
        run=uuid.uuid4().hex
        waiting=flow.start(run,**request())
        done=flow.resume(run,expected_revision=waiting['revision'],choice='continue')
        report=flow.report(run)
        assert report['audit']['receiptSha256']==flow.store.load_run(run).state['invocations'][0]['receipt_sha256']
        flow.config=replace(flow.config,profiles={'fixture':replace(flow.config.profiles['fixture'],model='changed')})
        with pytest.raises(CastleJobError,match='binding_unavailable'):
            flow.resume(run,expected_revision=done['revision'])
        assert len(calls)==1
