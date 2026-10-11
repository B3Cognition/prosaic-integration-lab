import copy
import hashlib
from pathlib import Path
import pytest
from lab_runner.gates import validate,export

def receipt(mode='audit'):
    active = Path(__file__).resolve().parents[2] / 'dependencies/releases.json'
    return {'mode':mode,'passed':True,'cleanup':'verified','dependency_mode':'released',
        'test_returncode':0,'test_count':{'audit':88,'identity':20,'ingress':5}[mode],
        'payload_audit':'verified','released_manifest_sha256':hashlib.sha256(active.read_bytes()).hexdigest(),
        'skipped':0,'failed_tests':[],'host_architecture':'arm64',
        'images':{'consumer':'sha256:'+'1'*64,'postgres':'postgres:16@sha256:'+'2'*64}}

@pytest.mark.parametrize('patch',[{'passed':False},{'cleanup':'failed'},{'skipped':1},
    {'test_count':76},{'test_returncode':1},{'failed_tests':['test_failed']},
    {'dependency_mode':'candidate'},{'error':'EngineError'},{'host_architecture':'unknown'},
    {'payload_audit':None},{'released_manifest_sha256':'wrong'}])
def test_required_gate_rejects_incomplete_or_nonrelease_receipt(patch):
    item=receipt(); item.update(patch)
    with pytest.raises(ValueError): validate(item,'audit',16,candidate=False)

def test_required_gate_requires_exact_mode_and_database_major():
    with pytest.raises(ValueError): validate(receipt(),'identity',16,candidate=False)
    with pytest.raises(ValueError): validate(receipt(),'audit',18,candidate=False)

def test_lago_release_gate_requires_verified_pinned_billing_image():
    import json
    from pathlib import Path
    image=json.loads((Path(__file__).resolve().parents[2]/'dependencies/lago.json').read_text())['image']
    item=receipt(); item.update(mode='lago',test_count=25)
    item['images']['lago']=image
    validate(item,'lago',16)
    assert export(item)['images']['lago']==image
    for invalid in (None,'getlago/lago:latest','getlago/lago:v1@sha256:'+'1'*64):
        item['images']['lago']=invalid
        with pytest.raises(ValueError): validate(item,'lago',16)

@pytest.mark.parametrize('item',[None,[],{'images':None}])
def test_malformed_receipts_fail_closed_and_have_safe_export(item):
    with pytest.raises(ValueError): validate(item,'audit',16,candidate=False)
    assert export(item)['passed'] is False

def test_candidate_receipts_require_matching_explicit_manifest():
    item=receipt(); item['dependency_mode']='candidate'
    with pytest.raises(ValueError): validate(item,'audit',16,candidate=True,manifest_sha='3'*64)
    item['candidate_manifest_sha256']='3'*64
    validate(item,'audit',16,candidate=True,manifest_sha='3'*64)

def test_safe_export_does_not_copy_arbitrary_receipt_fields():
    item=receipt(); item.update(token='PRIVATE',error='PRIVATE',failed_tests=['PRIVATE'])
    assert 'PRIVATE' not in str(export(item))
    assert export(item)['passed'] is False


def test_qualification_failures_export_closed_cases_from_sanitized_junit(tmp_path):
    import json
    from lab_runner.results import sanitize_junit
    junit=tmp_path/'private.xml'
    junit.write_text('<testsuites><testsuite>'
        '<testcase name="test_real_fairness_reads_growth_and_usage_are_measured"><failure>PRIVATE_DSN</failure></testcase>'
        '<testcase name="test_real_restore_cli_reports_measured_markers_and_verified_cleanup[legacy]"><error>PRIVATE_TOKEN</error></testcase>'
        '<testcase name="test_real_restore_cli_reports_measured_markers_and_verified_cleanup[native]"><error>PRIVATE_TOKEN</error></testcase>'
        '<testcase name="PRIVATE_PATH"><failure>PRIVATE_CONFIG</failure></testcase>'
        '</testsuite></testsuites>')
    item=receipt();item.update(mode='qualification',passed=False,test_returncode=1,
        **sanitize_junit(junit))
    safe=export(item)
    assert safe['failed_cases']==['capacity','native_restore','restore','unknown']
    assert safe['failed_count']==4 and safe['passed'] is False
    assert 'PRIVATE' not in json.dumps(safe)
    # A fabricated parameter suffix must never turn into a public test identity.
    item['failed_tests']=['test_real_fairness_reads_growth_and_usage_are_measured[PRIVATE]']
    assert export(item)['failed_cases']==['unknown']
    assert 'PRIVATE' not in json.dumps(export(item))


def test_native_fault_failures_export_only_fixed_owned_cases():
    item=receipt();item.update(mode='native',passed=False,test_returncode=1,failed_tests=[
        'test_native_accepted_transport_fault_never_redispatches_or_duplicates_effect[reset-post-tool]',
        'test_native_live_sql_partition_takeover_fences_late_a_and_allows_fresh_session',
        'test_native_accepted_transport_fault_never_redispatches_or_duplicates_effect[PRIVATE]'])
    safe=export(item)
    assert safe['failed_cases']==['live_sql_fence','provider_transport','unknown']
    assert safe['failed_count']==3 and safe['passed'] is False
    assert 'PRIVATE' not in str(safe)


@pytest.mark.parametrize('mode,names,codes',[
    ('native-persistence',['test_public_json_input_type_survives_native_reservation_and_replay[nested]',
        'test_lost_claim_acknowledgement_never_grants_redispatch',
        'test_post_effect_invalid_result_preserves_uncertain_row[PRIVATE]','PRIVATE'],
        ['json_inputs','lost_claim_ack','unknown']),
    ('native',['test_native_saved_receipt_adoption_durable_usage_and_no_duplicate_provider',
        'test_worker_loss_claim_effect_commit_never_infers_redispatch[tool-effect-1-uncertain]',
        'test_worker_loss_claim_effect_commit_never_infers_redispatch[PRIVATE]','PRIVATE'],
        ['effect_recovery','saved_receipt','unknown']),
    ('legacy-upgrade',['test_original_synthetic_waiting_recovers_exact_frozen_accounting',
        'test_original_missing_usage_stays_unknown_after_approval','PRIVATE'],
        ['legacy_unknown_usage','legacy_waiting','unknown'])])
def test_workflow_failure_codes_only_match_fixed_owned_cases(mode,names,codes):
    import json
    item=receipt();item.update(mode=mode,failed_tests=names,passed=False,test_returncode=1)
    safe=export(item)
    assert safe['failed_cases']==codes and safe['passed'] is False
    assert 'PRIVATE' not in json.dumps(safe)
