"""Experimental host protocol for two independent public SDK runs.

Host adapters verify domain truth and accounting. This journal grants no
execution, retry, refund, authentication or effect-completion authority.
"""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import secrets

from .quality.allowance import counts,private_directory,private_write,_private
from .quality.contracts import decode,encode,identifier,sha

MAXIMUM=dict(providerRequests=4,toolCalls=2,reportedTokens=8192)
CHILD=dict(providerRequests=2,toolCalls=1,reportedTokens=4096)
_ASSIGNMENT={'workerId','sourceId','sourceRevision','assignmentDigest'}
_REPORT=_ASSIGNMENT|{'status','fact','usage','evidenceDigest'}


def make_plan(binding_digest,assignments):
    sha(binding_digest)
    if type(assignments) is not list or len(assignments)!=2:
        raise ValueError('exactly two host assignments required')
    for row in assignments:
        if type(row) is not dict or set(row)!=_ASSIGNMENT:raise ValueError('closed assignment required')
        for key in ('workerId','sourceId','sourceRevision'):identifier(row[key])
        sha(row['assignmentDigest'])
    if any(len({r[k] for r in assignments})!=2 for k in ('workerId','sourceId','assignmentDigest')):
        raise ValueError('distinct assignments required')
    return decode(encode(dict(version=1,bindingDigest=binding_digest,
        assignments=sorted(assignments,key=lambda r:r['workerId']))))


def _plan(plan):
    if type(plan) is not dict or set(plan)!={'version','bindingDigest','assignments'} or type(plan['version']) is not int or plan['version']!=1:
        raise ValueError('closed coordination plan required')
    result=make_plan(plan['bindingDigest'],plan['assignments'])
    if result!=plan:raise ValueError('canonical plan order required')
    return result


def _report(plan,report):
    if type(report) is not dict or set(report)!=_REPORT:raise ValueError('closed worker report required')
    expected=next((a for a in plan['assignments'] if a['workerId']==report['workerId']),None)
    if expected is None or any(report[k]!=expected[k] for k in _ASSIGNMENT):
        raise ValueError('foreign worker report')
    if report['status'] not in ('completed','failed','unknown'):raise ValueError('invalid report status')
    sha(report['evidenceDigest'])
    if report['fact'] is not None and type(report['fact']) is not bool:raise ValueError('invalid fact')
    if report['status']!='completed' and report['fact'] is not None:raise ValueError('unverified fact')
    if report['usage'] is None:
        if report['status']!='unknown':raise ValueError('unknown accounting required')
    else:
        counts(report['usage'])
        if report['status']=='unknown':raise ValueError('unknown report requires unknown usage')
    return decode(encode(report))


def join_reports(plan,reports):
    plan=_plan(plan)
    if type(reports) is not list or len(reports)>2:raise ValueError('bounded reports required')
    rows=[_report(plan,r) for r in reports]
    if len({r['workerId'] for r in rows})!=len(rows):raise ValueError('duplicate worker report')
    rows.sort(key=lambda r:r['workerId'])
    complete=len(rows)==2 and all(r['usage'] is not None for r in rows)
    usage={k:sum(r['usage'][k] for r in rows) for k in MAXIMUM} if complete else None
    if any(r['usage'] is not None and any(r['usage'][k]>CHILD[k] for k in CHILD) for r in rows):status='budget'
    elif usage and any(usage[k]>MAXIMUM[k] for k in MAXIMUM):status='budget'
    elif any(r['status']=='failed' for r in rows):status='failed'
    elif not complete:status='incomplete'
    elif any(r['fact'] is None for r in rows):status='missing'
    elif rows[0]['fact']!=rows[1]['fact']:status='conflict'
    else:status='ready' if rows[0]['fact'] else 'hold'
    statuses=[next((r['status'] for r in rows if r['workerId']==a['workerId']),'unfinished')
              for a in plan['assignments']]
    return dict(version=1,status=status,usage=usage,workerStatuses=statuses)


def read_private(path):
    """Bounded private data only; integrity/authenticity remain host duties."""
    path=Path(path)
    if not path.is_absolute() or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('private physical path required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        if _private(fd).st_size>65536:raise ValueError('coordination data limit')
        return decode(os.read(fd,65537),maximum=65536)
    finally:os.close(fd)


class CoordinationJournal:
    def __init__(self,path,*,plan,create=True):
        self.path=Path(path);self.plan=_plan(plan)
        if type(create) is not bool:raise ValueError('invalid create policy')
        if create:
            private_directory(self.path.parent)
            with self._lock():
                if not self.path.exists() and not self.path.is_symlink():
                    private_write(self.path,dict(version=1,plan=self.plan,workers={
                        a['workerId']:dict(token=None,report=None) for a in self.plan['assignments']}))
                self._read()
        else:self._read()

    @contextmanager
    def _lock(self):
        fd=os.open(str(self.path)+'.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            _private(fd);fcntl.flock(fd,fcntl.LOCK_EX);yield
        finally:os.close(fd)

    def _read(self):
        state=read_private(self.path)
        if (type(state) is not dict or set(state)!={'version','plan','workers'} or
            type(state['version']) is not int or state['version']!=1 or state['plan']!=self.plan or
            type(state['workers']) is not dict or set(state['workers'])!={a['workerId'] for a in self.plan['assignments']}):
            raise ValueError('journal binding mismatch')
        for name,row in state['workers'].items():
            if type(row) is not dict or set(row)!={'token','report'}:raise ValueError('invalid worker state')
            if row['token'] is not None:sha(row['token'])
            if row['report'] is not None:
                if row['token'] is None or _report(self.plan,row['report'])['workerId']!=name:
                    raise ValueError('invalid terminal report')
        return state

    def claim(self,worker_id):
        with self._lock():
            state=self._read()
            if worker_id not in state['workers'] or state['workers'][worker_id]['token'] is not None:
                raise ValueError('worker already launched or foreign')
            token=secrets.token_hex(32);state['workers'][worker_id]['token']=token
            private_write(self.path,state)
            return token

    def settle(self,worker_id,token,report):
        sha(token);report=_report(self.plan,report)
        with self._lock():
            state=self._read();row=state['workers'].get(worker_id)
            if row is None or row['token']!=token or report['workerId']!=worker_id:
                raise ValueError('foreign worker authority')
            if row['report'] is not None and row['report']!=report:raise ValueError('conflicting settlement')
            if row['report'] is None:
                row['report']=report;private_write(self.path,state)
            return report

    def inspect(self):
        state=self._read()
        return dict(plan=self.plan,workers={name:dict(status=(row['report']['status'] if row['report'] is not None else
            'active' if row['token'] is not None else 'unclaimed'),report=row['report']) for name,row in state['workers'].items()})
