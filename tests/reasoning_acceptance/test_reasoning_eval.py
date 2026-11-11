"""Reasoning lab consumes actual installed SDK transports, without live models."""
import json
import pytest


def test_fixture_lane_observes_all_adapters_and_rejects_unsupported_efforts():
    from lab_runner.reasoning_eval import run_fixtures
    report = run_fixtures()
    assert report['passed'] is True
    assert report['origin'] == 'scripted_fixture'
    assert report['liveInvocations'] == 0
    assert report['modelQualityQualified'] is False
    assert {row['adapter'] for row in report['samples']} == {
        'openai-compatible', 'claude-code', 'codex-cli'}
    assert len(report['samples']) >= 35
    assert all(row['passed'] for row in report['samples'])
    assert any(row['effort'] == 'ultra' and row['adapter'] == 'codex-cli'
               and row['dispatched'] for row in report['samples'])
    assert all(not row['dispatched'] for row in report['samples']
               if row['expectedRejection'])
    serialized = json.dumps(report)
    assert 'Bearer' not in serialized and '127.0.0.1' not in serialized


@pytest.mark.parametrize('effort', ['none', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra'])
def test_packaged_blueprints_are_canonical_prose(effort):
    from lab_runner.reasoning_eval import load_artifact
    artifact = load_artifact(effort)
    assert artifact.frontmatter['effort'] == effort
    assert artifact.frontmatter['tools'] == []
    assert 'ALWAYS' in artifact.body and 'NEVER' in artifact.body
    assert 'model' not in artifact.frontmatter


def test_effort_blueprints_change_only_effort_metadata():
    from lab_runner.reasoning_eval import EFFORTS, load_artifact
    reference = load_artifact('low')
    frontmatter = dict(reference.frontmatter)
    frontmatter.pop('effort')
    for effort in EFFORTS:
        artifact = load_artifact(effort)
        metadata = dict(artifact.frontmatter)
        metadata.pop('effort')
        assert metadata == frontmatter
        assert artifact.body == reference.body


@pytest.mark.parametrize('timeout', [0, -1, 301, True, float('inf'), float('nan')])
def test_invalid_live_deadline_fails_before_private_config_or_allowance(tmp_path, timeout):
    from lab_runner.reasoning_eval import run_live
    with pytest.raises(ValueError, match='timeout'):
        run_live(kind='api', config_path=tmp_path / 'missing-private.yml', profile='qwen',
            efforts=['low'], live=True, maximum=1,
            allowance_path=tmp_path / 'allowance.json', timeout_s=timeout)
    assert not (tmp_path / 'allowance.json').exists()


def test_grading_keeps_answer_quality_separate_from_json_format():
    from lab_runner.reasoning_eval import grade
    assert grade('{"answer":423}') == (True, True)
    assert grade('```json\n{"answer":423}\n```') == (False, True)
    assert grade('{"answer":173}') == (True, False)
    assert grade('{"answer":true}') == (False, False)
    assert grade('{"answer":423,"answer":173}') == (False, False)


@pytest.mark.parametrize('live,efforts,maximum', [
    (False, ['low'], 1), (True, ['unknown'], 1), (True, ['low'], 0),
    (True, ['low', 'medium'], 1), (True, ['low'], True),
])
def test_invalid_live_options_fail_before_loading_private_config(tmp_path, live, efforts, maximum):
    from lab_runner.reasoning_eval import run_live
    with pytest.raises(ValueError):
        run_live(kind='api', config_path=tmp_path / 'missing-private.yml', profile='qwen',
                 efforts=efforts, live=live, maximum=maximum,
                 allowance_path=tmp_path / 'allowance.json', timeout_s=30)
    assert not (tmp_path / 'allowance.json').exists()


def test_live_fixture_retains_allowance_and_sanitizes_receipt(tmp_path):
    from lab_runner.reasoning_eval import run_live
    from lab_runner.reasoning_eval.fixtures import api_fixture
    import yaml
    with api_fixture() as (url, requests):
        config = tmp_path / 'runtime.yml'
        config.write_text(yaml.safe_dump({'default_profile': 'gemma', 'allowed_tools': [],
            'profiles': {'gemma': {'base_url': url, 'model': 'gemma-4-31B-it-oQ4e-mtp',
                'max_tokens': 4096, 'features': {'streaming': False}}}}))
        options = dict(kind='api', config_path=config, profile='gemma', efforts=['none', 'high'],
            live=True, maximum=2, allowance_path=tmp_path / 'allowance.json', timeout_s=10)
        report = run_live(**options)
        assert report['passed'] and len(requests) == 2
        assert report['controlsVerified'] is False
        assert all(r['answerCorrect'] and r['formatCorrect'] for r in report['samples'])
        assert all(r['providerRequests'] == 1 for r in report['samples'])
        assert report['allowance']['remaining'] == 0
        text = json.dumps(report)
        assert url not in text and '423' not in text and 'modulo' not in text
        exhausted = run_live(**options)
        assert exhausted['passed'] is False and exhausted['failureReason'] == 'allowance_exhausted'
        assert exhausted['samples'] == []
        assert len(requests) == 2


def test_live_unsupported_batch_is_rejected_before_any_request_or_reservation(tmp_path):
    from lab_runner.reasoning_eval import run_live
    from lab_runner.reasoning_eval.fixtures import api_fixture
    import yaml
    with api_fixture() as (url, requests):
        config = tmp_path / 'runtime.yml'
        config.write_text(yaml.safe_dump({'default_profile': 'qwen', 'allowed_tools': [],
            'profiles': {'qwen': {'base_url': url, 'model': 'ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ',
                'features': {'streaming': False}}}}))
        with pytest.raises(ValueError, match='effort'):
            run_live(kind='api', config_path=config, profile='qwen', efforts=['low', 'max'],
                live=True, maximum=2, allowance_path=tmp_path / 'allowance.json', timeout_s=10)
        assert requests == [] and not (tmp_path / 'allowance.json').exists()


def test_unwritable_receipt_parent_fails_before_live_dispatch(tmp_path):
    import os
    from pathlib import Path
    import subprocess
    import sys
    import yaml
    from lab_runner.reasoning_eval.fixtures import api_fixture
    from prosaic_integration_lab.dependencies import cache_directory
    root = Path(__file__).resolve().parents[2]
    manifest = root / 'dependencies/releases-reasoning.json'
    wheels = cache_directory(manifest, root / '.cache/wheels')
    with api_fixture() as (url, requests):
        config = tmp_path / 'runtime.yml'
        config.write_text(yaml.safe_dump({'default_profile': 'gemma', 'allowed_tools': [],
            'profiles': {'gemma': {'base_url': url, 'model': 'gemma-4-31B-it-oQ4e-mtp',
                'features': {'streaming': False}}}}))
        completed = subprocess.run([sys.executable, '-m', 'lab_runner.reasoning_eval', 'live',
            '--live', '--config', str(config), '--profile', 'gemma', '--effort', 'none',
            '--max-calls', '1', '--allowance', str(tmp_path / 'allowance.json'),
            '--manifest', str(manifest), '--wheel-dir', str(wheels),
            '--output', str(tmp_path / 'missing-parent/receipt.json')],
            cwd=root, capture_output=True, text=True, timeout=30,
            env={**os.environ, 'PYTHONPATH': str(root / 'src')})
        assert completed.returncode != 0
        assert requests == []
        assert not (tmp_path / 'allowance.json').exists()


def test_harness_blueprint_validates_without_a_provider_key(tmp_path):
    import os
    from pathlib import Path
    import subprocess
    import sys
    from lab_runner.reasoning_eval import DATA
    environment = dict(os.environ)
    environment.pop('REASONING_API_KEY', None)
    environment['PATH'] = str(Path(sys.executable).parent) + os.pathsep + environment['PATH']
    completed = subprocess.run([str(Path(sys.executable).with_name('prosaic-harness')),
        'validate', str(DATA / 'workflow.yml')], cwd=tmp_path, capture_output=True,
        text=True, env=environment, timeout=30)
    assert completed.returncode == 0, completed.stderr
