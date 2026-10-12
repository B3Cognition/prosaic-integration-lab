"""Required acceptance receipts and safe publication summaries."""
import re
import hashlib
import json
from pathlib import Path

COUNTS = {'audit':88,'identity':20,'ingress':5,'lago':25,'native-persistence':26,'native':54,'legacy-upgrade':10,'qualification':3}

# Fixed identities from the owned acceptance fixtures. Arbitrary names and
# parameter values never become exported strings or dynamic code labels.
FAILURE_CASES={
    'native-persistence':{
        'test_proposal_replay_after_bundle_upgrade_keeps_original_reference':'proposal_replay',
        'test_concurrent_bundle_admission_returns_only_original_winning_reference':'proposal_race',
        'test_body_conflict_and_other_owner_lookup_do_not_expose_original':'proposal_owner',
        'test_native_reservation_keeps_original_owner_billing_scope_and_inputs':'native_scope',
        'test_runtime_role_cannot_mutate_immutable_proposals_or_migrate':'immutable_role',
        'test_capacity_exhaustion_keeps_replay_and_blocks_new_key':'proposal_capacity',
        'test_schema_constraints_bound_raw_immutable_storage':'schema_bounds',
        'test_readiness_rejects_accidentally_granted_proposal_update':'readiness_grants',
        'test_concurrent_explicit_migrations_share_transaction_lock':'migration_race',
        'test_version_two_upgrade_preserves_every_legacy_field_and_phase':'migration_fields',
        'test_uncertain_claim_never_reclaims_and_stale_token_cannot_commit':'journal_fence',
        'test_same_scope_concurrent_claim_has_only_one_dispatch_winner':'journal_race',
        'test_lost_commit_acknowledgement_discovers_committed_replay':'lost_commit_ack',
        'test_lost_claim_acknowledgement_never_grants_redispatch':'lost_claim_ack',
        'test_restricted_role_cannot_replace_signature_or_fencing_token':'journal_role'},
    'qualification':{
        'test_real_fairness_reads_growth_and_usage_are_measured':'capacity',
        'test_real_restore_cli_reports_measured_markers_and_verified_cleanup[legacy]':'restore',
        'test_real_restore_cli_reports_measured_markers_and_verified_cleanup[native]':'native_restore'},
    'native':{
        'test_prepared_context_cross_tier_database_handoff_on_fresh_replica':'context_handoff',
        'test_native_adoption_demo_runs_public_protocol_and_filtered_receipt':'native_demo',
        'test_native_graph_cross_worker_fresh_process_pause_approval_and_provenance':'native_graph',
        'test_invalid_structured_response_preserves_committed_revision[response0]':'invalid_response',
        'test_invalid_structured_response_preserves_committed_revision[response1]':'invalid_response',
        'test_stale_response_cannot_record_human_decision':'stale_response',
        'test_owner_isolation_catalogue_proposal_run_interaction_usage':'owner_isolation',
        'test_same_operation_keys_are_independent_between_tenant_owners':'tenant_keys',
        'test_inline_grant_never_implies_composition':'inline_composition',
        'test_omitted_model_tier_uses_host_default_with_empty_explicit_allowlist':'default_model',
        'test_inline_grant_never_implies_tools':'inline_tools',
        'test_check_failure_and_rejected_output_usage':'check_rejection',
        'test_gate_failure_is_observable_without_running_pause':'gate_rejection',
        'test_graph_revisit_rejects_stale_dependent_artifact_before_next_call':'graph_revisit',
        'test_finish_requires_cannot_accept_missing_specialist':'finish_requires',
        'test_run_budget_prevents_next_provider_dispatch':'run_budget',
        'test_current_revocation_prevents_resume_on_fresh_worker':'revocation',
        'test_original_proposal_replay_new_bundle_and_reordered_reference_json':'proposal_replay',
        'test_missing_retained_bundle_is_operator_condition_without_default_fallback':'missing_bundle',
        'test_completed_native_business_operation_replays_without_duplicate_domain_effect':'effect_replay',
        'test_same_business_key_has_distinct_trusted_tenant_namespaces':'effect_tenants',
        'test_concurrent_native_claims_execute_only_one_domain_handler':'effect_concurrent',
        'test_native_invocation_cap_blocks_next_dispatch_and_retains_real_sql_evidence[tools-native_effect_batch-tool_call_limit]':'tool_budget',
        'test_native_invocation_cap_blocks_next_dispatch_and_retains_real_sql_evidence[provider-native_effect-provider_request_limit]':'provider_budget',
        'test_stale_fence_cannot_overwrite_original_committed_native_result':'stale_fence',
        'test_changed_operation_signature_conflicts_without_mutating_effect_evidence[arguments]':'effect_signature',
        'test_changed_operation_signature_conflicts_without_mutating_effect_evidence[version]':'effect_signature',
        'test_native_saved_receipt_adoption_durable_usage_and_no_duplicate_provider':'saved_receipt',
        'test_native_interrupted_provider_requires_consent_and_preserves_unknown_usage':'interrupted_provider',
        'test_native_live_sql_partition_takeover_fences_late_a_and_allows_fresh_session':'live_sql_fence'},
    'legacy-upgrade':{
        'test_actual_baseline_generated_all_five_states_before_schema_upgrade':'legacy_states',
        'test_original_approval_revision_owner_and_zero_model_calls':'legacy_approval',
        'test_original_synthetic_waiting_recovers_exact_frozen_accounting':'legacy_waiting',
        'test_original_saved_receipt_adopted_by_fresh_worker_without_inference_or_new_receipt':'legacy_receipt',
        'test_original_missing_usage_stays_unknown_after_approval':'legacy_unknown_usage',
        'test_original_starting_dispatch_uncertainty_requires_consent_and_no_retry':'legacy_starting',
        'test_runtime_role_cannot_perform_application_migration':'legacy_role',
        'test_incompatible_schema_aborts_transaction_without_partial_native_creation':'legacy_schema',
        'test_missing_retained_assets_blocks_legacy_run_without_default_fallback':'legacy_assets',
        'test_changed_current_defaults_never_replace_original_ownership_idempotency_assets_or_receipts':'legacy_defaults'}}
