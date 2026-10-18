"""Experimental single-host admission containment, not an SDK execution engine.

Only trusted host code may supply identity, bindings, decisions and reconciled
evidence. This journal grants neither provider dispatch nor retry authorization.
"""
from contextlib import contextmanager
import fcntl
import math
import os
from pathlib import Path
import secrets
import time

from .quality.allowance import DIMENSIONS, counts, private_directory, private_write, _private
from .quality.contracts import decode, encode, identifier, sha

_MAXIMUM = dict(providerRequests=4, toolCalls=2, reportedTokens=8192)
_STATES = {'admitted', 'active', 'quarantined', 'completed', 'failed', 'unknown', 'overrun'}
_ROW_KEYS = {'binding', 'token', 'state', 'maximum', 'admittedAt', 'deadline',
             'actual', 'evidenceDigest', 'isolationDecision', 'recoveryDecision', 'outcome'}


class FailureIsolation:
    """Private fsynced local journal within an already authorized allowance.

    No reservation is refunded. A revoked token fences journal writes only;
    consumers must stop workers separately and never redispatch uncertain work.
    """

    def __init__(self, path, *, identity, limits):
        self.path = Path(path)
        self.identity = sha(identity)
        self.limits = counts(limits)
        private_directory(self.path.parent)
        with self._lock():
            if self.path.exists():
                self._read()
            else:
                if self.path.is_symlink():
                    raise ValueError('journal symlink denied')
                private_write(self.path, dict(version=1, identity=self.identity,
                                             limits=self.limits, work={}))

    @contextmanager
    def _lock(self):
        fd = os.open(str(self.path) + '.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            _private(fd)
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)

    def _read(self):
        try:
            fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                if _private(fd).st_size > 4_194_304:
                    raise ValueError('journal too large')
                state = decode(os.read(fd, 4_194_305))
            finally:
                os.close(fd)
            if (type(state) is not dict or set(state) != {'version', 'identity', 'limits', 'work'} or
                    type(state['version']) is not int or state['version'] != 1 or
                    state['identity'] != self.identity or state['limits'] != self.limits or
                    type(state['work']) is not dict or len(state['work']) > 1024):
                raise ValueError('journal binding mismatch')
            for name, row in state['work'].items():
                identifier(name)
                self._validate_row(row)
            return state
        except (OSError, KeyError, TypeError):
            raise ValueError('journal unavailable') from None

    @staticmethod
    def _validate_row(row):
        if type(row) is not dict or set(row) != _ROW_KEYS:
            raise ValueError('invalid work record')
        sha(row['binding'])
        if row['state'] not in _STATES or row['maximum'] != _MAXIMUM:
            raise ValueError('invalid work state')
        for key in ('admittedAt', 'deadline'):
            if type(row[key]) not in (float, int) or not math.isfinite(row[key]):
                raise ValueError('invalid work deadline')
        if row['deadline'] != row['admittedAt'] + 600:
            raise ValueError('changed work deadline')
        for key in ('token', 'isolationDecision', 'recoveryDecision'):
            if row[key] is not None:
                sha(row[key])
        if row['actual'] is not None:
            counts(row['actual'])
            sha(row['evidenceDigest'])
            exceeded = any(row['actual'][k] > _MAXIMUM[k] for k in DIMENSIONS)
            if (row['state'] not in {'completed', 'failed', 'overrun'} or
                    exceeded != (row['state'] == 'overrun') or
                    row['outcome'] != ('completed' if row['state'] == 'completed' else 'failed')):
                raise ValueError('invalid known evidence')
        elif (row['evidenceDigest'] is not None or
              row['state'] not in {'admitted', 'active', 'quarantined', 'unknown'} or
              row['outcome'] != ('unknown' if row['state'] == 'unknown' else None)):
            raise ValueError('invalid unknown evidence')
        if row['isolationDecision'] is None:
            if row['token'] is None or row['recoveryDecision'] is not None or row['state'] in {'quarantined', 'unknown'}:
                raise ValueError('missing writer authority')
        elif (row['token'] is not None or
              (row['state'] == 'quarantined') != (row['recoveryDecision'] is None)):
            raise ValueError('invalid recovery authority')

    @staticmethod
    def _view(row):
        return decode(encode({key: value for key, value in row.items() if key != 'token'}))

    @staticmethod
    def _retained(state):
        return {k: sum(max(row['maximum'][k], (row['actual'] or row['maximum'])[k])
                       for row in state['work'].values()) for k in DIMENSIONS}

    @staticmethod
    def _row(state, work_id):
        identifier(work_id)
        if work_id not in state['work']:
            raise ValueError('unknown work')
        return state['work'][work_id]

    def admit(self, work_id, *, binding):
        identifier(work_id)
        sha(binding)
        with self._lock():
            state = self._read()
            retained = self._retained(state)
            if (work_id in state['work'] or len(state['work']) >= 1024 or
                    any(r['state'] == 'overrun' for r in state['work'].values()) or
                    any(retained[k] + _MAXIMUM[k] > self.limits[k] for k in DIMENSIONS)):
                raise ValueError('work claimed or containment budget exhausted')
            now = time.time()
            token = secrets.token_hex(32)
            state['work'][work_id] = dict(binding=binding, token=token, state='admitted',
                maximum=dict(_MAXIMUM), admittedAt=now, deadline=now + 600, actual=None,
                evidenceDigest=None, isolationDecision=None, recoveryDecision=None, outcome=None)
            private_write(self.path, state)
            return token

    def start(self, work_id, token):
        """Persist uncertain dispatch intent once, before entering public SDKs."""
        sha(token)
        with self._lock():
            state = self._read()
            row = self._row(state, work_id)
            if (row['state'] != 'admitted' or row['token'] != token or time.time() >= row['deadline'] or
                    any(r['state'] == 'overrun' for r in state['work'].values())):
                raise ValueError('dispatch intent denied')
            row['state'] = 'active'
            private_write(self.path, state)
            return self._view(row)

    @staticmethod
    def _settlement(actual, evidence_digest, outcome):
        if outcome not in {'completed', 'failed', 'unknown'}:
            raise ValueError('invalid host outcome')
        if actual is None:
            if outcome != 'unknown' or evidence_digest is not None:
                raise ValueError('unknown usage cannot become success')
            return dict(actual=None, evidenceDigest=None, outcome='unknown', state='unknown')
        actual = counts(actual)
        sha(evidence_digest)
        if outcome == 'unknown':
            raise ValueError('known counts require known outcome')
        exceeded = any(actual[k] > _MAXIMUM[k] for k in DIMENSIONS)
        return dict(actual=actual, evidenceDigest=evidence_digest,
                    outcome='failed' if exceeded else outcome, state='overrun' if exceeded else outcome)

    def complete(self, work_id, token, *, actual, evidence_digest, outcome='completed'):
        """Record trusted host-verified SDK evidence; uncertainty needs recovery."""
        sha(token)
        settled = self._settlement(actual, evidence_digest, outcome)
        if actual is None:
            raise ValueError('isolate unknown work before explicit recovery')
        with self._lock():
            state = self._read()
            row = self._row(state, work_id)
            if row['token'] != token:
                raise ValueError('stale writer denied')
            if row['state'] in {'completed', 'failed', 'overrun'}:
                if any(row[k] != v for k, v in settled.items()):
                    raise ValueError('conflicting completion')
                return self._view(row)
            if row['state'] != 'active':
                raise ValueError('work is not active')
            if settled['outcome'] == 'completed' and time.time() >= row['deadline']:
                raise ValueError('late acceptance denied; explicit recovery required')
            row.update(settled)
            private_write(self.path, state)
            return self._view(row)

    def isolate(self, work_id, *, binding, decision_digest):
        """Host revokes journal writer; it must separately stop the worker."""
        sha(binding)
        sha(decision_digest)
        with self._lock():
            state = self._read()
            row = self._row(state, work_id)
            if row['binding'] != binding:
                raise ValueError('changed work binding')
            if row['state'] == 'quarantined' and row['isolationDecision'] == decision_digest:
                return self._view(row)
            if row['state'] not in {'admitted', 'active'}:
                raise ValueError('work cannot be isolated again')
            row.update(state='quarantined', token=None, isolationDecision=decision_digest)
            private_write(self.path, state)
            return self._view(row)

    def recover(self, work_id, *, binding, decision_digest, actual, evidence_digest, outcome):
        """Explicit receipt-only reconciliation or conservative unknown closure."""
        sha(binding)
        sha(decision_digest)
        settled = self._settlement(actual, evidence_digest, outcome)
        with self._lock():
            state = self._read()
            row = self._row(state, work_id)
            if row['binding'] != binding:
                raise ValueError('changed recovery binding')
            if row['recoveryDecision'] is not None:
                if row['recoveryDecision'] != decision_digest or any(row[k] != v for k, v in settled.items()):
                    raise ValueError('conflicting recovery')
                return self._view(row)
            if row['state'] != 'quarantined':
                raise ValueError('explicit isolation required')
            if settled['outcome'] == 'completed' and time.time() >= row['deadline']:
                raise ValueError('late acceptance denied')
            row.update(settled, recoveryDecision=decision_digest)
            private_write(self.path, state)
            return self._view(row)

    def inspect(self, work_id):
        with self._lock():
            return self._view(self._row(self._read(), work_id))

    def status(self):
        with self._lock():
            state = self._read()
            retained = self._retained(state)
            return dict(retained=retained, remaining={k: max(0, self.limits[k] - retained[k]) for k in DIMENSIONS},
                        admissionBlocked=any(r['state'] == 'overrun' for r in state['work'].values()),
                        work={name: self._view(row) for name, row in state['work'].items()})
