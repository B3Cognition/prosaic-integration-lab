"""Keep an owned local conversation stack running for browser interaction."""
import argparse
import hashlib
import ipaddress
import json
import re
import os
import secrets
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie, CookieError
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
        self.cookie_name='prosaic-chat-'+hashlib.sha256(origin.encode()).hexdigest()[:12]
        self.sessions={}

    async def verified(self, scope, receive, token):
        """Validate the exact credential through the ordinary host auth boundary."""
        status=0
        async def capture(message):
            nonlocal status
            if message['type']=='http.response.start':status=message['status']
        child={**scope,'method':'GET','path':'/chat/connection',
            'raw_path':b'/chat/connection','query_string':b'', 'state':{},
            'headers':[(b'authorization',('Bearer '+token).encode('ascii'))]}
        await self.app(child,receive,capture)
        return status==200

    async def __call__(self, scope, receive, send):
        if (scope['type'] != 'http' or scope['path'] not in {'/chat/bootstrap','/chat/session'}
                or scope['method'] != 'POST'):
            return await self.app(scope, receive, send)
        from starlette.responses import JSONResponse
        headers = scope.get('headers', [])
        codes = [value for key, value in headers if key.lower() == b'x-chat-launch']
        origins = [value for key, value in headers if key.lower() == b'origin']
        markers=[value for key,value in headers if key.lower()==b'x-chat-session']
        same_origin=len(origins)==1 and origins[0]==self.origin.encode()
        manual=None
        if scope['path']=='/chat/session' and same_origin and markers==[b'connect']:
            authorization=[value for key,value in headers if key.lower()==b'authorization']
            if len(authorization)==1 and authorization[0].startswith(b'Bearer ') and 7<len(authorization[0])<=8192:
                try:
                    candidate=authorization[0][7:].decode('ascii')
                    if await self.verified(scope,receive,candidate):manual=candidate
                except UnicodeError:pass
        session=None
        record=None
        with self.lock:
            now=time.monotonic()
            self.sessions={key:value for key,value in self.sessions.items() if now<value['expires']}
            if scope['path']=='/chat/bootstrap':
                valid = (same_origin and now < self.expires and len(codes)==1 and
                    self.code and secrets.compare_digest(codes[0], self.code.encode()))
                if valid and len(self.sessions)<32:
                    self.code=''
                    record={'token':self.token,'label':self.label,'expires':now+8*3600}
            elif manual is not None:
                if len(self.sessions)<32:
                    record={'token':manual,'label':'Lab API credential verified','expires':now+8*3600}
            else:
                cookies=[value for key,value in headers if key.lower()==b'cookie']
                cookie=SimpleCookie()
                try:
                    if len(cookies)==1 and len(cookies[0])<=8192:cookie.load(cookies[0].decode('ascii'))
                except (CookieError,UnicodeError):pass
                entry=cookie.get(self.cookie_name)
                if same_origin and markers==[b'restore'] and entry is not None:
                    record=self.sessions.get(entry.value)
            if record is not None and markers!=[b'restore']:
                session=secrets.token_urlsafe(32)
                self.sessions[session]=record
        response = JSONResponse({key:record[key] for key in ('token','label')} if record is not None else
            {'detail': 'launch_link_unavailable'}, status_code=200 if record is not None else 403,
            headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'})
        if session is not None:
            response.set_cookie(self.cookie_name,session,path='/chat',httponly=True,samesite='strict',max_age=8*3600)
        await response(scope, receive, send)


def _local_sse_chunks(chunks):
    """Translate only oMLX's empty prefill sentinel; preserve real wire evidence."""
    def unique(items):
        value={}
        for key,item in items:
            if key in value:raise ValueError('duplicate heartbeat key')
            value[key]=item
        return value

    def frame(raw):
        if len(raw)>4096:return raw
        lines=[line for line in raw.splitlines() if line]
        if len(lines)!=1 or not lines[0].startswith(b'data:'):return raw
        try:
            value=json.loads(lines[0][5:].decode('utf-8'),object_pairs_hook=unique)
        except (ValueError,UnicodeError,RecursionError):return raw
        if (type(value) is not dict or set(value)!={'id','object','created','model','choices'} or
                value['model']!='keepalive' or value['object']!='chat.completion.chunk' or
                type(value['created']) is not int or value['created']!=0 or
                type(value['id']) is not str or
                re.fullmatch(r'chatcmpl-(?:[0-9a-f]{8}|keepalive)',value['id']) is None or
                type(value['choices']) is not list or len(value['choices'])!=1):return raw
        choice=value['choices'][0]
        if (type(choice) is not dict or set(choice)!={'index','delta','finish_reason'} or
                type(choice['index']) is not int or choice['index']!=0 or
                choice['finish_reason'] is not None or
                choice['delta']!={'role':'assistant','content':''}):return raw
        return b': keep-alive\n\n'

    boundary=re.compile(rb'\r?\n\r?\n')
    pending=bytearray();search=0
    for chunk in chunks:
        pending.extend(chunk);start=0
        while match:=boundary.search(pending,search):
            end=match.end()
            yield frame(bytes(pending[start:end]))
            start=search=end
        if start:del pending[:start]
        search=max(0,len(pending)-3)
    if pending:yield bytes(pending)


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
                streaming_started=False
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
                            body.get('stream') is not None and type(body['stream']) is not bool):
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
                        if (body.get('stream') is True and
                                result.headers.get('content-type','').split(';')[0].strip().lower()=='text/event-stream'):
                            self.send_response(200)
                            self.send_header('Content-Type','text/event-stream')
                            self.send_header('Cache-Control','no-store')
                            self.end_headers();streaming_started=True
                            def bounded_chunks():
                                total=0;deadline=time.monotonic()+30
                                for chunk in result.iter_bytes():
                                    total+=len(chunk)
                                    if total>8*1024*1024 or time.monotonic()>deadline:
                                        raise ValueError('local response limit')
                                    yield chunk
                            for chunk in _local_sse_chunks(bounded_chunks()):
                                self.wfile.write(chunk);self.wfile.flush()
                            return
                        content = bytearray()
                        for chunk in result.iter_bytes():
                            content.extend(chunk)
                            if len(content) > 8 * 1024 * 1024:
                                return self.reply(502, b'{"error":"local_response_limit"}')
                        self.reply(200, bytes(content))
                except (ValueError, TypeError, OSError, httpx.HTTPError):
                    if not streaming_started:self.reply(502, b'{"error":"local_provider_unavailable"}')
                    else:self.close_connection=True
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


