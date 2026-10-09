import json
import socket
import ssl
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit
import httpx
import pytest
from test_approval import headers
from test_accounting import count

@pytest.fixture
def gateway(lab):
    with httpx.Client(base_url=lab['ingress']['url'],
        verify=ssl.create_default_context(cafile=lab['ingress']['ca_file']),
        trust_env=False,timeout=15) as client:
        yield client

def test_tls_nonsticky_owner_review_and_original_billing_scope(lab,gateway):
    with httpx.Client(trust_env=False,timeout=3) as untrusted:
        with pytest.raises(httpx.ConnectError):
            untrusted.get(lab['ingress']['url']+'/readyz')
    seen = {gateway.get('/readyz').headers['x-lab-upstream'] for _ in range(6)}
    assert len(seen) == 2
    before = count(lab)
    key = uuid.uuid4().hex
    auth = {**headers(lab),'Idempotency-Key':key,'X-Tenant-ID':'SPOOF',
        'X-Actor-ID':'bob','X-Billing-Account-ID':'SPOOF','Forwarded':'for=evil'}
    run = gateway.post('/runs',headers=auth,json={'workflow':'synthetic','task':'private'}).json()
    path = '/runs/'+run['run_id']
    assert gateway.get(path,headers=headers(lab,'bob')).status_code == 404
    review = gateway.get(path,headers=headers(lab)).json()
    assert review['review']['revision'] == run['revision']
    assert gateway.post(path+'/resume',headers=headers(lab),json={
        'choice':'approve','expected_revision':review['revision']}).json()['status'] == 'completed'
    assert gateway.post('/runs',headers=auth,json={'workflow':'synthetic','task':'private'}).json()['run_id'] == run['run_id']
    assert count(lab) == before+1
    from prosaic_runtime_postgres import PostgresRecorder
    ledger = PostgresRecorder(lab['accounting_dsn'],namespace=lab['namespace'],environment=lab['environment'])
    context = ledger.calls(run_id=run['run_id'])[0]['intent']['context']
    assert (context['tenant_id'],context['actor_id'],context['billing_account_id']) == ('tenant-a','alice','account-a')

def test_initial_header_deadline_and_body_limit_no_dispatch(lab,gateway):
    before = count(lab)
    url = urlsplit(lab['ingress']['url'])
    context = ssl.create_default_context(cafile=lab['ingress']['ca_file'])
    with context.wrap_socket(socket.create_connection((url.hostname,url.port),timeout=5),server_hostname=url.hostname) as conn:
        conn.settimeout(5)
        conn.sendall(b'POST /runs HTTP/1.1\r\nHost: localhost\r\nX-Slow: ')
        started = time.monotonic()
        result = conn.recv(4096)
        assert b'408' in result or result == b''
        assert time.monotonic()-started < 4
    assert gateway.post('/runs',headers=headers(lab),content=b'x'*9000).status_code == 413
    assert gateway.post('/runs',content=b'PRIVATE').status_code == 401
    assert count(lab) == before

def test_lost_client_reply_reinspection_and_same_key_do_not_redispatch(lab,gateway):
    from test_recovery import wait_for
    before = count(lab)
    url = urlsplit(lab['ingress']['url'])
    context = ssl.create_default_context(cafile=lab['ingress']['ca_file'])
    key = uuid.uuid4().hex
    body = json.dumps({'workflow':'synthetic','task':'lost-reply'}).encode()
    token = headers(lab)['Authorization']
    httpx.post(lab['model']+'/control',json={'blocked':True},timeout=5).raise_for_status()
    try:
        with context.wrap_socket(socket.create_connection((url.hostname,url.port),timeout=5),server_hostname=url.hostname) as conn:
            request = (f'POST /runs HTTP/1.1\r\nHost: localhost\r\nAuthorization: {token}\r\n'
                f'Idempotency-Key: {key}\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n').encode()+body
            conn.sendall(request)
            wait_for(lambda:count(lab) == before+1,timeout=5)
            # Dispatch count is not completion. Drop the reply while work is held.
        import psycopg
        with psycopg.connect(lab['app_dsn']) as connection:
            run_id=connection.execute('SELECT run_id FROM lab_app.runs WHERE actor_id=%s AND idempotency_key=%s',
                ('alice',key)).fetchone()[0]
        response = gateway.post('/runs',headers={**headers(lab),'Idempotency-Key':key},
            json={'workflow':'synthetic','task':'lost-reply'})
        assert response.status_code in {200,503}
        if response.status_code==200:
            assert response.json()['run_id']==run_id
            assert response.json()['status'] in {'running','start_uncertain'}
        else:
            assert response.json()=={'detail':'capacity_exhausted'}
        assert count(lab)==before+1
    finally:
        httpx.post(lab['model']+'/control',json={},timeout=5).raise_for_status()
    wait_for(lambda:gateway.get('/runs/'+run_id,headers=headers(lab)).json().get('status')=='waiting',timeout=10)
    recovered=gateway.post('/runs',headers={**headers(lab),'Idempotency-Key':key},
        json={'workflow':'synthetic','task':'lost-reply'})
    assert recovered.status_code==200
    assert recovered.json()['run_id']==run_id and recovered.json()['status']=='waiting'
    assert count(lab) == before+1

