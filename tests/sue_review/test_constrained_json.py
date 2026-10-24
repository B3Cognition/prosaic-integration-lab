"""Explicit schema generation preserves raw SUE validation and frozen policy."""
from copy import deepcopy
import json
import uuid

import castle_sue as engine
import pytest
from prosaic_harness import FileRunStore
from prosaic_runtime import EndpointConfig, ProsaicRuntime, RuntimeConfig

from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.sue_review.contracts import ReviewError, ReviewSettings, digest
from prosaic_integration_lab.sue_review.session import SueReviewSession
from tests.sue_review.test_execution import CLAIM, SOURCE, answer, fixture, script


def session(store, url, *, constrained=True, enabled=True):
    config = RuntimeConfig({'fixture': EndpointConfig(url, 'sue-fixture', features={'streaming': False})}, {}, 'fixture')
    settings = {'enabled': True} if enabled else {'enabled': False}
    return SueReviewSession(settings=settings, store=store, config=config,
        principal=Principal('tenant', 'alice', 'payer'), namespace='sue-test', constrained_json=constrained)


def start(flow, run_id, *, max_turns=14):
    return flow.start(run_id, seed=CLAIM, sources=[{'sourceId': 'spec', 'text': SOURCE}], max_turns=max_turns)


def require_candidate_or_fail_closed(flow, run_id, requests):
    if 'json_schema_v1' in ProsaicRuntime.capabilities:
        return True
    with pytest.raises(ReviewError, match='constrained_json_unavailable'):
        start(flow, run_id)
    assert requests == []
    return False


@pytest.mark.parametrize('value', [0, 1, 'true', None])
def test_constrained_json_setting_requires_a_boolean(value):
    with pytest.raises(ReviewError, match='invalid_review_settings'):
        session(None, 'http://127.0.0.1:9/v1', constrained=value)


def test_generation_is_disabled_and_legacy_policy_is_byte_compatible(tmp_path):
    assert ReviewSettings().enabled is False
    with fixture([answer('DEFINE')]) as (url, requests), FileRunStore(tmp_path/'runs', namespace='sue-test') as store:
        flow = session(store, url, constrained=False); run_id = uuid.uuid4().hex
        waiting = start(flow, run_id, max_turns=1)
        request = store.load_run(run_id).state['inputs']
        assert 'constrained_json' not in request['reviewPolicy']
        assert start(flow, run_id, max_turns=1) == waiting
        result = flow.resume(run_id, expected_revision=waiting['revision'], choice='continue')
        assert result['status'] == 'completed' and len(requests) == 1
        assert 'response_format' not in requests[0]


def test_each_turn_requests_exact_canonical_dynamic_schema(tmp_path):
    values, final_state = script()
    with fixture(values) as (url, requests), FileRunStore(tmp_path/'runs', namespace='sue-test') as store:
        flow = session(store, url); run_id = uuid.uuid4().hex
        if not require_candidate_or_fail_closed(flow, run_id, requests): return
        waiting = start(flow, run_id)
        assert requests == [] and waiting['proposal']['policy']['constrained_json'] is True
        result = flow.resume(run_id, expected_revision=waiting['revision'], choice='continue')
        assert result['status'] == 'completed' and result['terminal'] == final_state['terminal']
        assert len(requests) == len(values)
        state = engine.initial_state(CLAIM, max_turns=14)
        for wire, value in zip(requests, values, strict=True):
            schema = engine.schema(state)
            assert wire['response_format'] == {'type': 'json_schema', 'json_schema': {'name': 'response', 'schema': schema, 'strict': True}}
            assert wire.get('tools', []) == []
            state, failure = engine.advance(state, value, SOURCE.splitlines())
            assert failure is None
        before = len(requests)
        assert flow.resume(run_id, expected_revision=result['revision']) == result
        assert len(requests) == before


