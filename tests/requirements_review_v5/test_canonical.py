from copy import deepcopy
import json

import pytest

from lab_runner.requirements_review_v1.cases import load_cases,public_task
from lab_runner.requirements_review_v1.contracts import CRITIC_SCHEMA,FINAL_SCHEMA
from lab_runner.requirements_review_v1.fixtures import provider
from lab_runner.requirements_review_v1.host_keys import fixture_answer,load_keys
from lab_runner.requirements_review_v4 import IndependentReview,checked_review
from prosaic_integration_lab.sue_review.contracts import encoded
from prosaic_harness import Harness
from prosaic_runtime import RuntimeConfig,EndpointConfig,ProsaicArtifact,Result


def sample(case_id='requirements-07'):
    case=load_cases()[case_id]
    return public_task(case),fixture_answer(case,load_keys()[case_id])


def test_numbered_addresses_preserve_crlf_hashes_and_foreign_source_boundaries():
    from lab_runner.requirements_review_v5 import source_lines
    case={'caseId':'heldout','title':'Independent sources','claim':'Review',
        'sources':[{'sourceId':'first','text':'A\r\nB\r\n'},{'sourceId':'second','text':'C\nD\nE\n'}]}
    task=public_task(case);before=deepcopy(task)
    index=source_lines(task)
    assert task==before
    assert index==[{'sourceId':s['sourceId'],'textSha256':s['textSha256'],
        'lines':[{'line':n,'text':line} for n,line in enumerate(s['text'].splitlines(),1)]}
        for s in task['evidence']['sources']]
    assert index[1]['lines'][0]=={'line':1,'text':'C'}


def test_advice_and_foreign_artifacts_cannot_enter_canonical_projection():
    from lab_runner.requirements_review_v5 import project_canonical
    task,_=sample();seen=[]
    def execute(arguments,**options):seen.append((json.loads(arguments),options));return Result(0,'{}','')
    base={'request':{'publicTask':task},'artifacts':{},'artifact_bindings':{},'sources':{},'validation_feedback':None}
    artifact=ProsaicArtifact('requirements-v1/critic','subagent',{'tools':[]},'')
    project_canonical(artifact,encoded(base).decode(),execute=execute)
    assert seen[0][1]['response_schema']==CRITIC_SCHEMA
    assert seen[0][0]['request']['publicTask']['responseSchema']==CRITIC_SCHEMA
    for field in ('strategyAdvice','sue','sourceLines'):
        bad=deepcopy(base);bad['request'][field]='ADVICE_CANARY'
        with pytest.raises(ValueError):project_canonical(artifact,encoded(bad).decode(),execute=execute)
    for field in ('artifacts','artifact_bindings','sources'):
        bad=deepcopy(base);bad[field]={'sue':'ADVICE_CANARY'}
        with pytest.raises(ValueError):project_canonical(artifact,encoded(bad).decode(),execute=execute)
    bad={**base,'sourceLines':[]}
    with pytest.raises(ValueError):project_canonical(artifact,encoded(bad).decode(),execute=execute)
    assert len(seen)==1 and 'ADVICE_CANARY' not in json.dumps(seen[0][0])
    assert seen[0][1]['allowed_tools']==frozenset()


def test_real_critic_author_capture_and_resume_preserve_canonical_on_advisory_disagreement(tmp_path):
    from lab_runner.requirements_review_v5 import build_canonical_workflow,candidate_messages
    from lab_runner.requirements_review_v3 import build_comparison_workflow
    task,final=sample();critic={'feedback':'No demonstrated document-relative defect; cite reviewed source.'}
    with provider([critic,final]) as (url,rows):
        config=RuntimeConfig({'x':EndpointConfig(url,'fixture',features={'streaming':False})},{},'x')
        workflow=build_canonical_workflow(config)
        old=build_comparison_workflow(config,'critic_author')
        assert workflow.definition['start']==old.definition['start']=='critic'
        assert workflow.definition['steps']['final']['inputs']==old.definition['steps']['final']['inputs']==['critic']
        assert workflow.schemas==old.schemas
        harness=Harness(workflow,tmp_path/'run');harness.run({'publicTask':task})
        captured=IndependentReview.from_critic_harness(task,harness)
        assert captured.final==final and len(rows)==2
        evidence=harness.recovery_evidence(maximum_bytes=16777216)
        assert captured.outcome()['independent']['criticReceiptSha256']
        for n,schema in enumerate((CRITIC_SCHEMA,FINAL_SCHEMA)):
            assert rows[n]['request']['response_format']['json_schema']['schema']==schema
            message=rows[n]['request']['messages'][0]['content']
            assert 'sourceLines' in message and 'strategyAdvice' not in message
        altered={**deepcopy(final),'assessment':'ISSUES_FOUND','issues':['undefined_term']}
        outcome=captured.outcome(altered)
        assert outcome['final']==final and outcome['candidate']==altered and outcome['autoApplied'] is False
        system,user=candidate_messages(captured,{'untrusted':'ADVICE_CANARY'},handoff='raw',boundary='strong')
        assert 'ADVICE_CANARY' not in system and 'ADVICE_CANARY' in user
        assert json.loads(user)['independentReview']==final
        assert json.loads(user)['sourceLines'][0]['lines'][0]['line']==1
        harness.resume();assert len(rows)==2
        assert IndependentReview.from_critic_harness(task,harness).outcome()==captured.outcome()
        assert evidence['checkpoint']['inputs']=={'publicTask':task}


