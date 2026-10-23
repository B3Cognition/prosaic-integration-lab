from concurrent.futures import ThreadPoolExecutor
import pytest


def make(tmp_path, **overrides):
    from lab_runner.quality.allowance import BenchmarkAllowance
    limits=dict(providerRequests=4,toolCalls=4,reportedTokens=4096,maxSamples=4,timeoutSeconds=60)
    limits.update(overrides)
    return BenchmarkAllowance(tmp_path/'allowance.json',identity='a'*64,limits=limits)


def test_reopen_preserves_unknown_reservation(tmp_path):
    a=make(tmp_path)
    a.reserve('sample-1',dict(providerRequests=4,toolCalls=4,reportedTokens=4096))
    b=make(tmp_path)
    assert b.status()['remaining']['providerRequests']==0
    assert b.status()['pendingSamples']==1
    with pytest.raises(ValueError):b.reserve('sample-1',dict(providerRequests=1,toolCalls=1,reportedTokens=1))


def test_complete_settlement_idempotence_and_conflict(tmp_path):
    a=make(tmp_path)
    a.reserve('sample-1',dict(providerRequests=4,toolCalls=4,reportedTokens=4096))
    actual=dict(providerRequests=2,toolCalls=1,reportedTokens=100)
    a.finish('sample-1',actual=actual,evidence_digest='b'*64)
    a.finish('sample-1',actual=actual,evidence_digest='b'*64)
    assert make(tmp_path).status()['remaining']['providerRequests']==2
    with pytest.raises(ValueError):a.finish('sample-1',actual=actual|{'providerRequests':1},evidence_digest='b'*64)


def test_unknown_halts_and_does_not_refund(tmp_path):
    a=make(tmp_path)
    a.reserve('sample-1',dict(providerRequests=2,toolCalls=2,reportedTokens=2048))
    a.finish('sample-1',actual=None,evidence_digest=None)
    assert a.status()['remaining']['providerRequests']==2
    with pytest.raises(ValueError):a.reserve('sample-2',dict(providerRequests=1,toolCalls=1,reportedTokens=1))


def test_concurrent_claims_do_not_overspend(tmp_path):
    a=make(tmp_path)
    def reserve(i):
        try:a.reserve('sample-'+str(i),dict(providerRequests=1,toolCalls=1,reportedTokens=1024));return True
        except ValueError:return False
    with ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(reserve,range(8)))
    assert sum(results)==4


@pytest.mark.parametrize('actual',[True,-1,5])
def test_invalid_actual_never_settles(tmp_path,actual):
    a=make(tmp_path);a.reserve('s',dict(providerRequests=4,toolCalls=4,reportedTokens=4096))
    with pytest.raises(ValueError):a.finish('s',actual=dict(providerRequests=actual,toolCalls=0,reportedTokens=0),evidence_digest='b'*64)
    assert a.status()['pendingSamples']==1


def test_reopen_cannot_change_limits_or_identity(tmp_path):
    a=make(tmp_path)
    with pytest.raises(ValueError):make(tmp_path,providerRequests=5)
    from lab_runner.quality.allowance import BenchmarkAllowance
    with pytest.raises(ValueError):BenchmarkAllowance(a.path,identity='c'*64,limits=a.limits)


def test_corruption_and_symlink_fail_closed(tmp_path):
    make(tmp_path);(tmp_path/'allowance.json').write_text('{')
    with pytest.raises(ValueError):make(tmp_path)
    (tmp_path/'allowance.json').unlink();(tmp_path/'allowance.json').symlink_to(tmp_path/'elsewhere')
    with pytest.raises(ValueError):make(tmp_path)
