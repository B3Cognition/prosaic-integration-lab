"""Actual consumer deadline projection, public SDK checkpoints and resume."""
from copy import deepcopy
import json

import pytest
from prosaic_runtime import RuntimeAdapter,ProsaicRuntime

from lab_runner.memory_benchmark import completeness_profile as review, generation as g
from lab_runner.memory_benchmark.workflow import initial_packet, run_answer
from .test_completeness_profile import fixture,Provider

PROFILE='bounded-120s-v1'


def test_long_profile_reaches_all_calls_and_prevents_cross_profile_resume(tmp_path,monkeypatch):
    q,draft,frames,identity=fixture();packet=initial_packet(q,frames,identity)
    wire=g.encode_candidate(draft,packet);policies=[];delegated=[]
    original=RuntimeAdapter.run
    def observe(self,*args,**kw):
        policies.append(kw['policy'])
        return original(self,*args,**kw)
    monkeypatch.setattr(RuntimeAdapter,'run',observe)
    delegate=ProsaicRuntime.run
    def observe_delegate(self,*args,**kw):
        delegated.append(kw['policy'])
        return delegate(self,*args,**kw)
    monkeypatch.setattr(ProsaicRuntime,'run',observe_delegate)
    with Provider([wire,dict(feedback='No supported correction.'),wire,wire]) as server:
        base=run_answer(server.config,packet,tmp_path/'base',generation_profile=g.QUESTION_FOCUSED,execution_profile=PROFILE)
        assert base['candidate']==draft
        frozen=review.freeze_packet(q,draft,frames,identity=identity)
        final=review.run_review(server.config,frozen,tmp_path/'review',generation_profile=g.QUESTION_FOCUSED,execution_profile=PROFILE)
        assert final['candidate']==draft
        assert len(policies)==3 and all(119 < p.timeout_s <= 120 for p in policies)
        assert len(delegated)==3 and all(119 < p.timeout_s <= 120 for p in delegated)
        assert run_answer(server.config,packet,tmp_path/'base',generation_profile=g.QUESTION_FOCUSED,execution_profile=PROFILE)['usage']['providerRequests']==0
        assert review.run_review(server.config,frozen,tmp_path/'review',generation_profile=g.QUESTION_FOCUSED,execution_profile=PROFILE)['usage']['providerRequests']==0
        with pytest.raises(ValueError):run_answer(server.config,packet,tmp_path/'base',generation_profile=g.QUESTION_FOCUSED)
        with pytest.raises(ValueError):review.run_review(server.config,frozen,tmp_path/'review',generation_profile=g.QUESTION_FOCUSED)
        assert len(server.requests)==3
        reduced=run_answer(server.config,packet,tmp_path/'reduced',elapsed_seconds=2,generation_profile=g.QUESTION_FOCUSED,execution_profile=PROFILE)
        assert reduced['candidate']==draft and 0 < policies[-1].timeout_s <= 2
        assert 0 < delegated[-1].timeout_s <= 2
        for request in server.requests:
            assert request['max_tokens']==4096 and 'tools' not in request


def test_review_policy_gives_both_calls_full_time_and_retains_other_grants(monkeypatch):
    policies=[];original=review.WorkflowFactory.__init__
    def observe(self,*args,**kwargs):
        policies.append(kwargs['policy'])
        original(self,*args,**kwargs)
    monkeypatch.setattr(review.WorkflowFactory,'__init__',observe)
    q,draft,frames,identity=fixture();packet=review.freeze_packet(q,draft,frames,identity=identity)
    with Provider([]) as server:
        legacy=review.build_workflow(server.config,packet,generation_profile=g.QUESTION_FOCUSED)
        long=review.build_workflow(server.config,packet,generation_profile=g.QUESTION_FOCUSED,execution_profile=PROFILE)
        assert policies[0].timeout_s==60 and policies[0].max_run_s==120
        assert policies[1].timeout_s==120 and policies[1].max_run_s==270
        assert policies[1].max_calls==2 and policies[1].max_attempts==1
        assert policies[1].max_tokens==65536 and policies[1].max_output_bytes==16384
        assert long.fingerprint!=legacy.fingerprint


def test_runner_keeps_full_sample_reservation_and_replays_long_profile(tmp_path):
    from lab_runner.memory_benchmark.dataset import freeze
    from lab_runner.memory_benchmark.fixture import FixtureServer
    from lab_runner.memory_benchmark.runner import run,replay
    from .test_runner import inputs
    inputs(tmp_path)
    frozen=tmp_path/'long-frozen'
    freeze(tmp_path/'dataset.json',tmp_path/'policy.json',frozen,generation_profile=g.QUESTION_FOCUSED,execution_profile=PROFILE)
    output=tmp_path/'run';result=run(frozen,output,fixture=True,review=True)
    assert result['completed']==result['acceptedReviews']==3 and result['providerRequests']==9
    assert replay(frozen,output)==result
    with FixtureServer(missing_usage=True) as server:
        unknown=run(frozen,tmp_path/'unknown',fixture=True,review=True,_fixture_server=server)
        assert unknown['unknownSamples']==1 and unknown['blocked']==2
        assert unknown['actualTokens'] is None and unknown['retained']==dict(providerRequests=3,reportedTokens=98304,toolCalls=0)
        assert replay(frozen,tmp_path/'unknown')==unknown
        assert len(server.requests)==1


@pytest.mark.parametrize('profile', [PROFILE,'bounded-60s-v1'])
def test_long_profile_clips_calls_to_remaining_shared_time_without_changing_legacy(profile,tmp_path,monkeypatch):
    import time
    from types import SimpleNamespace
    from lab_runner.memory_benchmark import runner
    from lab_runner.memory_benchmark.dataset import freeze
    from lab_runner.memory_benchmark.storage import read
    from .test_runner import inputs
    inputs(tmp_path);frozen=tmp_path/'timed';output=tmp_path/'run'
    freeze(tmp_path/'dataset.json',tmp_path/'policy.json',frozen,generation_profile=g.QUESTION_FOCUSED,execution_profile=profile)
    monkeypatch.setattr(runner,'time',SimpleNamespace(monotonic=time.monotonic,
        time=lambda:read(output/'allowance.json')['deadline']-2))
    policies=[];original=ProsaicRuntime.run
    def observe(self,*args,**kw):
        policies.append(kw['policy']);return original(self,*args,**kw)
    monkeypatch.setattr(ProsaicRuntime,'run',observe)
    result=runner.run(frozen,output,fixture=True,review=True)
    assert result['completed']==3 and len(policies)==9
    if profile==PROFILE:assert all(0<p.timeout_s<=2 for p in policies)
    else:assert all(59<p.timeout_s<=60 for p in policies)
