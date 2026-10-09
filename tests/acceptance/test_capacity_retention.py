from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
import httpx
import psycopg
from test_approval import start,headers
from test_accounting import count
from test_scope import deliver_owned_config
from test_recovery import mutate_replica,wait_for,fixture_identity

def rows(lab):
    with psycopg.connect(lab['migration_dsn']) as conn:
        return conn.execute('SELECT count(*) FROM lab_app.runs').fetchone()[0]

@contextmanager
def configured(lab,capacity):
    source=Path(lab['fixture_manifest']).parent/'secrets/service.json'
    original=source.read_text(); config=json.loads(original); config['capacity']=capacity
    def restart():
        deliver_owned_config(lab)
        for replica in ('a','b'):
            mutate_replica(lab,'kill',replica); mutate_replica(lab,'start',replica)
            wait_for(lambda:httpx.get(lab[replica]+'/readyz',timeout=2).status_code==200)
    try:
        source.write_text(json.dumps(config)); restart(); yield
    finally: source.write_text(original); restart()

def test_configured_tenant_quota_leaves_other_tenant_capacity(lab):
    with configured(lab,{'writes':2,'per_tenant':1}):
        before=count(lab)
        httpx.post(lab['model']+'/control',json={'blocked':True},timeout=5).raise_for_status()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first=pool.submit(start,lab,'alice','synthetic')
            try:
                wait_for(lambda:count(lab)==before+1,timeout=5)
                rejected=start(lab,'bob','synthetic')
                assert rejected.status_code==503 and rejected.json()['detail']=='capacity_exhausted'
                second=pool.submit(start,lab,'carol','synthetic')
                wait_for(lambda:count(lab)==before+2,timeout=5)
                assert httpx.get(lab['a']+'/healthz',timeout=3).status_code==200
            finally: httpx.post(lab['model']+'/control',json={},timeout=5).raise_for_status()
            assert first.result(timeout=15).status_code==200
            assert second.result(timeout=15).status_code==200
        assert count(lab)==before+2

def test_atomic_cross_replica_record_ceiling_preserves_existing_idempotency(lab):
    ceiling=rows(lab)+1; before=count(lab); keys=[uuid.uuid4().hex,uuid.uuid4().hex]
    with configured(lab,{'max_runs':ceiling}):
        def submit(index):
            local={**lab,'a':lab['a' if index==0 else 'b']}
            return start(local,'alice' if index==0 else 'carol',key=keys[index])
        with ThreadPoolExecutor(max_workers=2) as pool: responses=list(pool.map(submit,(0,1)))
        assert sorted(response.status_code for response in responses)==[200,503]
        rejected=next(response for response in responses if response.status_code==503)
        assert rejected.json()['detail']=='retention_capacity_exhausted'
        assert rows(lab)==ceiling
        winner=next(index for index,response in enumerate(responses) if response.status_code==200)
        repeated=start(lab,'alice' if winner==0 else 'carol',key=keys[winner])
        assert repeated.status_code==200 and repeated.json()['run_id']==responses[winner].json()['run_id']
        assert count(lab)==before

def test_advisory_lock_pressure_is_bounded_without_new_reservation(lab):
    from prosaic_integration_lab.metadata import RESERVATION_LOCK_ID
    before=rows(lab); calls=count(lab); key=uuid.uuid4().hex
    with psycopg.connect(lab['migration_dsn']) as connection:
        connection.execute('SELECT pg_advisory_lock(%s::bigint)',(RESERVATION_LOCK_ID,))
        try:
            began=time.monotonic(); response=start(lab,key=key,task='PRIVATE_LOCK_PRESSURE')
            assert response.status_code==503 and time.monotonic()-began<3
            assert 'PRIVATE' not in response.text
            assert rows(lab)==before and count(lab)==calls
            assert httpx.get(lab['a']+'/healthz',timeout=3).status_code==200
        finally: connection.execute('SELECT pg_advisory_unlock(%s::bigint)',(RESERVATION_LOCK_ID,))
    assert start(lab,key=key,task='PRIVATE_LOCK_PRESSURE').status_code==200

