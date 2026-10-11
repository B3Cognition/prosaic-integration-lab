"""Preflight is credential-free and makes no inference calls."""
import importlib.util
import json
import os
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def implementation():
    path = ROOT / 'scripts/local_routing_smoke.py'
    assert path.is_file(), 'bounded local routing smoke is missing'
    spec = importlib.util.spec_from_file_location('local_routing_smoke_preflight', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_config(tmp_path, **changes):
    data = yaml.safe_load((ROOT / 'configs/runtime-local.example.yml').read_text())
    data.update(changes)
    path = tmp_path / 'local.yml'
    path.write_text(yaml.safe_dump(data))
    return path


@pytest.mark.parametrize(('optin', 'allowance'), [(False, 3), (True, 0), (True, 2), (True, 4), (True, True)])
def test_optin_and_exact_three_call_allowance_precede_configuration_read(optin, allowance, tmp_path):
    with pytest.raises(ValueError, match='opt-in|three'):
        implementation().preflight(tmp_path / 'missing.yml', live_local=optin, max_calls=allowance)


@pytest.mark.parametrize('cloud_url', ['https://example.invalid/v1', 'http://127.0.0.1.nip.io/v1',
    'http://localhost/v1', 'http://127.0.0.1:8000/v1?secret=hidden'])
def test_cloud_or_ambiguous_profile_rejected_before_secret_read(cloud_url, tmp_path):
    path = write_config(tmp_path, profiles={'local': {'base_url': cloud_url, 'model': 'local',
        'api_key_file': str(tmp_path / 'absent-secret'), 'max_tokens': 32}})
    with pytest.raises(ValueError):
        implementation().preflight(path, live_local=True, max_calls=3)
    assert not (tmp_path / 'absent-secret').exists()


def test_missing_route_is_rejected_before_secret_read(tmp_path):
    path = write_config(tmp_path, routes={'fast': 'local', 'balanced': 'local'})
    with pytest.raises(ValueError, match='route'):
        implementation().preflight(path, live_local=True, max_calls=3)


def test_example_retains_fast_and_defines_distinct_balanced_strong_secret_files():
    config = implementation().preflight(ROOT / 'configs/runtime-local.example.yml',
        live_local=True, max_calls=3)
    assert config.routes['fast'] == 'local'
    assert config.profiles[config.routes['balanced']].model == 'mlx-community--Qwen2.5-Coder-7B-Instruct-4bit'
    assert config.profiles[config.routes['strong']].model == 'ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ'
    assert all(p.api_key_file == '~/.omlx_token' for p in config.profiles.values())
    assert all(p.max_tokens <= 512 and p.features['streaming'] is False for p in config.profiles.values())


@pytest.mark.parametrize('field', ['api_key_env', 'tools', 'tokens'])
def test_unbounded_or_non_secret_managed_configuration_fails(tmp_path, field):
    data = yaml.safe_load((ROOT / 'configs/runtime-local.example.yml').read_text())
    if field == 'api_key_env':
        data['profiles']['local']['api_key_env'] = 'MODEL_KEY'
    elif field == 'tools':
        data['allowed_tools'] = ['read']
    else:
        data['profiles']['local']['max_tokens'] = None
    path = tmp_path / 'bad.yml'
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError):
        implementation().preflight(path, live_local=True, max_calls=3)


@pytest.mark.parametrize('raise_inside', [False, True])
def test_proxy_scope_removes_all_case_variants_and_restores_exact_environment(monkeypatch, raise_inside):
    module = implementation()
    assert callable(getattr(module, 'loopback_environment', None)), 'proxy isolation scope is missing'
    monkeypatch.setenv('http_proxy', 'http://private.invalid')
    monkeypatch.setenv('NO_PROXY', 'original-bypass')
    monkeypatch.setenv('CuStOm_PrOxY', 'http://another.invalid')
    monkeypatch.setenv('LOCAL_ROUTING_SENTINEL', 'unchanged')
    before = dict(os.environ)
    try:
        with module.loopback_environment():
            proxies = {k: v for k, v in os.environ.items() if k.lower().endswith('_proxy')}
            assert proxies == {'no_proxy': '*', 'NO_PROXY': '*'}
            assert os.environ['LOCAL_ROUTING_SENTINEL'] == 'unchanged'
            if raise_inside: raise ValueError('fixture failure')
    except ValueError:
        assert raise_inside
    assert dict(os.environ) == before


