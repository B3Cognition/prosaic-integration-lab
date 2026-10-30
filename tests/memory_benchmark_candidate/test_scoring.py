import json

import pytest

from tests.memory_benchmark_candidate.test_runner import inputs
from lab_runner.memory_benchmark.dataset import freeze
from lab_runner.memory_benchmark.runner import run
from lab_runner.memory_benchmark.scoring import grade_template, report
from lab_runner.memory_benchmark.storage import read


def test_unlabelled_fixture_never_becomes_a_quality_pass(tmp_path):
    frozen=inputs(tmp_path);out=tmp_path/'run';run(frozen,out,fixture=True)
    result=report(frozen,out)
    assert result['semanticQuality']=='unmeasured' and result['execution']['scheduled']==3
    assert result['arms']['manual']['base']['complete'] is None
    with pytest.raises(ValueError):grade_template(frozen,out)


def labelled(tmp_path):
    unused=inputs(tmp_path)
    key={'version':1,'cases':[{'id':'q0','expectedAbstention':False,'facets':[
        {'id':'default','description':'Memory is disabled by default','sources':[
            {'sourceId':'note','start':0,'end':33,'quote':'Memory stays disabled by default.'}]}]}]}
    kp=tmp_path/'key.json';kp.write_text(json.dumps(key));frozen=tmp_path/'labelled'
    freeze(tmp_path/'dataset.json',tmp_path/'policy.json',frozen,key_path=kp)
    return frozen


def test_bound_complete_verdicts_require_answer_and_displayed_source_proofs(tmp_path):
    frozen=labelled(tmp_path);out=tmp_path/'run';run(frozen,out,fixture=True)
    template=grade_template(frozen,out)
    template['reviewer']='synthetic-test-adjudicator'
    assert len(template['judgments'])==6
    for judgment in template['judgments']:
        row=read(out/f"outcomes/{judgment['sampleId']}.json",67108864)
        qualified=row['base']['qualifiedCandidate'];answer=qualified['baseFirstAnswer'] if judgment['rendering']=='base' else qualified['firstAnswer']
        quote='Memory stays disabled by default.';start=answer.index(quote)
        evidence=row['base']['candidate']['evidence'][0]
        judgment.update(contradiction=False,unsupportedClaims=False,abstentionCorrect=True)
        judgment['facets'][0].update(satisfied=True,reason='Explicit default, exact displayed source support.',
            answerQuotes=[dict(start=start,end=start+len(quote),quote=quote)],evidenceQuotes=[
                {k:evidence[k] for k in ('frameId','displaySha256','start','end','quote')}])
    vp=tmp_path/'verdict.json';vp.write_text(json.dumps(template))
    summary=report(frozen,out,verdict_path=vp)
    assert summary['semanticQuality']=='externally_adjudicated'
    assert summary['arms']['manual']['base']['complete']==1
    assert summary['arms']['expanded']['full']['denominator']==1
    assert summary['reviewCandidateQuality']=='unmeasured'
    template['judgments'][0]['facets'][0]['answerQuotes'][0]['quote']='forged'
    vp.write_text(json.dumps(template))
    with pytest.raises(ValueError):report(frozen,out,verdict_path=vp)


def test_missing_verdict_facets_and_wrong_bindings_cannot_inflate_results(tmp_path):
    frozen=labelled(tmp_path);out=tmp_path/'run';run(frozen,out,fixture=True)
    verdict=grade_template(frozen,out);vp=tmp_path/'verdict.json'
    verdict['judgments'].pop();vp.write_text(json.dumps(verdict))
    with pytest.raises(ValueError):report(frozen,out,verdict_path=vp)
    verdict=grade_template(frozen,out);verdict['runBinding']='0'*64;vp.write_text(json.dumps(verdict))
    with pytest.raises(ValueError):report(frozen,out,verdict_path=vp)
