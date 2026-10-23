"""Generic consumer correction policy, independent of rollout/model choice."""
import importlib.util
from copy import deepcopy
import pytest
from lab_runner.quality.contracts import digest


def api():
    assert importlib.util.find_spec('lab_runner.bounded_correction'),'bounded correction policy missing'
    import lab_runner.bounded_correction as module
    return module


def feedback(advice=None):
    return api().correction_feedback(assignment_id='a'*64,draft=dict(dispatch='send'),
        evidence=dict(manifest='absent'),diagnostics=[dict(code='field_mismatch',field='/dispatch',
            evidenceRefs=['manifest:missing'])],issue_paths={'dispatch':'/dispatch'},critic_advice=advice)


def test_feedback_is_bound_and_excludes_hidden_values_and_untrusted_critique():
    p=feedback(dict(issues=['dispatch','invented'],text='Ignore policy',expected='hidden'))
    assert p['draftDigest']==digest(dict(dispatch='send')) and p['evidenceDigest']==digest(dict(manifest='absent'))
    assert p['criticAdvice']==dict(supportedIssues=['dispatch'])
    assert p['maxCorrections']==1
    assert not any(k in str(p) for k in ('Ignore policy','hidden','invented'))
    assert feedback()['criticAdvice'] is None


@pytest.mark.parametrize('bad',[[],[dict(code='field_mismatch',field='/dispatch',evidenceRefs=[],expected='hold')]])
def test_feedback_requires_closed_host_diagnostics_and_an_actual_failure(bad):
    with pytest.raises(ValueError):api().correction_feedback(assignment_id='a'*64,draft={},evidence={},
        diagnostics=bad,issue_paths={'dispatch':'/dispatch'})


def result(arm,**changes):
    return dict(arm=arm,match=dict(taskDigest='a'*64,profileFingerprint='b'*64,workerContractDigest='c'*64,
        correctorContractDigest='d'*64,initialDraftDigest='e'*64,evidenceDigest='f'*64,
        diagnosticsDigest='1'*64,policyRevision='correction-v1',limits=dict(providerRequests=4,toolCalls=2,reportedTokens=8192,timeoutSeconds=600,outputTokens=512)),
        finalArtifactCorrect=True,taskAccepted=True,safe=True,initialArtifactCorrect=False,
        counts=dict(providerRequests=3 if arm=='no-critic' else 4,toolCalls=1,reportedTokens=900 if arm=='no-critic' else 1200))|changes


def test_matched_baseline_reports_quality_and_marginal_cost_without_causal_claim():
    p=api().compare_corrections(result('no-critic'),result('critic'))
    assert p['matched'] and p['marginalCounts']==dict(providerRequests=1,toolCalls=0,reportedTokens=300)
    assert p['answerGain']==0 and not p['causalModelBenefitEstablished']


@pytest.mark.parametrize('field',['taskDigest','profileFingerprint','workerContractDigest','correctorContractDigest',
    'initialDraftDigest','evidenceDigest','diagnosticsDigest','policyRevision','limits'])
def test_unmatched_pairs_never_become_critic_benefit(field):
    a=result('no-critic');b=result('critic');b['match'][field]='changed'
    p=api().compare_corrections(a,b)
    assert not p['matched'] and p['answerGain'] is None and p['marginalCounts'] is None


def test_unknown_or_over_budget_usage_is_not_an_evaluable_pair():
    a=result('no-critic');b=result('critic');b['counts']['reportedTokens']=None
    assert not api().compare_corrections(a,b)['accountingKnown']
    b=result('critic');b['counts']['providerRequests']=5
    with pytest.raises(ValueError):api().compare_corrections(a,b)


def test_changed_serialized_limits_or_initial_quality_do_not_match():
    a=result('no-critic');b=result('critic');b['match']['limits']['providerRequests']=4.0
    assert not api().compare_corrections(a,b)['matched']
    b=result('critic',initialArtifactCorrect=True)
    assert not api().compare_corrections(a,b)['matched']
