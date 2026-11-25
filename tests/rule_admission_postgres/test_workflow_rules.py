"""Required PG16/18 recovery through public stores and copied installed blueprint."""
import json
import os
from pathlib import Path
import runpy
import sys
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import pytest
import yaml

from lab_runner.rule_admission.fixtures import scripted_provider


@pytest.mark.parametrize('wire',['openai-compatible','anthropic'])
@pytest.mark.parametrize('accepted',[True,False])
def test_workflow_guard_receipt_survives_postgres_reopen_without_http(tmp_path,wire,accepted):
    from prosaic_harness import Harness
    from prosaic_harness_postgres import PostgresRunStore
    from lab_runner.blueprints import copy_blueprint
    base=os.environ.get('PROSAIC_RULE_POSTGRES_DSN')
    assert base, 'required workflow lane needs an explicitly owned disposable PROSAIC_RULE_POSTGRES_DSN'
    name='workflow_rules_lab_'+uuid4().hex
    with psycopg.connect(base,autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    dsn=make_conninfo(base,dbname=name)
    class LostReceiptAcknowledgment(BaseException): pass
    class Store(PostgresRunStore):
        def save_receipt(self,run_id,invocation_id,receipt,lease):
            super().save_receipt(run_id,invocation_id,receipt,lease)
            if receipt['step']=='revised_review':
                raise LostReceiptAcknowledgment()
    store=None
    try:
        store=Store(dsn,namespace='workflow-rules')
        store.initialize()
        project=copy_blueprint('workflow-enforcement',tmp_path/'copy')
        with scripted_provider(wire) as provider:
            config=yaml.safe_load((project/'runtime.yml').read_text())
            config['profiles']['local'].update(base_url=provider.url,provider=wire,max_tokens=256)
            (project/'runtime.yml').write_text(yaml.safe_dump(config))
            host=runpy.run_path(str(project/'host.py'))
            workflow=host['workflow'](executable=str(Path(sys.executable).with_name('prosaic')))
            request={'insights':[{'id':'A','text':'first'},{'id':'B','text':'second'},{'id':'C','text':'untouched'}]}
            provider.queue_text('{"findings":[{"insight_id":"A","text":"flagged"}]}')
            provider.queue_text('{"insights":[{"id":"A","text":"first"},{"id":"B","text":"edited"},{"id":"C","text":"untouched"}]}')
            provider.queue_text('{"findings":[{"insight_id":"C","text":"untouched"}]}')
            provider.queue_text(json.dumps({'findings':[{'insight_id':'B' if accepted else 'C','text':'final'}]}))
            run_id=uuid4().hex
            h=Harness(workflow,store=store,run_id=run_id,validators=host['validators']())
            with pytest.raises(LostReceiptAcknowledgment):h.run(request)
            store.close()
            store=PostgresRunStore(dsn,namespace='workflow-rules');store.check_ready()
            fresh=Harness(workflow,store=store,run_id=run_id,validators=host['validators']())
            evidence=fresh.recovery_evidence()
            assert evidence['recoveryStatus']=='receiptAvailable'
            assert evidence['receipts'][-1]['result']['metadata']['workflow_rules_v1']['rules']['violated']
            state=fresh.resume()
            assert state['status']==('waiting' if accepted else 'blocked') and len(provider.requests)==4
            if accepted:
                state=fresh.resume(choice='accept',expected_revision=fresh.status().revision)
                assert state['status']=='completed'
            else: assert state['reason']=='rule_violation'
            assert fresh.resume()['status']==state['status'] and len(provider.requests)==4
    finally:
        try:
            if store is not None:store.close()
        finally:
            with psycopg.connect(base,autocommit=True) as admin:
                admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
                assert admin.execute('SELECT 1 FROM pg_database WHERE datname=%s',(name,)).fetchone() is None
