"""New declared-order profile through public installed SDKs and actual HTTP."""
from copy import deepcopy

import pytest

from lab_runner.memory_benchmark import completeness_profile as review, generation as g
from lab_runner.memory_benchmark.workflow import initial_packet, run_answer
from .test_completeness_profile import fixture, Provider

ORDERED = 'compact-question-first-v1'
FOCUSED = 'compact-question-focused-v1'


@pytest.mark.parametrize('castle', [False, True])
@pytest.mark.parametrize('profile', [ORDERED, FOCUSED])
def test_order_profile_transport_strict_answer_review_and_bound_resume(castle, profile, tmp_path):
    q, draft, frames, identity = fixture(castle=castle)
    packet = initial_packet(q, frames, identity)
    wire = g.encode_candidate(draft, packet)
    with Provider([wire, dict(feedback='No supported corrections.'), wire]) as server:
        base = run_answer(server.config, packet, tmp_path/'base', generation_profile=profile)
        assert base['candidate'] == draft
        assert run_answer(server.config, packet, tmp_path/'base', generation_profile=profile)['usage']['providerRequests'] == 0
        with pytest.raises(ValueError): run_answer(server.config, packet, tmp_path/'base', generation_profile=g.COMPACT)
        frozen = review.freeze_packet(q, draft, frames, identity=identity)
        final = review.run_review(server.config, frozen, tmp_path/'review', generation_profile=profile)
        assert final['candidate'] == draft
        assert review.run_review(server.config, frozen, tmp_path/'review', generation_profile=profile)['usage']['providerRequests'] == 0
        assert len(server.requests) == 3
        schema = server.requests[0]['response_format']['json_schema']['schema']
        assert list(schema['properties']) == list(review.ANSWER_SCHEMA['properties'])
        assert list(schema['properties'])[0] == 'questionParts'
        assert list(schema['properties']['questionParts']['items']['properties']) == list(
            review.ANSWER_SCHEMA['properties']['questionParts']['items']['properties'])
        receipt = base['evidence']['receipts'][0]['result']
        assert receipt['metadata']['response_schema_order_v1']['mode'] == 'declared'
        assert set(server.requests[1]['response_format']['json_schema']['schema']['properties']) == {'feedback'}
        for request in server.requests:
            assert request['max_tokens'] == 4096 and 'tools' not in request
        import json
        critic_args = json.loads(server.requests[1]['messages'][-1]['content'].split('Task arguments:\n', 1)[-1])
        repair_args = json.loads(server.requests[2]['messages'][-1]['content'].split('Task arguments:\n', 1)[-1])
        assert critic_args['artifacts'] == critic_args['artifact_bindings'] == {}
        assert set(repair_args['artifacts']) == {'critic'}
        assert critic_args['request']['packet']['frames'] == repair_args['request']['packet']['frames']
        assert critic_args['request']['packet']['frames'] == g.model_request(frozen, initial=False, profile=g.COMPACT)['packet']['frames']


def test_order_profile_rejects_invalid_wire_keeps_receipt_and_never_retries(tmp_path):
    q, draft, frames, identity = fixture(); packet = initial_packet(q, frames, identity)
    wire = g.encode_candidate(draft, packet); wire['questionParts'][0]['claimIds'] = ['foreign']
    with Provider([wire]) as server:
        result = run_answer(server.config, packet, tmp_path/'base', generation_profile=ORDERED)
        assert result['candidate'] is None
        assert 'foreign' in result['evidence']['receipts'][0]['result']['stdout']
        run_answer(server.config, packet, tmp_path/'base', generation_profile=ORDERED)
        assert len(server.requests) == 1


def test_reordering_semantically_equal_schema_cannot_resume_silently(tmp_path, monkeypatch):
    q, draft, frames, identity = fixture(); packet = initial_packet(q, frames, identity)
    wire = g.encode_candidate(draft, packet)
    with Provider([wire]) as server:
        assert run_answer(server.config, packet, tmp_path/'base', generation_profile=ORDERED)['candidate'] == draft
        original = g.response_schema
        def reordered(*args, **kwargs):
            schema = original(*args, **kwargs)
            schema['properties'] = dict(reversed(list(schema['properties'].items())))
            return schema
        monkeypatch.setattr(g, 'response_schema', reordered)
        with pytest.raises(ValueError): run_answer(server.config, packet, tmp_path/'base', generation_profile=ORDERED)
        assert len(server.requests) == 1


@pytest.mark.parametrize('profile', [ORDERED, FOCUSED])
def test_fixture_runner_profile_replay_and_unknown_reservation(profile, tmp_path):
    from lab_runner.memory_benchmark.dataset import freeze
    from lab_runner.memory_benchmark.fixture import FixtureServer
    from lab_runner.memory_benchmark.runner import run, replay
    from .test_runner import inputs
    inputs(tmp_path)
    frozen = tmp_path/'frozen-profile'
    freeze(tmp_path/'dataset.json', tmp_path/'policy.json', frozen, generation_profile=profile)
    output = tmp_path/'run'
    result = run(frozen, output, fixture=True, review=True)
    assert result['completed'] == result['acceptedReviews'] == 3
    assert result['providerRequests'] == 9 and result['semanticQuality'] == 'unmeasured'
    assert replay(frozen, output) == result
    with FixtureServer(missing_usage=True) as server:
        result = run(frozen, tmp_path/'unknown', fixture=True, review=True, _fixture_server=server)
        assert result['unknownSamples'] == 1 and result['blocked'] == 2
        assert result['actualTokens'] is None
        assert result['retained'] == {'providerRequests': 3, 'reportedTokens': 98304, 'toolCalls': 0}
        assert replay(frozen, tmp_path/'unknown') == result
        assert len(server.requests) == 1
