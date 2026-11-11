"""Actual SDK transport/checkpoint tests; synthetic responses, no model quality."""
from copy import deepcopy
from pathlib import Path

import pytest

from lab_runner.memory_benchmark import completeness_profile as review, generation as g
from lab_runner.memory_benchmark.workflow import initial_packet, run_answer
from lab_runner.memory_benchmark.runner import _check_stage, run, replay
from lab_runner.memory_benchmark.storage import read, sha
from lab_runner.memory_benchmark.dataset import freeze
from .test_completeness_profile import fixture, Provider
from .test_runner import inputs


@pytest.mark.parametrize('castle', [False, True])
def test_compact_answer_critic_repair_and_zero_call_resume(castle, tmp_path):
    q, draft, frames, identity = fixture(castle=castle)
    packet = initial_packet(q, frames, identity)
    wire = g.encode_candidate(draft, packet)
    with Provider([wire, dict(feedback='Retain all supported facts and the default boundary.'), wire]) as server:
        result = run_answer(server.config, packet, tmp_path/'base', generation_profile=g.COMPACT)
        assert result['candidate'] == draft and result['status'] == 'completed'
        assert result['evidence']['checkpoint']['outputs']['answer'] == wire
        _check_stage(result, packet, 'base', generation_profile=g.COMPACT)
        assert run_answer(server.config, packet, tmp_path/'base', generation_profile=g.COMPACT)['usage']['providerRequests'] == 0
        frozen = review.freeze_packet(q, draft, frames, identity=identity)
        final = review.run_review(server.config, frozen, tmp_path/'review', generation_profile=g.COMPACT)
        assert final['candidate'] == draft and final['status'] == 'completed'
        _check_stage(final, frozen, 'review', generation_profile=g.COMPACT)
        assert review.run_review(server.config, frozen, tmp_path/'review', generation_profile=g.COMPACT)['usage']['providerRequests'] == 0
        assert len(server.requests) == 3
        for request in server.requests:
            assert request['max_tokens'] == 4096 and 'tools' not in request
        assert set(server.requests[1]['response_format']['json_schema']['schema']['properties']) == {'feedback'}
        changed = deepcopy(result); changed['candidate']['claims'][0]['text'] = 'Unrecorded alteration'
        with pytest.raises(ValueError): _check_stage(changed, packet, 'base', generation_profile=g.COMPACT)
        with pytest.raises(ValueError): run_answer(server.config, packet, tmp_path/'base')
        assert len(server.requests) == 3


def test_bad_wire_rejected_with_untouched_raw_receipt_and_no_retry(tmp_path):
    q, draft, frames, identity = fixture(); packet = initial_packet(q, frames, identity)
    wire = g.encode_candidate(draft, packet); wire['evidence'][0]['quoteId'] = 'not-issued'
    with Provider([wire]) as server:
        result = run_answer(server.config, packet, tmp_path/'base', generation_profile=g.COMPACT)
        assert result['candidate'] is None and result['status'] != 'completed'
        assert 'not-issued' in result['evidence']['receipts'][0]['result']['stdout']
        run_answer(server.config, packet, tmp_path/'base', generation_profile=g.COMPACT)
        assert len(server.requests) == 1


def compact_inputs(tmp_path, count=1):
    inputs(tmp_path, count)
    output = tmp_path/'compact-frozen'
    freeze(tmp_path/'dataset.json', tmp_path/'policy.json', output, generation_profile=g.COMPACT)
    return output


def test_compact_fixture_runner_and_sealed_replay_keep_canonical_candidates(tmp_path):
    frozen = compact_inputs(tmp_path); output = tmp_path/'run'
    result = run(frozen, output, fixture=True, review=True)
    assert result['completed'] == 3 and result['acceptedReviews'] == 3 and result['providerRequests'] == 9
    assert result['semanticQuality'] == 'unmeasured'
    before = {str(p): sha(p.read_bytes()) for p in output.rglob('*') if p.is_file()}
    assert replay(frozen, output) == run(frozen, output, fixture=True, review=True) == result
    assert before == {str(p): sha(p.read_bytes()) for p in output.rglob('*') if p.is_file()}
    for sample in result['samples']:
        row = read(output/sample['path'])
        assert row['base']['candidate']['evidence'][0]['quote']
        assert 'quoteId' in row['base']['evidence']['checkpoint']['outputs']['answer']['evidence'][0]


def test_compact_unknown_usage_retains_full_reservation_and_blocks(tmp_path):
    from lab_runner.memory_benchmark.fixture import FixtureServer
    frozen = compact_inputs(tmp_path, 2); output = tmp_path/'run'
    with FixtureServer(missing_usage=True) as server:
        result = run(frozen, output, fixture=True, review=True, _fixture_server=server)
        assert result['unknownSamples'] == 1 and result['blocked'] == 5
        assert result['retained']['providerRequests'] == 3 and result['retained']['reportedTokens'] == 98304
        assert result['actualTokens'] is None
        assert replay(frozen, output) == result
        assert run(frozen, output, fixture=True, review=True, _fixture_server=server) == result
        assert len(server.requests) == 1
