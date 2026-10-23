"""Credential-free comparison adapter contract against real installed SDKs."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading


def test_local_adapter_counts_real_requests_and_matches_native_inputs(tmp_path):
    from prosaic_runtime import ProsaicRuntime, RuntimeConfig, EndpointConfig
    from lab_runner.native_eval.compare import local_sample
    from lab_runner.native_eval.runner import sample, fixture_config
    from lab_runner.native_eval.provenance import require_native
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            message = ({'role': 'assistant', 'content': None, 'tool_calls': [{
                'id': 'read-1', 'type': 'function', 'function': {'name': 'read_file',
                'arguments': '{"path":"inventory.json"}'}}]} if len(requests) == 1 else
                {'role': 'assistant', 'content': '{"total":12,"decision":"BLOCK"}'})
            payload = json.dumps({'id': 'synthetic', 'object': 'chat.completion', 'model': 'synthetic',
                'choices': [{'index': 0, 'message': message,
                    'finish_reason': 'tool_calls' if len(requests) == 1 else 'stop'}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15}}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        config = RuntimeConfig({'local': EndpointConfig(
            f'http://127.0.0.1:{server.server_port}/v1', 'synthetic',
            features={'streaming': False})}, {}, 'local', allowed_tools=frozenset({'read_file'}))
        local_workspace, native_workspace = tmp_path / 'local', tmp_path / 'native'
        local_workspace.mkdir()
        native_workspace.mkdir()
        local = local_sample(ProsaicRuntime(config), 'facts', local_workspace, timeout_s=5)
        native = sample(require_native().NativeRuntime(fixture_config(tmp_path)),
                        'claude', 'facts', native_workspace)
        assert local['passed'] and native['passed']
        assert local['providerRequests'] == len(requests) == 2
        assert local['toolCalls'] == 1
        assert local['reportedTokens'] == 30
        assert local['timeoutSeconds'] == 5
        assert local['timedOut'] is False
        completed = [e for e in local['timings'] if e['event'] == 'provider_request_completed']
        assert len(completed) == 2
        assert all(e['outcome'] == 'completed' and e['duration_ms'] >= 0 for e in completed)
        assert any(e['event'] == 'tool_completed' and e['name'] == 'read_file'
                   and e['status'] == 'ok' for e in local['timings'])
        assert local['inputSha256'] == native['inputSha256']
        assert local['artifactSha256'] == native['artifactSha256']
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_realistic_native_sample_records_unchanged_input_contract_failure(tmp_path):
    from lab_runner.native_eval.realistic import _sample
    from lab_runner.native_eval.runner import fixture_config
    from lab_runner.native_eval.provenance import require_native
    sdk=require_native()
    workspace=tmp_path/'workspace';workspace.mkdir()
    row=_sample(sdk.NativeRuntime(fixture_config(tmp_path)),'claude','release-brief',workspace,
                trial=1,timeout_s=5,native=True)
    assert row['completed'] and not row['passed']
    assert row['failureReason']=='contract_failed'
    assert row['grade']=={'workspaceIntegrity':True,'factualContract':False}
    assert row['nativeAttempts']==1 and row['model']=='synthetic'
    assert len(row['inputSha256'])==len(row['artifactSha256'])==64


def test_local_agent_requires_final_confirmation_after_valid_write(tmp_path):
    from dataclasses import replace
    from pathlib import Path
    from prosaic_runtime import ProsaicRuntime,RuntimeConfig
    from lab_runner.native_eval.realistic import _sample
    requests=[]
    answer={'status':'MITIGATED','rootCause':'UNCONFIRMED',
      'impact':{'failedRequests':216,'totalRequests':1200,'windowMinutes':16},
      'summary':'The incident is mitigated following rollback, with request errors back at baseline. The affected window lasted sixteen minutes and included two hundred sixteen failures. Deployment timing is correlated with the incident, but a root cause has not been confirmed. Platform should investigate while support follows up with affected customers.',
      'evidence':['timeline','metrics'],'actions':[{'owner':'platform','action':'Investigate root cause'},{'owner':'support','action':'Notify affected customers'}]}
    def call(identifier,name,args):
        return {'id':identifier,'type':'function','function':{'name':name,'arguments':json.dumps(args)}}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            calls=([call('r1','read_file',{'path':'packet.json'}),call('r2','read_file',{'path':'handoff.json'})]
                   if len(requests)==1 else [call('w1','write_file',{'path':'handoff.json','content':json.dumps(answer)})]
                   if len(requests)==2 else [])
            body=json.dumps({'id':'synthetic','object':'chat.completion','model':'synthetic',
                'choices':[{'index':0,'message':{'role':'assistant','content':None if calls else 'Saved.',
                  'tool_calls':calls},'finish_reason':'tool_calls' if calls else 'stop'}],
                'usage':{'prompt_tokens':10,'completion_tokens':5,'total_tokens':15}}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        config=RuntimeConfig.load(Path(__file__).resolve().parents[2]/'configs/runtime-comparison-local.example.yml')
        selected=config.default_profile
        endpoint=replace(config.profiles[selected],base_url=f'http://127.0.0.1:{server.server_port}/v1',
                         api_key_file=None,api_key_env=None)
        row=_sample(ProsaicRuntime(replace(config,profiles={selected:endpoint})),'local','incident-handoff',
                    tmp_path,trial=1,timeout_s=5,native=False)
        assert row['passed'] and row['completed'] and not row['timedOut']
        assert row['providerRequests']==len(requests)==3 and row['toolCalls']==3
        assert requests[-1]['messages'][-1]['role']=='tool'
        assert json.loads((tmp_path/'handoff.json').read_text())==answer
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)


def test_benchmark_codex_profile_pins_effort_over_artifact_default(tmp_path):
    from dataclasses import replace
    from pathlib import Path
    import sys
    from prosaic_runtime import NativeRuntime,NativeRuntimeConfig,NativePolicy,ProsaicArtifact
    config=NativeRuntimeConfig.load(Path(__file__).resolve().parents[2]/'configs/native-runtime.example.yml')
    script=tmp_path/'codex-fixture'
    script.write_text(f'#!{sys.executable}\n'+'''import json,sys
sys.stdin.read()
effort='unset'
for value in sys.argv[1:]:
    if value.startswith('model_reasoning_effort='):effort=json.loads(value.split('=',1)[1])
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':effort}}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':5,'output_tokens':2}}))
''')
    script.chmod(0o700)
    profile=replace(config.profiles['codex-main'],executable=str(script),model='synthetic')
    runtime=NativeRuntime(replace(config,profiles={**config.profiles,'codex-main':profile},
                                 capacity_file=str(tmp_path/'capacity.json')))
    result=runtime.run(ProsaicArtifact('profile-test','subagent',{'effort':'high'},'Return the selected effort.'),
                       cwd=tmp_path,profile='codex-main',policy=NativePolicy(timeout_s=5))
    assert result.exit_code==0
    assert result.stdout=='low'


def test_native_timing_retains_terminal_event_without_claiming_process_completion(tmp_path):
    import sys
    from prosaic_runtime import NativeRuntime,NativeRuntimeConfig,NativeProfile
    from lab_runner.native_eval.realistic import _sample
    script=tmp_path/'codex-slow-exit'
    script.write_text(f'#!{sys.executable}\n'+'''import json,sys,time
sys.stdin.read()
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'private-sentinel'}}),flush=True)
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':5,'output_tokens':2}}),flush=True)
time.sleep(10)
''')
    script.chmod(0o700)
    config=NativeRuntimeConfig({'codex':NativeProfile('codex-cli','synthetic','owned',executable=str(script),
                               permission_mode='workspace-write')},default_profile='codex',
                               capacity_file=str(tmp_path/'capacity.json'))
    workspace=tmp_path/'workspace';workspace.mkdir()
    row=_sample(NativeRuntime(config),'codex','invoice-sql',workspace,trial=1,timeout_s=1,native=True)
    assert not row['completed'] and not row['passed'] and row['timedOut']
    assert any(e.get('type')=='turn.completed' for e in row['timings'])
    assert all(0<=e['elapsedMs']<=row['durationMs'] for e in row['timings'])
    assert 'private-sentinel' not in json.dumps(row)