def test_frozen_opt_in_survives_reconstruction_and_retry(tmp_path):
    values, _ = script(max_turns=1)
    with fixture(['{}', *values]) as (url, requests), FileRunStore(tmp_path/'runs', namespace='sue-test') as store:
        flow = session(store, url); run_id = uuid.uuid4().hex
        if not require_candidate_or_fail_closed(flow, run_id, requests): return
        waiting = start(flow, run_id, max_turns=1)
        reconstructed = session(store, url, constrained=False)
        assert reconstructed.status(run_id) == waiting
        disabled = session(store, url, enabled=False)
        assert disabled.status(run_id) == waiting
        with pytest.raises(ReviewError, match='review_disabled'):
            disabled.resume(run_id, expected_revision=waiting['revision'], choice='continue')
        assert requests == []
        result = reconstructed.resume(run_id, expected_revision=waiting['revision'], choice='continue')
        assert result['status'] == 'completed' and result['acceptedTurns'] == 1
        assert len(requests) == 2 and requests[0]['response_format'] == requests[1]['response_format']
        saved = store.load_run(run_id).state
        assert len(saved['invocations']) == 2 and len(saved['outputs']) == 1
        assert reconstructed.report(run_id)['reportedTokens'] == 30


@pytest.mark.parametrize('mutation', ['missing_addresses', 'fenced', 'false_quote', 'future_turn', 'unsupported_claim'])
def test_constrained_request_never_admits_invalid_sue_output(tmp_path, mutation):
    value = deepcopy(answer('DEFINE'))
    if mutation == 'missing_addresses': value.pop('addresses')
    elif mutation == 'false_quote': value['evidence'][0]['quote'] = 'Fabricated source text.'
    elif mutation == 'future_turn': value['addresses'] = [1]
    elif mutation == 'unsupported_claim': value.update(verdict='CONTRADICTED', test_result='CONFLICT')
    raw = '```json\n' + json.dumps(value) + '\n```' if mutation == 'fenced' else json.dumps(value)
    with fixture([raw]) as (url, requests), FileRunStore(tmp_path/'runs', namespace='sue-test') as store:
        flow = session(store, url); run_id = uuid.uuid4().hex
        if not require_candidate_or_fail_closed(flow, run_id, requests): return
        waiting = start(flow, run_id)
        result = flow.resume(run_id, expected_revision=waiting['revision'], choice='continue')
        assert result['status'] == 'blocked' and result['acceptedTurns'] == 0
        assert len(requests) == 2 and store.load_run(run_id).state['outputs'] == {}
        assert all(w['response_format']['json_schema']['strict'] is True for w in requests)
        assert flow.report(run_id)['reportedTokens'] == 30


def test_opt_in_has_a_distinct_binding_without_changing_legacy_binding(tmp_path):
    from prosaic_integration_lab.sue_review.workflow import build_review_workflow
    from prosaic_integration_lab.sue_review.guidance import GUIDANCE_SHA256
    config = RuntimeConfig({'fixture': EndpointConfig('http://127.0.0.1:9/v1', 'sue-fixture')}, {}, 'fixture')
    settings = ReviewSettings(enabled=True)
    policy = {k: v for k, v in vars(settings).items() if k not in {'enabled', 'constrained_json'}}
    policy['engine_identity'] = engine.capabilities()['engineIdentity']['digest']
    legacy_version = 'sue-review-v1.2-' + digest({'engine': engine.capabilities(), 'policy': policy, 'answerGuidanceSha256': GUIDANCE_SHA256})
    legacy = build_review_workflow(config=config, settings=settings, engine=engine)
    with fixture([answer('DEFINE')]) as (url, requests), FileRunStore(tmp_path/'runs', namespace='sue-test') as store:
        flow = session(store, url, constrained=False); run_id = uuid.uuid4().hex
        waiting = start(flow, run_id, max_turns=1)
        result = flow.resume(run_id, expected_revision=waiting['revision'], choice='continue')
        assert result['status'] == 'completed'
        saved = store.load_run(run_id).state
        receipt = store.load_receipt(run_id, saved['invocations'][0]['id'])
        assert receipt['result']['metadata']['runtime_adapter_v1']['version'] == legacy_version
    if 'json_schema_v1' not in ProsaicRuntime.capabilities:
        with pytest.raises(ReviewError, match='constrained_json_unavailable'):
            build_review_workflow(config=config, settings=ReviewSettings(enabled=True), engine=engine, constrained_json=True)
    else:
        enabled = build_review_workflow(config=config, settings=ReviewSettings(enabled=True), engine=engine, constrained_json=True)
        assert enabled.fingerprint != legacy.fingerprint
