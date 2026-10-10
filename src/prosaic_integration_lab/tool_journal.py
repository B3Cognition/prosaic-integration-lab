"""Application-owned fenced business operations; uncertainty never expires."""
import json
import math
import re
import secrets

from psycopg.types.json import Jsonb
from .metadata import Metadata
from .proposals import bounded_text


def _snapshot_outcome(value):
    try:
        if type(value) is not dict or set(value) != {'status','result'} or value['status'] != 'ok':
            raise ValueError()
        pending = [(value,0)]
        count = 0
        while pending:
            item, depth = pending.pop()
            count += 1
            if count > 65536 or depth > 64:
                raise ValueError()
            if type(item) is dict:
                if any(type(key) is not str for key in item):
                    raise ValueError()
                pending.extend((child,depth+1) for pair in item.items() for child in pair)
            elif type(item) is list:
                pending.extend((child,depth+1) for child in item)
            elif type(item) not in (str,int,float,bool,type(None)):
                raise ValueError()
            elif type(item) is float and not math.isfinite(item):
                raise ValueError()
        # Include JSONB's separator overhead rather than only compact transport.
        text = json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False)
        if len(text.encode('utf-8')) > 262144:
            raise ValueError()
        return json.loads(text)
    except (ValueError,TypeError,UnicodeError,OverflowError,RecursionError):
        raise ValueError('invalid_outcome') from None


class PgToolJournal(Metadata):
    contract_version = 'tool-journal-v1'

    def __init__(self, dsn, *, identity):
        super().__init__(dsn)
        self.identity = bounded_text(identity)

    def claim(self, namespace, key, signature):
        from prosaic_runtime import ToolClaim
        bounded_text(namespace)
        bounded_text(key)
        if type(signature) is not str or re.fullmatch('[0-9a-f]{64}',signature) is None:
            raise ValueError('invalid_request')
        token = secrets.token_hex(32)
        with self.connection() as connection:
            inserted = connection.execute('''INSERT INTO lab_app.tool_operations
                (operation_namespace,operation_key,signature,claim_token,state)
                VALUES (%s,%s,%s,%s,'uncertain') ON CONFLICT DO NOTHING RETURNING claim_token''',
                (namespace,key,signature,token)).fetchone()
            row = connection.execute('''SELECT signature,state,outcome FROM lab_app.tool_operations
                WHERE operation_namespace=%s AND operation_key=%s''',(namespace,key)).fetchone()
            if row['signature'] != signature:
                raise ValueError('tool_identity_conflict')
            if inserted is not None:
                claim = ToolClaim('new',signature,claim_token=token)
            elif row['state'] == 'completed':
                claim = ToolClaim('replay',signature,outcome=_snapshot_outcome(row['outcome']))
            else:
                claim = ToolClaim('uncertain',signature)
        # Only a committed insertion returns dispatch permission.
        return claim

    def commit(self, namespace, key, claim_token, bounded_outcome):
        bounded_text(namespace)
        bounded_text(key)
        bounded_text(claim_token)
        snapshot = _snapshot_outcome(bounded_outcome)
        with self.connection() as connection:
            result = connection.execute('''UPDATE lab_app.tool_operations SET state='completed',outcome=%s
                WHERE operation_namespace=%s AND operation_key=%s AND claim_token=%s AND state='uncertain' ''',
                (Jsonb(snapshot),namespace,key,claim_token))
            if result.rowcount != 1:
                raise ValueError('tool_claim_conflict')
