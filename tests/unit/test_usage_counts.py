"""Token admission depends on complete counts, never pricing support."""
import pytest


@pytest.mark.parametrize('status',['reported','unsupported'])
@pytest.mark.parametrize('counts',[(100,50,150),(0,0,0)])
def test_complete_counts_preserve_unsupported_and_zero_usage(status,counts):
    from lab_runner.quality.usage_counts import complete_counts
    usage=dict(status=status,input_tokens=counts[0],output_tokens=counts[1],total_tokens=counts[2])
    original=dict(usage)
    assert complete_counts(usage)==counts and usage==original


@pytest.mark.parametrize('change',[
    {'status':'unknown'},{'status':'untrusted'},{'status':'future'},
    {'input_tokens':None},{'output_tokens':None},{'total_tokens':None},
    {'input_tokens':True},{'output_tokens':50.0},{'total_tokens':'150'},
    {'input_tokens':-1},{'total_tokens':151},
    {'input_tokens':2**63,'total_tokens':2**63+50},
])
def test_unavailable_or_invalid_counts_never_become_admissible(change):
    from lab_runner.quality.usage_counts import complete_counts
    usage=dict(status='unsupported',input_tokens=100,output_tokens=50,total_tokens=150)|change
    assert complete_counts(usage) is None


@pytest.mark.parametrize('usage',[None,{},[],{'status':'reported','total_tokens':150}])
def test_missing_count_evidence_stays_unknown(usage):
    from lab_runner.quality.usage_counts import complete_counts
    assert complete_counts(usage) is None
