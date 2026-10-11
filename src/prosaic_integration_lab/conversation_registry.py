"""Host ownership and retained quotas; session advancement belongs to Harness."""
import re
import unicodedata
import uuid

import psycopg
from psycopg.rows import dict_row
from fastapi import HTTPException


CREATION_LOCK = 0x4C414243484154
APPLICATION = 'integration-lab-chat'


def reference(value, maximum=128):
    if (type(value) is not str or not value or len(value.encode('utf-8')) > maximum or
            any(unicodedata.category(c) in {'Cc','Cf','Cs'} for c in value)):
        raise ValueError('invalid conversation reference')
    return value


def capacity(max_sessions=128,max_owner_sessions=16):
    if (type(max_sessions) is not int or type(max_owner_sessions) is not int or
            not 1 <= max_owner_sessions <= max_sessions <= 128):
        raise ValueError('invalid conversation retention bounds')


class ConversationRegistry:
    def __init__(self,dsn,*,namespace,environment):
        self.dsn=dsn
        self.namespace=reference(namespace)
        if environment not in {'sandbox','production'}:raise ValueError('invalid conversation environment')
        self.environment=environment

    def connection(self):
        return psycopg.connect(self.dsn,row_factory=dict_row,connect_timeout=5,
            options='-c statement_timeout=5000 -c lock_timeout=1000')

    def check_ready(self):
        from .conversation_schema import check_ready
        with self.connection() as connection:check_ready(connection)

    def _scope(self,principal):
        return (self.namespace,self.environment,APPLICATION,reference(principal.tenant_id),
            reference(principal.actor_id),reference(principal.billing_account_id))

    def _matches(self,row,scope,identity,version):
        expected=dict(zip(('namespace','environment','application','tenant_id','actor_id','billing_account_id'),scope))
        expected.update(binding_identity=identity,binding_version=version)
        if any(row[name]!=value for name,value in expected.items()):
            raise HTTPException(409,{'code':'bindingConflict'})

    def reserve_creation(self,principal,key,binding_identity,binding_version,*,
            max_sessions=128,max_owner_sessions=16):
        capacity(max_sessions,max_owner_sessions)
        reference(key);reference(binding_version)
        if type(binding_identity) is not str or not re.fullmatch('[0-9a-f]{64}',binding_identity):
            raise ValueError('invalid conversation binding identity')
        scope=self._scope(principal)
        lookup='''SELECT * FROM lab_chat.sessions WHERE namespace=%s AND environment=%s
            AND tenant_id=%s AND actor_id=%s AND idempotency_key=%s'''
        identity=(self.namespace,self.environment,principal.tenant_id,principal.actor_id,key)
        with self.connection() as connection:
            def replay():
                row=connection.execute(lookup,identity).fetchone()
                if row is not None:
                    row=dict(row);self._matches(row,scope,binding_identity,binding_version)
                return row
            row=replay()
            if row is not None:return row
            connection.execute('SELECT pg_advisory_xact_lock(%s::bigint)',(CREATION_LOCK,))
            row=replay()
            if row is not None:return row
            counts=connection.execute('''SELECT count(*) AS total,
                count(*) FILTER (WHERE tenant_id=%s AND actor_id=%s) AS owner
                FROM lab_chat.sessions''',(principal.tenant_id,principal.actor_id)).fetchone()
            if counts['total']>=max_sessions or counts['owner']>=max_owner_sessions:
                raise HTTPException(422,{'code':'sessionLimit'})
            connection.execute('''INSERT INTO lab_chat.sessions(session_id,namespace,environment,
                application,tenant_id,actor_id,billing_account_id,idempotency_key,binding_identity,
                binding_version,phase) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'reserved')''',
                (uuid.uuid4().hex,*scope,key,binding_identity,binding_version))
            return replay()

    def adopt_creation(self,reservation,session_id):
        if session_id!=reservation['session_id']:raise ValueError('conversation creation identity mismatch')
        with self.connection() as connection:
            row=connection.execute('SELECT * FROM lab_chat.sessions WHERE session_id=%s',(session_id,)).fetchone()
            if row is None or any(row[name]!=reservation[name] for name in
                    ('namespace','environment','application','tenant_id','actor_id','billing_account_id',
                     'binding_identity','binding_version','idempotency_key')):
                raise HTTPException(409,{'code':'bindingConflict'})
            connection.execute("UPDATE lab_chat.sessions SET phase='created' WHERE session_id=%s AND phase='reserved'",(session_id,))

    def creation(self,principal,key):
        reference(key)
        with self.connection() as connection:
            row=connection.execute('''SELECT * FROM lab_chat.sessions WHERE namespace=%s AND environment=%s
                AND tenant_id=%s AND actor_id=%s AND idempotency_key=%s''',
                (self.namespace,self.environment,principal.tenant_id,principal.actor_id,key)).fetchone()
            if row is None:return None
            row=dict(row)
            self._matches(row,self._scope(principal),row['binding_identity'],row['binding_version'])
            return row

    def owned(self,principal,session_id):
        if type(session_id) is not str or not re.fullmatch('[0-9a-f]{32}',session_id):return None
        with self.connection() as connection:
            row=connection.execute('''SELECT * FROM lab_chat.sessions
                WHERE session_id=%s AND tenant_id=%s AND actor_id=%s''',
                (session_id,principal.tenant_id,principal.actor_id)).fetchone()
            if row is None:return None
            row=dict(row)
            self._matches(row,self._scope(principal),row['binding_identity'],row['binding_version'])
            return row
