"""Installed public workflows preserve the new ownership boundary and receipts."""
from copy import deepcopy

import pytest

from lab_runner.memory_benchmark import generation as g, completeness_profile as review
from lab_runner.memory_benchmark.workflow import initial_packet, run_answer
from .test_completeness_profile import fixture, Provider

PROFILE='compact-host-claim-parts-v1'

@pytest.mark.parametrize('castle',[False,True])
def test_stable_quote_links_and_host_reasons_across_review_and_resume(castle,tmp_path):
    q,draft,frames,identity=fixture(castle=castle);packet=initial_packet(q,frames,identity)
    wire=g.encode_candidate(draft,packet,profile=PROFILE)
    with Provider([wire,dict(feedback='No supported correction.'),wire]) as server:
        base=run_answer(server.config,packet,tmp_path/'base',generation_profile=PROFILE)
        expected=g.resolve(wire,packet,profile=PROFILE)
        assert base['candidate']==expected
        assert len({e['id'] for e in expected['evidence']})==len(expected['evidence'])
        assert run_answer(server.config,packet,tmp_path/'base',generation_profile=PROFILE)['usage']['providerRequests']==0
        with pytest.raises(ValueError):run_answer(server.config,packet,tmp_path/'base',generation_profile=g.HOST_RESOLVED)
        frozen=review.freeze_packet(q,expected,frames,identity=identity)
        result=review.run_review(server.config,frozen,tmp_path/'review',generation_profile=PROFILE)
        assert result['candidate']==expected
        assert review.run_review(server.config,frozen,tmp_path/'review',generation_profile=PROFILE)['usage']['providerRequests']==0
        assert len(server.requests)==3
        assert all(r['max_tokens']==4096 and 'tools' not in r for r in server.requests)

@pytest.mark.parametrize('mutation',['duplicate','reason','question-part'])
def test_bad_model_bookkeeping_keeps_exact_raw_failure_without_retry(mutation,tmp_path):
    q,draft,frames,identity=fixture();packet=initial_packet(q,frames,identity)
    wire=g.encode_candidate(draft,packet,profile=PROFILE)
    if mutation=='duplicate':wire['evidence'].append(wire['evidence'][0])
    elif mutation=='reason':wire['frameReview'][0]['reason']='No selected evidence uses this frame.'
    else:wire['claims'][0]['questionPartIds']=[]
    before=deepcopy(wire)
    with Provider([wire]) as server:
        result=run_answer(server.config,packet,tmp_path/'bad',generation_profile=PROFILE)
        assert result['candidate'] is None
        import json
        assert json.loads(result['evidence']['receipts'][0]['result']['stdout'])==before
        run_answer(server.config,packet,tmp_path/'bad',generation_profile=PROFILE)
        assert len(server.requests)==1

def test_new_profile_fixture_replay_and_unknown_usage_stay_bounded(tmp_path):
    from lab_runner.memory_benchmark.dataset import freeze
    from lab_runner.memory_benchmark.fixture import FixtureServer
    from lab_runner.memory_benchmark.runner import run,replay
    from .test_runner import inputs
    inputs(tmp_path);frozen=tmp_path/'canonical-links-frozen'
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

def test_expanded_quote_limit_rejects_small_wire_without_pruning():
    from lab_runner.memory_benchmark.fixture import compact_fixture_answer
    from .test_completeness_profile import fixture
    import json
    q,draft,frames,identity=fixture()
    # Keep source identity and exact displayed bounds valid; large shown bodies
    # may be frozen but cannot expand into an oversized accepted answer.
    fid=next(iter(frames));frame=frames[fid]
    text='A'*18000
    span=frame['bodySpans'][0];prefix=frame['display'][:span['start']]
    frame['display']=prefix+text;span['end']=len(frame['display'])
    frame['metadata']['endChar']=frame['metadata']['startChar']+len(text)
    frozen=initial_packet(q,{fid:frame},identity)
    data=g.model_request(frozen,initial=True,profile=PROFILE)['packet']
    wire=compact_fixture_answer(data)
    ids={e['id']:e['quoteId'] for e in wire['evidence']}
    wire['evidence']=list(ids.values())
    for claim in wire['claims']:
        claim['text']='The displayed source contains a long statement.'
        claim['evidenceIds']=[ids[e] for e in claim['evidenceIds']]
        claim['questionPartIds']=[p['id'] for p in wire['questionParts'] if claim['id'] in p['claimIds']]
    for p in wire['questionParts']:
        del p['start'];del p['end'];del p['claimIds']
    wire['frameReview']=[dict(frameId=f['frameId'],unreferencedDisposition='insufficient') for f in wire['frameReview']]
    before=deepcopy(wire)
    assert len(json.dumps(wire).encode())<16384
    with pytest.raises(ValueError,match='JSON byte limit'):g.resolve(wire,frozen,profile=PROFILE)
    assert wire==before
