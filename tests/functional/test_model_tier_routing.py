"""Distinct dispatch evidence through the installed public factory and Harness."""
import importlib.util
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

import pytest
from prosaic_harness import Harness, WorkflowAdmissionError
from prosaic_runtime import EndpointConfig, RuntimeConfig

ROOT = Path(__file__).resolve().parents[2]


def implementation():
    path = ROOT / 'scripts/local_routing_smoke.py'
    assert path.is_file(), 'public factory routing consumer is missing'
    spec = importlib.util.spec_from_file_location('local_routing_smoke', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def routing_endpoint():
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            calls.append(body)
            content = json.dumps({'result': 'invalid' if body['model'] == 'fixture-fail' else 'routing ok'})
            response = json.dumps({'id': 'routing-fixture', 'object': 'chat.completion',
                'model': body['model'], 'choices': [{'index': 0, 'message': {
                    'role': 'assistant', 'content': content}, 'finish_reason': 'stop'}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15}}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1', calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()


def config(url, *, routes=None):
    return RuntimeConfig({tier: EndpointConfig(url, f'fixture-{tier}', max_tokens=128,
        features={'streaming': False}) for tier in ('default', 'balanced', 'strong')},
        {'balanced': 'balanced', 'strong': 'strong'} if routes is None else routes, 'default')


@pytest.mark.parametrize('tier', ['default', 'balanced', 'strong'])
def test_public_factory_selects_distinct_models(tier, routing_endpoint, tmp_path):
    url, calls = routing_endpoint
    module = implementation()
    grants = frozenset() if tier == 'default' else frozenset({tier})
    factory = module.create_factory(config(url), tiers=grants)
    workflow = factory.build_json(json.dumps(module.proposal(tier)))
    result = Harness(workflow, (tmp_path / tier).resolve()).run({})
    assert result['status'] == 'completed'
    assert [request['model'] for request in calls] == [f'fixture-{tier}']
    assert calls[0].get('stream', False) is False
    assert not calls[0].get('tools')
    assert calls[0]['max_tokens'] == 128


@pytest.mark.parametrize(('grants', 'routes', 'tier'), [
    (frozenset({'balanced'}), {'balanced': 'balanced', 'strong': 'strong'}, 'strong'),
    (frozenset({'strong'}), {'balanced': 'balanced'}, 'strong'),
])
def test_tier_requires_both_grant_and_route_before_state_or_dispatch(grants, routes, tier,
        routing_endpoint, tmp_path):
    url, calls = routing_endpoint
    module = implementation()
    factory = module.create_factory(config(url, routes=routes), tiers=grants)
    run_dir = tmp_path / 'rejected'
    with pytest.raises(WorkflowAdmissionError):
        workflow = factory.build_json(json.dumps(module.proposal(tier)))
        Harness(workflow, run_dir.resolve()).run({})
    assert not run_dir.exists()
    assert calls == []


def test_catalogue_projects_route_grant_intersection_without_host_bindings(routing_endpoint):
    url, calls = routing_endpoint
    factory = implementation().create_factory(config(url, routes={'balanced': 'balanced'}),
        tiers=frozenset({'balanced', 'strong'}))
    document = factory.describe()
    assert document['modelTiers'] == ['balanced']
    assert document['defaultModelTierAllowed'] is True
    serialized = json.dumps(document)
    assert url not in serialized and 'fixture-strong' not in serialized
    assert 'api_key' not in serialized
    assert calls == []


@pytest.mark.parametrize('composition', [False, True])
def test_balanced_then_strong_requires_independent_composition_grant(composition,
        routing_endpoint, tmp_path):
    url, calls = routing_endpoint
    module = implementation()
    factory = module.create_factory(config(url), tiers=frozenset({'balanced', 'strong'}),
        composition=composition)
    envelope = module.proposal('balanced')
    steps = envelope['definition']['steps']
    steps['ask']['next'] = 'review'
    steps['review'] = {'kind': 'agent', 'agent': 'strong', 'schema': 'result',
        'inputs': ['ask'], 'next': 'done'}
    steps['done']['requires'] = ['ask', 'review']
    run_dir = tmp_path / 'composition'
    if composition:
        workflow = factory.build_json(json.dumps(envelope))
        result = Harness(workflow, run_dir.resolve()).run({})
        assert result['status'] == 'completed'
        assert [body['model'] for body in calls] == ['fixture-balanced', 'fixture-strong']
    else:
        with pytest.raises(WorkflowAdmissionError):
            factory.build_json(json.dumps(envelope))
        assert calls == [] and not run_dir.exists()


@pytest.mark.parametrize('injection', [
    {'bindings': {'base_url': 'https://cloud.invalid/v1', 'api_key_file': '/private/token'}},
    {'resources': {'runtime': {'profiles': {'evil': {'model': 'private'}}}}},
])
def test_client_cannot_inject_host_bindings(injection, routing_endpoint, tmp_path):
    url, calls = routing_endpoint
    module = implementation()
    factory = module.create_factory(config(url), tiers=frozenset({'balanced', 'strong'}))
    envelope = module.proposal('default')
    envelope['definition'].update(injection)
    with pytest.raises(WorkflowAdmissionError):
        workflow = factory.build_json(json.dumps(envelope))
        Harness(workflow, (tmp_path / 'injection').resolve()).run({})
    assert calls == [] and not (tmp_path / 'injection').exists()


@pytest.mark.parametrize('fail_balanced', [False, True])
def test_local_smoke_shares_three_calls_and_stops_on_first_failed_output(fail_balanced,
        routing_endpoint, tmp_path):
    import yaml
    url, calls = routing_endpoint
    module = implementation()
    secret = tmp_path / 'fixture-token'
    secret.write_text('fixture-token-never-exported')
    data = {'default_profile': 'default', 'routes': {'balanced': 'balanced', 'strong': 'strong'},
        'profiles': {tier: {'base_url': url,
            'model': 'fixture-fail' if fail_balanced and tier == 'balanced' else f'fixture-{tier}',
            'api_key_file': str(secret), 'max_tokens': 128, 'features': {'streaming': False}}
            for tier in ('default', 'balanced', 'strong')}}
    path = tmp_path / 'local.yml'
    path.write_text(yaml.safe_dump(data))
    receipt = module.smoke(path, live_local=True, max_calls=3)
    assert receipt['passed'] is (not fail_balanced)
    assert len(calls) == receipt['invocations_reserved'] == (2 if fail_balanced else 3)
    assert [body['model'] for body in calls] == (['fixture-default', 'fixture-fail'] if fail_balanced
        else ['fixture-default', 'fixture-balanced', 'fixture-strong'])
    assert 'fixture-token-never-exported' not in json.dumps(receipt)
    assert receipt['provider_requests'] == (2 if fail_balanced else 3)
    assert receipt['tool_calls'] == 0
    if not fail_balanced:
        assert [row['request_model'] for row in receipt['cases']] == [body['model'] for body in calls]
        assert [row['profile'] for row in receipt['cases']] == ['default', 'balanced', 'strong']
        assert all(row['provider_requests'] == 1 and row['tool_calls'] == 0 and row['token_usage'] == 15
            for row in receipt['cases'])


@pytest.fixture
def trap_proxy():
    """A distinct actual HTTP proxy fixture; no private credential is used."""
    observed = []
    class Handler(BaseHTTPRequestHandler):
        def trap(self):
            observed.append({'path': self.path, 'authorization': self.headers.get('Authorization')})
            if self.command == 'POST': self.rfile.read(int(self.headers.get('Content-Length', '0')))
            self.send_response(502)
            self.send_header('Content-Length', '0')
            self.end_headers()
        do_GET = do_POST = do_CONNECT = trap
        def log_message(self, *_): pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', observed
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
        assert not thread.is_alive()


def local_configuration(tmp_path, url):
    import yaml
    secret = tmp_path / 'fixture-token'
    secret.write_text('fixture-token-never-exported')
    data = {'default_profile': 'default', 'routes': {'balanced': 'balanced', 'strong': 'strong'},
        'profiles': {tier: {'base_url': url, 'model': f'fixture-{tier}',
            'api_key_file': str(secret), 'max_tokens': 128, 'features': {'streaming': False}}
            for tier in ('default', 'balanced', 'strong')}}
    path = tmp_path / 'local.yml'; path.write_text(yaml.safe_dump(data))
    return path


def test_local_credentials_cannot_reach_ambient_external_proxy(routing_endpoint, trap_proxy,
        tmp_path, monkeypatch):
    url, calls = routing_endpoint
    proxy, trapped = trap_proxy
    monkeypatch.setenv('http_proxy', proxy)
    monkeypatch.setenv('HTTP_PROXY', proxy)
    monkeypatch.setenv('CUSTOM_PrOxY', proxy)
    monkeypatch.setenv('no_proxy', '')
    monkeypatch.setenv('NO_PROXY', '')
    before = dict(os.environ)
    receipt = implementation().smoke(local_configuration(tmp_path, url), live_local=True, max_calls=3)
    assert trapped == [], 'credential-bearing local request reached ambient proxy'
    assert receipt['passed'] is True and len(calls) == 3
    assert dict(os.environ) == before


@pytest.fixture
def redirect_endpoint(trap_proxy):
    target, trapped = trap_proxy
    accepted = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            accepted.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(302)
            self.send_header('Location', target + '/must-not-receive-credentials')
            self.send_header('Content-Length', '0')
            self.end_headers()
        def log_message(self, *_): pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1', accepted, trapped
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
        assert not thread.is_alive()


def test_redirect_is_not_followed_and_retains_first_call_without_next_invocation(redirect_endpoint, tmp_path):
    url, accepted, trapped = redirect_endpoint
    receipt = implementation().smoke(local_configuration(tmp_path, url), live_local=True, max_calls=3)
    assert trapped == [] and len(accepted) == 1
    assert accepted[0]['model'] == 'fixture-default'
    assert receipt['passed'] is False and receipt['invocations_reserved'] == 1
    assert receipt['provider_requests'] == 1 and receipt['tool_calls'] == 0
    assert receipt['cases'] == [{'tier': 'default', 'completed': False, 'profile': 'default',
        'request_model': None, 'provider_requests': 1, 'tool_calls': 0, 'token_usage': None}]


@pytest.mark.parametrize('tamper', ['wrong-model', 'missing-budgets', 'extra-provider'])
def test_completed_workflow_with_contradictory_recorded_receipt_stops_before_next_case(
        routing_endpoint, tmp_path, monkeypatch, tamper):
    import copy
    url, calls = routing_endpoint
    module = implementation()
    validate = module.recorded_evidence
    inspected = []
    def contradictory(state, receipt, **expected):
        # Test only the consumer's evidence boundary; installed SDKs stay unchanged.
        assert state['status'] == 'completed' and state['calls'] == 1
        inspected.append(receipt['id'])
        changed = copy.deepcopy(receipt)
        metadata = changed['result']['metadata']
        if tamper == 'wrong-model': metadata['request_model'] = 'private-unexpected-model'
        elif tamper == 'missing-budgets': metadata.pop('invocation_budgets_v1')
        else: metadata['invocation_budgets_v1']['provider_requests'] = 2
        return validate(state, changed, **expected)
    monkeypatch.setattr(module, 'recorded_evidence', contradictory)
    receipt = module.smoke(local_configuration(tmp_path, url), live_local=True, max_calls=3)
    assert receipt['passed'] is False and receipt['invocations_reserved'] == 1
    assert len(calls) == len(inspected) == len(receipt['cases']) == 1
    assert calls[0]['model'] == 'fixture-default'
    assert 'private-unexpected-model' not in json.dumps(receipt)
