"""Real loopback gateway bounds and one-use browser credential delivery."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest
from starlette.testclient import TestClient


def test_bootstrap_requires_matching_origin_and_one_use_code():
    from lab_runner.chat import Bootstrap
    async def downstream(scope, receive, send):
        if scope['type']=='lifespan':
            await receive();await send({'type':'lifespan.startup.complete'})
            await receive();await send({'type':'lifespan.shutdown.complete'})
            return
        from starlette.responses import JSONResponse
        await JSONResponse({'detail': 'unauthenticated'}, status_code=401)(scope, receive, send)
    app = Bootstrap(downstream, token='private-fixture-token', label='Local fixture', origin='http://testserver')
    with TestClient(app) as client:
        headers={'Origin':'http://testserver', 'X-Chat-Launch':app.code}
        assert client.post('/chat/bootstrap',headers={**headers,'Origin':'https://foreign.invalid'}).status_code==403
        assert client.post('/chat/bootstrap',headers={**headers,'X-Chat-Launch':'wrong'}).status_code==403
        assert client.get('/chat/bootstrap').status_code==401
        assert client.post('/chat/bootstrap',headers=headers).json()=={'token':'private-fixture-token','label':'Local fixture'}
        assert client.post('/chat/bootstrap',headers=headers).status_code==403
        assert client.post('/conversations',headers=headers).status_code==401


def test_launcher_session_reconnects_only_authorized_same_origin_browser(monkeypatch):
    from lab_runner.chat import Bootstrap
    from starlette.responses import JSONResponse
    async def protected(scope,receive,send):
        if scope['type']=='lifespan':
            await receive();await send({'type':'lifespan.startup.complete'})
            await receive();await send({'type':'lifespan.shutdown.complete'});return
        await JSONResponse({'detail':'unauthenticated'},status_code=401)(scope,receive,send)
    app=Bootstrap(protected,token='fixture-only-secret',label='Owned fixture',origin='http://testserver')
    headers={'Origin':'http://testserver','X-Chat-Session':'restore'}
    with TestClient(app) as browser:
        assert browser.post('/chat/session',headers=headers).status_code==403
        launched=browser.post('/chat/bootstrap',headers={'Origin':'http://testserver','X-Chat-Launch':app.code})
        assert launched.status_code==200
        cookie=launched.headers['set-cookie']
        assert 'HttpOnly' in cookie and 'SameSite=strict' in cookie and 'fixture-only-secret' not in cookie
        restored=browser.post('/chat/session',headers=headers)
        assert restored.status_code==200 and restored.json()=={'token':'fixture-only-secret','label':'Owned fixture'}
        assert restored.headers['cache-control']=='no-store'
        assert browser.post('/chat/session',headers={**headers,'Origin':'https://foreign.invalid'}).status_code==403
        assert browser.post('/chat/session',headers={'Origin':'http://testserver'}).status_code==403
        assert browser.post('/chat/session',headers={**headers,'Cookie':app.cookie_name+'="\\377"'}).status_code==403
        assert browser.get('/chat/session',headers=headers).status_code==401
        assert browser.post('/conversations',headers=headers).status_code==401
        with TestClient(app) as stranger:
            assert stranger.post('/chat/session',headers=headers).status_code==403
        monkeypatch.setattr('lab_runner.chat.time.monotonic',lambda:10**20)
        assert browser.post('/chat/session',headers=headers).status_code==403


def test_manual_browser_session_preserves_verified_principal_and_survives_refresh():
    from lab_runner.chat import Bootstrap
    from starlette.responses import JSONResponse
    seen=[]
    async def protected(scope,receive,send):
        if scope['type']=='lifespan':
            await receive();await send({'type':'lifespan.startup.complete'})
            await receive();await send({'type':'lifespan.shutdown.complete'});return
        seen.append((scope['method'],scope['path']))
        authorization=[v for k,v in scope['headers'] if k.lower()==b'authorization']
        valid=authorization==[b'Bearer bob-lab-token']
        await JSONResponse({'connected':True} if valid else {'detail':'unauthenticated'},
            status_code=200 if valid else 401)(scope,receive,send)
    app=Bootstrap(protected,token='alice-launcher-token',label='Alice',origin='http://testserver')
    connect={'Origin':'http://testserver','X-Chat-Session':'connect','Authorization':'Bearer bob-lab-token'}
    restore={'Origin':'http://testserver','X-Chat-Session':'restore'}
    with TestClient(app) as browser:
        assert browser.post('/chat/session',headers={**connect,'Authorization':'Bearer omlx-token'}).status_code==403
        assert browser.post('/chat/session',headers={**connect,'Origin':'https://foreign.invalid'}).status_code==403
        response=browser.post('/chat/session',headers=connect)
        assert response.status_code==200
        assert response.json()['token']=='bob-lab-token'
        assert 'bob-lab-token' not in response.headers['set-cookie']
        assert 'HttpOnly' in response.headers['set-cookie']
        assert browser.post('/chat/session',headers=restore).json()['token']=='bob-lab-token'
        assert 'alice-launcher-token' not in response.text
        assert set(seen)=={('GET','/chat/connection')}
        with TestClient(app) as stranger:
            assert stranger.post('/chat/session',headers=restore).status_code==403


def test_gateway_does_not_follow_redirects_or_dispatch_after_allowance(tmp_path):
    from lab_runner.chat import ModelGateway
    from prosaic_runtime import EndpointConfig
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            calls.append((self.headers.get('Authorization'),json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
            self.send_response(307);self.send_header('Location','https://foreign.invalid/');self.send_header('Content-Length','0');self.end_headers()
        def log_message(self,*args):pass
    origin=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=origin.serve_forever,daemon=True);thread.start()
    key=tmp_path/'key';key.write_text('fixture-only-key')
    profile=EndpointConfig('http://127.0.0.1:'+str(origin.server_port)+'/v1','qwen-fixture',api_key_file=str(key),max_tokens=100)
    try:
        with ModelGateway(profile,maximum=1) as gateway:
            payload={'model':'qwen-fixture','messages':[], 'stream':False}
            assert httpx.post(gateway.url+'/chat/completions',json=payload,
                headers={'Origin':'https://foreign.invalid'},trust_env=False).status_code==403
            assert httpx.post(gateway.url+'/chat/completions',content=json.dumps(payload),
                headers={'Content-Type':'text/plain'},trust_env=False).status_code==415
            assert calls==[] and gateway.used==0
            first=httpx.post(gateway.url+'/chat/completions',json=payload,trust_env=False)
            assert first.status_code==502
            assert httpx.post(gateway.url+'/chat/completions',json=payload,trust_env=False).status_code==429
            assert httpx.post(gateway.url+'/other',json=payload,trust_env=False).status_code==404
        assert len(calls)==1 and calls[0][0]=='Bearer fixture-only-key'
        assert calls[0][1]['max_tokens']==100
    finally:
        origin.shutdown();origin.server_close();thread.join()


def test_gateway_rejects_nonlocal_provider_before_reading_credentials():
    from lab_runner.chat import ModelGateway
    from prosaic_runtime import EndpointConfig
    with pytest.raises(ValueError,match='loopback'):
        ModelGateway(EndpointConfig('https://provider.invalid/v1','qwen',api_key_file='/must/not/read'),maximum=32)


def test_gateway_forwards_sse_before_completion_and_charges_one_request(tmp_path):
    from lab_runner.chat import ModelGateway
    from prosaic_runtime import EndpointConfig
    release=threading.Event();calls=[]
    first=b'data: {"choices":[{"delta":{"content":"Hello "}}]}\n\n'
    last=b'data: {"choices":[{"delta":{"content":"world"}}]}\n\ndata: [DONE]\n\n'
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            self.wfile.write(first);self.wfile.flush()
            release.wait(5)
            self.wfile.write(last);self.wfile.flush()
    origin=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    worker=threading.Thread(target=origin.serve_forever,daemon=True);worker.start()
    key=tmp_path/'key';key.write_text('fixture-only-key')
    profile=EndpointConfig(f'http://127.0.0.1:{origin.server_port}/v1','qwen-fixture',api_key_file=str(key))
    try:
        with ModelGateway(profile,maximum=1) as gateway:
            payload={'model':'qwen-fixture','messages':[],'stream':True}
            with httpx.stream('POST',gateway.url+'/chat/completions',json=payload,trust_env=False) as result:
                assert result.status_code==200
                assert result.headers['content-type'].startswith('text/event-stream')
                lines=result.iter_lines();assert next(lines)==first.decode().splitlines()[0]
                assert not release.is_set()
                release.set();assert '[DONE]' in '\n'.join(lines)
            assert gateway.used==1 and len(calls)==1 and calls[0]['stream'] is True
            assert httpx.post(gateway.url+'/chat/completions',json=payload,trust_env=False).status_code==429
    finally:
        release.set();origin.shutdown();origin.server_close();worker.join()


@pytest.mark.parametrize('stream',[1,'true',[],{}])
def test_gateway_rejects_invalid_stream_flags_before_consuming_allowance(tmp_path,stream):
    from lab_runner.chat import ModelGateway
    from prosaic_runtime import EndpointConfig
    key=tmp_path/'key';key.write_text('fixture-only-key')
    with ModelGateway(EndpointConfig('http://127.0.0.1:9/v1','qwen-fixture',api_key_file=str(key)),maximum=1) as gateway:
        result=httpx.post(gateway.url+'/chat/completions',json={'model':'qwen-fixture','stream':stream},trust_env=False)
        assert result.status_code==422 and gateway.used==0