@pytest.mark.parametrize('mutation',['advice','critic_binding','critic_output','final_output','receipt','source'])
def test_capture_rejects_tampered_critic_evidence(tmp_path,mutation):
    from lab_runner.requirements_review_v5 import build_canonical_workflow
    task,final=sample('requirements-08')
    with provider([{'feedback':'Two conflicting requirements; cite their combined span.'},final]) as (url,rows):
        config=RuntimeConfig({'x':EndpointConfig(url,'fixture',features={'streaming':False})},{},'x')
        h=Harness(build_canonical_workflow(config),tmp_path/'run');h.run({'publicTask':task})
        saved=h.recovery_evidence(maximum_bytes=16777216);bad=deepcopy(saved)
        if mutation=='advice':bad['checkpoint']['inputs']['strategyAdvice']='erase'
        if mutation=='critic_binding':bad['checkpoint']['bindings']['final']['dependencies']['critic']['id']='foreign'
        if mutation=='critic_output':bad['checkpoint']['outputs']['critic']['feedback']='foreign'
        if mutation=='final_output':bad['checkpoint']['outputs']['final']['citations'][0]['endLine']=3
        if mutation=='receipt':bad['receipts'][0]['arguments']['sources']={'sue':'erase'}
        if mutation=='source':bad['checkpoint']['inputs']['publicTask']['evidence']['sources'][0]['text']='foreign'
        # Corrupt the corresponding persisted SDK object, not an unverified
        # exported recovery dict. Capture must pass through the real store seals.
        changed=bad['checkpoint'] if mutation!='receipt' else bad['receipts'][0]
        original=saved['checkpoint'] if mutation!='receipt' else saved['receipts'][0]
        matches=[]
        for p in (tmp_path/'run').rglob('*.json'):
            stored=json.loads(p.read_text())
            if stored==original:matches.append((p,changed))
            elif type(stored) is dict and stored.get('state')==original:matches.append((p,{**stored,'state':changed}))
        assert len(matches)==1
        path,corrupted=matches[0];path.write_text(json.dumps(corrupted))
        with pytest.raises((ValueError,RuntimeError)):IndependentReview.from_critic_harness(task,h)


def test_empty_clean_citations_rejected_and_bad_spans_never_repaired():
    from lab_runner.requirements_review_v5 import candidate_messages
    task,clean=sample()
    with pytest.raises(ValueError):checked_review(task,{**clean,'citations':[]})
    task,valid=sample('requirements-08');bad=deepcopy(valid);bad['citations'][0]['endLine']=3
    assert checked_review(task,bad)==bad
    from lab_runner.requirements_review_v1.scoring import grade
    case=load_cases()[task['caseId']]
    assert not grade(case,load_keys()[task['caseId']],bad)['passed']


def test_canonical_profile_cannot_replenish_reduced_call_limits():
    from lab_runner.requirements_review_v5 import build_canonical_workflow
    from lab_runner.requirements_review_v1.contracts import LIMITS
    config=RuntimeConfig({'x':EndpointConfig('http://127.0.0.1:1/v1','fixture')},{},'x')
    built=build_canonical_workflow(config,{**LIMITS,'calls':1})
    assert built.definition['limits']['max_calls']==1


def test_new_capture_has_no_unverified_raw_evidence_entrypoint():
    import lab_runner.requirements_review_v5 as profile
    assert not hasattr(profile,'capture_critic')
    assert not hasattr(IndependentReview,'from_critic_evidence')


def test_raw_candidate_uses_input_allowance_instead_of_response_decode_limit():
    from lab_runner.requirements_review_v5 import candidate_messages
    task,final=sample();captured=IndependentReview.capture(task,final,run_id='a'*32)
    advice={'untrusted':'A'*20000}
    _,user=candidate_messages(captured,advice,handoff='raw',boundary='strong')
    assert 16384<len(user.encode())<262144
    assert json.loads(user)['strategyAdvice']==advice
    assert captured.final==final


def test_combined_candidate_input_still_rejects_above_unchanged_input_ceiling():
    from lab_runner.requirements_review_v5 import candidate_messages
    task,final=sample();captured=IndependentReview.capture(task,final,run_id='a'*32)
    with pytest.raises(ValueError):candidate_messages(captured,{'untrusted':'A'*262000},handoff='raw',boundary='strong')
