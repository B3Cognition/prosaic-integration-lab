"""Explicit candidate-only lane; missing native SDK is a failure, never a skip."""
import json
from pathlib import Path
import subprocess
import sys


def test_installed_native_runtime_acceptance_includes_failures_and_cleanup():
    from lab_runner.native_eval.runner import run_acceptance
    report = run_acceptance()
    assert report['passed'] is True, report
    assert report['origin'] == 'scripted_fixture'
    assert report['cleanup'] == 'verified'
    assert report['caseCount'] >= 7
    assert report['liveInvocations'] == 0
    assert report['checks']['quota_fallback'] is True
    assert report['checks']['uncertain_effect_no_replay'] is True
    assert report['checks']['cross_process_cooldown'] is True


def test_fixture_benchmark_compares_same_tasks_per_selector():
    from lab_runner.native_eval.runner import fixture_benchmark
    report = fixture_benchmark(repetitions=2)
    assert report['passed'] is True
    assert report['sampleCount'] == 12
    assert report['nativeAttempts'] == 12
    assert report['providerRequests'] is None
    assert report['modelQualityQualified'] is False
    assert all(row['passRate'] == 1 and row['samples'] == 4 for row in report['groups'])
    assert all(row['model'] == 'synthetic' and row['backend'] in {'claude-code', 'codex-cli'}
               and row['selectedProfile'] in {'claude', 'codex'} for row in report['samples'])
    for case in ('facts', 'repair'):
        assert len({row['inputSha256'] for row in report['samples'] if row['case'] == case}) == 1


def test_fixture_benchmark_rejects_missing_native_sdk_instead_of_skipping():
    from lab_runner.native_eval.provenance import require_native
    sdk = require_native()
    assert sdk.NativeRuntime.capabilities == frozenset({'native_profiles_v1', 'profile_pools_v1'})
    assert 'site-packages' in Path(sdk.__file__).parts


def test_native_cli_bootstraps_only_lab_source_in_sdk_only_environment():
    root = Path(__file__).resolve().parents[2]
    code = ('import sys; sys.path.insert(0,sys.argv[1]); '
            'import lab_runner.native_eval.__main__; import prosaic_integration_lab; '
            'assert prosaic_integration_lab.__file__.startswith(sys.argv[1]+"/src/")')
    result = subprocess.run([sys.executable, '-I', '-c', code, str(root)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_live_admission_path_with_owned_fixture_clis(tmp_path):
    from dataclasses import asdict
    import yaml
    from lab_runner.native_eval.runner import fixture_config
    from lab_runner.native_eval.live import preflight, run_live
    config = fixture_config(tmp_path)
    path = tmp_path / 'private.yml'
    path.write_text(yaml.safe_dump({'kind': 'native', 'profiles': {
        k: asdict(v) for k, v in config.profiles.items()}, 'default_profile': 'claude'}))
    path.chmod(0o600)
    options = dict(config_path=path, selectors=['claude', 'codex'], repetitions=1, maximum=4, timeout_s=5)
    readiness = preflight(**options)
    assert readiness['passed'] is True and readiness['liveInvocations'] == 0
    output = tmp_path / 'run'
    report = run_live(**options, output=output, provenance={'test': 'scripted_clis_only'})
    assert report['passed'] is True and report['nativeAttempts'] == 4
    assert report['allowance']['remaining'] == 0
    assert (output / 'report.json').stat().st_mode & 0o777 == 0o600
    assert not list(output.glob('workspaces-*'))
    import pytest
    with pytest.raises(FileExistsError):
        run_live(**options, output=output, provenance={})
