import pytest
from lab_runner.load_profile import validate,qualify

def test_profile_limits_bound_duration_arrivals_and_client_workers():
    validate(10,2,2,2,.05)
    for values in ((301,2,2,2,.05),(10,101,2,2,.05),(300,100,2,2,.05),(10,2,65,2,.05)):
        with pytest.raises(ValueError): validate(*values)

def test_latency_and_rejection_slo_failures_are_not_hidden_by_accounting_correctness():
    result=qualify(offered=10,completed=8,rejected=2,shed=0,errors=0,latencies=[.1]*7+[3],
        observed=8,ledger_calls=8,unknown=0,duration=10,rate=1,p95_target=2,max_rejection=.05)
    assert result['correctness_passed'] is True and result['slo_passed'] is False
    assert result['p95_seconds']==3

def test_unknown_usage_or_dispatch_mismatch_cannot_qualify():
    result=qualify(offered=2,completed=2,rejected=0,shed=0,errors=0,latencies=[.1,.1],
        observed=3,ledger_calls=2,unknown=1,duration=2,rate=1,p95_target=2,max_rejection=.05)
    assert result['correctness_passed'] is False
    assert result['slo_passed'] is False
