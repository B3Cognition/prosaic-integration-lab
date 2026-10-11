import asyncio
import json
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError
from prosaic_harness import StoreError
from .config import load_config
from .execution import Execution
from .http_guard import HttpGuard
from .identity import make_authenticator
from .metadata import RequestConflict
from .observability import Metrics,Observability
from .proposals import MAX_CHOICE_CHARACTERS


class StartRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    workflow: Literal['approval', 'synthetic'] = 'approval'
    task: str = Field(max_length=2048)


class ResumeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    expected_revision: str = Field(min_length=1, max_length=512)
    choice: str | None = Field(default=None,min_length=1,max_length=MAX_CHOICE_CHARACTERS)
    response: JsonValue = None
    retry_interrupted: bool = False


class NativeStartRequest(BaseModel):
    model_config = ConfigDict(extra='forbid',strict=True)
    proposal_id: str = Field(min_length=1,max_length=128)
    inputs: JsonValue


class ConversationMessageRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    messageId: str=Field(min_length=1,max_length=128,pattern=r'^[A-Za-z0-9][A-Za-z0-9._:-]*$')
    message: str=Field(min_length=1,max_length=16384)
    expectedRevision: str=Field(min_length=1,max_length=512)
    interactionRef: str | None=Field(default=None,min_length=1,max_length=512)


class ConversationRetryRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    expectedRevision: str=Field(min_length=1,max_length=512)
    acknowledgeEffectRisk: bool


