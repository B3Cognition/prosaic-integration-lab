"""Scripted held-out integration mechanics, not a model-quality experiment."""
from copy import deepcopy
import uuid

import pytest
from prosaic_harness import FileRunStore,Harness
from prosaic_runtime import EndpointConfig,RuntimeConfig
from tests.sue_review.test_execution import answer,fixture,session
from lab_runner.requirements_review_v1.contracts import digest,ISSUES,FINAL_SCHEMA
from lab_runner.requirements_review_v1.cases import public_task
from lab_runner.requirements_review_v1.scoring import grade
from lab_runner.requirements_review_v3 import build_comparison_workflow
from lab_runner.requirements_review_v3.diagnostics import review_diagnostics


@pytest.mark.parametrize('source,claim,issue,assessment,progress,extra',[
    ('A refund invokes the bank.\nRecovery behavior is unspecified.\n',
     'Refund failure behavior is unspecified.','missing_failure_behavior','ISSUES_FOUND',True,False),
    ('Archiving must follow standard R-9.\nStandard R-9 was not supplied.\n',
     'Required archiving context is unavailable.','missing_context','INSUFFICIENT_CONTEXT',False,False),
    ('All devices are assumed calibrated.\nNo calibration rule is provided.\n',
     'The calibration assumption lacks support.','unsupported_assumption','ISSUES_FOUND',False,True),
])
def test_heldout_dialogues_project_progress_uncertainty_and_extra_findings(
        tmp_path,source,claim,issue,assessment,progress,extra):
    import castle_sue as engine
    case={'caseId':'held-out','title':'Held-out mechanics','claim':claim,
          'sources':[{'sourceId':'held-out','text':source,'revision':'r1'}]}
    task=public_task(case);frozen=task['evidence'];values=[]
    if progress:
        state=engine.initial_state(claim,cycle_guard=True)
        while not state['terminal']:
            op=state['operator'];value=answer(op)
            value.update(answer=f'Examined {op} using the stated refund commitments.',
                claim=claim if op=='DEFINE' else None,
                evidence=[{'line':2,'quote':source.splitlines()[1]}],evidence_lines=[2],
                premises=[{'statement':source.splitlines()[1],'kind':'stated','evidence_lines':[2]}])
            if len(values)==1:
                value.update(verdict='PARTIAL',test_result='INCOMPLETE',open_questions=['Separate success from failure.'])
            if len(values)==2:value['addresses']=[2]
            values.append(deepcopy(value));state,error=engine.advance(state,value,source.splitlines())
            assert error is None
        assert state['terminal']=='RESOLVED' and len(values)==8
    else:
        value=answer('DEFINE');value.update(answer='The required support is unavailable.',
            verdict='SILENT',test_result='UNKNOWN',claim=None,evidence=[],evidence_lines=[],premises=[],
            open_questions=['Which supplied rule establishes the missing support?'])
        values=[value]
    key={'caseSha256':digest(case),'assessment':assessment,'issues':[issue],
         'support':[{'sourceId':'held-out','startLine':1,'endLine':2}]}
    final={'caseId':'held-out','assessment':assessment,
           'issues':[issue,'undefined_term'] if extra else [issue],
           'citations':[{**key['support'][0],'textSha256':frozen['sources'][0]['textSha256']}]}
    with fixture([*values,final]) as (url,rows),FileRunStore(tmp_path/'s',namespace='sue-test') as store:
        flow=session(store,url,cycle_guard=True,constrained_json=True)
        run=uuid.uuid4().hex
        waiting=flow.start(run,seed=claim,sources=frozen,review_context={
            'purpose':'Assess the supplied requirements.','issueDefinitions':ISSUES,'instructions':task['instructions']})
        finished=flow.resume(run,expected_revision=waiting['revision'],choice='continue')
        assert finished['terminal']==('RESOLVED' if progress else 'APORIA_UNDEFINED')
        report=flow.report(run)
        if progress:assert report['coverage']['open_issues']==[]
        config=RuntimeConfig({'x':EndpointConfig(url,'sue-fixture',features={'streaming':False})},{},'x')
        h=Harness(build_comparison_workflow(config,'sue'),tmp_path/'final')
        h.run({'publicTask':task,'strategyAdvice':report})
        output=h.status().state['outputs']['final']
        assert output==final and len(rows)==len(values)+1
        scored=grade(case,key,output)
        assert scored['passed'] is (not extra)
        diagnostic=review_diagnostics(scored,report)
        assert diagnostic['semanticEntailmentVerified'] is False
        assert diagnostic['examinationComplete'] is progress
        if extra:assert diagnostic['failedChecks']==['issues']
