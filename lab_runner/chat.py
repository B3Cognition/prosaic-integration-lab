"""Keep an owned local conversation stack running for browser interaction."""
import argparse
import ipaddress
import json
import os
import secrets
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from .stack import OwnedStack, ROOT


class Bootstrap:
    """Deliver a fixture API token once, to this launch's same-origin browser."""
    def __init__(self, app, *, token, label, origin):
        self.app, self.token, self.label, self.origin = app, token, label, origin
        self.code = secrets.token_urlsafe(32)
        self.expires = time.monotonic() + 600
        self.lock = threading.Lock()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'] != '/chat/bootstrap' or scope['method'] != 'POST':
            return await self.app(scope, receive, send)
        from starlette.responses import JSONResponse
        headers = scope.get('headers', [])
        codes = [value for key, value in headers if key.lower() == b'x-chat-launch']
        origins = [value for key, value in headers if key.lower() == b'origin']
        with self.lock:
            valid = (time.monotonic() < self.expires and len(codes) == len(origins) == 1 and
                origins[0] == self.origin.encode() and self.code and
                secrets.compare_digest(codes[0], self.code.encode()))
            if valid:
                self.code = ''
        response = JSONResponse({'token': self.token, 'label': self.label} if valid else
            {'detail': 'launch_link_unavailable'}, status_code=200 if valid else 403,
            headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'})
        await response(scope, receive, send)


class ModelGateway:
    """A loopback-only, nonretrying, shared request allowance for a local model."""
    def __init__(self, profile, *, maximum):
        parsed = urlsplit(profile.base_url)
        try:
            local = ipaddress.ip_address(parsed.hostname).is_loopback
        except ValueError:
            local = False
        if (not local or parsed.scheme != 'http' or parsed.username or parsed.password or
                parsed.query or parsed.fragment or parsed.path.rstrip('/') != '/v1' or
                profile.provider != 'openai-compatible' or 'qwen' not in profile.model.lower()):
            raise ValueError('local Qwen requires a literal loopback HTTP /v1 provider')
        if type(maximum) is not int or not 1 <= maximum <= 128:
            raise ValueError('provider request allowance must be between 1 and 128')
        if not profile.api_key_file or profile.api_key_env:
            raise ValueError('local model requires a secret-managed API key file')
        self.profile, self.maximum = profile, maximum
        self.used = 0
        self.lock = threading.Lock()

    def __enter__(self):
        key = Path(self.profile.api_key_file).expanduser().read_text().strip()
        if not key or '\n' in key or '\r' in key or len(key) > 8192:
            raise ValueError('invalid local credential file')
        self.client = httpx.Client(trust_env=False, follow_redirects=False, timeout=30,
            headers={'Authorization': 'Bearer ' + key})
        gateway = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, status, content):
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            def do_POST(self):
                if self.path != '/v1/chat/completions':
                    return self.reply(404, b'{"error":"not_found"}')
                # The SDK is a server-side client. Browser requests must never
                # borrow the local model credential, including simple form POSTs.
                if self.headers.get('Origin') is not None or self.headers.get('Sec-Fetch-Site') is not None:
                    return self.reply(403, b'{"error":"browser_dispatch_denied"}')
                if self.headers.get('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json':
                    return self.reply(415, b'{"error":"json_required"}')
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                    if not 0 < length <= 196608:
                        return self.reply(413, b'{"error":"request_limit"}')
                    self.connection.settimeout(5)
                    body = json.loads(self.rfile.read(length))
                    if (type(body) is not dict or body.get('model') != gateway.profile.model or
                            body.get('stream') not in (None, False)):
                        return self.reply(422, b'{"error":"invalid_request"}')
                    body['max_tokens'] = min(body.get('max_tokens', 512), gateway.profile.max_tokens or 512)
                    with gateway.lock:
                        if gateway.used >= gateway.maximum:
                            return self.reply(429, b'{"error":"local_allowance_exhausted"}')
                        gateway.used += 1
                    with gateway.client.stream('POST', gateway.profile.base_url.rstrip('/') +
                            '/chat/completions', json=body) as result:
                        if result.status_code != 200:
                            return self.reply(502, b'{"error":"local_provider_failed"}')
                        content = bytearray()
                        for chunk in result.iter_bytes():
                            content.extend(chunk)
                            if len(content) > 8 * 1024 * 1024:
                                return self.reply(502, b'{"error":"local_response_limit"}')
                        self.reply(200, bytes(content))
                except (ValueError, TypeError, OSError, httpx.HTTPError):
                    self.reply(502, b'{"error":"local_provider_unavailable"}')
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_port) + '/v1'
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.client.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-local', action='store_true', help='explicitly use approved local Qwen')
    parser.add_argument('--runtime-config', type=Path, default=ROOT/'configs/runtime-local.example.yml')
    parser.add_argument('--profile', default='local-strong')
    parser.add_argument('--max-calls', type=int, default=32)
    parser.add_argument('--postgres-version', type=int, choices=(16,18), default=16)
    parser.add_argument('--no-open', action='store_true')
    args = parser.parse_args(argv)
    sys.path.insert(0, str(ROOT/'src'))
    from contextlib import ExitStack
    from prosaic_runtime import RuntimeConfig
    from prosaic_integration_lab.app import create_app
    import uvicorn
    stack = OwnedStack(postgres_major=args.postgres_version, conversation=True)
    try:
        with ExitStack() as resources:
            gateway = None
            if args.live_local:
                config = RuntimeConfig.load(args.runtime_config)
                profile = config.profiles[args.profile]
                gateway = resources.enter_context(ModelGateway(profile, maximum=args.max_calls))
            stack.start()
            stack.start_model()
            host = json.loads((stack.secrets/'host.json').read_text())
            allowed = {'namespace','environment','harness_dsn','accounting_dsn','app_dsn','principals','conversation'}
            config = {key:value for key,value in host.items() if key in allowed}
            config['assets'] = str(ROOT/'assets')
            config['fixture_events_url'] = stack.manifest['endpoints']['model'] + '/events'
            for definition in config['conversation']['bundles']:
                definition['version'] = 'chat-' + ('local' if gateway else 'synthetic') + '-' + definition['version']
                definition['model_url'] = gateway.url if gateway else stack.manifest['endpoints']['model'] + '/v1'
                if gateway:
                    definition['model'] = profile.model
                    definition['policy'] = {'max_provider_requests': args.max_calls}
            for tenant in config['conversation']['tenants'].values():
                tenant['binding_version'] = 'chat-' + ('local' if gateway else 'synthetic') + '-' + tenant['binding_version']
            if not gateway:
                httpx.post(stack.manifest['endpoints']['model']+'/control', json={'scenario':'conversation'}, trust_env=False).raise_for_status()
            stack._secret('chat-service.json', json.dumps(config))
            token = next(key for key,value in config['principals'].items() if value['actor_id']=='alice')
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                listener.listen(128)
                origin = 'http://127.0.0.1:' + str(listener.getsockname()[1])
                previous_config = os.environ.get('LAB_CONFIG')
                os.environ['LAB_CONFIG'] = str(stack.secrets/'chat-service.json')
                try:
                    app = create_app()
                finally:
                    if previous_config is None:
                        os.environ.pop('LAB_CONFIG', None)
                    else:
                        os.environ['LAB_CONFIG'] = previous_config
                label = ('Local Qwen · ' + profile.model + ' · ' + str(args.max_calls) + ' request allowance' if gateway else
                    'Synthetic fixture · scripted responses') + ' · synthetic workflow tools'
                app = Bootstrap(app, token=token, label=label, origin=origin)
                launch = origin + '/chat#connect=' + app.code
                stack._secret('chat-launch.json', json.dumps({'url':launch,'owner':stack.owner}))
                print('Chat: ' + origin + '/chat', flush=True)
                print('Connection file: ' + str(stack.secrets/'chat-launch.json'), flush=True)
                print(label + '\nPress Ctrl+C to stop and clean up the owned stack.', flush=True)
                if not args.no_open:
                    import webbrowser
                    threading.Timer(1, webbrowser.open, args=(launch,)).start()
                uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', access_log=False, log_level='warning')).run(sockets=[listener])
    except KeyboardInterrupt:
        pass
    finally:
        stack.stop()
        print('Owned stack cleanup: verified', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
