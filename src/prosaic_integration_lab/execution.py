"""Bounded SDK execution; never redispatch uncertain starts."""
from pathlib import Path
import math
from fastapi import HTTPException
from prosaic_harness import Harness, RunNotFound, Workflow
from prosaic_harness_postgres import PostgresRunStore
from prosaic_runtime import ExecutionContext, RateCard, ProsaicRuntime
from prosaic_runtime_postgres import PostgresRecorder
from .config import assets_hash
from .metadata import Metadata
from .views import public_run, public_usage, uncertain_run
from .admission import Admission
from .diagnostics import stage
from .observability import bind_run,accounting_observation,workflow_observation
from .capacity import policy

def validate_workflow_limits(definition):
    limits = definition.get('limits',{})
    for name,maximum in (('max_calls',3),('max_tokens',4096)):
        value = limits.get(name)
        if type(value) is not int or not 1 <= value <= maximum:
            raise ValueError('finite service execution policy is required')
    duration = limits.get('max_run_s')
    if type(duration) not in {float,int} or not math.isfinite(duration) or not 0 < duration <= 120:
        raise ValueError('finite service execution duration is required')

def retained_workflows(config):
    retained={}
    for identity,definition in config.get('legacy_bundles',{}).items():
        if (type(definition) is not dict or set(definition)!={'assets'} or
                type(identity) is not str or assets_hash(definition['assets'])!=identity):
            raise ValueError('retained legacy assets conflict')
        workflows={name:Workflow.load(Path(definition['assets'])/(name+'.yml'))
                   for name in ('approval','synthetic')}
        for workflow in workflows.values():validate_workflow_limits(workflow.definition)
        retained[identity]=workflows
    return retained

class Execution:
    def __init__(self, config, *, metrics=None):
        self.config = config
        self.capacity=policy(config.get('capacity',{}))
        self.fingerprint = assets_hash(config['assets'])
        self.workflows = {name: Workflow.load(Path(config['assets']) / (name + '.yml')) for name in ('approval', 'synthetic')}
        for workflow in self.workflows.values():
            validate_workflow_limits(workflow.definition)
        self.legacy_bundles=retained_workflows(config)
        self.metadata = Metadata(config['app_dsn'])
        self.store = PostgresRunStore(config['harness_dsn'], namespace=config['namespace'], max_active_leases=2,
            lease_s=15, renew_s=3, operation_timeout_s=5, pool_timeout_s=2, connect_timeout_s=3,
            lock_timeout_s=1, statement_timeout_s=3)
        self.recorder = PostgresRecorder(config['accounting_dsn'], namespace=config['namespace'],
            environment=config['environment'], rate_card=RateCard('synthetic-v1', 'test-model', '2', '8', '0.5'))
        self.operations = Admission(self.capacity['writes'],metrics=metrics,per_tenant=self.capacity['per_tenant'])
        self.reads = Admission(self.capacity['reads'],metrics=metrics,pool_name='reads')
        self.observer = (workflow_observation if metrics is not None and
            'observer_v1' in getattr(ProsaicRuntime,'capabilities',()) else None)
        self.native = None
        if config.get('native'):
            from .native_execution import NativeExecution
            self.native = NativeExecution(self)

    def ready(self):
        self.metadata.check_ready()
        self.store.check_ready()
        self.recorder.check_ready()

    def close(self):
        self.operations.close()
        self.reads.close()
        self.store.close()

    def harness(self, reservation):
        if reservation['workflow'] == 'native':
            return self.native.harness(reservation)
        self.check_scope(reservation)
        workflows=self.workflows if reservation['assets_hash']==self.fingerprint else self.legacy_bundles.get(reservation['assets_hash'])
        if workflows is None:raise HTTPException(409, 'asset_conflict')
        context = ExecutionContext(application_id='integration-lab', tenant_id=reservation['tenant_id'],
            actor_id=reservation['actor_id'], billing_account_id=reservation['billing_account_id'], request_id=reservation['run_id'])
        return Harness(workflows[reservation['workflow']], store=self.store,
                       run_id=reservation['run_id'], context=context, accounting=self.recorder,
                       **({'observer':self.observer} if self.observer is not None else {}),
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
        bind_run(reservation)
        if reservation['workflow'] == 'native': return self.native.status(reservation)
        try:
            snapshot = self.harness(reservation).status()
        except RunNotFound:
            return uncertain_run(reservation['run_id'])
        return public_run(reservation['run_id'], snapshot.state, snapshot.revision,workflow=reservation['workflow'])

    def start(self, reservation):
        bind_run(reservation)
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
                namespace=self.config['namespace'],environment=self.config['environment'],
                max_runs=self.capacity['max_runs'],max_tenant_runs=self.capacity['max_tenant_runs'])
        if reservation['phase'] != 'reserved':
            return self.status(reservation)
        return self.start(reservation)

    def resume(self, reservation, revision, choice, retry, response=None):
        bind_run(reservation)
        if reservation.get('workflow') == 'native':
            return self.native.resume(reservation,revision,choice,response,retry)
        if choice not in (None,'approve','reject') or response is not None:
            raise ValueError('invalid_request')
        if choice is not None:
            reviewed = self.status(reservation)
            if reviewed.get('status') == 'waiting' and not reviewed.get('review'):
                raise HTTPException(409,'approval_view_unavailable')
        self.harness(reservation).resume(choice=choice, expected_revision=revision, retry_interrupted=retry)
        return self.status(reservation)

    def usage(self, reservation):
        bind_run(reservation)
        self.check_scope(reservation)
        report=self.recorder.report(application_id='integration-lab', tenant_id=reservation['tenant_id'],
            billing_account_id=reservation['billing_account_id'], actor_id=reservation['actor_id'],
            request_id=reservation['run_id'], run_id=reservation['run_id'])
        calls=self.recorder.calls(run_id=reservation['run_id'])
        accounting_observation(report,calls)
        return public_usage(report)

    async def admitted(self, function, *args):
        owner = args[0]
        key = (owner['tenant_id'],owner['actor_id']) if isinstance(owner,dict) else (owner.tenant_id,owner.actor_id)
        return await self.operations.run(function,*args,key=key)

    async def inspected(self, function, *args):
        return await self.reads.run(function,*args)

    def read(self, function, *args):
        return self.reads.run_sync(function,*args)
