"""Host containment boundaries; no model or provider calls."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

MAX = dict(providerRequests=4, toolCalls=2, reportedTokens=8192)
TWO = dict(providerRequests=8, toolCalls=4, reportedTokens=16384)
ACTUAL = dict(providerRequests=2, toolCalls=1, reportedTokens=300)


def journal(path, **kwargs):
    assert importlib.util.find_spec('lab_runner.failure_isolation'), 'durable isolation blueprint missing'
    from lab_runner.failure_isolation import FailureIsolation
    return FailureIsolation(path, identity=kwargs.pop('identity', 'a'*64), limits=kwargs.pop('limits', TWO), **kwargs)


def test_unknown_isolated_without_releasing_reservation_or_blocking_other_work(tmp_path):
    path=tmp_path/'journal.json';j=journal(path)
    token=j.admit('lost',binding='b'*64);j.start('lost',token)
    j=journal(path)  # restart cannot make a dispatch intent safe to retry
    assert j.inspect('lost')['state']=='active'
    j.isolate('lost',binding='b'*64,decision_digest='c'*64)
    with pytest.raises(ValueError):j.complete('lost',token,actual=ACTUAL,evidence_digest='d'*64)
    with pytest.raises(ValueError):j.admit('lost',binding='b'*64)
    j.recover('lost',binding='b'*64,decision_digest='e'*64,actual=None,evidence_digest=None,outcome='unknown')
    assert j.inspect('lost')['actual'] is None
    token=j.admit('other',binding='f'*64);j.start('other',token)
    j.complete('other',token,actual=ACTUAL,evidence_digest='d'*64)
    assert j.inspect('other')['outcome']=='completed'
    assert j.status()['retained']==TWO
    with pytest.raises(ValueError):j.admit('third',binding='f'*64)


@pytest.mark.parametrize('boundary',['admitted','active','completed'])
def test_process_loss_preserves_single_claim_and_terminal_evidence(tmp_path,boundary):
    path=tmp_path/'journal.json';journal(path)
    code='''
import os,sys
from lab_runner.failure_isolation import FailureIsolation
j=FailureIsolation(sys.argv[1],identity='a'*64,limits=dict(providerRequests=8,toolCalls=4,reportedTokens=16384))
t=j.admit('crash',binding='b'*64)
if sys.argv[2]!='admitted':j.start('crash',t)
if sys.argv[2]=='completed':j.complete('crash',t,actual=dict(providerRequests=2,toolCalls=1,reportedTokens=300),evidence_digest='d'*64)
os._exit(23)
'''
    env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[2]))
    result=subprocess.run([sys.executable,'-c',code,str(path),boundary],env=env,capture_output=True)
    assert result.returncode==23,result.stderr.decode()
    j=journal(path)
    assert j.inspect('crash')['state']==boundary
    assert j.status()['retained']==MAX
    with pytest.raises(ValueError):j.admit('crash',binding='b'*64)
    if boundary!='completed':
        j.isolate('crash',binding='b'*64,decision_digest='c'*64)
        j.recover('crash',binding='b'*64,decision_digest='d'*64,actual=None,evidence_digest=None,outcome='unknown')
        assert j.inspect('crash')['actual'] is None


def test_concurrent_reservations_cannot_overspend(tmp_path):
    path=tmp_path/'journal.json';j=journal(path,limits=MAX)
    def admit(n):
        try:j.admit(str(n),binding='b'*64);return True
        except ValueError:return False
    with ThreadPoolExecutor(max_workers=8) as pool:assert sum(pool.map(admit,range(20)))==1
    assert j.status()['retained']==MAX


def test_recovery_is_explicit_bound_and_idempotent(tmp_path):
    path=tmp_path/'journal.json';j=journal(path);t=j.admit('one',binding='b'*64);j.start('one',t)
    with pytest.raises(ValueError):journal(path,identity='c'*64)
    with pytest.raises(ValueError):journal(path,limits=MAX)
    with pytest.raises(ValueError):j.isolate('one',binding='c'*64,decision_digest='d'*64)
    args=dict(binding='b'*64,decision_digest='e'*64,actual=ACTUAL,evidence_digest='f'*64,outcome='completed')
    with pytest.raises(ValueError):j.recover('one',**args)
    j.isolate('one',binding='b'*64,decision_digest='d'*64)
    j.isolate('one',binding='b'*64,decision_digest='d'*64)
    with pytest.raises(ValueError):j.isolate('one',binding='b'*64,decision_digest='f'*64)
    result=j.recover('one',**args)
    assert journal(path).recover('one',**args)==result
    with pytest.raises(ValueError):j.recover('one',**(args|dict(decision_digest='c'*64)))
    with pytest.raises(ValueError):j.complete('one',t,actual=ACTUAL,evidence_digest='f'*64)
    assert 'token' not in j.inspect('one')
    assert j.status()['retained']==MAX


@pytest.mark.parametrize('actual',[None,{},dict(providerRequests=True,toolCalls=0,reportedTokens=1),
    dict(providerRequests=1,toolCalls=0,reportedTokens=-1),dict(providerRequests=1,toolCalls=0,reportedTokens=1.5)])
def test_incomplete_counts_cannot_become_success(tmp_path,actual):
    j=journal(tmp_path/'journal.json');t=j.admit('one',binding='b'*64);j.start('one',t)
    with pytest.raises(ValueError):j.complete('one',t,actual=actual,evidence_digest='f'*64)
    assert j.inspect('one')['actual'] is None
    assert j.status()['retained']==MAX


def test_known_overrun_is_honest_and_blocks_admission(tmp_path):
    j=journal(tmp_path/'journal.json');t=j.admit('one',binding='b'*64);j.start('one',t)
    j.complete('one',t,actual=dict(providerRequests=1,toolCalls=0,reportedTokens=8516),evidence_digest='f'*64)
    assert j.inspect('one')['state']=='overrun'
    assert j.inspect('one')['outcome']=='failed'
    assert j.status()['retained']==dict(providerRequests=4,toolCalls=2,reportedTokens=8516)
    with pytest.raises(ValueError):j.admit('other',binding='c'*64)


@pytest.mark.parametrize('route',['completion','recovery'])
@pytest.mark.parametrize('actual',[
    dict(providerRequests=5,toolCalls=1,reportedTokens=300),
    dict(providerRequests=2,toolCalls=3,reportedTokens=300),
    dict(providerRequests=2,toolCalls=1,reportedTokens=10000)])
def test_pre_admitted_work_cannot_start_after_any_recorded_overrun(tmp_path,route,actual):
    path=tmp_path/'journal.json';j=journal(path)
    first=j.admit('first',binding='b'*64)
    queued=j.admit('queued',binding='c'*64)
    j.start('first',first)
    if route=='completion':
        j.complete('first',first,actual=actual,evidence_digest='d'*64)
    else:
        j.isolate('first',binding='b'*64,decision_digest='e'*64)
        j.recover('first',binding='b'*64,decision_digest='f'*64,
                  actual=actual,evidence_digest='d'*64,outcome='failed')
    j=journal(path)
    assert j.status()['admissionBlocked']
    with pytest.raises(ValueError):j.start('queued',queued)
    assert j.inspect('queued')['state']=='admitted'
    assert j.inspect('queued')['actual'] is None
    assert j.status()['retained']['reportedTokens'] >= 16384
    j.isolate('queued',binding='c'*64,decision_digest='e'*64)
    j.recover('queued',binding='c'*64,decision_digest='f'*64,
              actual=None,evidence_digest=None,outcome='unknown')
    assert j.status()['admissionBlocked']


def test_deadline_survives_restart_and_does_not_authorize_late_success(tmp_path,monkeypatch):
    import time
    j=journal(tmp_path/'journal.json');t=j.admit('one',binding='b'*64)
    deadline=j.inspect('one')['deadline']
    monkeypatch.setattr(time,'time',lambda:deadline+1)
    j=journal(tmp_path/'journal.json')
    assert j.inspect('one')['deadline']==deadline
    with pytest.raises(ValueError):j.start('one',t)
    j.isolate('one',binding='b'*64,decision_digest='c'*64)
    with pytest.raises(ValueError):j.recover('one',binding='b'*64,decision_digest='d'*64,
        actual=ACTUAL,evidence_digest='f'*64,outcome='completed')
    j.recover('one',binding='b'*64,decision_digest='d'*64,actual=ACTUAL,evidence_digest='f'*64,outcome='failed')
    assert j.inspect('one')['outcome']=='failed'


def test_corrupt_or_public_journal_fails_closed(tmp_path):
    path=tmp_path/'journal.json';journal(path);path.write_bytes(b'{}')
    with pytest.raises(ValueError):journal(path)
    path.unlink();journal(path);path.chmod(0o644)
    with pytest.raises(ValueError):journal(path)
