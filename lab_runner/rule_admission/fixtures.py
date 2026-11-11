"""Owned loopback OpenAI-compatible provider with scripted replies; never a real model."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Lock, Thread

USAGE = {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 5}


class ScriptedProvider:
    """Replies in queue order and records each raw request body; an empty queue is a 500."""

    def __init__(self, provider='openai-compatible'):
        if provider not in {'openai-compatible', 'anthropic'}:
            raise ValueError('unsupported synthetic provider wire')
        self.provider = provider
        self.raw_requests, self.captured_headers, self._replies, self._lock = [], [], [], Lock()
        self.url = None

    @property
    def requests(self):
        return [json.loads(raw) for raw in self.raw_requests]

    def queue_text(self, text):
        if self.provider == 'anthropic':
            self._replies.append({'id': 'synthetic', 'type': 'message', 'role': 'assistant',
                'model': 'synthetic-model', 'content': [{'type': 'text', 'text': text}],
                'stop_reason': 'end_turn', 'usage': {'input_tokens': 2, 'output_tokens': 3}})
            return
        self._replies.append(
            {
                'model': 'synthetic-model',
                'choices': [{'message': {'role': 'assistant', 'content': text}, 'finish_reason': 'stop'}],
                'usage': USAGE,
            }
        )

    def queue_calls(self, *calls):
        """Queue one assistant message calling tools; each call is (call_id, name, arguments)."""
        if self.provider == 'anthropic':
            self._replies.append({'id': 'synthetic', 'type': 'message', 'role': 'assistant',
                'model': 'synthetic-model', 'content': [
                    {'type': 'tool_use', 'id': call_id, 'name': name, 'input': arguments}
                    for call_id, name, arguments in calls],
                'stop_reason': 'tool_use', 'usage': {'input_tokens': 2, 'output_tokens': 3}})
            return
        wire = [
            {'id': call_id, 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(arguments)}}
            for call_id, name, arguments in calls
        ]
        self._replies.append(
            {
                'model': 'synthetic-model',
                'choices': [
                    {'message': {'role': 'assistant', 'content': '', 'tool_calls': wire}, 'finish_reason': 'tool_calls'}
                ],
                'usage': USAGE,
            }
        )

    def _reply(self, raw):
        with self._lock:
            self.raw_requests.append(raw)
            return (200, self._replies.pop(0)) if self._replies else (500, {'error': {'message': 'script exhausted'}})


@contextmanager
def scripted_provider(provider='openai-compatible'):
    provider = ScriptedProvider(provider)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            provider.captured_headers.append({key.lower(): value for key, value in self.headers.items()})
            status, document = provider._reply(self.rfile.read(int(self.headers['Content-Length'])))
            body = json.dumps(document).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    provider.url = f'http://127.0.0.1:{server.server_port}/v1'
    try:
        yield provider
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
        if worker.is_alive():
            raise RuntimeError('fixture cleanup failed')
