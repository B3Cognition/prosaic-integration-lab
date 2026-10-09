import asyncio
import threading
import pytest
from fastapi import HTTPException
from prosaic_integration_lab.admission import Admission


def test_capacity_rejects_before_work_and_cancelled_client_does_not_release_worker():
    async def exercise():
        operations = Admission(1)
        gate, entered = threading.Event(), threading.Event()
        effects = []
        def work():
            entered.set()
            gate.wait(2)
            effects.append('completed')
        task = asyncio.create_task(operations.run(work))
        try:
            assert await asyncio.to_thread(entered.wait,1)
            task.cancel()
            with pytest.raises(asyncio.CancelledError): await task
            with pytest.raises(HTTPException) as error:
                await operations.run(lambda: effects.append('excess'))
            assert error.value.status_code == 503
            assert effects == []
        finally:
            gate.set()
            await asyncio.to_thread(operations.close)
        assert effects == ['completed']
    asyncio.run(exercise())


def test_failing_operation_releases_capacity():
    async def exercise():
        operations = Admission(1)
        try:
            def fail(): raise ValueError('neutral fixture error')
            with pytest.raises(ValueError): await operations.run(fail)
            assert await operations.run(lambda: 42) == 42
        finally:
            operations.close()
    asyncio.run(exercise())


def test_one_actor_cannot_take_both_execution_slots():
    async def exercise():
        operations = Admission(2)
        gate,entered = threading.Event(),threading.Event()
        def wait():
            entered.set()
            gate.wait(2)
        first = asyncio.create_task(operations.run(wait,key=('tenant-a','alice')))
        try:
            assert await asyncio.to_thread(entered.wait,1)
            with pytest.raises(HTTPException):
                await operations.run(lambda: 'excess',key=('tenant-a','alice'))
            assert await operations.run(lambda: 'bob',key=('tenant-a','bob')) == 'bob'
        finally:
            gate.set()
            await first
            operations.close()
    asyncio.run(exercise())
