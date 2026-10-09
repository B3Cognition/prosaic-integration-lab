from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import httpx
import psycopg
import pytest
from test_approval import headers,start
from test_accounting import count
from test_recovery import wait_for,fixture_identity

def scrape(lab,replica='a'):
    return httpx.get(lab[replica]+'/metrics',headers={'Authorization':'Bearer '+lab['metrics_token']},timeout=15)

def test_operator_auth_generated_correlation_and_safe_logs(lab):
    import subprocess,sys,os
    terminal=subprocess.run([sys.executable,'-m','lab_runner','metrics','--url',lab['a'],
        '--lab-http','--token-env','LAB_METRICS_TOKEN'],capture_output=True,text=True,timeout=15,
        env={**os.environ,'LAB_METRICS_TOKEN':lab['metrics_token']})
    assert terminal.returncode==0 and 'lab_readiness 1' in terminal.stdout
    assert lab['metrics_token'] not in terminal.stdout+terminal.stderr
    for replica in ('a','b'):
        assert httpx.get(lab[replica]+'/metrics',headers=headers(lab),timeout=5).status_code==401
        assert httpx.get(lab[replica]+'/metrics',timeout=5).status_code==401
        assert scrape(lab,replica).status_code==200
    run=start(lab,task='PRIVATE_OBSERVABILITY_TASK').json()
    response=httpx.get(lab['a']+'/runs/'+run['run_id'],headers={**headers(lab),'X-Request-ID':'PRIVATE_HEADER'},timeout=5)
    request_id=response.headers['x-request-id']
    assert re.fullmatch('[0-9a-f]{32}',request_id)
    manifest=fixture_identity(lab)
    # Application structured logs are on stderr; inspect both streams privately.
    import subprocess
    result=subprocess.run([manifest['engine'],'logs',manifest['replica_ids']['a']],capture_output=True,text=True,timeout=5)
    logs=result.stdout+result.stderr
    assert 'PRIVATE_OBSERVABILITY_TASK' not in logs and 'PRIVATE_HEADER' not in logs
    assert lab['metrics_token'] not in logs
    records=[]
    for line in logs.splitlines():
        try: record=json.loads(line)
        except ValueError: continue
        if record.get('event')=='request_finished' and record.get('request_id')==request_id: records.append(record)
    assert len(records)==1 and records[0]['run_id']==run['run_id']
    assert re.fullmatch('[0-9a-f]{16}',records[0]['tenant_ref'])
    assert records[0]['route']=='run_status'

def test_unknown_usage_observation_is_positive_and_call_refs_are_safe(lab):
    httpx.post(lab['model']+'/control',json={'scenario':'missing_usage'},timeout=5).raise_for_status()
    try: run=start(lab,workflow='synthetic').json()
    finally: httpx.post(lab['model']+'/control',json={'scenario':'normal'},timeout=5).raise_for_status()
    usage=httpx.get(lab['a']+'/runs/'+run['run_id']+'/usage',headers=headers(lab),timeout=10)
    assert usage.status_code==200 and usage.json()['unresolved_calls']==1
    response=scrape(lab)
    assert response.status_code==200
    value=re.search(r'lab_accounting_unknown_observations_total (\d+)',response.text)
    assert value and int(value.group(1))>=1
    assert all(value not in response.text for value in ('alice','tenant-a','account-a',run['run_id'],lab['metrics_token']))
    manifest=fixture_identity(lab)
    import subprocess
    result=subprocess.run([manifest['engine'],'logs',manifest['replica_ids']['a']],capture_output=True,text=True,timeout=5)
    records=[]
    for line in (result.stdout+result.stderr).splitlines():
        try: record=json.loads(line)
        except ValueError: continue
        if record.get('event')=='accounting_observed' and record.get('run_id')==run['run_id']: records.append(record)
    assert records and records[-1]['unknown_calls']==1
    assert len(records[-1]['call_refs'])==1 and re.fullmatch('[0-9a-f]{16}',records[-1]['call_refs'][0])

def test_write_saturation_visible_while_reads_remain_bounded_and_live(lab):
    before=count(lab)
    httpx.post(lab['model']+'/control',json={'blocked':True},timeout=5).raise_for_status()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(start,lab,actor,'synthetic') for actor in ('alice','bob')]
        try:
            wait_for(lambda:count(lab)==before+2,timeout=5)
            response=scrape(lab)
            assert response.status_code==200
            assert 'lab_admission_active{pool="writes"} 2' in response.text
            assert 'lab_reservation_phase{phase="starting"}' in response.text
            rejected=start(lab,'carol','synthetic')
            assert rejected.status_code==503
            assert count(lab)==before+2
            assert re.search(r'lab_admission_rejections_total\{pool="writes"\} [1-9]\d*',scrape(lab).text)
        finally: httpx.post(lab['model']+'/control',json={},timeout=5).raise_for_status()
        assert all(future.result(timeout=15).status_code==200 for future in futures)

def test_readiness_fault_is_curated_and_recovers_in_operator_scrape(lab):
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute('REVOKE INSERT ON prosaic_metering_intents FROM accounting_runtime')
    try:
        assert httpx.get(lab['a']+'/readyz',timeout=10).status_code==503
        response=scrape(lab)
        assert response.status_code==503 and response.json()=={'detail':'metrics_unavailable'}
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute('GRANT INSERT ON prosaic_metering_intents TO accounting_runtime')
    response=scrape(lab)
    assert response.status_code==200 and 'lab_readiness 1' in response.text
    assert re.search(r'lab_readiness_failures_total [1-9]\d*',response.text)

def test_real_owned_engine_fault_keeps_code_and_never_exports_stderr(lab):
    from lab_runner.stack import command,EngineError
    from lab_runner.manifest import validate_resource
    manifest=fixture_identity(lab)
    identifier=None
    for resource in manifest['resources']:
        if resource['kind']!='container': continue
        state=json.loads(command(manifest['engine'],'inspect',resource['id']))[0]
        if state['Name'].endswith('-model'):
            validate_resource(state,resource['id'],manifest['owner']); identifier=resource['id']; break
    assert identifier is not None
    with pytest.raises(EngineError) as caught:
        command(manifest['engine'],'exec',identifier,'python','-c',
            'import sys; sys.stderr.write("PRIVATE_ENGINE_DIAGNOSTIC"); raise SystemExit(17)')
    assert caught.value.diagnostic=={'operation':'exec','return_code':17,'category':'engine_failed','outcome':'unknown'}
    assert 'PRIVATE' not in str(caught.value) and 'PRIVATE' not in str(caught.value.diagnostic)
