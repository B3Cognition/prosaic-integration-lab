"""Real Lago quantities and fixture charges through public Prosaic APIs."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime,timezone
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
import httpx
import psycopg
import pytest
from prosaic_runtime_postgres import PostgresRecorder
from prosaic_integration_lab.billing_projection import project,account_scope,digest,DIMENSIONS
from prosaic_integration_lab.billing_scan import scan
from prosaic_integration_lab.billing_store import BillingStore
from prosaic_integration_lab.billing_delivery import LagoClient,deliver,DeliveryError
from prosaic_integration_lab.metadata import Metadata
from lab_runner.lago import seed,reconcile,endpoint,wait_ready
from lab_runner.stack import command
from lab_runner.manifest import validate_resource
from lab_runner.accounting_demo import capture_accounting


def setup(lab):
    store = BillingStore(lab['billing_dsn'])
    store.check_ready()
    metadata = Metadata(lab['billing_dsn'])
    mappings = seed(lab['lago'],metadata.billing_reservations(),store)
    factory = lambda namespace,environment: PostgresRecorder(lab['billing_dsn'],namespace=namespace,environment=environment)
    return store,metadata,mappings,factory


def drain(lab,store,scope=None):
    deadline = time.monotonic()+180
    store.check_ready()
    with httpx.Client() as http:
        client = LagoClient(lab['lago']['url'],lab['lago']['key'],http)
        while time.monotonic() < deadline:
            deliver(store,client,100,scope=scope)
            states = store.summary(scope)
            assert not states.get('failed') and not states.get('conflict')
            if not states.get('pending'): return
            time.sleep(0.2)
    pytest.fail('billing drain deadline')


def expected_from_ledger(metadata,factory,mappings):
    quantities = {}
    counts = {'all':0,'admissible':0,'excluded':0}
    for r in metadata.billing_reservations():
        key = (r['namespace'],r['environment'],r['tenant_id'],r['billing_account_id'])
        if key not in quantities: quantities[key] = dict.fromkeys(DIMENSIONS,0)
        recorder = factory(r['namespace'],r['environment'])
        filters = dict(application_id='integration-lab',tenant_id=r['tenant_id'],actor_id=r['actor_id'],
                       billing_account_id=r['billing_account_id'],request_id=r['run_id'],run_id=r['run_id'])
        calls = []
        for offset in range(0,10000,1000):
            page = recorder.calls(limit=1000,offset=offset,**filters)
            calls += page
            if len(page)<1000: break
        report = recorder.report(**filters)
        assert report['total_calls'] == len(calls)
        assert report['billing_eligible'] is False
        for call in calls:
            counts['all'] += 1
            u = (call['observation'] or {}).get('usage') or {}
            if call['measurement_state'] != 'complete' or u.get('cached_input_tokens') is None:
                counts['excluded'] += 1
                continue
            counts['admissible'] += 1
            quantities[key]['input_tokens'] += u['input_tokens']-u['cached_input_tokens']
            quantities[key]['cached_input_tokens'] += u['cached_input_tokens']
            quantities[key]['output_tokens'] += u['output_tokens']
    return quantities,counts


def test_multiuser_usage_replay_and_exact_charges(lab):
    report = capture_accounting(lab,lab['namespace'])
    assert report['independent_model_calls'] == 6
    for run in report['runs']:
        for call in run['calls']:
            if call['measurement_state'] == 'complete':
                assert (call['input_tokens'],call['cached_input_tokens'],call['output_tokens'],call['total_tokens']) == (100,20,25,125)
    store,metadata,mappings,factory = setup(lab)
    with ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda _:scan(metadata,factory,store,mappings),range(2)))
    drain(lab,store)
    quantities,counts = expected_from_ledger(metadata,factory,mappings)
    assert counts['excluded'] == 1
    assert sum(store.summary().values()) == 3*counts['admissible']
    evidence = []
    with httpx.Client() as http:
        client = LagoClient(lab['lago']['url'],lab['lago']['key'],http)
        for key,q in quantities.items():
            mapping = mappings[key]
            scope = digest(dict(namespace=key[0],environment=key[1],tenant_id=key[2],billing_account_id=key[3],application_id='integration-lab'))
            evidence.append(reconcile(lab['lago'],mapping,q))
            for row in store.events(scope): client.send(row['payload'])
            assert reconcile(lab['lago'],mapping,q) == evidence[-1]
    scan(metadata,factory,store,mappings)
    assert store.summary() == {'acknowledged':3*counts['admissible']}
    output = Path(lab['fixture_manifest']).parent/'billing.json'
    output.write_text(json.dumps(dict(counts=counts,usage=evidence,runtime_billing_eligible=False),indent=2))


def owned_lago(lab):
    cfg = lab['lago']
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    state = json.loads(command(cfg['engine'],'inspect',cfg['id']))[0]
    validate_resource(state,cfg['id'],manifest['owner'])
    return cfg


def test_lago_outage_retains_usage_and_recovers_without_model_retry(lab):
    cfg = owned_lago(lab)
    command(cfg['engine'],'stop',cfg['id'])
    try:
        # Existing subscriptions were provisioned by the earlier scenario.
        report = capture_accounting(lab,lab['namespace'])
        store = BillingStore(lab['billing_dsn'])
        metadata = Metadata(lab['billing_dsn'])
        mappings = {}
        for r in metadata.billing_reservations():
            key = (r['namespace'],r['environment'],r['tenant_id'],r['billing_account_id'])
            scope = digest(account_scope(r))
            mappings[key] = store.get_mapping(scope)
        factory = lambda namespace,environment:PostgresRecorder(lab['billing_dsn'],namespace=namespace,environment=environment)
        scan(metadata,factory,store,mappings)
        with httpx.Client() as http: deliver(store,LagoClient(cfg['url'],cfg['key'],http),limit=1)
        assert store.summary()['pending'] == 15
        before = httpx.get(lab['model']+'/stats').json()['calls']
    finally:
        command(cfg['engine'],'start',cfg['id'])
        cfg['url'] = endpoint(cfg['engine'],cfg['id'])
        wait_ready(cfg)
    drain(lab,BillingStore(lab['billing_dsn']))
    assert httpx.get(lab['model']+'/stats').json()['calls'] == before
    quantities,_ = expected_from_ledger(metadata,factory,mappings)
    for key,q in quantities.items(): reconcile(cfg,mappings[key],q)


def test_lost_ack_replays_identical_remote_event(lab):
    store,metadata,mappings,factory = setup(lab)
    # Generate new measured calls; deliberately send one without acknowledging it.
    capture_accounting(lab,lab['namespace'])
    scan(metadata,factory,store,mappings)
    row = store.claim(1,30)[0]
    with httpx.Client() as http:
        LagoClient(lab['lago']['url'],lab['lago']['key'],http).send(row['payload'])
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute("UPDATE lab_billing.events SET lease_until=clock_timestamp()-interval '1 second' WHERE key=%s",(row['key'],))
    recovered = BillingStore(lab['billing_dsn'])
    drain(lab,recovered)
    assert recovered.ack(row['key'],row['token']) is False
    quantities,_ = expected_from_ledger(metadata,factory,mappings)
    for key,q in quantities.items(): reconcile(lab['lago'],mappings[key],q)
    # Conflicting writes are rejected by Runtime; they do not silently replace
    # or quarantine the retained complete observation or mint a billing event.
    from prosaic_runtime import AccountingError
    recorder = PostgresRecorder(lab['accounting_dsn'],namespace=lab['namespace'],environment='sandbox')
    call = next(c for c in recorder.calls() if c['measurement_state']=='complete')
    changed = deepcopy(call['observation'])
    changed['usage']['output_tokens'] += 1
    changed['usage']['total_tokens'] += 1
    before_report = recorder.report()
    with pytest.raises(AccountingError):
        recorder.observe(call['intent']['provider_call_id'],changed)
    after_report = recorder.report()
    assert after_report['estimated_amounts'] == before_report['estimated_amounts']
    assert after_report['quarantined_calls'] == before_report['quarantined_calls']
    before_events = store.summary()
    scan(metadata,factory,store,mappings)
    assert store.summary() == before_events


def test_pagination_delayed_observation_and_exclusions(lab):
    store,metadata,mappings,factory = setup(lab)
    r = metadata.billing_reservations()[0]
    recorder = PostgresRecorder(lab['accounting_dsn'],namespace=r['namespace'],environment=r['environment'])
    original = recorder.calls(run_id=r['run_id'])[0]
    base = deepcopy(original['intent'])
    if original['measurement_state'] != 'complete':
        original = next(c for c in recorder.calls() if c['observation'] and c['measurement_state']=='complete')
    observation = deepcopy(original['observation'])
    now = datetime.now(timezone.utc).isoformat()
    base['started_at'] = now
    observation['finished_at'] = now
    ids = []
    prefix = 'pagination-'+uuid.uuid4().hex+'-'
    for i in range(1001):
        call_id = prefix+format(i,'04d')
        intent = {**base,'provider_call_id':call_id}
        recorder.prepare(intent)
        if i != 1000:
            recorder.observe(call_id,{**observation,'provider_call_id':call_id})
        ids.append(call_id)
    scan(metadata,factory,store,mappings)
    recorder.observe(ids[1000],{**observation,'provider_call_id':ids[1000]})
    scan(metadata,factory,store,mappings)
    # Immutable complete input/output with unknown cache is excluded.
    for name,status in [('unknown-cache','reported'),('quarantine','untrusted'),('unsupported','unsupported')]:
        call_id = name+'-'+uuid.uuid4().hex
        recorder.prepare({**base,'provider_call_id':call_id})
        obs = deepcopy(observation)
        obs['provider_call_id'] = call_id
        obs['usage']['status'] = status
        obs['usage']['cached_input_tokens'] = None
        recorder.observe(call_id,obs)
    scan(metadata,factory,store,mappings)
    reasons = [s['exclusion'] for s in store.sources()]
    assert 'unknown_cached_input' in reasons and 'quarantined' in reasons and 'unsupported' in reasons
    assert sum(s['exclusion'] is None for s in store.sources()) >= 1001
    drain(lab,store)
    quantities,counts = expected_from_ledger(metadata,factory,mappings)
    for key,q in quantities.items(): reconcile(lab['lago'],mappings[key],q)
    assert counts['admissible'] >= 1001
    assert store.summary() == {'acknowledged':3*counts['admissible']}


@pytest.mark.parametrize('stage',['before-send','after-send'])
def test_actual_exporter_process_crash_at_delivery_barrier(lab,stage,tmp_path):
    from prosaic_integration_lab.billing_exporter import tick
    # A finite batch of actual Harness calls supplies new delivery rows.
    capture_accounting(lab,lab['namespace'])
    store,metadata,mappings,factory = setup(lab)
    scan(metadata,factory,store,mappings)
    cfg = tmp_path/'exporter.json'
    # Exporter credentials are separate from replica, inference and owner keys.
    cfg.write_text(json.dumps({'billing_dsn':lab['billing_dsn'],'lago':lab['lago']}))
    cfg.chmod(0o600)
    barrier = tmp_path/'barrier'
    child = subprocess.Popen([sys.executable,'tests/fixtures/billing_worker.py',str(cfg),stage,str(barrier)],
        env={**os.environ,'PYTHONPATH':'src'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic()+15
        while not barrier.exists() and time.monotonic()<deadline:
            assert child.poll() is None
            time.sleep(0.02)
        assert barrier.exists()
    finally:
        if child.poll() is None: child.kill()
        child.wait(timeout=10)
    before = httpx.get(lab['model']+'/stats').json()['calls']
    # Wait through a real database lease, rather than modifying persisted state.
    deadline = time.monotonic()+15
    while time.monotonic()<deadline:
        r = subprocess.run([sys.executable,'-m','prosaic_integration_lab.billing_exporter','--config',str(cfg)],
            env={**os.environ,'PYTHONPATH':'src'},capture_output=True,text=True,timeout=30)
        assert r.returncode == 0
        if not store.summary().get('pending'): break
        time.sleep(0.2)
    assert not store.summary().get('pending')
    assert httpx.get(lab['model']+'/stats').json()['calls'] == before
    quantities,counts = expected_from_ledger(metadata,factory,mappings)
    assert store.summary() == {'acknowledged':3*counts['admissible']}
    for key,q in quantities.items(): reconcile(lab['lago'],mappings[key],q)


def test_same_account_name_in_distinct_tenants_and_known_zero_cache(lab):
    from prosaic_integration_lab.identity import Principal
    writer = Metadata(lab['app_dsn'])
    store,metadata,mappings,factory = setup(lab)
    template = next(c for c in factory(lab['namespace'],'sandbox').calls()
                    if c['measurement_state']=='complete')
    reservations = []
    cases = [('billing-tenant-one','same-actor',100,0,10),
             ('billing-tenant-two','same-actor',100,0,30),
             ('billing-rounding','rounding-actor',14,10,1)]
    for tenant,actor,inp,cached,output in cases:
        r = writer.reserve(Principal(tenant,actor,'same-account'),uuid.uuid4().hex,
            {'workflow':'synthetic','task':'Direct public-ledger billing fixture'},'a'*64,
            namespace=lab['namespace'],environment='sandbox')
        reservations.append(r)
        seed(lab['lago'],[r],store)
        context = deepcopy(template['intent']['context'])
        context.update(application_id='integration-lab',tenant_id=tenant,actor_id=actor,
            billing_account_id='same-account',request_id=r['run_id'],run_id=r['run_id'])
        now = datetime.now(timezone.utc).isoformat()
        call_id = 'isolation-'+uuid.uuid4().hex
        recorder = PostgresRecorder(lab['accounting_dsn'],namespace=lab['namespace'],environment='sandbox')
        recorder.prepare({**template['intent'],'provider_call_id':call_id,'context':context,'started_at':now})
        obs = deepcopy(template['observation'])
        obs.update(provider_call_id=call_id,finished_at=now)
        obs['usage'].update(input_tokens=inp,cached_input_tokens=cached,output_tokens=output,total_tokens=inp+output,
                            reasoning_output_tokens=min(5,output),status='reported')
        recorder.observe(call_id,obs)
    store,metadata,mappings,factory = setup(lab)
    scan(metadata,factory,store,mappings)
    for r,(_,_,inp,cached,output) in zip(reservations,cases):
        scope = digest(account_scope(r))
        drain(lab,store,scope)
        key = (r['namespace'],r['environment'],r['tenant_id'],r['billing_account_id'])
        evidence = reconcile(lab['lago'],mappings[key],dict(input_tokens=inp-cached,cached_input_tokens=cached,output_tokens=output))
        if cached:
            # 0.8c + 0.5c + 0.8c becomes three 1c charge lines, rather than
            # rounding their combined 2.1c once. Pins per-line half-up rounding.
            assert evidence['amount_cents'] == '3'
    assert mappings[(lab['namespace'],'sandbox','billing-tenant-one','same-account')]['subscription'] != mappings[(lab['namespace'],'sandbox','billing-tenant-two','same-account')]['subscription']


def test_out_of_period_evidence_is_not_sent_or_acknowledged(lab):
    from prosaic_integration_lab.identity import Principal
    writer = Metadata(lab['app_dsn'])
    r = writer.reserve(Principal('period-negative','actor','period-account'),uuid.uuid4().hex,
        {'workflow':'synthetic','task':'Direct period-negative ledger fixture'},'a'*64,
        namespace=lab['namespace'],environment='sandbox')
    store,metadata,mappings,factory = setup(lab)
    key = (r['namespace'],r['environment'],r['tenant_id'],r['billing_account_id'])
    mapping = mappings[key]
    template = next(c for c in factory(lab['namespace'],'sandbox').calls() if c['measurement_state']=='complete')
    from prosaic_integration_lab.billing_delivery import timestamp
    when = datetime.fromtimestamp(float(timestamp(mapping['period_from']))-60,timezone.utc).isoformat()
    call_id = 'out-of-period-'+uuid.uuid4().hex
    context = {**template['intent']['context'],**{k:r[k] for k in ('tenant_id','actor_id','billing_account_id')},
               'request_id':r['run_id'],'run_id':r['run_id']}
    recorder = PostgresRecorder(lab['accounting_dsn'],namespace=lab['namespace'],environment='sandbox')
    recorder.prepare({**template['intent'],'provider_call_id':call_id,'context':context,'started_at':when})
    recorder.observe(call_id,{**template['observation'],'provider_call_id':call_id,'finished_at':when})
    scan(metadata,factory,store,mappings)
    scope = digest(account_scope(r))
    with httpx.Client() as http:
        client = LagoClient(lab['lago']['url'],lab['lago']['key'],http)
        deliver(store,client,scope=scope)
        rows = store.events(scope)
        assert all(row['state'] != 'acknowledged' for row in rows)
        assert any(row['category']=='period' for row in rows)
        assert store.claim(3,30,scope=scope) == []
        for row in rows:
            response = client.request('GET','/events/'+row['key'],params={'external_subscription_id':mapping['subscription']})
            assert response.status_code == 404
    reconcile(lab['lago'],mapping,dict.fromkeys(DIMENSIONS,0))
