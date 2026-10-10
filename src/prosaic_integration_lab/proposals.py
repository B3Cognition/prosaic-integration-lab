"""Transport validation and immutable, owner-scoped admitted proposals."""
import hashlib
import json
import math
import uuid

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from .metadata import Metadata, RequestConflict, RESERVATION_LOCK_ID


MAX_CHOICE_CHARACTERS = 64


def proposal_transport_schema():
    """Host HTTP limits, independent of the SDK's graph admission contract."""
    return {'properties':{'definition':{'properties':{'steps':{
        'additionalProperties':{'properties':{'choices':{
            'propertyNames':{'maxLength':MAX_CHOICE_CHARACTERS}}}}}}}}}


def validate_proposal_transport(content):
    from jsonschema import Draft202012Validator
    if not Draft202012Validator(proposal_transport_schema()).is_valid(json.loads(content)):
        raise ValueError('invalid_request')


def canonical_proposal(text: str | bytes) -> str:
    """Validate JSON transport only; graph admission belongs to Harness."""
    def invalid():
        raise ValueError('invalid_request') from None

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                invalid()
            result[key] = value
        return result

    try:
        if type(text) not in (str, bytes):
            invalid()
        raw = text.encode('utf-8') if type(text) is str else text
        if len(raw) > 65536:
            invalid()
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=lambda _: invalid())
        if type(value) is not dict:
            invalid()
        pending = [(value, 0)]
        nodes = 0
        while pending:
            item, depth = pending.pop()
            nodes += 1
            if nodes > 65536 or depth > 64:
                invalid()
            if type(item) is dict:
                pending.extend((child, depth + 1) for pair in item.items() for child in pair)
            elif type(item) is list:
                pending.extend((child, depth + 1) for child in item)
            elif type(item) is float and not math.isfinite(item):
                invalid()
            elif type(item) is str:
                item.encode('utf-8')
        canonical = json.dumps(value, ensure_ascii=False, sort_keys=True,
                               separators=(',', ':'), allow_nan=False)
        if len(canonical.encode('utf-8')) > 65536:
            invalid()
        return canonical
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        invalid()


def bounded_text(value, maximum=128):
    try:
        valid = type(value) is str and bool(value) and '\x00' not in value and len(value.encode('utf-8')) <= maximum
    except UnicodeError:
        valid = False
    if not valid:
        raise ValueError('invalid_request')
    return value


def capacity(maximum, tenant):
    if type(maximum) is not int or type(tenant) is not int or not 1 <= tenant <= maximum <= 10000:
        raise ValueError('invalid retention capacity')


class ProposalStore(Metadata):
    def owned(self, principal, proposal_id):
        with self.connection() as connection:
            return connection.execute('''SELECT * FROM lab_app.proposals
                WHERE proposal_id=%s AND tenant_id=%s AND actor_id=%s''',
                (proposal_id, principal.tenant_id, principal.actor_id)).fetchone()

    def replay(self, principal, key, request_digest):
        with self.connection() as connection:
            row = self._lookup(connection, principal, key)
            return self._matching(row, request_digest)

    @staticmethod
    def _matching(row, digest):
        if row is not None and row['request_digest'] != digest:
            raise RequestConflict('idempotency_conflict')
        return row

    @staticmethod
    def _lookup(connection, principal, key):
        return connection.execute('''SELECT * FROM lab_app.proposals
            WHERE tenant_id=%s AND actor_id=%s AND idempotency_key=%s''',
            (principal.tenant_id, principal.actor_id, key)).fetchone()

    def reserve(self, principal, key, prepared, *, maximum_records, maximum_tenant_records):
        from prosaic_harness import PreparedWorkflow, WorkflowReference
        if type(prepared) is not PreparedWorkflow:
            raise ValueError('invalid_request')
        content = canonical_proposal(prepared.proposal_json)
        if content != prepared.proposal_json:
            raise ValueError('invalid_request')
        digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
        with self.connection() as connection:
            row = self._matching(self._lookup(connection, principal, key), digest)
            if row is not None:
                return row
            reference = WorkflowReference.from_dict(prepared.reference.to_dict()).to_dict()
            serialized = json.dumps(reference, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
            if len(serialized.encode('utf-8')) > 4096 or reference['proposalSha256'] != digest:
                raise ValueError('invalid_request')
            capacity(maximum_records, maximum_tenant_records)
            for value in (principal.tenant_id, principal.actor_id, key, reference['bundleVersion']):
                bounded_text(value)
            connection.execute('SELECT pg_advisory_xact_lock(%s::bigint)', (RESERVATION_LOCK_ID,))
            row = self._matching(self._lookup(connection, principal, key), digest)
            if row is not None:
                return row
            counts = connection.execute('''SELECT count(*) AS total,
                count(*) FILTER (WHERE tenant_id=%s) AS tenant FROM lab_app.proposals''',
                (principal.tenant_id,)).fetchone()
            if counts['total'] >= maximum_records or counts['tenant'] >= maximum_tenant_records:
                raise HTTPException(503, 'retention_capacity_exhausted')
            connection.execute('''INSERT INTO lab_app.proposals
                (proposal_id,tenant_id,actor_id,idempotency_key,request_digest,proposal_json,
                 bundle_version,bundle_identity,policy_digest,workflow_fingerprint,reference)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(tenant_id,actor_id,idempotency_key) DO NOTHING''',
                (uuid.uuid4().hex, principal.tenant_id, principal.actor_id, key, digest, content,
                 # This internal policy_digest identifies the full immutable admission/binding
                 # bundle, including policy. The public reference exposes no policy-only digest.
                 reference['bundleVersion'], reference['bundleIdentity'], reference['bundleIdentity'],
                 reference['workflowFingerprint'], Jsonb(reference)))
            return self._matching(self._lookup(connection, principal, key), digest)
