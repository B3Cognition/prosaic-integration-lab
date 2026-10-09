import asyncio
from prosaic_integration_lab.http_guard import HttpGuard

IDENTITY = {'token': {'tenant_id':'a','actor_id':'alice','billing_account_id':'payer'}}

async def invoke(guard, authorization=b'Bearer token', receive=None):
    messages = []
    async def empty(): return {'type':'http.request','body':b'{}','more_body':False}
    async def send(message): messages.append(message)
    await guard({'type':'http','method':'POST','path':'/runs','headers':
        [(b'authorization',authorization)]},receive or empty,send)
    return messages[0]['status']

def test_unauthenticated_request_never_reads_body():
    async def forbidden(): raise AssertionError('body consumed before authentication')
    async def downstream(*args): raise AssertionError('unauthenticated dispatch')
    assert asyncio.run(invoke(HttpGuard(downstream,IDENTITY),b'Bearer invalid',forbidden)) == 401

def test_incomplete_authenticated_body_times_out_and_releases_slot():
    async def scenario():
        async def never(): await asyncio.Future()
        async def downstream(scope,receive,send):
            await send({'type':'http.response.start','status':204,'headers':[]})
        guard = HttpGuard(downstream,IDENTITY,body_timeout=.01,capacity=1)
        assert await invoke(guard,receive=never) == 408
        assert await invoke(guard) == 204
    asyncio.run(scenario())

def test_capacity_rejects_before_read_and_health_remains_available():
    async def scenario():
        entered = asyncio.Event()
        release = asyncio.Event()
        async def waiting():
            entered.set()
            await release.wait()
            return {'type':'http.request','body':b'{}','more_body':False}
        async def downstream(scope,receive,send):
            await send({'type':'http.response.start','status':204,'headers':[]})
        guard = HttpGuard(downstream,IDENTITY,capacity=1)
        first = asyncio.create_task(invoke(guard,receive=waiting))
        await entered.wait()
        async def forbidden(): raise AssertionError('body read at capacity')
        assert await invoke(guard,receive=forbidden) == 503
        messages = []
        async def send(message): messages.append(message)
        await guard({'type':'http','path':'/healthz'},forbidden,send)
        assert messages[0]['status'] == 204
        release.set()
        assert await first == 204
    asyncio.run(scenario())

def test_actor_rate_bound_precedes_body_reads():
    async def downstream(scope,receive,send):
        await send({'type':'http.response.start','status':204,'headers':[]})
    guard = HttpGuard(downstream,IDENTITY,rate=.01,burst=1)
    assert asyncio.run(invoke(guard)) == 204
    async def forbidden(): raise AssertionError('rate limited body consumed')
    assert asyncio.run(invoke(guard,receive=forbidden)) == 429

def test_rate_is_scoped_by_trusted_actor_and_body_is_replayed_once():
    async def downstream(scope,receive,send):
        assert scope['state']['principal'].billing_account_id == 'payer'
        assert await receive() == {'type':'http.request','body':b'{}','more_body':False}
        await send({'type':'http.response.start','status':204,'headers':[]})
    mapping = {**IDENTITY,'second':{**IDENTITY['token'],'actor_id':'bob'}}
    guard = HttpGuard(downstream,mapping,rate=.01,burst=1)
    assert asyncio.run(invoke(guard)) == 204
    assert asyncio.run(invoke(guard,b'Bearer second')) == 204

def test_unexpected_dispatch_error_is_curated_without_rethrow_or_message_leak(caplog):
    async def failed(*args): raise RuntimeError('PRIVATE_CREDENTIAL_SENTINEL')
    assert asyncio.run(invoke(HttpGuard(failed,IDENTITY))) == 503
    assert 'PRIVATE_CREDENTIAL_SENTINEL' not in caplog.text