for name,parameters,code in (
    ('test_client_registration_references_never_hydrate_host_code',
     ('operation_namespace-attacker','reference-value1','endpoint-http://attacker.invalid','assets-/private'),'client_references'),
    ('test_changed_retained_binding_never_falls_back_or_dispatches',
     ('operation_namespace-altered-namespace','journal_identity-altered-journal','model_url-http://model:8000/altered','policies-value3','fixture_effect_version-v2'),'changed_binding'),
    ('test_worker_loss_claim_effect_commit_never_infers_redispatch',
     ('tool-claimed-0-uncertain','tool-effect-1-uncertain','tool-committed-1-replay'),'effect_recovery')):
    FAILURE_CASES['native'].update({name+'['+parameter+']':code for parameter in parameters})
FAILURE_CASES['native'].update({
    'test_native_accepted_transport_fault_never_redispatches_or_duplicates_effect['+fault+'-'+phase+']':'provider_transport'
    for fault in ('reset','truncated_json','429','503','malformed_shape','slow')
    for phase in ('first','post-tool')})
for name,parameters,code in (
    ('test_public_json_input_type_survives_native_reservation_and_replay',
     ('null','boolean','integer','float','string','array','object','nested'),'json_inputs'),
    ('test_post_effect_invalid_result_preserves_uncertain_row',
     ('oversize','nonfinite','unserializable'),'invalid_effect_result')):
    FAILURE_CASES['native-persistence'].update({name+'['+parameter+']':code for parameter in parameters})

def validate(item,mode,postgres_major,*,candidate=False,manifest_sha=None,lineage_sha=None):
    if not isinstance(item,dict): raise ValueError('invalid acceptance receipt')
    if (mode not in COUNTS or item.get('mode') != mode or
        item.get('passed') is not True or item.get('cleanup') != 'verified' or
        type(item.get('test_returncode')) is not int or item['test_returncode'] != 0 or type(item.get('test_count')) is not int or
        item['test_count'] != COUNTS[mode] or type(item.get('skipped')) is not int or item['skipped'] != 0 or
        item.get('failed_tests') != [] or 'error' in item or
        item.get('host_architecture') not in {'arm64','aarch64','x86_64','AMD64'}):
        raise ValueError('required acceptance receipt did not pass')
    images = item.get('images',{})
    if not isinstance(images,dict): raise ValueError('invalid image provenance')
    if (not re.fullmatch(r'sha256:[0-9a-f]{64}',images.get('consumer','')) or
        not re.fullmatch(r'postgres:'+str(postgres_major)+r'@sha256:[0-9a-f]{64}',images.get('postgres',''))):
        raise ValueError('required image provenance missing')
    if mode=='lago':
        image=json.loads((Path(__file__).resolve().parents[1]/'dependencies/lago.json').read_text())['image']
        if images.get('lago')!=image: raise ValueError('billing image provenance missing')
    if mode=='legacy-upgrade':
        from .legacy_upgrade import BASELINE_COMMIT,BASELINE_SHA256
        if (item.get('baseline_source')!=BASELINE_COMMIT or item.get('baseline_manifest_sha256')!=BASELINE_SHA256 or
            item.get('baseline_payload_audit')!='verified' or item.get('migration')!='v2-to-v3' or
            item.get('legacy_fixture_count')!=5 or
            not re.fullmatch(r'sha256:[0-9a-f]{64}',images.get('baseline',''))):
            raise ValueError('historical upgrade provenance missing')
    expected = 'candidate' if candidate else 'released'
    if item.get('dependency_mode') != expected:
        raise ValueError('dependency provenance differs from required lane')
    released_sha = hashlib.sha256((Path(__file__).resolve().parents[1]/'dependencies/releases.json').read_bytes()).hexdigest()
    if item.get('released_manifest_sha256') != released_sha or item.get('payload_audit') != 'verified':
        raise ValueError('installed payload provenance missing')
    if candidate and (not isinstance(manifest_sha,str) or not re.fullmatch('[0-9a-f]{64}',manifest_sha) or
        item.get('candidate_manifest_sha256') != manifest_sha):
        raise ValueError('candidate manifest provenance missing')
    if candidate and mode in FAILURE_CASES and (
        not isinstance(lineage_sha,str) or not re.fullmatch('[0-9a-f]{64}',lineage_sha) or
        item.get('candidate_lineage_sha256')!=lineage_sha):
        raise ValueError('qualified candidate lineage missing')