async def conversation_body(request,model=None):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate JSON field')
            result[key]=value
        return result
    try:
        value=json.loads(await request.body(),object_pairs_hook=pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
        if type(value) is not dict:raise ValueError('invalid conversation body')
        if model is None:
            if value:raise ValueError('invalid conversation body')
            return None
        return model.model_validate(value)
    except (ValueError,ValidationError,UnicodeError,RecursionError):
        raise HTTPException(422,'invalid_request') from None


def create_app():
    config = load_config()
    metrics=Metrics(config.get('metrics_token'))
    authenticator = make_authenticator(config)
    @asynccontextmanager
    async def lifespan(app):
        execution = None
        try:
            try:
                execution = Execution(config,metrics=metrics)
            except Exception:
                raise RuntimeError('lab startup configuration failed') from None
            app.state.execution = execution
            try:
                await asyncio.to_thread(execution.ready)
                metrics.ready=1
            except Exception:
                raise RuntimeError('lab startup readiness failed') from None
            yield
        finally:
            try:
                if execution is not None:
                    await asyncio.to_thread(execution.close)
            finally:
                await authenticator.close()
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    app.add_middleware(HttpGuard,authenticator=authenticator,**config.get('http_bounds',{}))
    app.add_middleware(Observability,metrics=metrics,operator_token=config.get('metrics_token'))

    def principal(request: Request):
        return request.state.principal

    @app.exception_handler(RequestValidationError)
    async def invalid(request, error):
        return JSONResponse({'detail': 'invalid_request'}, status_code=422)

    @app.exception_handler(StoreError)
    async def store_error(request, error):
        status = 404 if error.code=='session_not_found' else 409 if error.code in {'run_busy', 'revision_conflict', 'run_already_exists', 'receipt_conflict','session_busy','session_already_exists'} else 503
        return JSONResponse({'detail': error.code}, status_code=status)

    @app.exception_handler(RequestConflict)
    async def conflict(request, error):
        return JSONResponse({'detail': 'idempotency_conflict'}, status_code=409)

    @app.exception_handler(ValueError)
    async def value_error(request, error):
        if config.get('conversation'):
            from prosaic_harness import ConversationError
            if isinstance(error,ConversationError):
                detail={'code':error.code}
                if error.limit is not None:detail['limit']=error.limit
                status=409 if error.code in {'bindingMismatch','identityMismatch','messageConflict','interactionStale'} else 422
                return JSONResponse({'detail':detail},status_code=status)
        # New native diagnostics are already closed and redacted by the SDK.
        # Import lazily so the legacy application still starts on historical pins.
        if config.get('native'):
            from prosaic_harness import HumanResponseError,WorkflowAdmissionError
            if isinstance(error,HumanResponseError):
                return JSONResponse({'detail':error.to_dict()},status_code=422)
            if isinstance(error,WorkflowAdmissionError):
                return JSONResponse({'detail':{'code':error.code,'location':error.location}},status_code=422)
        return JSONResponse({'detail': 'invalid_request'}, status_code=422)

    @app.exception_handler(Exception)
    async def unexpected(request, error):
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
            request.app.state.execution.read(request.app.state.execution.ready)
        except Exception:
            raise HTTPException(503, 'not_ready') from None
        return {'status': 'ready'}

    @app.post('/runs')
    async def start(body: StartRequest, request: Request, actor=Depends(principal),
                    idempotency_key: str = Header(min_length=1, max_length=128)):
        execution = request.app.state.execution
        return await execution.admitted(execution.start_request,actor,idempotency_key,body.model_dump())

    def native(execution):
        if execution.native is None: raise HTTPException(404,'not_found')
        return execution.native

    @app.get('/workflow-catalogue')
    def catalogue(request: Request, actor=Depends(principal)):
        execution = request.app.state.execution
        return execution.read(native(execution).catalogue,actor)

    @app.post('/workflow-proposals')
    async def propose(request: Request, actor=Depends(principal),
                      idempotency_key: str = Header(min_length=1,max_length=128)):
        execution = request.app.state.execution
        text = await request.body()
        return await execution.admitted(native(execution).propose,actor,idempotency_key,text)

    @app.post('/native-runs')
    async def native_start(body: NativeStartRequest, request: Request, actor=Depends(principal),
                           idempotency_key: str = Header(min_length=1,max_length=128)):
        execution = request.app.state.execution
        return await execution.admitted(native(execution).start_request,actor,idempotency_key,body.proposal_id,body.inputs)

    @app.get('/runs/{run_id}')
    def status(run_id: str, request: Request, actor=Depends(principal)):
        execution = request.app.state.execution
        return execution.read(lambda: execution.status(owned(execution,actor,run_id)))

    @app.post('/runs/{run_id}/resume')
    async def resume(run_id: str, body: ResumeRequest, request: Request, actor=Depends(principal)):
        execution = request.app.state.execution
        reservation = await execution.inspected(owned,execution,actor,run_id)
        return await execution.admitted(execution.resume, reservation, body.expected_revision,
                                        body.choice, body.retry_interrupted, body.response)

    @app.get('/runs/{run_id}/usage')
    def usage(run_id: str, request: Request, actor=Depends(principal)):
        execution = request.app.state.execution
        return execution.read(lambda: execution.usage(owned(execution,actor,run_id)))

    def conversation(execution):
        if getattr(execution,'conversation',None) is None:raise HTTPException(404,'not_found')
        return execution.conversation

    @app.post('/conversations')
    async def chat_create(request: Request,actor=Depends(principal),
            idempotency_key: str=Header(min_length=1,max_length=128)):
        await conversation_body(request)
        execution=request.app.state.execution
        return await execution.admitted(conversation(execution).create_request,actor,idempotency_key)

    @app.get('/conversations/{session_id}')
    def chat_status(session_id: str,request: Request,actor=Depends(principal)):
        execution=request.app.state.execution
        return execution.read(conversation(execution).status_request,actor,session_id)

    @app.get('/conversations/{session_id}/history')
    def chat_history(session_id: str,request: Request,actor=Depends(principal)):
        execution=request.app.state.execution
        return execution.read(conversation(execution).history_request,actor,session_id)

    @app.get('/conversations/{session_id}/usage')
    def chat_usage(session_id: str,request: Request,actor=Depends(principal)):
        execution=request.app.state.execution
        return execution.read(conversation(execution).usage_request,actor,session_id)

    @app.post('/conversations/{session_id}/messages')
    async def chat_message(session_id: str,request: Request,actor=Depends(principal)):
        body=await conversation_body(request,ConversationMessageRequest)
        execution=request.app.state.execution
        chat=conversation(execution)
        return await execution.admitted(lambda owner:chat.send_request(owner,session_id,
            message_id=body.messageId,message=body.message,expected_revision=body.expectedRevision,
            interaction_ref=body.interactionRef),actor)

    @app.post('/conversations/{session_id}/recover')
    async def chat_recover(session_id: str,request: Request,actor=Depends(principal)):
        await conversation_body(request)
        execution=request.app.state.execution
        return await execution.admitted(conversation(execution).recover_request,actor,session_id)

    @app.post('/conversations/{session_id}/retry')
    async def chat_retry(session_id: str,request: Request,actor=Depends(principal)):
        body=await conversation_body(request,ConversationRetryRequest)
        if body.acknowledgeEffectRisk is not True:raise HTTPException(422,'invalid_request')
        execution=request.app.state.execution
        chat=conversation(execution)
        return await execution.admitted(lambda owner:chat.retry_request(owner,session_id,
            expected_revision=body.expectedRevision,acknowledge_effect_risk=True),actor)

    return app
