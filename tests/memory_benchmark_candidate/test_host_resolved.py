"""Public installed Runtime/Harness acceptance and frozen unknown-usage lanes."""
from copy import deepcopy

import pytest

from lab_runner.memory_benchmark import generation as g, completeness_profile as review
from lab_runner.memory_benchmark.workflow import initial_packet, run_answer
from .test_completeness_profile import fixture, Provider

PROFILE='compact-host-resolved-v1'

@pytest.mark.parametrize('castle',[False,True])
def test_host_format_canonical_acceptance_review_and_resume(castle,tmp_path):
    q,draft,frames,identity=fixture(castle=castle);packet=initial_packet(q,frames,identity)
    wire=g.encode_candidate(draft,packet,profile=PROFILE)
    with Provider([wire,dict(feedback='No supported correction.'),wire]) as server:
        base=run_answer(server.config,packet,tmp_path/'base',generation_profile=PROFILE)
        assert base['candidate']==draft
        assert run_answer(server.config,packet,tmp_path/'base',generation_profile=PROFILE)['usage']['providerRequests']==0
        with pytest.raises(ValueError):run_answer(server.config,packet,tmp_path/'base',generation_profile=g.QUESTION_FOCUSED)
        frozen=review.freeze_packet(q,draft,frames,identity=identity)
        result=review.run_review(server.config,frozen,tmp_path/'review',generation_profile=PROFILE)
        assert result['candidate']==draft
        assert review.run_review(server.config,frozen,tmp_path/'review',generation_profile=PROFILE)['usage']['providerRequests']==0
        assert len(server.requests)==3
        schema=server.requests[0]['response_format']['json_schema']['schema']
        assert set(schema['properties']['questionParts']['items']['properties'])=={'id','quote','claimIds','missingEvidenceIndices'}
        assert set(schema['properties']['frameReview']['items']['properties'])=={'frameId','reason','unreferencedDisposition'}
        assert all(request['max_tokens']==4096 and 'tools' not in request for request in server.requests)

def test_rejected_nonexact_question_keeps_raw_receipt_without_retry(tmp_path):
    q,draft,frames,identity=fixture();packet=initial_packet(q,frames,identity)
    wire=g.encode_candidate(draft,packet,profile=PROFILE);wire['questionParts'][0]['quote']='not the frozen question'
    with Provider([wire]) as server:
        result=run_answer(server.config,packet,tmp_path/'base',generation_profile=PROFILE)
        assert result['candidate'] is None
        assert 'not the frozen question' in result['evidence']['receipts'][0]['result']['stdout']
        run_answer(server.config,packet,tmp_path/'base',generation_profile=PROFILE)
        assert len(server.requests)==1

def test_frozen_host_profile_fixture_and_unknown_reservation(tmp_path):
    from lab_runner.memory_benchmark.dataset import freeze
    from lab_runner.memory_benchmark.fixture import FixtureServer
    from lab_runner.memory_benchmark.runner import run,replay
    from .test_runner import inputs
    inputs(tmp_path);frozen=tmp_path/'host-frozen'
    freeze(tmp_path/'dataset.json',tmp_path/'policy.json',frozen,generation_profile=PROFILE)
    result=run(frozen,tmp_path/'run',fixture=True,review=True)
    assert result['completed']==result['acceptedReviews']==3
    assert result['providerRequests']==9 and result['semanticQuality']=='unmeasured'
    assert replay(frozen,tmp_path/'run')==result
    with FixtureServer(missing_usage=True) as server:
        unknown=run(frozen,tmp_path/'unknown',fixture=True,review=True,_fixture_server=server)
        assert unknown['unknownSamples']==1 and unknown['blocked']==2
        assert unknown['actualTokens'] is None
        assert unknown['retained']==dict(providerRequests=3,reportedTokens=98304,toolCalls=0)
        assert replay(frozen,tmp_path/'unknown')==unknown
        assert len(server.requests)==1
