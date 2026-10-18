import json
import pytest
from lab_runner.quality.allowance import BenchmarkAllowance


def make(tmp_path,version=2):
    return BenchmarkAllowance(tmp_path/'allowance.json',identity='a'*64,
        limits=dict(providerRequests=4,toolCalls=2,reportedTokens=8192,maxSamples=4,timeoutSeconds=60),
        version=version)


def test_known_overrun_persists_exact_actual_and_reopens_without_raising_ceiling(tmp_path):
    a=make(tmp_path); maximum=dict(providerRequests=4,toolCalls=2,reportedTokens=8192)
    a.reserve('s',maximum)
    actual=maximum|{'reportedTokens':8516}
    row=a.finish('s',actual=actual,evidence_digest='b'*64)
    assert row['state']=='overrun' and row['actual']==actual and row['maximum']==maximum
    reopened=make(tmp_path)
    assert reopened.status()['retained']==actual
    assert reopened.status()['remaining']['reportedTokens']==0
    assert reopened.status()['excess']['reportedTokens']==324
    assert reopened.status()['overrunSamples']==1 and reopened.limits['reportedTokens']==8192
    assert reopened.finish('s',actual=actual,evidence_digest='b'*64)==row
    with pytest.raises(ValueError):reopened.reserve('next',dict(providerRequests=0,toolCalls=0,reportedTokens=0))
    with pytest.raises(ValueError):reopened.finish('s',actual=maximum,evidence_digest='b'*64)


def test_per_reservation_breach_halts_even_when_aggregate_has_room(tmp_path):
    a=make(tmp_path); a.reserve('s',dict(providerRequests=1,toolCalls=0,reportedTokens=100))
    a.finish('s',actual=dict(providerRequests=2,toolCalls=0,reportedTokens=101),evidence_digest='b'*64)
    assert a.status()['excess']==dict(providerRequests=0,toolCalls=0,reportedTokens=0)
    with pytest.raises(ValueError):a.reserve('next',dict(providerRequests=1,toolCalls=0,reportedTokens=100))


def test_unknown_v2_is_retained_without_refund_or_reclassification(tmp_path):
    a=make(tmp_path); maximum=dict(providerRequests=4,toolCalls=2,reportedTokens=8192)
    a.reserve('s',maximum); a.finish('s',actual=None,evidence_digest=None)
    assert make(tmp_path).status()['retained']==maximum
    with pytest.raises(ValueError):a.finish('s',actual=maximum,evidence_digest='b'*64)


def test_v1_format_stays_unchanged_and_cannot_be_silently_upgraded(tmp_path):
    a=make(tmp_path,version=1); before=a.path.read_bytes()
    assert json.loads(before)['version']==1
    with pytest.raises(ValueError):make(tmp_path)
    assert a.path.read_bytes()==before


def test_false_overrun_state_is_rejected(tmp_path):
    a=make(tmp_path); a.reserve('s',dict(providerRequests=4,toolCalls=2,reportedTokens=8192))
    a.finish('s',actual=dict(providerRequests=1,toolCalls=1,reportedTokens=1),evidence_digest='b'*64)
    data=json.loads(a.path.read_bytes());data['samples']['s']['state']='overrun'
    a.path.write_text(json.dumps(data))
    with pytest.raises(ValueError):make(tmp_path)


def test_request_bound_violation_halts_below_sample_maximum(tmp_path):
    a=make(tmp_path);a.reserve('s',dict(providerRequests=4,toolCalls=2,reportedTokens=8192))
    actual=dict(providerRequests=1,toolCalls=0,reportedTokens=150)
    row=a.finish('s',actual=actual,evidence_digest='b'*64,violation='token_reservation_exceeded')
    assert row['state']=='overrun' and row['violation']=='token_reservation_exceeded'
    assert make(tmp_path).status()['retained']==actual
    with pytest.raises(ValueError):a.reserve('next',actual)
