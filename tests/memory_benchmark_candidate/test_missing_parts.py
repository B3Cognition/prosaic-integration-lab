"""Installed workflows, strict rejected output, resume and fixture controls."""
from copy import deepcopy
import json
import pytest
from lab_runner.memory_benchmark import generation as g, completeness_profile as review
from lab_runner.memory_benchmark.workflow import initial_packet,run_answer,unanswered
from .test_completeness_profile import fixture,Provider

PROFILE='compact-host-missing-parts-v1'

@pytest.mark.parametrize('castle',[False,True])
@pytest.mark.parametrize('missing',[False,True])
def test_answer_review_resume_keeps_explicit_model_owned_links(castle,missing,tmp_path):
    q,draft,frames,identity=fixture(castle=castle);packet=initial_packet(q,frames,identity)
    if missing:draft=unanswered(q,frames)
    wire=g.encode_candidate(draft,packet,profile=PROFILE)
    with Provider([wire,dict(feedback='No supported correction.'),wire]) as server:
        answer=run_answer(server.config,packet,tmp_path/'answer',generation_profile=PROFILE)
        expected=g.resolve(wire,packet,profile=PROFILE)
        assert answer['candidate']==expected
        assert run_answer(server.config,packet,tmp_path/'answer',generation_profile=PROFILE)['usage']['providerRequests']==0
        with pytest.raises(ValueError):run_answer(server.config,packet,tmp_path/'answer',generation_profile=g.CLAIM_PARTS)
        frozen=review.freeze_packet(q,expected,frames,identity=identity)
        result=review.run_review(server.config,frozen,tmp_path/'review',generation_profile=PROFILE)
        assert result['candidate']==expected
        assert review.run_review(server.config,frozen,tmp_path/'review',generation_profile=PROFILE)['usage']['providerRequests']==0
        assert len(server.requests)==3
        assert all(r['max_tokens']==4096 and 'tools' not in r for r in server.requests)

@pytest.mark.parametrize('mutation',['foreign','empty','numeric','answered'])
def test_bad_missing_ownership_keeps_raw_failure_no_retry(mutation,tmp_path):
    q,_,frames,identity=fixture();packet=initial_packet(q,frames,identity)
    wire=g.encode_candidate(unanswered(q,frames),packet,profile=PROFILE)
    if mutation=='foreign':wire['missingEvidence'][0]['questionPartIds']=['foreign']
    if mutation=='empty':wire['missingEvidence'][0]['questionPartIds']=[]
    if mutation=='numeric':wire['questionParts'][0]['missingEvidenceIndices']=[0]
    if mutation=='answered':wire['status']='answered'
    before=deepcopy(wire)
    with Provider([wire]) as server:
        result=run_answer(server.config,packet,tmp_path/'bad',generation_profile=PROFILE)
        assert result['candidate'] is None
        assert json.loads(result['evidence']['receipts'][0]['result']['stdout'])==before
        run_answer(server.config,packet,tmp_path/'bad',generation_profile=PROFILE)
        assert len(server.requests)==1

def test_fixture_replay_and_unknown_usage_reservations_stay_bounded(tmp_path):
    from lab_runner.memory_benchmark.dataset import freeze
    from lab_runner.memory_benchmark.fixture import FixtureServer
    from lab_runner.memory_benchmark.runner import run,replay
    from .test_runner import inputs
    inputs(tmp_path);frozen=tmp_path/'missing-parts-frozen'
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
        assert replay(frozen,tmp_path/'unknown')==unknown and len(server.requests)==1
