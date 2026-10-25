"""Held-out evidence variants separate mechanical acceptance from review quality."""
import pytest


@pytest.mark.parametrize('source',[
    'A refund invokes the bank.\nRecovery behavior is unspecified.\n',
    'Archiving must follow standard R-9.\nStandard R-9 was not supplied.\n',
    'All devices are assumed calibrated.\nNo calibration rule is provided.\n'])
def test_partial_or_conflicted_advice_is_never_quality_certified(source):
    from prosaic_integration_lab.sue_review.sources import freeze_documents
    from lab_runner.requirements_review_v3.diagnostics import review_diagnostics
    frozen=freeze_documents([{'sourceId':'held-out','text':source}])
    grade={'passed':False,'checks':{'schema':True,'case':True,'assessment':True,
                                  'issues':False,'citations':True}}
    advice={'terminal':'APORIA_CONTRADICTED','acceptedTurns':1,
            'coverage':{'missing':['DEFINE'],'open_issues':[{'turn':1}]},
            'sourcesSha256':frozen['sourcesSha256']}
    result=review_diagnostics(grade,advice)
    assert result['failedChecks']==['issues'] and result['strictPassed'] is False
    assert result['examinationComplete'] is False
    assert result['semanticEntailmentVerified'] is False
    assert result['sourcesSha256']==frozen['sourcesSha256']
    assert result['terminal']=='APORIA_CONTRADICTED'


def test_even_resolved_advice_does_not_certify_a_passing_final():
    from lab_runner.requirements_review_v3.diagnostics import review_diagnostics
    r=review_diagnostics({'passed':True,'checks':{'issues':True}},
        {'terminal':'RESOLVED','acceptedTurns':7,'coverage':{'missing':[],'open_issues':[]},
         'sourcesSha256':'a'*64})
    assert r['strictPassed'] is True and r['examinationComplete'] is True
    assert r['semanticEntailmentVerified'] is False
