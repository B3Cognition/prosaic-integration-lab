import copy
import json
from pathlib import Path

import pytest

from lab_runner.memory_benchmark.dataset import freeze
from lab_runner.memory_benchmark.runner import run, replay, fixture_settings
from lab_runner.memory_benchmark.storage import read, sha


def inputs(tmp_path, count=1):
    source=tmp_path/'inputs';source.mkdir()
    (source/'note.md').write_bytes(b'Memory stays disabled by default.\r\n')
    data={'version':1,'sources':[{'id':'note','path':'note.md','wing':'notes'}],
        'cases':[{'id':f'q{i}','question':'What is the memory default?', 'queries':['Memory'],
            'sourceIds':['note']} for i in range(count)]}
    policy={'version':1,'namespace':'fixture-owner','root':str(source),'allowedWings':['notes']}
    for name,value in [('dataset',data),('policy',policy)]:
        (tmp_path/(name+'.json')).write_text(json.dumps(value))
    out=tmp_path/'frozen';freeze(tmp_path/'dataset.json',tmp_path/'policy.json',out)
    return out


def test_real_sdk_fixture_answers_review_and_completed_resume_zero_calls(tmp_path):
    frozen=inputs(tmp_path);out=tmp_path/'run'
    result=run(frozen,out,fixture=True,review=True)
    assert result['scheduled']==3 and result['completed']==3
    assert result['providerRequests']==9 and result['acceptedReviews']==3
    assert result['semanticQuality']=='unmeasured' and result['origin']=='fixture'
    before={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    assert run(frozen,out,fixture=True,review=True)==result
    assert replay(frozen,out)==result
    assert before=={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    for row in result['samples']:
        packet=read(out/row['path'])
        assert packet['base']['candidate'] and packet['review']['candidate']
        assert 'facets' not in json.dumps(packet['base']['evidence']['checkpoint']['inputs'])


def test_review_off_by_default_and_no_live_without_explicit_host_config(tmp_path):
    frozen=inputs(tmp_path)
    with pytest.raises(ValueError):run(frozen,tmp_path/'live')
    report=run(frozen,tmp_path/'fixture',fixture=True)
    assert report['providerRequests']==3 and report['acceptedReviews']==0
    assert report['reviewEnabled'] is False


def test_unknown_completion_keeps_full_reservation_and_blocks_remaining(tmp_path):
    from lab_runner.memory_benchmark.fixture import FixtureServer
    frozen=inputs(tmp_path,2);out=tmp_path/'run'
    with FixtureServer(missing_usage=True) as server:
        result=run(frozen,out,fixture=True,review=True,_fixture_server=server)
        assert len(server.requests)==1
        assert run(frozen,out,fixture=True,review=True,_fixture_server=server)==result
        assert len(server.requests)==1
    assert result['scheduled']==6 and result['completed']==0 and result['blocked']==5
    assert result['unknownSamples']==1 and result['providerRequests']==1
    assert result['actualTokens'] is None and result['retained']['providerRequests']==3
    assert result['retained']['reportedTokens']==98304
    assert replay(frozen,out)==result


def test_tampered_outcome_or_source_never_resumes(tmp_path):
    frozen=inputs(tmp_path);out=tmp_path/'run';report=run(frozen,out,fixture=True)
    path=out/report['samples'][0]['path'];value=read(path);value['base']['candidate']['status']='abstained'
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):replay(frozen,out)
    with pytest.raises(ValueError):run(frozen,out,fixture=True)


def test_period_in_valid_case_id_does_not_silently_block_the_batch(tmp_path):
    unused=inputs(tmp_path)
    data=read(tmp_path/'dataset.json');data['cases'][0]['id']='q.v1'
    (tmp_path/'dataset.json').write_text(json.dumps(data));frozen=tmp_path/'dot-frozen'
    freeze(tmp_path/'dataset.json',tmp_path/'policy.json',frozen)
    result=run(frozen,tmp_path/'dot-run',fixture=True)
    assert result['scheduled']==3 and result['completed']==3 and result['providerRequests']==3
    assert all(row['caseId']=='q.v1' for row in result['samples'])


def test_unsealed_resume_refuses_edited_outcome_before_any_dispatch(tmp_path):
    frozen=inputs(tmp_path);out=tmp_path/'run';result=run(frozen,out,fixture=True)
    (out/'results-seal.json').unlink()  # Simulate the final sealing boundary being interrupted.
    path=out/result['samples'][0]['path'];row=read(path);row['usage']['reportedTokens']+=1
    path.write_text(json.dumps(row))
    with pytest.raises(ValueError):run(frozen,out,fixture=True)


def test_unavailable_capture_is_reportable_without_creating_or_retrying_a_model_run(tmp_path,monkeypatch):
    from lab_runner.memory_benchmark import runner
    frozen=inputs(tmp_path);out=tmp_path/'run';old=runner.fixture_provider
    def provider(*a):
        value=old(*a)
        def unavailable():raise OSError('unavailable')
        value.health=unavailable;return value
    monkeypatch.setattr(runner,'fixture_provider',provider)
    result=run(frozen,out,fixture=True)
    assert result['scheduled']==3 and result['completed']==1 and result['failed']==1 and result['blocked']==1
    assert result['providerRequests']==1  # Manual base completed; Castle made no model call.
    assert replay(frozen,out)==result
