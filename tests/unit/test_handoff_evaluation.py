from copy import deepcopy
import pytest


def values():
    clean=dict(assignmentId='a'*64,status='ready',answer=dict(decision='approve',facts=[],citations=[]),evidence=[])
    worker=deepcopy(clean);worker['answer']['decision']='reject'
    return clean,worker


@pytest.mark.parametrize('binding,issues,kind',[
    ('a'*64,['decision'],'caught'),('0'*64,['decision'],'invalidReview'),
    ('a'*64,[],'incorrectEscalation')])
def test_only_bound_complete_criticism_earns_a_catch(binding,issues,kind):
    from lab_runner.handoffs.evaluation import classify_review
    clean,worker=values()
    review=dict(assignmentId=binding,verdict='escalate',issues=issues)
    result=classify_review(clean,worker,review,usable=True)
    assert result['category']==kind
    assert result['flawCaught']==(kind=='caught')


def test_attempted_unknown_samples_remain_in_coverage():
    from lab_runner.handoffs.evaluation import coverage
    rows=[dict(alias='small',evidenceAvailable=False,claim='unknown')]
    result=coverage(['small','large'],[dict(alias='small'),dict(alias='large')],rows)
    assert result['small']['scheduled']==result['small']['attempted']==1
    assert result['small']['evidenceAvailable']==0
    assert result['small']['unknownSamples']==1 and result['small']['criticUsageComplete'] is False
    assert result['large']['attempted']==0 and result['large']['scheduled']==1


@pytest.mark.parametrize('state',['pending','unknown'])
def test_unsettled_claims_retain_whole_reservation_without_mutation(state):
    from lab_runner.handoffs.evaluation import charge_for
    claim=dict(state=state,maximum=dict(providerRequests=4,toolCalls=2,reportedTokens=8192),actual=None)
    before=deepcopy(claim)
    assert charge_for(claim)==dict(providerRequests=4,toolCalls=2,reportedTokens=8192)
    assert claim==before
