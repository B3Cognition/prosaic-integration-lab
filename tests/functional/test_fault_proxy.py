"""The relay must sever active sockets and refuse new ones without retaining data."""
import asyncio
import json

import pytest


def test_partition_severs_active_and_new_sockets_then_restores_fresh_connections():
    from lab_runner.fault_proxy import FaultProxy
    async def scenario():
        async def echo(reader, writer):
            try:
                while data := await reader.read(65536):
                    writer.write(data); await writer.drain()
            finally:
                writer.close(); await writer.wait_closed()
        target = await asyncio.start_server(echo, '127.0.0.1', 0)
        proxy = FaultProxy('127.0.0.1', target.sockets[0].getsockname()[1], lifetime_s=2)
        server = await asyncio.start_server(proxy.relay, '127.0.0.1', 0)
        port = server.sockets[0].getsockname()[1]
        try:
            reader, writer = await asyncio.open_connection('127.0.0.1', port)
            payload = b'PRIVATE_DSN_AND_SQL_SENTINEL'
            writer.write(payload); await writer.drain()
            assert await asyncio.wait_for(reader.readexactly(len(payload)), 1) == payload
            await proxy.control(True)
            assert await asyncio.wait_for(reader.read(), 1) == b''
            refused, refused_writer = await asyncio.open_connection('127.0.0.1', port)
            assert await asyncio.wait_for(refused.read(), 1) == b''
            await proxy.control(False)
            restored, restored_writer = await asyncio.open_connection('127.0.0.1', port)
            restored_writer.write(b'fresh'); await restored_writer.drain()
            assert await asyncio.wait_for(restored.readexactly(5), 1) == b'fresh'
            assert 'PRIVATE' not in json.dumps(proxy.stats())
            assert proxy.stats()['refused'] == 1
            for socket in (writer, refused_writer, restored_writer):
                socket.close(); await socket.wait_closed()
        finally:
            await proxy.control(True)
            server.close(); target.close()
            await server.wait_closed(); await target.wait_closed()
        assert proxy.stats()['active'] == 0
    asyncio.run(scenario())


def test_relay_lifetime_and_capacity_are_finite():
    from lab_runner.fault_proxy import FaultProxy
    async def scenario():
        async def hold(reader, writer):
            try: await reader.read()
            finally:
                writer.close(); await writer.wait_closed()
        target = await asyncio.start_server(hold, '127.0.0.1', 0)
        proxy = FaultProxy('127.0.0.1', target.sockets[0].getsockname()[1],
            max_connections=1, lifetime_s=.15)
        server = await asyncio.start_server(proxy.relay, '127.0.0.1', 0)
        try:
            port = server.sockets[0].getsockname()[1]
            first, writer = await asyncio.open_connection('127.0.0.1', port)
            async def wait_active():
                while proxy.stats()['active'] == 0: await asyncio.sleep(.001)
            await asyncio.wait_for(wait_active(), 1)
            second, other = await asyncio.open_connection('127.0.0.1', port)
            assert await asyncio.wait_for(second.read(), 1) == b''
            assert await asyncio.wait_for(first.read(), 1) == b''
            assert proxy.stats()['refused'] == 1
            writer.close(); other.close()
            await writer.wait_closed(); await other.wait_closed()
        finally:
            await proxy.control(True)
            server.close(); target.close()
            await server.wait_closed(); await target.wait_closed()
    asyncio.run(scenario())


@pytest.mark.parametrize('settings', [{'max_connections': 0}, {'max_connections': 1000},
    {'lifetime_s': 0}, {'lifetime_s': 301}, {'target_port': 0}])
def test_relay_rejects_unbounded_configuration(settings):
    from lab_runner.fault_proxy import FaultProxy
    with pytest.raises(ValueError): FaultProxy('127.0.0.1', **({'target_port': 9} | settings))
