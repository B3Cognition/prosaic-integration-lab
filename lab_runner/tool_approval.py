"""Experimental trusted-host approval; never expose these methods as model tools."""
from contextlib import contextmanager
from dataclasses import asdict
import fcntl
import math
import os
from pathlib import Path
import re
import time

from prosaic_runtime import InvocationScope, ToolExecutionContext
from .quality.allowance import private_directory, private_write, _private
from .quality.contracts import decode, encode, digest, identifier, integer, sha


def _scope(value):
    if type(value) is not InvocationScope or any(v is None for v in asdict(value).values()):
        raise ValueError('complete trusted invocation scope required')
    return asdict(value)


def _instant(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('invalid approval time')
    return value


class ApprovalGate:
    """Durable one-shot consent registry, separate from SDK effect evidence.

    Identity, policies, proposals and decisions come from authenticated host
    code. An actor string is an identifier, not an authentication credential.
    """

    def __init__(self, path, *, identity, tools, approvers):
        sha(identity)
        if type(tools) is not dict or not 1 <= len(tools) <= 64:
            raise ValueError('explicit tool policy required')
        for name, version in tools.items():
            if (type(name) is not str or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', name) or
                    type(version) is not str or not version.strip() or len(version.encode()) > 128):
                raise ValueError('invalid tool policy')
        if (type(approvers) not in (list, tuple) or not 1 <= len(approvers) <= 64 or
                any(identifier(actor) != actor for actor in approvers) or len(set(approvers)) != len(approvers)):
            raise ValueError('explicit authenticated approvers required')
        self._policy = decode(encode(dict(identity=identity, tools=tools, approvers=sorted(approvers))))
        self.path = Path(path)
        private_directory(self.path.parent)
        with self._lock():
            if self.path.exists():
                self._read()
            else:
                if self.path.is_symlink():
                    raise ValueError('approval symlink denied')
                private_write(self.path, dict(version=1, policy=self._policy, proposals={}))

    @contextmanager
    def _lock(self):
        fd = os.open(str(self.path)+'.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
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
                    raise ValueError('approval registry too large')
                data = decode(os.read(fd, 4_194_305))
            finally:
                os.close(fd)
            if (type(data) is not dict or set(data) != {'version', 'policy', 'proposals'} or
                    type(data['version']) is not int or data['version'] != 1 or
                    data['policy'] != self._policy or type(data['proposals']) is not dict or
                    len(data['proposals']) > 128):
                raise ValueError('approval policy mismatch')
            for name, row in data['proposals'].items():
                self._validate(identifier(name), row)
            return data
        except (OSError, KeyError, TypeError):
            raise ValueError('approval registry unavailable') from None

    def _validate(self, name, row):
        if type(row) is not dict or set(row) != {'proposal', 'proposalDigest', 'state', 'decisions', 'spentAt'}:
            raise ValueError('invalid approval record')
        p = row['proposal']
        if (type(p) is not dict or set(p) != {'proposalId', 'policyDigest', 'toolName', 'toolVersion',
                'scope', 'arguments', 'evidenceDigest', 'createdAt', 'expiresAt'} or p['proposalId'] != name or
                p['policyDigest'] != digest(self._policy) or p['toolName'] not in self._policy['tools'] or
                p['toolVersion'] != self._policy['tools'][p['toolName']] or
                type(p['arguments']) is not dict or row['proposalDigest'] != digest(p)):
            raise ValueError('changed approval proposal')
        encode(p['arguments'], 16384)
        sha(p['evidenceDigest'])
        if type(p['scope']) is not dict or set(p['scope']) != {'invocation_id', 'run_id', 'step_id', 'operation_namespace'}:
            raise ValueError('invalid approval scope')
        if _scope(InvocationScope(**p['scope'])) != p['scope']:
            raise ValueError('changed approval scope')
        if not 0 < _instant(p['expiresAt']) - _instant(p['createdAt']) <= 600:
            raise ValueError('invalid approval expiry')
        decisions = row['decisions']
        if type(decisions) is not list or len(decisions) > 2:
            raise ValueError('invalid host decisions')
        previous = p['createdAt']
        for d in decisions:
            if (type(d) is not dict or set(d) != {'actor', 'approved', 'decisionDigest', 'decidedAt'} or
                    d['actor'] not in self._policy['approvers'] or type(d['approved']) is not bool or
                    _instant(d['decidedAt']) < previous or
                    (d['approved'] and d['decidedAt'] >= p['expiresAt'])):
                raise ValueError('invalid host decision')
            sha(d['decisionDigest'])
            previous = d['decidedAt']
        approved = [d['approved'] for d in decisions]
        expected = {'pending': [], 'approved': [True], 'denied': [False], 'revoked': [True, False], 'spent': [True]}
        if row['state'] not in expected or approved != expected[row['state']]:
            raise ValueError('invalid approval state')
        if row['state'] == 'spent':
            if not previous <= _instant(row['spentAt']) < p['expiresAt']:
                raise ValueError('invalid spent consent')
        elif row['spentAt'] is not None:
            raise ValueError('unclaimed consent marked spent')

    @staticmethod
    def _view(row):
        return decode(encode(row['proposal'] | {k: v for k, v in row.items() if k != 'proposal'}))

    @staticmethod
    def _row(data, proposal_id):
        identifier(proposal_id)
        if proposal_id not in data['proposals']:
            raise ValueError('unknown approval proposal')
        return data['proposals'][proposal_id]

    def propose(self, proposal_id, *, tool_name, scope, arguments, evidence_digest, ttl_seconds=600):
        identifier(proposal_id)
        sha(evidence_digest)
        integer(ttl_seconds, 1, 600)
        if tool_name not in self._policy['tools'] or type(arguments) is not dict:
            raise ValueError('action outside host policy')
        arguments = decode(encode(arguments, 16384))
        trusted_scope = _scope(scope)
        with self._lock():
            data = self._read()
            if proposal_id in data['proposals'] or len(data['proposals']) >= 128:
                raise ValueError('proposal already claimed or registry full')
            now = time.time()
            proposal = dict(proposalId=proposal_id, policyDigest=digest(self._policy), toolName=tool_name,
                toolVersion=self._policy['tools'][tool_name], scope=trusted_scope, arguments=arguments,
                evidenceDigest=evidence_digest, createdAt=now, expiresAt=now+ttl_seconds)
            row = dict(proposal=proposal, proposalDigest=digest(proposal), state='pending', decisions=[], spentAt=None)
            data['proposals'][proposal_id] = row
            private_write(self.path, data)
            return self._view(row)

    def decide(self, proposal_id, *, actor, proposal_digest, approved, decision_digest):
        identifier(actor)
        sha(proposal_digest)
        sha(decision_digest)
        if actor not in self._policy['approvers'] or type(approved) is not bool:
            raise ValueError('authenticated host approver required')
        with self._lock():
            data = self._read()
            row = self._row(data, proposal_id)
            if row['proposalDigest'] != proposal_digest:
                raise ValueError('stale or different human review')
            decision = dict(actor=actor, approved=approved, decisionDigest=decision_digest)
            if row['state'] in {'approved', 'denied', 'revoked', 'spent'} and row['decisions'] and all(
                    row['decisions'][-1][k] == v for k, v in decision.items()):
                return self._view(row)
            if row['state'] not in {'pending', 'approved'} or (row['state'] == 'approved' and approved):
                raise ValueError('consent cannot be renewed or reset')
            now = time.time()
            if now < row['proposal']['createdAt'] or (approved and now >= row['proposal']['expiresAt']):
                raise ValueError('approval window unavailable')
            decision['decidedAt'] = now
            row['decisions'].append(decision)
            row['state'] = 'approved' if approved else 'revoked' if row['state'] == 'approved' else 'denied'
            private_write(self.path, data)
            return self._view(row)

    def authorizer(self, proposal_id):
        """Host-selected closure; proposal IDs and decisions are not tool arguments."""
        identifier(proposal_id)
        def authorize(arguments, context):
            try:
                if type(arguments) is not dict or type(context) is not ToolExecutionContext:
                    return False
                if context.cancelled():
                    return False
                context.remaining_timeout(600)
                actual_scope = _scope(context.scope)
                argument_digest = digest(arguments)
                if context.arguments_sha256 != argument_digest:
                    return False
                with self._lock():
                    data = self._read()
                    row = self._row(data, proposal_id)
                    if context.cancelled():
                        return False
                    context.remaining_timeout(600)
                    p = row['proposal']
                    now = time.time()
                    if (row['state'] != 'approved' or not row['decisions'][-1]['decidedAt'] <= now < p['expiresAt'] or
                            p['scope'] != actual_scope or p['toolName'] != context.tool_name or
                            p['toolVersion'] != context.tool_version or digest(p['arguments']) != argument_digest):
                        return False
                    row.update(state='spent', spentAt=now)
                    private_write(self.path, data)
                    return True
            except (ValueError, TypeError, OSError):
                return False
        return authorize

    def inspect(self, proposal_id):
        """Private review/recovery snapshot; never dispatch or infer effect completion."""
        with self._lock():
            return self._view(self._row(self._read(), proposal_id))