def configure_conversations(settings, *, model_url, streaming, profile=None, maximum=32):
    """Rename the disposable bindings and every grant reference together."""
    prefix='chat-'+('local' if profile is not None else 'synthetic')+('-stream-' if streaming else '-')
    versions={definition['version']:prefix+definition['version'] for definition in settings['bundles']}
    for definition in settings['bundles']:
        definition['version']=versions[definition['version']]
        definition['model_url']=model_url
        definition['streaming']=streaming
        definition['provider_request_limit']=min(2,maximum)
        if profile is not None:
            definition['model']=profile.model
            definition['policy']={'max_provider_requests':maximum}
    for tenant in settings['tenants'].values():
        tenant['binding_version']=versions[tenant['binding_version']]
        if 'retained_versions' in tenant:
            tenant['retained_versions']=[versions[version] for version in tenant['retained_versions']]


def main(argv=None, *, application_factory=None, landing_path='/chat', streaming=True):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-local', action='store_true', help='explicitly use approved local Qwen')
    parser.add_argument('--runtime-config', type=Path, default=ROOT/'configs/runtime-local.example.yml')
    parser.add_argument('--profile', default='local-strong')
    parser.add_argument('--max-calls', type=int, default=32)
    parser.add_argument('--postgres-version', type=int, choices=(16,18), default=16)
    parser.add_argument('--no-open', action='store_true')
    parser.add_argument('--consumer-image', help='immutable, provenance-checked consumer image')
    parser.add_argument('--fixture-latency',type=float,default=0,help='owned synthetic provider delay, 0–5 seconds')
    args = parser.parse_args(argv)
    if (type(args.max_calls) is not int or not 1<=args.max_calls<=128 or
            not 0<=args.fixture_latency<=5):
        parser.error('bounded request allowance and fixture latency required')
    sys.path.insert(0, str(ROOT/'src'))
    from contextlib import ExitStack
    from prosaic_runtime import RuntimeConfig
    from prosaic_integration_lab.app import create_app
    import uvicorn
    stack = OwnedStack(postgres_major=args.postgres_version, conversation=True,consumer_image=args.consumer_image)
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
            configure_conversations(config['conversation'],streaming=streaming,maximum=args.max_calls,
                model_url=gateway.url if gateway else stack.manifest['endpoints']['model']+'/v1',
                profile=profile if gateway else None)
            if not gateway:
                httpx.post(stack.manifest['endpoints']['model']+'/control', json={'scenario':'conversation',
                    'maximum_calls':args.max_calls,'provider_latency_s':args.fixture_latency},trust_env=False).raise_for_status()
            stack._secret('chat-service.json', json.dumps(config))
            token = next(key for key,value in config['principals'].items() if value['actor_id']=='alice')
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                listener.listen(128)
                origin = 'http://127.0.0.1:' + str(listener.getsockname()[1])
                previous_config = os.environ.get('LAB_CONFIG')
                os.environ['LAB_CONFIG'] = str(stack.secrets/'chat-service.json')
                try:
                    app = application_factory() if application_factory is not None else create_app()
                finally:
                    if previous_config is None:
                        os.environ.pop('LAB_CONFIG', None)
                    else:
                        os.environ['LAB_CONFIG'] = previous_config
                label = ('Local Qwen · ' + profile.model + ' · ' + str(args.max_calls) + ' request allowance' if gateway else
                    'Synthetic fixture · scripted responses') + ' · synthetic workflow tools'
                app = Bootstrap(app, token=token, label=label, origin=origin)
                launch = origin + landing_path + '#connect=' + app.code
                stack._secret('chat-launch.json', json.dumps({'url':launch,'owner':stack.owner}))
                print(('Chat: ' if landing_path == '/chat' else 'Observatory: ') + origin + landing_path, flush=True)
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