def export(item):
    # Only known scalars survive; arbitrary errors/failure names/paths never do.
    if not isinstance(item,dict): item = {}
    result = {'passed':item.get('passed') is True and 'error' not in item and
        item.get('cleanup') == 'verified' and item.get('failed_tests') == [] and item.get('skipped') == 0 and
        type(item.get('test_count')) is int and item.get('mode') in COUNTS and item['test_count'] == COUNTS[item['mode']] and
        type(item.get('test_returncode')) is int and item['test_returncode'] == 0 and item.get('payload_audit') == 'verified'}
    for key,choices in {'mode':set(COUNTS),'cleanup':{'verified','failed','pending'},
        'dependency_mode':{'released','candidate'},'host_architecture':{'arm64','aarch64','x86_64','AMD64'}}.items():
        value = item.get(key)
        result[key] = value if isinstance(value,str) and value in choices else 'unknown'
    for key in ('test_count','skipped','test_returncode'):
        value = item.get(key)
        result[key] = value if type(value) is int and 0 <= value <= 100000 else None
    result['failed_count'] = len(item.get('failed_tests',[])) if isinstance(item.get('failed_tests'),list) else None
    if item.get('mode') in FAILURE_CASES and type(item.get('failed_tests')) is list:
        # Fixed public phase codes identify owned cases. Never copy a
        # testcase name, parameter, error message or captured private output.
        cases=FAILURE_CASES[item['mode']]
        result['failed_cases']=sorted({cases.get(name,'unknown') if type(name) is str else 'unknown'
            for name in item['failed_tests']})
    result['payload_audit'] = 'verified' if item.get('payload_audit') == 'verified' else 'unverified'
    owner = item.get('owner')
    if isinstance(owner,str) and re.fullmatch('[0-9a-f]{32}',owner): result['owner'] = owner
    diagnostic=item.get('engine_diagnostic')
    if isinstance(diagnostic,dict):
        operation=diagnostic.get('operation')
        category=diagnostic.get('category')
        code=diagnostic.get('return_code')
        operations={'info','pull','run','create','start','stop','kill','exec','inspect','logs','ps','rm','unknown'}
        operations|={base+'_'+verb for base in ('network','volume','image') for verb in ('create','inspect','rm','ls')}
        if (operation in operations and category in {'command_timeout','rate_limited','image_missing',
            'engine_unavailable','network_timeout','permission_denied','engine_failed'} and
            (code is None or type(code) is int and -128 <= code <= 255) and diagnostic.get('outcome')=='unknown'):
            result['engine_diagnostic']={'operation':operation,'return_code':code,'category':category,'outcome':'unknown'}
    for key in ('released_manifest_sha256','candidate_manifest_sha256','baseline_manifest_sha256','candidate_lineage_sha256'):
        value = item.get(key)
        if isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value): result[key] = value
    if item.get('baseline_source')=='59752bef3e6b3ffde0ecbf38f34815d184043e20':result['baseline_source']=item['baseline_source']
    for key,value in {'baseline_payload_audit':'verified','migration':'v2-to-v3','legacy_fixture_count':5}.items():
        if item.get(key)==value:result[key]=value
    images = item.get('images',{})
    if not isinstance(images,dict): images = {}
    result['images'] = {key:value for key,value in images.items() if key in {'consumer','postgres','keycloak','ingress','lago','baseline'}
        and isinstance(value,str) and re.fullmatch(r'(?:[a-z0-9./:-]+@)?sha256:[0-9a-f]{64}',value)}
    return result