def recorded_case():
    invocation = {'id': 'invocation-one', 'step': 'ask', 'arguments_sha256': 'b' * 64,
        'status': 'complete', 'token_usage': 15, 'receipt_sha256': 'a' * 64}
    state = {'run_id': 'default', 'status': 'completed', 'calls': 1, 'pending': None,
        'invocations': [invocation]}
    receipt = {'run_id': 'default', 'id': invocation['id'], 'step': 'ask',
        'arguments_sha256': invocation['arguments_sha256'], 'sha256': invocation['receipt_sha256'],
        'result': {'exit_code': 0, 'timed_out': False, 'token_usage': 15,
            'metadata': {'profile': 'default', 'request_model': 'fixture-default',
                'invocation_budgets_v1': {'provider_requests': 1, 'tool_calls': 0,
                    'reported_tokens': 15, 'usage_complete': True}}}}
    return state, receipt


def evidence(state, receipt):
    module = implementation()
    assert callable(getattr(module, 'recorded_evidence', None)), 'public receipt evidence validation is missing'
    return module.recorded_evidence(state, receipt, expected_profile='default', expected_model='fixture-default')


def test_success_projects_observed_receipt_fields_and_counts():
    row = evidence(*recorded_case())
    assert row == {'completed': True, 'profile': 'default', 'request_model': 'fixture-default',
        'provider_requests': 1, 'tool_calls': 0, 'token_usage': 15}


@pytest.mark.parametrize('tamper', ['wrong-model', 'wrong-profile', 'missing-budgets', 'extra-provider',
    'no-provider', 'bool-provider', 'tool-call', 'unknown-token', 'conflicting-token', 'bad-seal',
    'wrong-id', 'wrong-run', 'wrong-step', 'wrong-arguments', 'two-invocations', 'two-calls', 'pending'])
def test_completed_state_cannot_replace_missing_or_contradictory_receipt_evidence(tamper):
    import copy
    state, receipt = recorded_case()
    result = receipt['result']; metadata = result['metadata']
    if tamper == 'wrong-model': metadata['request_model'] = 'private-unexpected-model'
    elif tamper == 'wrong-profile': metadata['profile'] = 'private-unexpected-profile'
    elif tamper == 'missing-budgets': metadata.pop('invocation_budgets_v1')
    elif tamper in {'extra-provider', 'no-provider', 'bool-provider'}:
        metadata['invocation_budgets_v1']['provider_requests'] = {
            'extra-provider': 2, 'no-provider': 0, 'bool-provider': True}[tamper]
    elif tamper == 'tool-call': metadata['invocation_budgets_v1']['tool_calls'] = 1
    elif tamper == 'unknown-token': result['token_usage'] = None
    elif tamper == 'conflicting-token': state['invocations'][0]['token_usage'] = 99
    elif tamper == 'bad-seal': receipt['sha256'] = 'z' * 64
    elif tamper == 'wrong-id': receipt['id'] = 'wrong'
    elif tamper == 'wrong-run': receipt['run_id'] = 'wrong'
    elif tamper == 'wrong-step': receipt['step'] = 'wrong'
    elif tamper == 'wrong-arguments': receipt['arguments_sha256'] = 'wrong'
    elif tamper == 'two-invocations': state['invocations'].append(copy.deepcopy(state['invocations'][0]))
    elif tamper == 'two-calls': state['calls'] = 2
    else: state['invocations'][0]['status'] = 'pending'
    row = evidence(state, receipt)
    assert row['completed'] is False
    assert 'private-unexpected' not in json.dumps(row)


def test_failed_provider_receipt_retains_its_one_recorded_request_without_claiming_success():
    state, receipt = recorded_case()
    state['status'] = 'blocked'
    receipt['result'].update(exit_code=302, token_usage=None)
    state['invocations'][0]['token_usage'] = None
    receipt['result']['metadata'].pop('request_model')
    row = evidence(state, receipt)
    assert row['completed'] is False and row['provider_requests'] == 1 and row['tool_calls'] == 0
    assert row['request_model'] is None and row['token_usage'] is None