def test_replica_sigterm_drains_inflight_dispatch_without_duplicate(lab,gateway):
    from concurrent.futures import ThreadPoolExecutor
    from lab_runner.stack import command
    from lab_runner.manifest import validate_resource
    from test_recovery import wait_for,mutate_replica
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    before = count(lab)
    key = uuid.uuid4().hex
    httpx.post(lab['model']+'/control',json={'blocked':True},timeout=5).raise_for_status()
    def submit():
        with httpx.Client(base_url=lab['ingress']['url'],verify=ssl.create_default_context(
            cafile=lab['ingress']['ca_file']),trust_env=False,timeout=15) as client:
            return client.post('/runs',headers={**headers(lab),'Idempotency-Key':key},
                json={'workflow':'synthetic','task':'inflight-drain'})
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(submit)
        try:
            wait_for(lambda:count(lab) == before+1,timeout=5)
            # Both workers receive drain; only one has this accepted dispatch.
            for name in ('a','b'):
                identifier = manifest['replica_ids'][name]
                state = json.loads(command(manifest['engine'],'inspect',identifier))[0]
                validate_resource(state,identifier,manifest['owner'])
                command(manifest['engine'],'kill','--signal=TERM',identifier)
        finally:
            httpx.post(lab['model']+'/control',json={},timeout=5).raise_for_status()
        response = future.result(timeout=15)
    assert response.status_code == 200
    assert response.json()['status'] == 'waiting'
    for name in ('a','b'):
        identifier = manifest['replica_ids'][name]
        wait_for(lambda:not json.loads(command(manifest['engine'],'inspect',identifier))[0]['State']['Running'],timeout=15)
        mutate_replica(lab,'start',name)
        wait_for(lambda:httpx.get(lab[name]+'/readyz',timeout=2).status_code == 200,timeout=15)
    repeated = gateway.post('/runs',headers={**headers(lab),'Idempotency-Key':key},
        json={'workflow':'synthetic','task':'inflight-drain'})
    assert repeated.status_code == 200
    assert repeated.json()['run_id'] == response.json()['run_id']
    assert count(lab) == before+1

def test_gateway_graceful_drain_preserves_waiting_run(lab,gateway):
    from concurrent.futures import ThreadPoolExecutor
    from lab_runner.stack import command
    from lab_runner.manifest import validate_resource
    from test_recovery import wait_for
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    identifier = manifest['ingress_id']
    state = json.loads(command(manifest['engine'],'inspect',identifier))[0]
    validate_resource(state,identifier,manifest['owner'])
    before = count(lab)
    httpx.post(lab['model']+'/control',json={'blocked':True},timeout=5).raise_for_status()
    def submit():
        with httpx.Client(base_url=lab['ingress']['url'],verify=ssl.create_default_context(
            cafile=lab['ingress']['ca_file']),trust_env=False,timeout=15) as client:
            return client.post('/runs',headers={**headers(lab),'Idempotency-Key':uuid.uuid4().hex},
                json={'workflow':'synthetic','task':'gateway-drain'})
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(submit)
        try:
            wait_for(lambda:count(lab) == before+1,timeout=5)
            command(manifest['engine'],'kill','--signal=QUIT',identifier)
            assert json.loads(command(manifest['engine'],'inspect',identifier))[0]['State']['Running']
        finally:
            httpx.post(lab['model']+'/control',json={},timeout=5).raise_for_status()
        completed = future.result(timeout=15)
    assert completed.status_code == 200
    run = completed.json()
    assert run['status'] == 'waiting'
    assert count(lab) == before+1
    deadline = time.monotonic()+20
    while json.loads(command(manifest['engine'],'inspect',identifier))[0]['State']['Running']:
        assert time.monotonic() < deadline
        time.sleep(.1)
    response = httpx.get(lab['b']+'/runs/'+run['run_id'],headers=headers(lab),timeout=5)
    assert response.json()['revision'] == run['revision']
    assert response.json()['status'] == 'waiting'
