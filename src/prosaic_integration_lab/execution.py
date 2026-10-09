"""Bounded SDK execution; never redispatch uncertain starts."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
from fastapi import HTTPException
from prosaic_harness import Harness, RunNotFound, Workflow
from prosaic_harness_postgres import PostgresRunStore
from prosaic_runtime import ExecutionContext, RateCard
from prosaic_runtime_postgres import PostgresRecorder
from .config import assets_hash
from .metadata import Metadata
from .views import public_run, public_usage, uncertain_run

class Execution:
    def __init__(self, config):
        self.config = config
        self.fingerprint = assets_hash(config['assets'])
        self.workflows = {name: Workflow.load(Path(config['assets']) / (name + '.yml')) for name in ('approval', 'synthetic')}
        self.metadata = Metadata(config['app_dsn'])
        self.store = PostgresRunStore(config['harness_dsn'], namespace=config['namespace'], max_active_leases=2,
            lease_s=15, renew_s=3, operation_timeout_s=5, pool_timeout_s=2, connect_timeout_s=3,
            lock_timeout_s=1, statement_timeout_s=3)
        self.recorder = PostgresRecorder(config['accounting_dsn'], namespace=config['namespace'],
            environment=config['environment'], rate_card=RateCard('synthetic-v1', 'test-model', '2', '8', '0.5'))
        self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='lab-execution')
        self.slots = threading.BoundedSemaphore(2)

    def ready(self):
        self.metadata.check_ready()
        self.store.check_ready()
        self.recorder.check_ready()

    def close(self):
        self.pool.shutdown(wait=True)
        self.store.close()

    def harness(self, reservation):
        if reservation['assets_hash'] != self.fingerprint:
            raise HTTPException(409, 'asset_conflict')
        context = ExecutionContext(application_id='integration-lab', tenant_id=reservation['tenant_id'],
            actor_id=reservation['actor_id'], billing_account_id=reservation['billing_account_id'], request_id=reservation['run_id'])
        return Harness(self.workflows[reservation['workflow']], store=self.store,
                       run_id=reservation['run_id'], context=context, accounting=self.recorder,
                       on_event=self.fixture_event if self.config.get('fixture_events_url') else None)

    def fixture_event(self, event):
        # Public Harness callback; the fixture sees only event type, never
        # operator state, arguments, IDs, prompts or event payloads.
        if event['event'] == 'accepted':
            import httpx
            response = httpx.post(self.config['fixture_events_url'] + '/accepted', timeout=25)
            response.raise_for_status()

    def status(self, reservation):
        try:
            snapshot = self.harness(reservation).status()
        except RunNotFound:
            return uncertain_run(reservation['run_id'])
        return public_run(reservation['run_id'], snapshot.state, snapshot.revision)

    def start(self, reservation):
        harness = self.harness(reservation)
        if not self.metadata.claim_start(reservation['run_id']):
            return self.status(reservation)
        harness.run({'task': reservation['request']['task']})
        self.metadata.started(reservation['run_id'])
        return self.status(reservation)

    def resume(self, reservation, revision, choice, retry):
        self.harness(reservation).resume(choice=choice, expected_revision=revision, retry_interrupted=retry)
        return self.status(reservation)

    def usage(self, reservation):
        return public_usage(self.recorder.report(application_id='integration-lab', tenant_id=reservation['tenant_id'],
            billing_account_id=reservation['billing_account_id'], actor_id=reservation['actor_id'],
            request_id=reservation['run_id'], run_id=reservation['run_id']))

    async def admitted(self, function, *args):
        if not self.slots.acquire(blocking=False):
            raise HTTPException(503, 'capacity_exhausted')
        def work():
            try:
                return function(*args)
            finally:
                self.slots.release()
        future = asyncio.get_running_loop().run_in_executor(self.pool, work)
        return await asyncio.shield(future)
