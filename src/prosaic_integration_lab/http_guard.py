"""Authenticate before receiving bodies; bound application HTTP work per replica."""
import asyncio
import math
import time
from starlette.responses import JSONResponse
from .identity import FixtureAuthenticator
from .oidc import IdentityUnavailable
from .diagnostics import stage


class HttpGuard:
    def __init__(self,app,principals=None,*,authenticator=None,capacity=32,body_timeout=2,rate=100,burst=200):
        if (type(capacity) is not int or not 1 <= capacity <= 1024 or
            type(burst) is not int or not 1 <= burst <= 10000 or
            not math.isfinite(body_timeout) or not 0 < body_timeout <= 30 or
            not math.isfinite(rate) or not 0 < rate <= 10000):
            raise ValueError('invalid HTTP bounds')
        self.app = app
        self.authenticator = authenticator or FixtureAuthenticator(principals)
        self.capacity,self.body_timeout,self.rate,self.burst = capacity,body_timeout,rate,burst
        self.active = 0
        self.buckets = {}

    def allowed(self,actor):
        now = time.monotonic()
        key = (actor.tenant_id,actor.actor_id)
        if key not in self.buckets and len(self.buckets) >= 10240:
            # Only discard fully replenished idle buckets; never bypass a limit.
            self.buckets = {key:value for key,value in self.buckets.items()
                if now-value[1] < self.burst/self.rate}
            if len(self.buckets) >= 10240:
                return False
        tokens,last = self.buckets.get(key,(self.burst,now))
        tokens = min(self.burst,tokens+(now-last)*self.rate)
        self.buckets[key] = (max(0,tokens-1) if tokens >= 1 else tokens,now)
        return tokens >= 1

    async def __call__(self,scope,receive,send):
        if scope['type'] != 'http' or scope['path'] in {'/healthz','/readyz'}:
            return await self.app(scope,receive,send)
        async def reject(status,detail):
            await JSONResponse({'detail':detail},status_code=status,
                headers={'Connection':'close'})(scope,receive,send)
        if self.active >= self.capacity:
            return await reject(503,'http_capacity_exhausted')
        self.active += 1
        try:
            headers = scope.get('headers',[])
            if sum(len(key)+len(value) for key,value in headers) > 16384:
                return await reject(431,'headers_too_large')
            authorization = [value for key,value in headers if key.lower() == b'authorization']
            try:
                if len(authorization) != 1:
                    raise ValueError('unauthenticated')
                actor = await self.authenticator.authenticate(authorization[0].decode('ascii'))
            except IdentityUnavailable:
                return await reject(503,'identity_unavailable')
            except (ValueError,UnicodeError):
                return await reject(401,'unauthenticated')
            scope.setdefault('state',{})['principal'] = actor
            if not self.allowed(actor):
                return await reject(429,'rate_limited')
            if scope['method'] == 'POST':
                content = bytearray()
                async def collect():
                    while True:
                        message = await receive()
                        if message['type'] == 'http.disconnect':
                            return 400
                        chunk = message.get('body',b'')
                        if len(content)+len(chunk) > 8192:
                            return 413
                        content.extend(chunk)
                        if not message.get('more_body',False):
                            return 0
                try:
                    status = await asyncio.wait_for(collect(),timeout=self.body_timeout)
                except TimeoutError:
                    return await reject(408,'body_timeout')
                if status:
                    return await reject(status,'request_too_large' if status == 413 else 'incomplete_request')
                delivered = False
                async def replay():
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {'type':'http.request','body':bytes(content),'more_body':False}
                    return await receive()
                return await self.dispatch(scope,replay,send)
            return await self.dispatch(scope,receive,send)
        finally:
            self.active -= 1

    async def dispatch(self,scope,receive,send):
        started = False
        async def observed(message):
            nonlocal started
            if message['type'] == 'http.response.start': started = True
            await send(message)
        try:
            with stage('http_dispatch'):
                await self.app(scope,receive,observed)
        except Exception:
            # Do not let an exception message/traceback reach the ASGI server's
            # logger. An already-started response remains incomplete/uncertain.
            if not started:
                await JSONResponse({'detail':'service_unavailable'},status_code=503,
                    headers={'Connection':'close'})(scope,receive,send)
