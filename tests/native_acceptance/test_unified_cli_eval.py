def test_installed_unified_cli_pool_acceptance():
    from lab_runner.native_eval.unified import run_unified_cli_acceptance
    report = run_unified_cli_acceptance()
    assert report['passed'], report
    assert report['caseCount'] == 13 and report['liveInvocations'] == 0
    assert report['cleanup'] == 'verified'
    assert set(report['checks']) == {'three_backend_cli_fallback', 'jsonl_terminal_result',
        'graded_output', 'cross_process_cooldown', 'zero_request_budget',
        'all_unavailable_no_dispatch', 'no_replay_after_tool', 'native_effect_no_replay',
        'native_success', 'explicit_backend_exclusion', 'zero_tool_budget',
        'text_output', 'temporary_workspace_cleanup'}
