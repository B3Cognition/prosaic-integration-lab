"""Ephemeral host journal for unit tests; owned acceptance uses the real PG host."""
import json,uuid
class Journal:
    identity='fixture-'+uuid.uuid4().hex
    contract_version='tool-journal-v1'
    def __init__(self):self.rows={}
    def claim(self,namespace,key,signature):
        from prosaic_runtime import ToolClaim
        if (namespace,key) not in self.rows:
            token=uuid.uuid4().hex;self.rows[namespace,key]=(signature,token,None)
            return ToolClaim('new',signature,claim_token=token)
        stored,_,outcome=self.rows[namespace,key]
        return ToolClaim('replay' if outcome else 'uncertain',stored,outcome=json.loads(outcome) if outcome else None)
    def commit(self,namespace,key,claim_token,outcome):
        signature,token,previous=self.rows[namespace,key]
        if token!=claim_token or previous is not None:raise ValueError('stale claim')
        self.rows[namespace,key]=(signature,token,json.dumps(outcome))
