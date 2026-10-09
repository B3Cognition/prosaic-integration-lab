import pytest
from lab_runner.recovery import plan_action,RecoveryError

def waiting():
    return {'status':'waiting','revision':'reviewed','review':{'revision':'reviewed'},
        'choices':['approve','reject'],'recovery_status':None}

def test_approval_requires_reviewed_revision_and_named_available_choice():
    assert plan_action(waiting(),'approve','reviewed',False) == {'expected_revision':'reviewed','choice':'approve'}
    with pytest.raises(RecoveryError,match='revision_conflict'):
        plan_action(waiting(),'approve','stale',False)

@pytest.mark.parametrize('action',['approve','reject','resume','retry'])
def test_uncertain_start_never_builds_a_mutating_request(action):
    with pytest.raises(RecoveryError,match='operator_reconciliation_required'):
        plan_action({'status':'start_uncertain','revision':None},action,'opaque',True)

def test_missing_receipt_needs_explicit_effect_risk_acknowledgement():
    snapshot = {'status':'blocked','revision':'r','recovery_status':'retry_consent_required'}
    with pytest.raises(RecoveryError,match='retry_consent_required'):
        plan_action(snapshot,'resume','r',False)
    with pytest.raises(RecoveryError,match='effect_risk_acknowledgement_required'):
        plan_action(snapshot,'retry','r',False)
    assert plan_action(snapshot,'retry','r',True) == {'expected_revision':'r','retry_interrupted':True}

def test_waiting_without_review_cannot_approve():
    snapshot = {**waiting(),'review':None}
    with pytest.raises(RecoveryError,match='approval_view_unavailable'):
        plan_action(snapshot,'approve','reviewed',False)

def test_completed_run_does_not_generate_resume_request():
    with pytest.raises(RecoveryError,match='no_recovery_action'):
        plan_action({'status':'completed','revision':'r'},'resume','r',False)
