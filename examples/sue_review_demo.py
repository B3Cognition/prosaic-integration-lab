"""Opt-in document-file SUE walkthrough with synthetic loopback answers only.

From the checkout: PYTHONPATH=src python -m examples.sue_review_demo --enable --directory /absolute/new/demo
Without --enable this imports no SUE engine, starts no server and writes nothing.
The demo creates a private host config, request and source; start pauses before
inference, then resume uses frozen text after the original document is deleted.
The explicit --enable flag permits this synthetic demonstration's continuation.
No live provider, credentials or truth/quality certification is involved.
"""

import argparse
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import threading


SOURCE = 'Only administrators may export data.\r\nConsent must be current.\r\n'
CLAIM = 'Administrators export with current consent.'


def _answers():
    import castle_sue as engine

    kinds = dict(DEFINE='definition',DISTINGUISH='distinction',CAUSE_OR_CRITERION='criterion',
        DIVIDE='case-split',COUNTEREXAMPLE='example',FOLLOW_CONSEQUENCE='consequence',
        TEST_OPPOSITE='consequence',REVISE='revision')
    results = dict(DEFINE='ESTABLISHED',DISTINGUISH='ESTABLISHED',CAUSE_OR_CRITERION='ESTABLISHED',
        DIVIDE='ESTABLISHED',COUNTEREXAMPLE='NOT_FOUND',FOLLOW_CONSEQUENCE='CONSISTENT',
        TEST_OPPOSITE='EXCLUDED',REVISE='REVISED')
    state = engine.initial_state(CLAIM,lens='euthyphro',max_turns=14)
    values = []
    while not state['terminal']:
        operator = state['operator']
        value = dict(answer='Synthetic interpretation for operator inspection.',verdict='SUPPORTED',
            answer_type=kinds[operator],evidence_lines=[1],claim=CLAIM if operator in {'DEFINE','REVISE'} else None,
            test_result=results[operator],evidence=[dict(line=1,quote=SOURCE.splitlines()[0])],
            premises=[dict(statement=SOURCE.splitlines()[0],kind='stated',evidence_lines=[1])],
            witness=None,open_questions=[],addresses=[],revision_reason=None)
        state,error = engine.advance(state,value,SOURCE.splitlines())
        if error is not None:
            raise RuntimeError('synthetic fixture answer rejected')
        values.append(value)
    return values


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enable',action='store_true')
    parser.add_argument('--directory',type=Path)
    args = parser.parse_args(argv)
    if not args.enable:
        print(json.dumps({'enabled':False,'executed':False}))
        return 0
    if args.directory is None or not args.directory.is_absolute():
        parser.error('--enable requires an absolute new --directory')
    args.directory.mkdir(mode=0o700)
    from lab_runner.sue_review import main as review_cli

    values, requests = _answers(), []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass

        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            index = len(requests)-1
            if index >= len(values):
                self.send_error(500)
                return
            response = dict(id='synthetic-sue-demo',model='sue-fixture',
                choices=[dict(index=0,message=dict(role='assistant',content=json.dumps(values[index])),finish_reason='stop')],
                usage=dict(prompt_tokens=10,completion_tokens=5,total_tokens=15))
            data = json.dumps(response).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        source = args.directory/'requirements.md'
        source.write_bytes(SOURCE.encode())
        request = args.directory/'request.json'
        request.write_text(json.dumps(dict(seed=CLAIM,sources=[dict(sourceId='spec',path=str(source),revision='r1')])))
        host = dict(namespace='sue-demo',principal=dict(tenant_id='tenant',actor_id='alice',billing_account_id='payer'),
            store=dict(kind='file',path=str(args.directory/'runs')),
            runtime=dict(base_url=f'http://127.0.0.1:{server.server_port}/v1',model='sue-fixture'),review=dict(enabled=True))
        config = args.directory/'host.json'
        config.write_text(json.dumps(host));config.chmod(0o600)

        def invoke(action,*extra):
            output = io.StringIO()
            with redirect_stdout(output):
                code = review_cli([action,'--config',str(config),*extra])
            if code:
                raise RuntimeError('synthetic walkthrough action failed')
            return json.loads(output.getvalue())

        waiting = invoke('start','--request',str(request))
        if requests or waiting['status'] != 'waiting':
            raise RuntimeError('start did not pause before inference')
        source.unlink()
        run_id = waiting['runId']
        completed = invoke('resume','--run-id',run_id,'--expected-revision',waiting['revision'],'--choice','continue')
        before_report = len(requests)
        host['review'] = {'enabled':False}
        config.write_text(json.dumps(host))
        report = invoke('report','--run-id',run_id)
        if (completed['status'] != 'completed' or len(requests) != len(values)
                or before_report != len(requests) or not report['citations']
                or report['citations'][0]['quote'] != SOURCE.splitlines()[0]):
            raise RuntimeError('synthetic walkthrough evidence mismatch')
        from prosaic_integration_lab.sue_review.reporting import render_markdown
        report_file = args.directory/'advisory.md'
        report_file.write_text(render_markdown(report),encoding='utf-8')
        print(json.dumps(dict(enabled=True,executed=True,data='synthetic requirements only',
            model='scripted loopback fixture, not an LLM',runId=run_id,
            status=completed['status'],terminal=report['terminal'],modelCalls=len(requests),
            acceptedTurns=report['acceptedTurns'],reportedTokens=report['reportedTokens'],
            frozenSourcePreserved=True,reportWithReviewDisabled=True,report=str(report_file)),indent=2))
        return 0
    finally:
        server.shutdown();server.server_close();thread.join(5)
        if thread.is_alive():
            raise RuntimeError('synthetic fixture did not close')


if __name__ == '__main__':
    raise SystemExit(main())
