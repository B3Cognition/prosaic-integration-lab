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
