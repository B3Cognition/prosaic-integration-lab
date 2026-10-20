from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import pytest


def protocol():
    from lab_runner.coordination import CoordinationJournal,make_plan,join_reports
    return CoordinationJournal,make_plan,join_reports


def plan():
    return protocol()[1]('a'*64,[dict(workerId=w,sourceId='source-'+w,
        sourceRevision='v1',assignmentDigest=d*64) for w,d in (('alpha','b'),('beta','c'))])


def report(worker='alpha',fact=True,**changes):
    assignment=next(a for a in plan()['assignments'] if a['workerId']==worker)
    return dict(assignment,status='completed',fact=fact,
        usage=dict(providerRequests=2,toolCalls=1,reportedTokens=300),evidenceDigest='d'*64)|changes


@pytest.mark.parametrize('facts,status',[((True,True),'ready'),((False,False),'hold'),
    ((True,False),'conflict'),((None,True),'missing')])
def test_join_is_order_independent_and_requires_current_evidence(facts,status):
    rows=[report('alpha',facts[0]),report('beta',facts[1])]
    join=protocol()[2]
    result=join(plan(),rows)
    assert result==join(plan(),rows[::-1])
    assert result['status']==status
    assert result['usage']==dict(providerRequests=4,toolCalls=2,reportedTokens=600)


def test_partial_and_unknown_are_not_success_or_free():
    join=protocol()[2]
    assert join(plan(),[report()])['status']=='incomplete'
    result=join(plan(),[report(),report('beta',None,status='unknown',usage=None)])
    assert result['status']=='incomplete' and result['usage'] is None
    assert join(plan(),[report(),report('beta',None,status='failed')])['status']=='failed'
    result=join(plan(),[report(),report('beta',usage=dict(providerRequests=3,toolCalls=1,reportedTokens=300))])
    assert result['status']=='budget' and result['usage']['providerRequests']==5


def test_verified_failure_remains_failure_when_peer_is_unfinished():
    result=protocol()[2](plan(),[report(fact=None,status='failed')])
    assert result['status']=='failed' and result['usage'] is None


def test_safe_join_omits_assignment_identifiers():
    result=protocol()[2](plan(),[report(),report('beta')])
    assert not any(value in json.dumps(result) for value in ('alpha','beta','source-'))


@pytest.mark.parametrize('change',[dict(workerId='foreign'),dict(assignmentDigest='f'*64),
    dict(sourceRevision='old'),dict(extra=True),dict(status='unknown'),dict(fact=1),
    dict(usage={'providerRequests':True,'toolCalls':1,'reportedTokens':300})])
def test_foreign_or_ambiguous_reports_refuse_join(change):
    with pytest.raises(ValueError):protocol()[2](plan(),[report(**change),report('beta')])


def test_duplicate_result_or_assignment_is_refused():
    with pytest.raises(ValueError):protocol()[2](plan(),[report(),report()])
    p=plan()
    with pytest.raises(ValueError):protocol()[1](p['bindingDigest'],[p['assignments'][0]]*2)


def test_concurrent_claim_restart_and_idempotent_terminal_report(tmp_path):
    cls=protocol()[0];path=tmp_path/'journal.json';j=cls(path,plan=plan())
    def claim(_):
        try:return j.claim('alpha')
        except ValueError:return None
    with ThreadPoolExecutor(max_workers=8) as pool:tokens=list(pool.map(claim,range(16)))
    token=next(t for t in tokens if t)
    assert sum(t is not None for t in tokens)==1
    restored=cls(path,plan=plan(),create=False)
    assert restored.inspect()['workers']['alpha']['status']=='active'
    with pytest.raises(ValueError):restored.claim('alpha')
    restored.settle('alpha',token,report())
    assert restored.settle('alpha',token,report())==report()
    with pytest.raises(ValueError):restored.settle('alpha',token,report(fact=False))
    assert 'token' not in str(restored.inspect())
    with pytest.raises(ValueError):cls(path,plan=plan()|dict(bindingDigest='e'*64))


@pytest.mark.parametrize('fault',['missing','corrupt','symlink','oversize','public'])
def test_read_only_inspection_refuses_unsafe_saved_state(tmp_path,fault):
    cls=protocol()[0];path=tmp_path/'journal.json'
    if fault!='missing':cls(path,plan=plan())
    if fault=='corrupt':path.write_text('{}')
    elif fault=='symlink':path.rename(tmp_path/'original');path.symlink_to(tmp_path/'original')
    elif fault=='oversize':path.write_text(' '*65537)
    elif fault=='public':path.chmod(0o644)
    with pytest.raises((ValueError,OSError)):cls(path,plan=plan(),create=False).inspect()
