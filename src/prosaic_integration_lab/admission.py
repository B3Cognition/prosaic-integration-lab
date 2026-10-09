"""Non-queueing admission that remains held until the actual worker exits."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from contextvars import copy_context
from fastapi import HTTPException


class Admission:
    def __init__(self, capacity, *, metrics=None, pool_name='writes'):
        self.metrics,self.pool_name=metrics,pool_name
        self.slots = threading.BoundedSemaphore(capacity)
        self.pool = ThreadPoolExecutor(max_workers=capacity, thread_name_prefix='lab-operation')
        self.lock = threading.Lock()
        self.owners = set()

    def submit(self, function, *args, key=None):
        if not self.slots.acquire(blocking=False):
            if self.metrics is not None: self.metrics.admission(self.pool_name,rejected=True)
            raise HTTPException(503,'capacity_exhausted')
        if key is not None:
            with self.lock:
                if key in self.owners:
                    if self.metrics is not None: self.metrics.admission(self.pool_name,rejected=True)
                    self.slots.release()
                    raise HTTPException(503,'capacity_exhausted')
                self.owners.add(key)
        if self.metrics is not None: self.metrics.admission(self.pool_name,delta=1)
        def release():
            if key is not None:
                with self.lock:
                    self.owners.remove(key)
            self.slots.release()
            if self.metrics is not None: self.metrics.admission(self.pool_name,delta=-1)
        def work():
            try:
                return function(*args)
            finally:
                release()
        try:
            return self.pool.submit(copy_context().run,work)
        except Exception:
            release()
            raise

    async def run(self, function, *args, key=None):
        future = asyncio.wrap_future(self.submit(function,*args,key=key))
        # A disconnected client must neither release its worker nor leak a raw
        # background exception through the event-loop's unhandled-future logger.
        future.add_done_callback(lambda completed: completed.exception() if not completed.cancelled() else None)
        return await asyncio.shield(future)

    def run_sync(self, function, *args):
        return self.submit(function,*args).result()

    def close(self):
        self.pool.shutdown(wait=True)
