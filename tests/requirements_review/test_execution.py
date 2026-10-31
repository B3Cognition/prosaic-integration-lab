"""Mandatory enabled requirements profile; needs the pinned optional SUE wheel."""

import json

import pytest


def test_shared_outer_budget_covers_sue_and_final_synthesis(tmp_path):
    from lab_runner.requirements_review_v1.fixtures import run_fixture_sample
    report,evidence=run_fixture_sample('requirements-01','sue',tmp_path/'sample')
    assert report['executionStatus']=='completed' and report['grade']['passed']
    assert report['strategyDiagnostic']['terminal']=='RESOLVED'
    assert report['usage']['providerRequests']==report['strategyDiagnostic']['attempts']+1
    assert report['usage']['providerRequests']==len(evidence['wire'])
    assert report['usage']['reportedTokens']==15*len(evidence['wire'])
    assert report['replayAdditionalRequests']==0


@pytest.mark.parametrize('strategy',['direct','critic_author','sue'])
def test_invalid_attempts_remain_charged_without_hidden_feedback(tmp_path,strategy):
    from lab_runner.requirements_review_v1.fixtures import run_fixture_sample
    report,evidence=run_fixture_sample('requirements-01',strategy,tmp_path/'sample',scenario='invalid-first')
    assert report['grade']['passed'] and report['usage']['providerRequests']>=2
    assert report['usage']['providerRequests']==len(evidence['wire'])
    prompts=json.dumps([row['request'] for row in evidence['wire']])
    assert 'caseSha256' not in prompts and 'host-key-private' not in prompts


def test_resolved_is_independent_of_wrong_final_grade(tmp_path):
    from lab_runner.requirements_review_v1.fixtures import run_fixture_sample
    report,_=run_fixture_sample('requirements-01','sue',tmp_path/'sample',scenario='wrong-final')
    assert report['strategyDiagnostic']['terminal']=='RESOLVED' and not report['grade']['passed']


def test_outer_call_limit_stops_sue_without_funding_extra_final(tmp_path):
    from lab_runner.requirements_review_v1.fixtures import run_fixture_sample
    report,evidence=run_fixture_sample('requirements-01','sue',tmp_path/'sample',limits={'calls':1,'tokens':65536,'elapsedSeconds':120})
    assert report['usage']['providerRequests']==len(evidence['wire'])==1
    assert report['grade'] is None and report['executionStatus']!='completed'


def test_unknown_usage_never_becomes_a_reasoning_failure_or_free_retry(tmp_path):
    from lab_runner.requirements_review_v1.fixtures import run_fixture_sample
    report,evidence=run_fixture_sample('requirements-01','sue',tmp_path/'sample',scenario='missing-usage')
    assert report['usage']['providerRequests']==1 and not report['usage']['usageComplete']
    assert report['grade'] is None and report['executionStatus']!='completed'


def test_fixture_matrix_replay_is_zero_dispatch_and_output_is_non_overwriting(tmp_path,monkeypatch):
    from lab_runner.requirements_review_v1.runner import run_fixture, replay
    result=run_fixture(tmp_path/'matrix')
    assert result['cells']==24 and result['passed']==24
    assert result['providerRequests']==88 and result['reportedTokens']==1320
    assert [result['strategies'][s]['providerRequests'] for s in ('direct','critic_author','sue')]==[8,16,64]
    import socket
    def forbidden(*args,**kwargs):raise AssertionError('network during scoring replay')
    monkeypatch.setattr(socket,'socket',forbidden)
    replayed=replay(tmp_path/'matrix')
    assert replayed['cells']==24 and replayed['passed']==24 and replayed['additionalProviderRequests']==0
    with pytest.raises(FileExistsError):run_fixture(tmp_path/'matrix')


def test_replay_rejects_modified_saved_wire(tmp_path):
    from lab_runner.requirements_review_v1.fixtures import run_fixture_sample
    from lab_runner.requirements_review_v1.evidence import read_sample
    run_fixture_sample('requirements-01','direct',tmp_path/'sample')
    path=tmp_path/'sample'/'evidence.json';value=json.loads(path.read_text())
    value['wire'][0]['response']['usage']['total_tokens']=999
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):read_sample(tmp_path/'sample')


@pytest.mark.parametrize('mutation',['final','prompt','receipt'])
def test_evidence_join_rejects_unbound_final_prompt_or_receipt(tmp_path,mutation):
    from lab_runner.requirements_review_v1.fixtures import run_fixture_sample
    from lab_runner.requirements_review_v1.evidence import assess
    _,evidence=run_fixture_sample('requirements-01','direct',tmp_path/'sample')
    if mutation=='final':evidence['final']['issues']=[]
    elif mutation=='prompt':evidence['wire'][0]['request']['messages'][0]['content']='The source was omitted.'
    else:evidence['runs'][0]['receipts'][0]['id']='foreign'
    with pytest.raises(ValueError):assess(evidence)
