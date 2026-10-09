import asyncio
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from prosaic_harness import StoreError
from .config import load_config
from .execution import Execution
from .identity import authenticate
from .metadata import RequestConflict


class StartRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    workflow: Literal['approval', 'synthetic'] = 'approval'
    task: str = Field(max_length=2048)


class ResumeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    expected_revision: str = Field(min_length=1, max_length=512)
    choice: Literal['approve', 'reject'] | None = None
    retry_interrupted: bool = False


def create_app():
    config = load_config()
    @asynccontextmanager
    async def lifespan(app):
        try:
            execution = Execution(config)
        except Exception:
            raise RuntimeError('lab startup configuration failed') from None
        app.state.execution = execution
        try:
            try:
                await asyncio.to_thread(execution.ready)
            except Exception:
                raise RuntimeError('lab startup readiness failed') from None
            yield
        finally:
            await asyncio.to_thread(execution.close)
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    def principal(authorization: str | None = Header(default=None)):
        try:
            return authenticate(authorization, config['principals'])
        except ValueError:
            raise HTTPException(401, 'unauthenticated') from None

    @app.exception_handler(RequestValidationError)
    async def invalid(request, error):
        return JSONResponse({'detail': 'invalid_request'}, status_code=422)

    @app.exception_handler(StoreError)
    async def store_error(request, error):
        status = 409 if error.code in {'run_busy', 'revision_conflict', 'run_already_exists', 'receipt_conflict'} else 503
        return JSONResponse({'detail': error.code}, status_code=status)

    @app.exception_handler(RequestConflict)
    async def conflict(request, error):
        return JSONResponse({'detail': 'idempotency_conflict'}, status_code=409)

    @app.exception_handler(ValueError)
    async def value_error(request, error):
        return JSONResponse({'detail': 'invalid_request'}, status_code=422)

    @app.exception_handler(Exception)
    async def unexpected(request, error):
        return JSONResponse({'detail': 'service_unavailable'}, status_code=503)

    @app.middleware('http')
    async def bounded_body(request: Request, call_next):
        if request.method == 'POST':
            content = bytearray()
            async for chunk in request.stream():
                content.extend(chunk)
                if len(content) > 8192:
                    return JSONResponse({'detail': 'request_too_large'}, status_code=413)
            request._body = bytes(content)
        try:
            return await call_next(request)
        except Exception:
            return JSONResponse({'detail': 'service_unavailable'}, status_code=503)

    def owned(execution, actor, run_id):
        reservation = execution.metadata.owned(actor, run_id)
        if reservation is None:
            raise HTTPException(404, 'not_found')
        return reservation

    @app.get('/healthz')
    def health():
        return {'status': 'alive'}

    @app.get('/readyz')
    def ready(request: Request):
        try:
            request.app.state.execution.ready()
        except Exception:
            raise HTTPException(503, 'not_ready') from None
        return {'status': 'ready'}

    @app.post('/runs')
    async def start(body: StartRequest, request: Request, actor=Depends(principal),
                    idempotency_key: str = Header(min_length=1, max_length=128)):
        execution = request.app.state.execution
        reservation = await asyncio.to_thread(execution.metadata.reserve, actor, idempotency_key,
                                             body.model_dump(), execution.fingerprint)
        if reservation['phase'] != 'reserved':
            return await asyncio.to_thread(execution.status, reservation)
        return await execution.admitted(execution.start, reservation)

    @app.get('/runs/{run_id}')
    def status(run_id: str, request: Request, actor=Depends(principal)):
        execution = request.app.state.execution
        return execution.status(owned(execution, actor, run_id))

    @app.post('/runs/{run_id}/resume')
    async def resume(run_id: str, body: ResumeRequest, request: Request, actor=Depends(principal)):
        execution = request.app.state.execution
        reservation = await asyncio.to_thread(owned, execution, actor, run_id)
        return await execution.admitted(execution.resume, reservation, body.expected_revision,
                                        body.choice, body.retry_interrupted)

    @app.get('/runs/{run_id}/usage')
    def usage(run_id: str, request: Request, actor=Depends(principal)):
        execution = request.app.state.execution
        return execution.usage(owned(execution, actor, run_id))

    return app
