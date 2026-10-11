"""Bounded synthetic TCP relay; opaque bytes are never captured or logged."""
import argparse
import asyncio
import math

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, StrictBool


class FaultProxy:
    def __init__(self, target_host, target_port, *, max_connections=32, lifetime_s=300):
        if (type(target_host) is not str or not 0 < len(target_host) <= 253 or
            type(target_port) is not int or not 1 <= target_port <= 65535 or
            type(max_connections) is not int or not 1 <= max_connections <= 64 or
            type(lifetime_s) not in {int,float} or not math.isfinite(lifetime_s) or
            not 0 < lifetime_s <= 300):
            raise ValueError('invalid bounded relay configuration')
        self.target_host, self.target_port = target_host, target_port
        self.max_connections, self.lifetime_s = max_connections, lifetime_s
        self.blocked = False
        self.accepted = self.refused = self.closed = 0
        self._connections = set()

    def stats(self):
        return {'blocked':self.blocked,'active':len(self._connections),
                'accepted':self.accepted,'refused':self.refused,'closed':self.closed}

    async def control(self, blocked):
        if type(blocked) is not bool:raise ValueError('invalid partition control')
        self.blocked = blocked
        if blocked:
            for connection in tuple(self._connections):
                for writer in connection:
                    writer.transport.abort()
        # Let aborted handlers drain before acknowledging the barrier.
        for _ in range(100):
            if not blocked or not self._connections:break
            await asyncio.sleep(.01)
        return self.stats()

    @staticmethod
    async def _close(writer):
        writer.close()
        try:
            await asyncio.wait_for(writer.wait_closed(), 1)
        except (OSError,asyncio.TimeoutError):pass

    async def _pump(self, reader, writer):
        while data := await reader.read(65536):
            writer.write(data)
            await asyncio.wait_for(writer.drain(), 3)

    async def relay(self, reader, writer):
        if self.blocked or len(self._connections) >= self.max_connections:
            self.refused += 1
            await self._close(writer)
            return
        connection = (writer,)
        self._connections.add(connection)
        self.accepted += 1
        tasks = []
        upstream = None
        try:
            async with asyncio.timeout(self.lifetime_s):
                upstream_reader, upstream = await asyncio.wait_for(
                    asyncio.open_connection(self.target_host,self.target_port,limit=65536),3)
                self._connections.remove(connection)
                connection = (writer,upstream)
                self._connections.add(connection)
                if self.blocked:return
                for socket in connection:socket.transport.set_write_buffer_limits(high=65536,low=16384)
                tasks = [asyncio.create_task(self._pump(reader,upstream)),
                         asyncio.create_task(self._pump(upstream_reader,writer))]
                done,_ = await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
                for task in done:task.result()
        except (OSError,asyncio.TimeoutError):pass
        finally:
            for task in tasks:task.cancel()
            if tasks:await asyncio.gather(*tasks,return_exceptions=True)
            await self._close(writer)
            if upstream is not None:await self._close(upstream)
            self._connections.discard(connection)
            self.closed += 1


class Control(BaseModel):
    model_config = ConfigDict(extra='forbid')
    blocked: StrictBool


def control_app(proxy):
    app = FastAPI()
    @app.get('/stats')
    async def stats():return proxy.stats()
    @app.post('/control')
    async def control(body:Control):return await proxy.control(body.blocked)
    return app


async def serve(args):
    import uvicorn
    proxy = FaultProxy(args.target_host,args.target_port)
    relay = await asyncio.start_server(proxy.relay,args.listen_host,args.listen_port,limit=65536)
    server = uvicorn.Server(uvicorn.Config(control_app(proxy),host=args.control_host,
        port=args.control_port,log_level='critical',access_log=False))
    try:await server.serve()
    finally:
        await proxy.control(True)
        relay.close();await relay.wait_closed()


def main():
    parser=argparse.ArgumentParser(description='Owned opaque SQL fault fixture')
    parser.add_argument('--target-host',default='database')
    parser.add_argument('--target-port',type=int,default=5432)
    parser.add_argument('--listen-host',default='0.0.0.0')
    parser.add_argument('--listen-port',type=int,default=5433)
    parser.add_argument('--control-host',default='0.0.0.0')
    parser.add_argument('--control-port',type=int,default=8001)
    asyncio.run(serve(parser.parse_args()))


if __name__ == '__main__':main()
