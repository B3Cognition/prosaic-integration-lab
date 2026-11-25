"""Owned HTTP/CLI fixtures inspect actual SDK transports, never real providers."""
from contextlib import contextmanager
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread

from . import EFFORTS, load_artifact, require_sdk

MODELS = {
    'gemma-4-31B-it-oQ4e-mtp': ('none', 'low', 'medium', 'high', 'xhigh', 'max'),
    'ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ': ('none', 'low', 'medium', 'xhigh'),
    'qwen3.8-max': ('none', 'low', 'medium', 'xhigh'),
    'deepseek-v4-pro': ('none', 'low', 'high', 'max'),
    'nvidia/nemotron-3.5-super-vl-120b-a12b': ('low', 'medium', 'high'),
    'gpt-6.1-sol': ('low', 'medium', 'high', 'xhigh', 'max'),
}


def expected_control(model, effort):
    if model == 'gemma-4-31B-it-oQ4e-mtp':
        return {'chat_template_kwargs': {'enable_thinking': effort != 'none'}}
    if model == 'ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ':
        return {'chat_template_kwargs': {'enable_thinking': effort != 'none'},
                **({'reasoning_effort': effort} if effort != 'none' else {})}
    return {'reasoning_effort': effort}


@contextmanager
def api_fixture(*, on_request=None):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            if on_request is not None:
                on_request(requests)
            body = json.dumps({'model': 'fixture', 'choices': [{'message': {
                'role': 'assistant', 'content': '{"answer":423}'}, 'finish_reason': 'stop'}],
                'usage': {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 5}}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1', requests
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
        if worker.is_alive():
            raise RuntimeError('fixture cleanup failed')


def control(payload):
    return {key: payload[key] for key in ('reasoning_effort', 'chat_template_kwargs') if key in payload}


def api_rows(sdk, root):
    rows = []
    with api_fixture() as (url, requests):
        for model, supported in MODELS.items():
            endpoint = sdk.EndpointConfig(url, model, temperature=None, features={
                'streaming': False, 'reasoning_effort': 'low'})
            runtime = sdk.ProsaicRuntime(sdk.RuntimeConfig({'api': endpoint}, {}, 'api'))
            for effort in EFFORTS:
                before = len(requests)
                rejected = False
                completed = False
                try:
                    result = runtime.run(load_artifact(effort), cwd=root,
                        policy=sdk.RunPolicy(timeout_s=10, max_provider_requests=1))
                    completed = result.exit_code == 0
                except ValueError:
                    rejected = True
                dispatched = len(requests) - before
                expected_rejection = effort not in supported
                observed = control(requests[-1]) if dispatched else {}
                passed = ((rejected and dispatched == 0) if expected_rejection else
                          (completed and dispatched == 1 and observed == expected_control(model, effort)))
                rows.append(dict(adapter='openai-compatible', model=model, effort=effort,
                    expectedRejection=expected_rejection, dispatched=bool(dispatched),
                    observedControl=observed, passed=passed))
        for default in (None, 'high'):
            endpoint = sdk.EndpointConfig(url, 'gemma-4-31B-it-oQ4e-mtp', features={
                'streaming': False, **({'reasoning_effort': default} if default else {})})
            runtime = sdk.ProsaicRuntime(sdk.RuntimeConfig({'api': endpoint}, {}, 'api'))
            prose = load_artifact('low')
            frontmatter = dict(prose.frontmatter)
            del frontmatter['effort']
            before = len(requests)
            result = runtime.run(replace(prose, frontmatter=frontmatter), cwd=root)
            expected = {} if default is None else {'chat_template_kwargs': {'enable_thinking': True}}
            rows.append(dict(adapter='openai-compatible', model=endpoint.model, effort='omitted',
                expectedRejection=False, dispatched=len(requests) - before == 1,
                observedControl=control(requests[-1]) if len(requests) > before else {},
                passed=result.exit_code == 0 and len(requests) - before == 1
                    and control(requests[-1]) == expected))
    return rows


def native_rows(sdk, root):
    rows = []
    for backend in ('claude-code', 'codex-cli'):
        supported = EFFORTS[1:-1] if backend == 'claude-code' else EFFORTS[1:]
        log = root / f'{backend}.jsonl'
        script = root / f'{backend}-fixture'
        script.write_text(f'''#!{sys.executable}
import json,sys
from pathlib import Path
if '--version' in sys.argv:
    print('2.1.308' if {backend!r} == 'claude-code' else '0.154.0');sys.exit(0)
sys.stdin.read()
if {backend!r} == 'claude-code':
    effort=sys.argv[sys.argv.index('--effort')+1]
else:
    effort=next(json.loads(x.split('=',1)[1]) for x in sys.argv if x.startswith('model_reasoning_effort='))
with Path({str(log)!r}).open('a') as stream:stream.write(json.dumps(effort)+'\\n')
if {backend!r} == 'claude-code':
    print(json.dumps({{'type':'result','subtype':'success','is_error':False,'result':effort,'usage':{{'input_tokens':2,'output_tokens':3}}}}))
else:
    print(json.dumps({{'type':'item.completed','item':{{'type':'agent_message','text':effort}}}}))
    print(json.dumps({{'type':'turn.completed','usage':{{'input_tokens':2,'output_tokens':3}}}}))
''')
        script.chmod(0o700)
        profile = sdk.NativeProfile(backend, 'fixture-model', backend, str(script),
            effort='low', supported_efforts=supported)
        runtime = sdk.NativeRuntime(sdk.NativeRuntimeConfig({'fixture': profile}, default_profile='fixture'))
        for effort in EFFORTS:
            before = log.read_text().splitlines() if log.exists() else []
            completed = False
            try:
                result = runtime.run(load_artifact(effort), cwd=root, profile='fixture',
                                     policy=sdk.NativePolicy(timeout_s=10))
                completed = result.exit_code == 0
            except ValueError:
                pass
            after = log.read_text().splitlines() if log.exists() else []
            dispatched = len(after) - len(before)
            expected_rejection = effort not in supported
            observed = json.loads(after[-1]) if dispatched else None
            passed = (dispatched == 0 and not completed) if expected_rejection else (
                completed and dispatched == 1 and observed == effort and result.stdout.strip() == effort)
            rows.append(dict(adapter=backend, model='fixture-model', effort=effort,
                expectedRejection=expected_rejection, dispatched=bool(dispatched),
                observedControl=observed, passed=passed))
    return rows


def run(*, provenance=None):
    sdk = require_sdk()
    with TemporaryDirectory(prefix='lab-reasoning-fixtures-') as temporary:
        root = Path(temporary)
        rows = api_rows(sdk, root) + native_rows(sdk, root)
    return summarize(rows, provenance=provenance)


def summarize(rows, *, provenance=None):
    passed = bool(rows) and all(r['passed'] for r in rows)
    return dict(schemaVersion=1, origin='scripted_fixture', passed=passed,
                controlsVerified=passed, modelQualityQualified=False, liveInvocations=0,
                samples=rows, provenance=provenance or {}, cleanup='verified')
