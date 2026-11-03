"""Failed/contended live batches retain evidence without exceeding allowance."""
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from lab_runner.live_allowance import SharedLiveAllowance
from lab_runner.reasoning_eval import load_artifact, run_live
from lab_runner.reasoning_eval.fixtures import api_fixture


def config_file(root, url):
    path = root / 'runtime.yml'
    path.write_text(yaml.safe_dump({'default_profile': 'gemma', 'allowed_tools': [],
        'profiles': {'gemma': {'base_url': url, 'model': 'gemma-4-31B-it-oQ4e-mtp',
            'features': {'streaming': False}}}}))
    return path


def options(root, config):
    return dict(kind='api', config_path=config, profile='gemma', efforts=['none', 'low'],
        live=True, maximum=2, allowance_path=root / 'allowance.json', timeout_s=10)


def test_partial_allowance_rejects_entire_batch_and_cli_retains_failed_receipt(tmp_path):
    from prosaic_integration_lab.dependencies import cache_directory
    allowance = SharedLiveAllowance(tmp_path / 'allowance.json', max_calls=2)
    token = allowance.reserve(maximum_requests=1)
    allowance.finish(token, actual_requests=1)
    root = Path(__file__).resolve().parents[2]
    manifest = root / 'dependencies/releases-reasoning.json'
    wheels = cache_directory(manifest, root / '.cache/wheels')
    receipt = tmp_path / 'receipt.json'
    with api_fixture() as (url, requests):
        config = config_file(tmp_path, url)
        completed = subprocess.run([sys.executable, '-m', 'lab_runner.reasoning_eval', 'live',
            '--live', '--config', str(config), '--profile', 'gemma',
            '--effort', 'none', '--effort', 'low', '--max-calls', '2',
            '--allowance', str(tmp_path / 'allowance.json'), '--manifest', str(manifest),
            '--wheel-dir', str(wheels), '--output', str(receipt)],
            cwd=root, capture_output=True, text=True, timeout=30)
        assert completed.returncode == 1
        assert requests == []
        report = json.loads(receipt.read_text())
        assert report['passed'] is False
        assert report['failureReason'] == 'allowance_exhausted'
        assert report['samples'] == [] and report['allowance']['remaining'] == 1
        assert url not in receipt.read_text()


def test_concurrent_consumer_cannot_take_reserved_batch_capacity(tmp_path):
    competitor = SharedLiveAllowance(tmp_path / 'allowance.json', max_calls=2)
    denied = []
    def compete(requests):
        if len(requests) != 1:
            return
        try:
            token = competitor.reserve(maximum_requests=1)
        except ValueError:
            denied.append(True)
        else:
            competitor.finish(token, actual_requests=1)
            denied.append(False)
    with api_fixture(on_request=compete) as (url, requests):
        report = run_live(**options(tmp_path, config_file(tmp_path, url)))
        assert report['passed'] and len(requests) == 2 and denied == [True]
        assert report['allowance']['remaining'] == 0


def test_execution_exception_retains_completed_samples_and_unknown_reservation(tmp_path):
    from prosaic_runtime import EndpointConfig, RuntimeConfig, ProsaicRuntime, RunPolicy
    from lab_runner.reasoning_eval.execution import execute_batch
    with api_fixture() as (url, requests):
        sdk_runtime = ProsaicRuntime(RuntimeConfig({'gemma': EndpointConfig(url,
            'gemma-4-31B-it-oQ4e-mtp', features={'streaming': False})}, {}, 'gemma'))
        class FailSecond:
            def __init__(self):
                self.calls = 0
            def run(self, *args, **kwargs):
                self.calls += 1
                if self.calls == 2:
                    raise RuntimeError('fixture-private-exception-do-not-export')
                return sdk_runtime.run(*args, **kwargs)
        allowance = SharedLiveAllowance(tmp_path / 'allowance.json', max_calls=3)
        report = execute_batch(runtime=FailSecond(), artifacts=[load_artifact(e) for e in
            ('none', 'low', 'medium')], kind='api', profile='gemma',
            policy=RunPolicy(timeout_s=10, max_provider_requests=1),
            allowance=allowance, cwd=tmp_path)
        assert len(requests) == 1 and report['passed'] is False
        assert len(report['samples']) == 2
        assert report['samples'][0]['completed'] and report['samples'][0]['reportedTokens'] == 5
        assert report['samples'][1]['providerRequests'] is None
        assert report['samples'][1]['reportedTokens'] is None
        assert report['failureReason'] == 'execution_exception'
        assert report['allowance']['unknown'] == 1 and report['allowance']['remaining'] == 0
        assert 'fixture-private' not in json.dumps(report) and url not in json.dumps(report)


@pytest.mark.parametrize('rows', [[], [{'passed': False}], [{'passed': True}, {'passed': False}]])
def test_failed_or_empty_control_checks_never_claim_verified(rows):
    from lab_runner.reasoning_eval.fixtures import summarize
    report = summarize(rows, provenance={})
    assert report['passed'] is False and report['controlsVerified'] is False
