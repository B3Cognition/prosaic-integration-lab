"""Durable benchmark reservations; independent of legacy live allowance formats."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat
import tempfile
import time
from .contracts import decode, encode, identifier, integer, sha

DIMENSIONS = ('providerRequests','toolCalls','reportedTokens')


def counts(value):
    if type(value) is not dict or set(value) != set(DIMENSIONS):
        raise ValueError('invalid benchmark allowance')
    return {key:integer(value[key]) for key in DIMENSIONS}


def private_directory(path):
    path = Path(path)
    if not path.is_absolute() or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('private absolute benchmark directory required')
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('benchmark directory must be private')
    return path


def _private(fd):
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('benchmark file must be private')
    return info


def private_write(path, value):
    path = Path(path)
    private_directory(path.parent)
    data = encode(value)
    temporary = None
    try:
        fd, temporary = tempfile.mkstemp(prefix='.quality-',dir=path.parent)
        with os.fdopen(fd,'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        if path.is_symlink(): raise ValueError('benchmark symlink denied')
        os.replace(temporary,path)
        parent = os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(parent)
        finally: os.close(parent)
    finally:
        if temporary and os.path.exists(temporary): os.unlink(temporary)


class BenchmarkAllowance:
    def __init__(self,path,*,identity,limits):
        self.path=Path(path); self.identity=sha(identity)
        if type(limits) is not dict or set(limits) != {*DIMENSIONS,'maxSamples','timeoutSeconds'}:
            raise ValueError('invalid benchmark ceilings')
        self.limits={k:integer(v,1,1_000_000_000) for k,v in limits.items()}
        if not self.path.is_absolute(): raise ValueError('absolute allowance required')
        private_directory(self.path.parent)
        if self.path.is_symlink(): raise ValueError('benchmark symlink denied')
        with self._lock():
            if self.path.exists(): self._read()
            else:
                now=time.time()
                private_write(self.path,dict(version=1,identity=identity,limits=self.limits,
                    startedAt=now,deadline=now+self.limits['timeoutSeconds'],samples={}))

    @contextmanager
    def _lock(self):
        fd=os.open(str(self.path)+'.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            _private(fd);fcntl.flock(fd,fcntl.LOCK_EX);yield
        finally:os.close(fd)

    def _read(self):
        try:
            fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW)
            try:
                if _private(fd).st_size > 4_194_304: raise ValueError('allowance limit')
                state=decode(os.read(fd,4_194_305))
            finally:os.close(fd)
            if (set(state) != {'version','identity','limits','startedAt','deadline','samples'} or
                    type(state['version']) is not int or state['version'] != 1 or
                    state['identity'] != self.identity or state['limits'] != self.limits or
                    type(state['samples']) is not dict or len(state['samples'])>self.limits['maxSamples'] or
                    type(state['startedAt']) not in (int,float) or
                    state['deadline'] != state['startedAt']+self.limits['timeoutSeconds']):
                raise ValueError('benchmark binding mismatch')
            for sample,row in state['samples'].items():
                identifier(sample)
                if set(row) != {'maximum','actual','state','evidenceDigest'} or row['state'] not in {'pending','unknown','known'}:
                    raise ValueError('invalid reservation')
                counts(row['maximum'])
                if row['state']=='known':
                    counts(row['actual']);sha(row['evidenceDigest'])
                    if any(row['actual'][k]>row['maximum'][k] for k in DIMENSIONS):raise ValueError('overspent')
                elif row['actual'] is not None or row['evidenceDigest'] is not None:
                    raise ValueError('invalid uncertainty')
            if any(self._retained(state)[k]>self.limits[k] for k in DIMENSIONS):raise ValueError('overspent')
            return state
        except (OSError,KeyError,TypeError):raise ValueError('benchmark allowance unavailable') from None

    @staticmethod
    def _retained(state):
        return {k:sum((r['actual'] if r['state']=='known' else r['maximum'])[k]
                      for r in state['samples'].values()) for k in DIMENSIONS}

    def reserve(self,sample_id,maximum):
        identifier(sample_id);maximum=counts(maximum)
        with self._lock():
            state=self._read();retained=self._retained(state)
            if (time.time()>=state['deadline'] or sample_id in state['samples'] or
                    len(state['samples'])>=self.limits['maxSamples'] or
                    any(r['state']=='unknown' for r in state['samples'].values()) or
                    any(retained[k]+maximum[k]>self.limits[k] for k in DIMENSIONS)):
                raise ValueError('benchmark allowance exhausted or sample claimed')
            row=dict(maximum=maximum,actual=None,state='pending',evidenceDigest=None)
            state['samples'][sample_id]=row;private_write(self.path,state)
            return decode(encode(row))

    def finish(self,sample_id,*,actual,evidence_digest):
        identifier(sample_id)
        if actual is not None:actual=counts(actual);sha(evidence_digest)
        elif evidence_digest is not None:raise ValueError('unknown evidence')
        with self._lock():
            state=self._read();previous=state['samples'][sample_id]
            if actual is not None and any(actual[k]>previous['maximum'][k] for k in DIMENSIONS):
                raise ValueError('benchmark reservation exceeded')
            row=dict(maximum=previous['maximum'],actual=actual,
                     state='unknown' if actual is None else 'known',evidenceDigest=evidence_digest)
            if previous['state']!='pending' and previous!=row:
                raise ValueError('conflicting benchmark settlement')
            state['samples'][sample_id]=row;private_write(self.path,state)
            return decode(encode(row))

    def status(self):
        with self._lock():
            state=self._read();retained=self._retained(state)
            return dict(retained=retained,remaining={k:self.limits[k]-retained[k] for k in DIMENSIONS},
                pendingSamples=sum(r['state']=='pending' for r in state['samples'].values()),
                unknownSamples=sum(r['state']=='unknown' for r in state['samples'].values()),
                samples=len(state['samples']),deadline=state['deadline'])

    def sample(self,sample_id):
        identifier(sample_id)
        with self._lock():return decode(encode(self._read()['samples'].get(sample_id)))