def test_application_connection_pressure_fails_closed_and_recovers(lab):
    from lab_runner.stack import command
    from lab_runner.manifest import validate_resource
    manifest=fixture_identity(lab); identifier=manifest['database_id']
    validate_resource(json.loads(command(manifest['engine'],'inspect',identifier))[0],identifier,manifest['owner'])
    def limit(value): command(manifest['engine'],'exec',identifier,'psql','-U','postgres','-d','lab',
        '-v','ON_ERROR_STOP=1','-c',f'ALTER ROLE app_runtime CONNECTION LIMIT {value}')
    before=rows(lab); calls=count(lab)
    limit(1)
    try:
        with psycopg.connect(lab['app_dsn']) as held:
            assert held.execute('SELECT 1').fetchone()==(1,)
            began=time.monotonic(); response=start(lab,task='PRIVATE_CONNECTION_PRESSURE')
            assert response.status_code==503 and time.monotonic()-began<8
            assert 'PRIVATE' not in response.text
            assert rows(lab)==before and count(lab)==calls
            assert httpx.get(lab['a']+'/healthz',timeout=3).status_code==200
    finally: limit(-1)
    assert httpx.get(lab['a']+'/readyz',timeout=8).status_code==200

def test_private_archive_preserves_unknown_uncertain_and_original_keys_without_dispatch(lab):
    key=uuid.uuid4().hex; run=start(lab,key=key,task='PRIVATE_ARCHIVE_TASK').json()
    completed=httpx.post(lab['b']+'/runs/'+run['run_id']+'/resume',headers=headers(lab),
        json={'choice':'approve','expected_revision':run['revision']},timeout=10)
    assert completed.json()['status']=='completed'
    from prosaic_integration_lab.metadata import Metadata
    from prosaic_integration_lab.identity import Principal
    from prosaic_integration_lab.config import assets_hash
    from lab_runner.stack import ROOT
    Metadata(lab['app_dsn']).reserve(Principal('tenant-a','alice','account-a'),uuid.uuid4().hex,
        {'workflow':'synthetic','task':'PRIVATE_UNCERTAIN_ARCHIVE'},assets_hash(ROOT/'assets'),
        namespace=lab['namespace'],environment=lab['environment'])
    httpx.post(lab['model']+'/control',json={'scenario':'missing_usage'},timeout=5).raise_for_status()
    try: unknown=start(lab,workflow='synthetic').json()
    finally: httpx.post(lab['model']+'/control',json={'scenario':'normal'},timeout=5).raise_for_status()
    before=rows(lab); calls=count(lab)
    destination=Path(lab['fixture_manifest']).parent/('archive-'+uuid.uuid4().hex)
    source=Path(lab['fixture_manifest']).parent/'secrets/host.json'
    result=subprocess.run([sys.executable,'-m','lab_runner','retention','--config',str(source),
        '--archive','--destination',str(destination)],capture_output=True,text=True,timeout=60)
    assert result.returncode==0
    summary=json.loads(result.stdout)
    assert summary['deletion_allowed'] is False and summary['point_in_time_backup'] is False
    assert summary['archive_complete'] is True and summary['retain_uncertain']>=1 and summary['retain_unresolved']>=1
    assert summary['terminal_copy']>=1 and 'PRIVATE' not in result.stdout+result.stderr
    assert destination.stat().st_mode & 0o777==0o700
    archive=destination/'records.jsonl'
    assert archive.stat().st_mode & 0o777==0o600
    assert 'PRIVATE_ARCHIVE_TASK' in archive.read_text() and 'PRIVATE_UNCERTAIN_ARCHIVE' in archive.read_text()
    assert rows(lab)==before and count(lab)==calls
    assert start(lab,key=key,task='PRIVATE_ARCHIVE_TASK').json()['run_id']==run['run_id']
    usage=httpx.get(lab['b']+'/runs/'+unknown['run_id']+'/usage',headers=headers(lab),timeout=10).json()
    assert usage['unresolved_calls']==1 and usage['billing_eligible'] is False

def test_finite_arrival_profile_has_measurable_slo_and_reconciled_dispatch(lab):
    from lab_runner.load_profile import run
    from lab_runner.workload import Events
    directory=Path(lab['fixture_manifest']).parent/('profile-'+uuid.uuid4().hex); directory.mkdir(mode=0o700)
    result=run(lab,3,4,1,2,Events(directory))
    assert result['passed'] is True and result['slo_passed'] is True
    assert result['independent_model_calls']==result['accepted']==result['completed']==4
    assert result['client_shed']==0 and result['errors']==0 and result['billing_eligible'] is False
    assert all(item['completed']>=1 for item in result['per_user'].values())
    (directory/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
