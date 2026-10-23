from importlib import import_module
from importlib.util import find_spec


def test_installed_unified_pool_acceptance_covers_three_backends_and_no_replay():
    assert find_spec('lab_runner.native_eval.unified') is not None, 'missing unified consumer acceptance lane'
    lane = import_module('lab_runner.native_eval.unified')
    report = lane.run_unified_acceptance()
    assert report['passed'], report
    assert report['origin'] == 'scripted_fixture'
    assert report['caseCount'] >= 10 and report['liveInvocations'] == 0
    assert report['cleanup'] == 'verified'
    for name in ('three_backend_fallback', 'api_to_native_fallback', 'native_effect_no_replay',
                 'api_effect_no_replay', 'shared_quota_no_bypass', 'all_unavailable_no_dispatch',
                 'cross_process_cooldown', 'explicit_native_permission', 'api_write_scope', 'api_request_budget'):
        assert report['checks'][name] is True
