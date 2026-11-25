"""Same-origin local Explorer boundary; public assets never grant live authority."""
from contextlib import asynccontextmanager
import hmac
import ipaddress
import json
from pathlib import Path
import re
import threading
import time
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool


TASKS = frozenset({'release-brief', 'incident-handoff', 'invoice-sql'})
POLICY = dict(nativeTimeoutSeconds=60, localTimeoutSeconds=180, poolTimeoutSeconds=300,
              maxAttempts=3, maxNativeAttempts=2, maxApiRequests=8, maxToolCalls=7,
              maxToolRounds=8, maxReportedTokens=65536, nativePermissions='workspace-write')
SAFE_ERRORS = frozenset({'config_invalid', 'config_changed', 'busy', 'blocked',
    'request_conflict', 'invalid_request', 'not_found', 'allowance_exhausted',
    'receipt_conflict', 'storage_invalid', 'root_locked'})
CSP = ("default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
       "font-src 'self'; img-src 'self' data:; connect-src 'self'; "
       "frame-ancestors 'none'; base-uri 'none'; form-action 'none'; object-src 'none'")


def create_app(*, origin, token, launch_code, coordinator=None, web_root=None):
    parsed = urlsplit(origin)
    if (parsed.scheme != 'http' or parsed.path or parsed.query or parsed.fragment or
            parsed.username or not ipaddress.ip_address(parsed.hostname).is_loopback):
        raise ValueError('numeric loopback origin required')
    if not isinstance(token, str) or len(token) < 32 or not isinstance(launch_code, str) or len(launch_code) < 24:
        raise ValueError('private launcher credentials required')
    root = Path(web_root) if web_root is not None else Path(__file__).parent / 'web'
    root = root.resolve()
    bootstrap = {'code': launch_code, 'expires': time.monotonic() + 600}
    lock = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            if coordinator is not None:
                await run_in_threadpool(coordinator.close)

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    def error(code, status=400):
        return JSONResponse({'error': code}, status_code=status)

    @app.middleware('http')
    async def boundary(request, call_next):
        response = None
        if request.headers.get('host') != parsed.netloc:
            response = error('invalid_host')
        elif request.url.path.startswith('/api/'):
            if request.method not in {'GET', 'POST'}:
                response = error('method_not_allowed', 405)
            elif request.method == 'POST' and request.headers.get('origin') != origin:
                response = error('origin_rejected', 403)
            elif request.url.path != '/api/bootstrap' and not hmac.compare_digest(
                    request.headers.get('authorization', '').encode(), ('Bearer ' + token).encode()):
                response = error('authentication_required', 401)
        if response is None:
            response = await call_next(request)
        response.headers.update({'Content-Security-Policy': CSP, 'Referrer-Policy': 'no-referrer',
            'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'no-store',
            'Cross-Origin-Resource-Policy': 'same-origin'})
        return response

    async def read_body(request):
        data = bytearray()
        async for part in request.stream():
            data.extend(part)
            if len(data) > 4096:
                return None, error('body_too_large', 413)
        if not data:
            return {}, None
        if request.headers.get('content-type', '').split(';')[0] != 'application/json':
            return None, error('json_required', 415)
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise ValueError('duplicate key')
                result[key] = value
            return result
        try:
            document = json.loads(data, object_pairs_hook=pairs,
                                  parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            if type(document) is not dict:
                raise ValueError()
        except (ValueError, UnicodeError, RecursionError):
            return None, error('invalid_request', 422)
        return document, None

    async def host_call(name, *args):
        if coordinator is None:
            return error('live_not_enabled', 403)
        try:
            result = await run_in_threadpool(getattr(coordinator, name), *args)
            return JSONResponse(result, status_code=202 if name == 'submit' else 200)
        except Exception as exc:
            code = str(exc)
            if code not in SAFE_ERRORS:
                code = 'execution_unavailable'
            return error(code, 404 if code == 'not_found' else 409)

    @app.get('/healthz')
    def health():
        return {'status': 'ready'}

    @app.post('/api/bootstrap')
    async def bootstrap_token(request: Request):
        body, failure = await read_body(request)
        if failure is not None:
            return failure
        if body:
            return error('invalid_request', 422)
        with lock:
            supplied = request.headers.get('x-explorer-launch', '')
            valid = (bootstrap['code'] and time.monotonic() < bootstrap['expires'] and
                     hmac.compare_digest(supplied.encode(), bootstrap['code'].encode()))
            if not valid:
                return error('launch_unavailable', 401)
            bootstrap['code'] = ''
        return {'token': token}

    @app.get('/api/status')
    async def status():
        if coordinator is None:
            return {'liveEnabled': False, 'profiles': [], 'policy': POLICY,
                    'allowance': None, 'blocked': False, 'activeRunId': None, 'runs': []}
        return await host_call('status')

    @app.post('/api/runs')
    async def submit(request: Request):
        body, failure = await read_body(request)
        if failure is not None:
            return failure
        if (set(body) - {'requestId', 'task', 'confirmed', 'localTimeoutSeconds'} or
                body.get('confirmed') is not True or
                not isinstance(body.get('requestId'), str) or
                not re.fullmatch('[0-9a-f]{32}', body['requestId']) or
                not isinstance(body.get('task'), str) or body['task'] not in TASKS or
                type(body.get('localTimeoutSeconds', 180)) is not int or
                body.get('localTimeoutSeconds', 180) not in {180, 240}):
            return error('invalid_request', 422)
        return await host_call('submit', body['requestId'], body['task'], body.get('localTimeoutSeconds', 180))

    @app.get('/api/runs/{run_id}')
    async def get_run(run_id: str):
        if not re.fullmatch('[0-9a-f]{32}', run_id):
            return error('invalid_request', 422)
        return await host_call('get', run_id)

    @app.post('/api/runs/{run_id}/cancel')
    async def cancel(run_id: str, request: Request):
        body, failure = await read_body(request)
        if failure is not None:
            return failure
        if body or not re.fullmatch('[0-9a-f]{32}', run_id):
            return error('invalid_request', 422)
        return await host_call('cancel', run_id)

    @app.get('/{asset_path:path}')
    def assets(asset_path: str):
        if asset_path.startswith('api/'):
            return error('not_found', 404)
        relative = asset_path or 'index.html'
        candidate = root / relative
        if (candidate.is_symlink() or not candidate.resolve().is_relative_to(root) or
                candidate.suffix not in {'.html', '.js', '.css', '.woff', '.woff2', '.txt', '.svg', '.json'}):
            return error('not_found', 404)
        if not candidate.is_file():
            return error('assets_unavailable' if not asset_path else 'not_found', 503 if not asset_path else 404)
        return FileResponse(candidate)

    return app
