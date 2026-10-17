"""Installed public-API response/usage faults; synthetic loopback, no live inference."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
from pathlib import Path
import json
import shutil
import sys
from threading import Thread


def stream(provider, value):
    if provider == 'openai-compatible':
        choice = value['choices'][0]
        event = {**value, 'choices': [dict(index=0, delta=choice['message'], finish_reason=choice['finish_reason'])]}
        return ('data: ' + json.dumps(event) + '\n\ndata: [DONE]\n\n').encode()
    start = {**value, 'content': [], 'stop_reason': None}
    events = [{'type': 'message_start', 'message': start}]
    for index, block in enumerate(value['content']):
        events += [{'type': 'content_block_start', 'index': index, 'content_block': {
            **block, **({'input': {}} if block['type'] == 'tool_use' else {})}}]
        if block['type'] == 'tool_use':events += [{'type': 'content_block_delta', 'index': index,
            'delta': {'type': 'input_json_delta', 'partial_json': json.dumps(block['input'])}}]
        events += [{'type': 'content_block_stop', 'index': index}]
    events += [{'type': 'message_delta', 'delta': {'stop_reason': value['stop_reason']},
        'usage': {'output_tokens': 50}}, {'type': 'message_stop'}]
    return ''.join('event: ' + e['type'] + '\ndata: ' + json.dumps(e) + '\n\n' for e in events).encode()


@contextmanager
def fixture(provider, mode, case):
    class State:requests = 0
    state = State()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):pass
        def do_POST(self):
            from lab_runner.quality.checks import assess_evidence
            native = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            state.requests += 1
            tool = state.requests == 1
            ids = case['requiredRecords']
            answer = assess_evidence(case, [case['records'][key] for key in ids])['answer']
            if provider == 'anthropic':
                assert self.path == '/v1/messages'
                content = ([dict(type='tool_use', id='lookup1', name='lookup_records', input={'recordIds': ids})]
                    if tool else [dict(type='text', text=json.dumps(answer))])
                value = dict(id='fixture', type='message', role='assistant', model=native['model'],
                    content=content, stop_reason='tool_use' if tool else 'end_turn',
                    usage=dict(input_tokens=100, output_tokens=50))
            else:
                assert self.path == '/v1/chat/completions'
                message = (dict(role='assistant', content=None, tool_calls=[dict(id='lookup1', type='function',
                    function=dict(name='lookup_records', arguments=json.dumps({'recordIds': ids})))])
                    if tool else dict(role='assistant', content=json.dumps(answer)))
                value = dict(id='fixture', model=native['model'], choices=[dict(index=0,
                    message=message, finish_reason='tool_calls' if tool else 'stop')],
                    usage=dict(prompt_tokens=100, completion_tokens=50, total_tokens=150))
            status = 200;content_type = 'application/json'
            if mode == 'missing' or mode == 'after-tool-missing' and not tool:value.pop('usage')
            elif mode == 'incomplete':value['usage'] = {'input_tokens': 100} if provider == 'anthropic' else {'prompt_tokens': 100}
            elif mode == 'invalid':value['usage'] = {'input_tokens': True} if provider == 'anthropic' else {'total_tokens': True}
            elif mode == 'provider-error':value = {'error': {'message': 'PRIVATE_FAULT_SECRET'}}
            elif mode in {'contradictory-error', 'stream-contradictory'}:value['error'] = {'message': 'PRIVATE_FAULT_SECRET'}
            elif mode == 'shape':value = {'unknown': 'PRIVATE_FAULT_SECRET'}
            raw = json.dumps(value).encode()
            if mode == 'malformed':raw = b'PRIVATE_FAULT_SECRET not-json'
            elif mode == 'duplicate':raw = b'{"usage":{},"usage":{},"secret":"PRIVATE_FAULT_SECRET"}'
            elif mode == 'encoding':raw = b'\xffPRIVATE_FAULT_SECRET'
            elif mode in {'http-error', 'http-redirect'}:
                status = 302 if mode == 'http-redirect' else 503
                raw = b'{"error":{"message":"PRIVATE_FAULT_SECRET"}}'
            elif mode.startswith('stream-'):
                content_type = 'text/event-stream'
                if mode == 'stream-error':
                    raw = b'data: {"type":"error","error":{"message":"PRIVATE_FAULT_SECRET"}}\n\n'
                elif mode == 'stream-malformed':raw = b'data: PRIVATE_FAULT_SECRET not-json\n\n'
                else:
                    raw = stream(provider, value)
                    if mode == 'stream-encoding':raw = b':\xff\n\n' + raw
            self.send_response(status);self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(raw)));self.end_headers();self.wfile.write(raw)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler);server.daemon_threads = True
    thread = Thread(target=server.serve_forever, daemon=True);thread.start()
    state.url = f'http://127.0.0.1:{server.server_port}/v1'
    try:yield state
    finally:server.shutdown();server.server_close();thread.join(timeout=3);assert not thread.is_alive()


def run(output):
    from prosaic_runtime import (EndpointConfig, RuntimeConfig, TokenCounterDescriptor, TokenCounterRegistration)
    from lab_runner.memory.corpus import Corpus
    from lab_runner.memory.execution import execute_case, recover_case, LIMITS
    from lab_runner.memory_policy.scoped import ScopedCorpus
    from lab_runner.memory_policy.native import ScopedContext
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.allowance import private_directory, private_write
    from lab_runner.quality.contracts import decode, digest
    output = private_directory(output)
    denied = {'value': False}
    def audit(event, args):
        if denied['value'] and event.startswith('socket.'):raise AssertionError('network during receipt replay')
    sys.addaudithook(audit)
    class Counter:
        def count_tokens(self, native):return 100
    results = []
    for provider in ('openai-compatible', 'anthropic'):
        for mode in ('healthy', 'missing', 'incomplete', 'invalid', 'provider-error', 'contradictory-error',
                     'shape', 'malformed', 'duplicate', 'encoding', 'http-error', 'after-tool-missing',
                     'stream-healthy', 'stream-error', 'stream-malformed', 'stream-contradictory', 'stream-encoding', 'http-redirect'):
            case = deepcopy(load_suite()['cases'][0])
            case.update(tenantId='synthetic', asOf='2026-01-01T00:00:00Z', entity='fixture', topics=['rollout'])
            document = dict(version=1, episodes=[]);sources = dict(version=1, sources=[])
            metadata = dict(version=1, episodes=[], currentSources=[])
            descriptor = TokenCounterDescriptor(identity='synthetic-fault-' + provider, provider=provider,
                model='fixture', framing_revision='anthropic-messages-v1' if provider == 'anthropic' else 'openai-chat-v1',
                context_capacity_tokens=32768, implementation_version='synthetic-v1', tokenizer_assets_digest='a'*64,
                template_assets_digest='b'*64, counting_kind='exact', guarantee='Synthetic units only, not live tokenizer qualification.')
            builder = ScopedContext(ScopedCorpus(document, sources, metadata), counter_descriptor=descriptor.to_dict(),
                quote_inputs=lambda request: [100]*4, quote_identity='c'*64, limits=LIMITS,
                output_tokens=512, continuation_budget=True)
            path = output/(provider + '-' + mode)
            with fixture(provider, mode, case) as fx:
                config = RuntimeConfig({'fixture': EndpointConfig(fx.url, 'fixture', provider=provider,
                    max_tokens=512, features={'streaming': mode.startswith('stream-')})}, {}, 'fixture')
                options = dict(corpus=Corpus(document, sources), arm='disabled', config=config, profile='fixture',
                    output=path, sample_id='qualification', evidence_format='typed', context_builder=builder, bounded_recovery=True)
                evidence = execute_case(case, **options, token_counter=TokenCounterRegistration(descriptor, Counter()))
                healthy = mode in {'healthy', 'stream-healthy'}
                known_error = mode in {'contradictory-error', 'stream-contradictory'}
                assert fx.requests == evidence['counts']['providerRequests'] == (2 if healthy or mode == 'after-tool-missing' else 1)
                assert evidence['counts']['toolCalls'] == (1 if healthy or mode == 'after-tool-missing' else 0)
                diagnostics = [r['result']['metadata']['response_diagnostics_v1'] for r in evidence['receipts']]
                assert 'PRIVATE_FAULT_SECRET' not in json.dumps(diagnostics)
                if healthy:assert evidence['completed'] and evidence['counts']['reportedTokens'] == 300
                elif known_error:assert not evidence['completed'] and evidence['counts']['reportedTokens'] == 150
                else:assert not evidence['completed'] and evidence['counts']['reportedTokens'] is None
                expected_kind = {'provider-error': 'providerError', 'contradictory-error': 'providerError',
                    'shape': 'unexpectedShape', 'malformed': 'malformedJson', 'duplicate': 'ambiguousJson',
                    'encoding': 'invalidEncoding', 'http-error': 'httpError', 'stream-error': 'providerError',
                    'http-redirect': 'httpError', 'stream-encoding': 'invalidEncoding',
                    'stream-contradictory': 'providerError', 'stream-malformed': 'malformedJson'}.get(mode, 'stream' if mode.startswith('stream-') else 'message')
                assert diagnostics[0]['attempts'][-1]['responseKind'] == expected_kind
                before = {p: p.read_bytes() for p in path.rglob('*') if p.is_file()}
                replay = output/(provider + '-' + mode + '-replay')
                shutil.copytree(path, replay)
                trace = replay/'qualification-context-trace.json'
                trace_before = trace.read_bytes()
                receipt_bytes = {p: p.read_bytes() for p in replay.glob('store/**/attempts/*.json')}
                assert receipt_bytes
                denied['value'] = True
                try:recovered = recover_case(case, **{**options, 'output': replay})
                finally:denied['value'] = False
                assert fx.requests == evidence['counts']['providerRequests']
                assert all(p.read_bytes() == value for p, value in before.items())
                assert trace.read_bytes() == trace_before
                assert all(p.read_bytes() == value for p, value in receipt_bytes.items())
                if healthy:
                    assert recovered is not None
                    assert [digest(r) for r in recovered['receipts']] == [digest(r) for r in evidence['receipts']]
                if mode == 'after-tool-missing':
                    observed = decode(trace_before)['observations'].values()
                    assert sum(r['usage']['total_tokens'] or 0 for r in observed) == 150
                results.append(dict(provider=provider, mode=mode, counts=evidence['counts'], completed=evidence['completed'],
                    reason=evidence['reason'], diagnostics=diagnostics, receiptDigests=[digest(r) for r in evidence['receipts']],
                    replayAdditionalRequests=0))
                print(provider, mode, 'qualified', flush=True)
    report = dict(version=1, origin='synthetic-loopback-only', scenarios=len(results), liveDispatches=0,
        limits=dict(**LIMITS, outputTokens=512), networkDeniedReceiptReplay=True, originalEvidenceBytesPreserved=True,
        installedVersions={name: version(name) for name in ('prosaic-integration-lab', 'b3-prosaic-runtime', 'b3-prosaic-harness')}, results=results)
    private_write(output/'qualification.json', report)
    return report


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True);args = parser.parse_args()
    import lab_runner, prosaic_runtime
    for package in (lab_runner, prosaic_runtime):
        owner = Path(package.__file__).resolve()
        assert owner.is_relative_to(Path(sys.prefix).resolve()) and not owner.is_relative_to(args.source_root.resolve())
    report = run(args.output.resolve())
    print('Installed response fault qualification passed:', report['scenarios'], 'synthetic scenarios; no live inference.')


if __name__ == '__main__':main()
