import json
import os
import subprocess
import sys
import time
import uuid
import httpx
import psycopg
from pathlib import Path
from lab_runner.manifest import validate_resource
from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.metadata import Metadata
from test_approval import headers,start
from test_accounting import count
from test_recovery import crash_during

def terminal(lab,run_id,action='inspect',revision=None,actor='alice',ack=False):
    arguments = [sys.executable,'-m','lab_runner','recover','--url',lab['b'],'--lab-http',
        '--run-id',run_id,'--action',action,'--token-env','LAB_RECOVERY_TOKEN']
    if revision: arguments += ['--expected-revision',revision]
    if ack: arguments += ['--acknowledge-effect-risk']
    response = subprocess.run(arguments,env={**os.environ,'LAB_RECOVERY_TOKEN':headers(lab,actor)['Authorization'][7:]},
        capture_output=True,text=True,timeout=20)
    assert response.stderr == ''
    return response.returncode,json.loads(response.stdout)

def test_terminal_owner_review_approval_and_stale_action_without_inference(lab):
    run = start(lab,workflow='synthetic').json()
    before = count(lab)
    code,report = terminal(lab,run['run_id'])
    assert code == 0 and report['run']['review']['revision'] == run['revision']
    assert report['usage']['complete_calls'] == 1
    denied,report = terminal(lab,run['run_id'],actor='bob')
    assert denied == 1 and report['reason'] == 'http_404'
    stale,report = terminal(lab,run['run_id'],'approve','stale')
    assert stale == 1 and report['reason'] == 'revision_conflict'
    approved,report = terminal(lab,run['run_id'],'approve',run['revision'])
    assert approved == 0 and report['run']['status'] == 'completed'
    assert count(lab) == before

def test_terminal_unknown_usage_and_uncertain_start_do_not_authorize_retry(lab):
    httpx.post(lab['model']+'/control',json={'scenario':'missing_usage'},timeout=5).raise_for_status()
    try:
        unknown = start(lab,workflow='synthetic').json()
    finally:
        httpx.post(lab['model']+'/control',json={'scenario':'normal'},timeout=5).raise_for_status()
    code,report = terminal(lab,unknown['run_id'])
    assert code == 0 and report['usage']['unresolved_calls'] == 1
    assert report['usage']['fully_costed'] is False
    metadata = Metadata(lab['app_dsn'])
    principal = Principal('tenant-a','alice','account-a')
    row = metadata.owned(principal,unknown['run_id'])
    uncertain = metadata.reserve(principal,uuid.uuid4().hex,{'workflow':'synthetic','task':'uncertain'},
        row['assets_hash'],namespace=lab['namespace'],environment=lab['environment'])
    metadata.claim_start(uncertain['run_id'])
    before = count(lab)
    code,report = terminal(lab,uncertain['run_id'])
    assert code == 0 and report['run']['status'] == 'start_uncertain'
    refused,report = terminal(lab,uncertain['run_id'],'retry','unavailable',ack=True)
    assert refused == 1 and report['reason'] == 'operator_reconciliation_required'
    assert count(lab) == before

def test_terminal_receipt_crash_recovery_has_no_blind_mutation_retry_or_new_call(lab):
    before = count(lab)
    accepted = httpx.get(lab['model']+'/stats',timeout=5).json()['accepted_events']
    run_id = crash_during(lab,{'accepted_gate':True},
        lambda:httpx.get(lab['model']+'/stats',timeout=5).json()['accepted_events'] > accepted)
    code,report = terminal(lab,run_id)
    assert code == 0 and report['run']['status'] == 'running'
    # Deliberate operator wait for lease expiry, followed by one explicit action.
    time.sleep(16)
    resumed,report = terminal(lab,run_id,'resume',report['run']['revision'])
    assert resumed == 0 and report['run']['status'] == 'waiting'
    assert report['usage']['complete_calls'] == 1
    assert count(lab) == before+1

def test_database_failure_details_never_reach_public_response_or_server_traceback(lab):
    before = count(lab)
    sentinel = 'PRIVATE_DB_FAILURE_DETAIL_SENTINEL'
    with psycopg.connect(lab['migration_dsn']) as connection:
        connection.execute('ALTER TABLE lab_app.runs ADD CONSTRAINT owned_failure_probe CHECK (false) NOT VALID')
    try:
        response = start(lab,workflow='synthetic',task=sentinel)
        assert response.status_code == 503
        assert response.json() == {'detail':'service_unavailable'}
        assert count(lab) == before
        manifest = json.loads(Path(lab['fixture_manifest']).read_text())
        identifier = manifest['replica_ids']['a']
        inspected = subprocess.run([manifest['engine'],'inspect',identifier],capture_output=True,text=True)
        assert inspected.returncode == 0
        validate_resource(json.loads(inspected.stdout)[0],identifier,manifest['owner'])
        logs = subprocess.run([manifest['engine'],'logs',identifier],capture_output=True,text=True)
        assert logs.returncode == 0
        assert sentinel not in logs.stdout+logs.stderr
        assert 'http_dispatch' in logs.stderr+logs.stdout
    finally:
        with psycopg.connect(lab['migration_dsn']) as connection:
            connection.execute('ALTER TABLE lab_app.runs DROP CONSTRAINT owned_failure_probe')
