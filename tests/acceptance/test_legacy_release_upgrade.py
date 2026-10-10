"""Recover actual immutable Lab 0.2.0 evidence with a fresh SDK/image/schema."""
import json
from pathlib import Path

import httpx
import psycopg
import pytest

from lab_runner.legacy_upgrade import BASELINE_COMMIT,BASELINE_SHA256,snapshot
from lab_runner.native_scenarios import calls,replace_worker
from lab_runner.accounting_report import accounting_snapshot
from prosaic_integration_lab.migrations import migrate
from test_approval import headers
from test_recovery import wait_for


@pytest.fixture
def historical(lab):
    if not lab.get('legacy_fixture'):pytest.fail('actual historical release fixture is required')
    fixture=json.loads(Path(lab['legacy_fixture']).read_text())
    assert fixture['baseline_source']==BASELINE_COMMIT and fixture['baseline_manifest_sha256']==BASELINE_SHA256
    return fixture


def item(fixture,case):return next(row for row in fixture['runs'] if row['case']==case)


def view(lab,row):
    result=httpx.get(lab['b']+'/runs/'+row['view']['run_id'],headers=headers(lab),timeout=5)
    result.raise_for_status();return result.json()


def resume(lab,row,**extra):
    def attempt():
        current=view(lab,row)
        result=httpx.post(lab['b']+'/runs/'+current['run_id']+'/resume',headers=headers(lab),
            json={'expected_revision':current['revision'],**extra},timeout=20)
        if result.status_code==409:
            assert result.json()['detail']=='run_busy';return None
        result.raise_for_status();return result.json()
    return wait_for(attempt,timeout=40)


def usage(lab,row):
    result=httpx.get(lab['b']+'/runs/'+row['view']['run_id']+'/usage',headers=headers(lab),timeout=5)
    result.raise_for_status();return result.json()


def test_actual_baseline_generated_all_five_states_before_schema_upgrade(lab,historical):
    assert len(historical['runs'])==5 and historical['call_delta']==4
    assert historical['before_recovery']==historical['original']
    assert historical['migration']=='v2-to-v3'
    assert len(historical['original']['receipts'])==3
    assert len(historical['original']['intents'])==4


def test_original_approval_revision_owner_and_zero_model_calls(lab,historical):
    row=item(historical,'approval');before=calls(lab)
    assert view(lab,row)['revision']==row['view']['revision']
    assert resume(lab,row,choice='approve')['status']=='completed'
    assert usage(lab,row)['total_calls']==0 and calls(lab)==before


def test_original_synthetic_waiting_recovers_exact_frozen_accounting(lab,historical):
    row=item(historical,'synthetic');before=calls(lab);original=usage(lab,row)
    assert original['total_calls']==1 and original['complete_calls']==1
    assert resume(lab,row,choice='approve')['status']=='completed'
    assert accounting_snapshot(usage(lab,row))==accounting_snapshot(original) and calls(lab)==before


def test_original_saved_receipt_adopted_by_fresh_worker_without_inference_or_new_receipt(lab,historical):
    row=item(historical,'saved-receipt');before=calls(lab)
    result=resume(lab,row)
    assert result['status']=='waiting'
    assert usage(lab,row)['complete_calls']==1
    assert resume(lab,row,choice='approve')['status']=='completed'
    assert calls(lab)==before
    with psycopg.connect(lab['migration_dsn']) as connection:
        assert connection.execute('SELECT count(*) FROM prosaic_harness.receipts WHERE run_id=%s',(row['view']['run_id'],)).fetchone()==(1,)


def test_original_missing_usage_stays_unknown_after_approval(lab,historical):
    row=item(historical,'unknown-usage');before=calls(lab)
    original_view=view(lab,row)
    assert original_view['status']=='blocked'
    assert original_view['recovery_status']=='usage_reconciliation_required'
    assert original_view['revision']==row['view']['revision']
    original=usage(lab,row)
    assert original['unresolved_calls']==1 and original['fully_costed'] is False
    # A human choice cannot waive the original finite token budget's unknown
    # usage. Approval preserves the exact blocked checkpoint and accounting.
    assert resume(lab,row,choice='approve')==original_view
    assert accounting_snapshot(usage(lab,row))==accounting_snapshot(original) and calls(lab)==before


def test_original_starting_dispatch_uncertainty_requires_consent_and_no_retry(lab,historical):
    row=item(historical,'starting');before=calls(lab)
    blocked=resume(lab,row)
    assert blocked['status']=='blocked' and blocked['recovery_status']=='retry_consent_required'
    blocked=resume(lab,row,retry_interrupted=True)
    assert blocked['status']=='blocked' and blocked['recovery_status']=='usage_reconciliation_required'
    assert usage(lab,row)['unresolved_calls']==1 and calls(lab)==before


def test_runtime_role_cannot_perform_application_migration(lab,historical):
    original=snapshot(lab['migration_dsn'])
    with pytest.raises(psycopg.errors.InsufficientPrivilege):migrate(lab['app_dsn'],runtime_role='app_runtime')
    assert snapshot(lab['migration_dsn'])==original


def test_incompatible_schema_aborts_transaction_without_partial_native_creation(lab,owned_database):
    isolated=owned_database('upgrade_negative')
    migrate(isolated['migration_dsn'],runtime_role='app_runtime')
    with psycopg.connect(isolated['migration_dsn']) as connection:
        connection.execute('ALTER TABLE lab_app.runs ADD COLUMN incompatible text')
        connection.execute('UPDATE lab_app.schema_version SET version=2')
    with pytest.raises(ValueError):migrate(isolated['migration_dsn'],runtime_role='app_runtime')
    with psycopg.connect(isolated['migration_dsn']) as connection:
        assert connection.execute('SELECT version FROM lab_app.schema_version').fetchone()==(2,)
        assert connection.execute('SELECT count(*) FROM lab_app.runs').fetchone()==(0,)


def test_missing_retained_assets_blocks_legacy_run_without_default_fallback(lab,historical):
    row=item(historical,'synthetic');before=calls(lab)
    identity=historical['assets_hash']
    try:
        replace_worker(lab,config_patch={'legacy_bundles':{}})
        result=httpx.get(lab['b']+'/runs/'+row['view']['run_id'],headers=headers(lab),timeout=5)
        assert result.status_code==409 and result.json()['detail']=='asset_conflict'
        assert calls(lab)==before
    finally:replace_worker(lab,config_patch={'legacy_bundles':{identity:{'assets':'/srv/lab/assets/legacy-0.2.0'}}})


def test_changed_current_defaults_never_replace_original_ownership_idempotency_assets_or_receipts(lab,historical):
    current=snapshot(lab['migration_dsn']);original=historical['original']
    fields=('run_id','tenant_id','actor_id','billing_account_id','idempotency_key','request_hash','request',
            'workflow','assets_hash','namespace','environment')
    assert [{key:row[key] for key in fields} for row in current['runs']]==[
        {key:row[key] for key in fields} for row in original['runs']]
    assert current['receipts']==original['receipts'] and current['intents']==original['intents']
    assert current['observations']==original['observations']
    assert calls(lab)==historical['calls']
