"""Bounded SDK execution; never redispatch uncertain starts."""
from pathlib import Path
from fastapi import HTTPException
from prosaic_harness import Harness, RunNotFound, Workflow
from prosaic_harness_postgres import PostgresRunStore
from prosaic_runtime import ExecutionContext, RateCard
from prosaic_runtime_postgres import PostgresRecorder
from .config import assets_hash
from .metadata import Metadata
from .views import public_run, public_usage, uncertain_run
from .admission import Admission
from .diagnostics import stage

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
        self.operations = Admission(2)
        self.reads = Admission(4)

    def ready(self):
        self.metadata.check_ready()
        self.store.check_ready()
        self.recorder.check_ready()

    def close(self):
        self.operations.close()
        self.reads.close()
        self.store.close()

    def harness(self, reservation):
        self.check_scope(reservation)
        if reservation['assets_hash'] != self.fingerprint:
            raise HTTPException(409, 'asset_conflict')
        context = ExecutionContext(application_id='integration-lab', tenant_id=reservation['tenant_id'],
            actor_id=reservation['actor_id'], billing_account_id=reservation['billing_account_id'], request_id=reservation['run_id'])
        return Harness(self.workflows[reservation['workflow']], store=self.store,
                       run_id=reservation['run_id'], context=context, accounting=self.recorder,
                       on_event=self.fixture_event if self.config.get('fixture_events_url') else None)

    def check_scope(self, reservation):
        if any(reservation[name] != self.config[name] for name in ('namespace', 'environment')):
            raise HTTPException(409, 'scope_conflict')

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
        return public_run(reservation['run_id'], snapshot.state, snapshot.revision,workflow=reservation['workflow'])

    def start(self, reservation):
        with stage('harness_config'):
            harness = self.harness(reservation)
        with stage('claim_start'):
            claimed = self.metadata.claim_start(reservation['run_id'])
        if not claimed:
            return self.status(reservation)
        with stage('harness_run'):
            harness.run({'task': reservation['request']['task']})
        with stage('mark_started'):
            self.metadata.started(reservation['run_id'])
        with stage('start_status'):
            return self.status(reservation)

    def start_request(self, principal, key, payload):
        # Called only inside admitted work. No fresh DB reservation is allocated
        # for execution that cannot be admitted; reservation still commits before dispatch.
        with stage('reserve'):
            reservation = self.metadata.reserve(principal,key,payload,self.fingerprint,
                namespace=self.config['namespace'],environment=self.config['environment'])
        if reservation['phase'] != 'reserved':
            return self.status(reservation)
        return self.start(reservation)

    def resume(self, reservation, revision, choice, retry):
        if choice is not None:
            reviewed = self.status(reservation)
            if reviewed.get('status') == 'waiting' and not reviewed.get('review'):
                raise HTTPException(409,'approval_view_unavailable')
        self.harness(reservation).resume(choice=choice, expected_revision=revision, retry_interrupted=retry)
        return self.status(reservation)

    def usage(self, reservation):
        self.check_scope(reservation)
        return public_usage(self.recorder.report(application_id='integration-lab', tenant_id=reservation['tenant_id'],
            billing_account_id=reservation['billing_account_id'], actor_id=reservation['actor_id'],
            request_id=reservation['run_id'], run_id=reservation['run_id']))

    async def admitted(self, function, *args):
        owner = args[0]
        key = (owner['tenant_id'],owner['actor_id']) if isinstance(owner,dict) else (owner.tenant_id,owner.actor_id)
        return await self.operations.run(function,*args,key=key)

    async def inspected(self, function, *args):
        return await self.reads.run(function,*args)

    def read(self, function, *args):
        return self.reads.run_sync(function,*args)
