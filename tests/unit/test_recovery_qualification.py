"""Missing measurements cannot be mistaken for zero-loss restoration."""
import pytest
import hashlib
import json

def identity():
    from test_qualification import profile
    return {'suite':'synthetic-capacity-v1','profile_sha256':hashlib.sha256(json.dumps(profile(),sort_keys=True,
        separators=(',',':'),ensure_ascii=False).encode()).hexdigest()}

def test_recovery_requires_owned_stack_before_any_effect():
    from lab_runner.recovery_qualification import run
    from test_qualification import profile
    with pytest.raises(ValueError):run(object(),profile())

@pytest.mark.parametrize('patch',[{'acknowledged':[]},{'restored':[]},{'ready_at':None},{'calls_after':3},
    {'restored':[999]}])
def test_missing_or_redispatched_restore_evidence_fails(patch):
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence=dict(acknowledged=[{'sequence':1,'time':10}],restored=[1],loss_at=11,ready_at=12,
        calls_before=2,calls_after=2,owner_verified=True,revision_verified=True,
        receipt_verified=True,unknown_usage_verified=True)
    evidence.update(patch)
    evidence.update(identity())
    assert evaluate(profile(),evidence)['qualification']=='not_qualified'

def test_observed_missing_marker_rpo_is_measured():
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence=dict(acknowledged=[{'sequence':1,'time':10},{'sequence':2,'time':15}],restored=[1],
        loss_at=16,ready_at=20,calls_before=2,calls_after=2,owner_verified=True,
        revision_verified=True,receipt_verified=True,unknown_usage_verified=True)
    evidence.update(identity())
    result=evaluate(profile(),evidence)
    assert result['observed_rpo_s']==5 and result['observed_rto_s']==4
    assert result['qualification']=='not_qualified'

def test_restore_identity_mismatch_cannot_qualify():
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    assert evaluate(profile(),{'suite':'other-suite'})['reason']=='evidence_identity_mismatch'
