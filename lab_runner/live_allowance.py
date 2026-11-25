"""A private shared request allowance; unknown dispatch retains its reservation."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid


class AllowanceExhausted(ValueError):
    pass


def _integer(value,minimum,maximum):
    if type(value) is not int or not minimum<=value<=maximum:
        raise ValueError('invalid live allowance')


def _private(fd):
    info=os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077:
        raise ValueError('live allowance must be an owned private file')


class SharedLiveAllowance:
    def __init__(self,path,*,max_calls,ceiling=12):
        # Larger experiments require an explicit trusted-host ceiling; ordinary
        # pilots retain their existing twelve-unit boundary and on-disk format.
        _integer(ceiling,1,256)
        _integer(max_calls,1,ceiling)
        self.path=Path(path)
        if not self.path.is_absolute() or self.path.is_symlink():
            raise ValueError('live allowance requires an explicit private path')
        parent=self.path.parent
        if not parent.is_dir() or parent.is_symlink():
            raise ValueError('live allowance parent unavailable')
        self.maximum=max_calls
        self.lock_path=parent/(self.path.name+'.lock')
        with self._locked():
            if self.path.exists():self._read()
            else:self._write({'version':1,'maxCalls':max_calls,'reservations':{}})

    @contextmanager
    def _locked(self):
        try:
            fd=os.open(self.lock_path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
            try:
                _private(fd)
                fcntl.flock(fd,fcntl.LOCK_EX)
                yield
            finally:os.close(fd)
        except OSError:
            raise ValueError('live allowance storage unavailable') from None

    def _read(self):
        def pairs(items):
            value={}
            for key,item in items:
                if key in value:raise ValueError('invalid live allowance record')
                value[key]=item
            return value
        try:
            fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW)
            try:
                _private(fd)
                if os.fstat(fd).st_size>65536:raise ValueError('invalid live allowance record')
                data=os.read(fd,65537)
            finally:os.close(fd)
            value=json.loads(data,object_pairs_hook=pairs)
            if (type(value) is not dict or set(value)!={'version','maxCalls','reservations'} or
                type(value['version']) is not int or value['version']!=1 or
                type(value['maxCalls']) is not int or value['maxCalls']!=self.maximum or
                type(value['reservations']) is not dict or len(value['reservations'])>64):
                raise ValueError('invalid live allowance record')
            for token,row in value['reservations'].items():
                if (not re.fullmatch('[0-9a-f]{32}',token) or type(row) is not dict or
                    set(row)!={'maximum','actual','status'} or row['status'] not in {'reserved','known','unknown'}):
                    raise ValueError('invalid live allowance record')
                _integer(row['maximum'],1,self.maximum)
                if row['status']=='known':_integer(row['actual'],0,row['maximum'])
                elif row['actual'] is not None:raise ValueError('invalid live allowance record')
            if self._retained(value)>self.maximum:raise ValueError('invalid live allowance record')
            return value
        except (OSError,UnicodeError,RecursionError,TypeError):
            raise ValueError('live allowance storage unavailable') from None

    @staticmethod
    def _retained(value):
        return sum(row['actual'] if row['status']=='known' else row['maximum']
            for row in value['reservations'].values())

    def _write(self,value):
        encoded=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
        if len(encoded)>65536:raise ValueError('live allowance record limit')
        temporary=None
        try:
            fd,temporary=tempfile.mkstemp(prefix='.live-allowance-',dir=self.path.parent)
            with os.fdopen(fd,'wb') as handle:
                handle.write(encoded);handle.flush();os.fsync(handle.fileno())
            os.replace(temporary,self.path)
            directory=os.open(self.path.parent,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(directory)
            finally:os.close(directory)
        finally:
            if temporary is not None and os.path.exists(temporary):os.unlink(temporary)

    def reserve(self,*,maximum_requests):
        _integer(maximum_requests,1,self.maximum)
        with self._locked():
            value=self._read()
            if self._retained(value)+maximum_requests>self.maximum or len(value['reservations'])>=64:
                raise AllowanceExhausted('live allowance exhausted')
            token=uuid.uuid4().hex
            value['reservations'][token]={'maximum':maximum_requests,'actual':None,'status':'reserved'}
            self._write(value)
            return token

    def finish(self,token,*,actual_requests):
        if type(token) is not str or not re.fullmatch('[0-9a-f]{32}',token):
            raise ValueError('invalid live reservation')
        with self._locked():
            value=self._read()
            row=value['reservations'].get(token)
            if row is None:raise ValueError('unknown live reservation')
            if actual_requests is not None:_integer(actual_requests,0,row['maximum'])
            status='unknown' if actual_requests is None else 'known'
            if row['status']!='reserved':
                if row['status']!=status or row['actual']!=actual_requests:
                    raise ValueError('conflicting live completion evidence')
                return
            row.update(status=status,actual=actual_requests)
            self._write(value)

    def status(self):
        with self._locked():
            value=self._read();retained=self._retained(value)
            return {'maximum':self.maximum,'retained':retained,'remaining':self.maximum-retained,
                'unknown':sum(row['status']=='unknown' for row in value['reservations'].values())}
