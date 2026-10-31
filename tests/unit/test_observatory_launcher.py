from starlette.testclient import TestClient
from starlette.responses import JSONResponse

from lab_runner.observatory import ObservatoryShell
from lab_runner.stack import ROOT


def test_shell_supports_embedded_model_textures_without_exposing_run_apis():
    async def protected(scope, receive, send):
        if scope['type'] == 'lifespan':
            await receive(); await send({'type': 'lifespan.startup.complete'})
            await receive(); await send({'type': 'lifespan.shutdown.complete'})
            return
        await JSONResponse({'detail': 'unauthenticated'}, status_code=401)(scope, receive, send)
    with TestClient(ObservatoryShell(protected, ROOT/'prototypes/observatory')) as client:
        response = client.get('/observatory/')
        assert response.status_code == 200
        assert "connect-src 'self' blob:" in response.headers['content-security-policy']
        assert 'https:' not in response.headers['content-security-policy']
        assert response.headers['cache-control'] == 'no-store'
        assert client.get('/observatory/missing.js').status_code == 404
        assert client.get('/conversations/private/observations').status_code == 401
        assert client.post('/observatory/',json={}).status_code == 401
        assert client.get('/observatory/%2e%2e/secrets/host.json').status_code == 401
