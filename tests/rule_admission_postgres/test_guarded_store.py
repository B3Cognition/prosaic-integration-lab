"""Required installed-SDK PostgreSQL lane; opt in with an owned disposable DSN."""
from dataclasses import replace
import os
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import pytest

from lab_runner.rule_admission.fixtures import scripted_provider


@pytest.mark.parametrize('wire', ['openai-compatible', 'anthropic'])
def test_guarded_receipt_survives_postgres_reopen_and_recovery(wire):
    from prosaic_harness import Conversation, ConversationScope
    from prosaic_harness_postgres import PostgresSessionStore
    from lab_runner.rule_admission.blueprint import host
    from lab_runner.rule_admission.blueprint.harness import build_bindings
    base = os.environ.get('PROSAIC_RULE_POSTGRES_DSN')
    assert base, 'this required lane needs PROSAIC_RULE_POSTGRES_DSN for an owned disposable PostgreSQL instance'
    name = 'rule_lab_' + uuid4().hex
    with psycopg.connect(base, autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    dsn = make_conninfo(base, dbname=name)
    store = PostgresSessionStore(dsn, namespace='rules')
    try:
        store.initialize()
        with scripted_provider(wire) as provider:
            cfg = host.load_config(base_url=provider.url)
            cfg = replace(cfg, profiles={cfg.default_profile: replace(cfg.profiles[cfg.default_profile], provider=wire)})
            bindings = build_bindings(config=cfg)
            scope = ConversationScope('rules', 'synthetic', 'catalogue', 'tenant', 'borrower')
            controller = Conversation(bindings, store=store, scope=scope)
            session = controller.create()
            provider.queue_text('The fee is EUR 999.')
            provider.queue_text('The fee is EUR 999.')
            class Crash(BaseException): pass
            def crash(event):
                if event['event'] == 'receiptSaved': raise Crash()
            with pytest.raises(Crash):
                controller.send(session.session_id, message_id='fee', message='What is the fee?',
                    expected_revision=session.revision, on_event=crash)
            state = store.load_session(session.session_id, scope=scope).state
            aid = state['turns'][-1]['attempts'][-1]
            stored = store.load_receipt(session.session_id, aid, scope=scope)
            assert stored['result']['failureCode'] == 'ruleViolation'
            assert stored['rules']['violated'] == ['subagents/catalogue-desk.md:12:value_in_tool_output']
            store.close()
            store = PostgresSessionStore(dsn, namespace='rules')
            store.check_ready()
            fresh = Conversation(bindings, store=store, scope=scope)
            reply = fresh.recover(session.session_id).document
            assert reply['status'] == 'failed' and reply['failureCode'] == 'ruleViolation'
            assert fresh.recover(session.session_id).document == reply
            assert len(provider.raw_requests) == 2
    finally:
        store.close()
        with psycopg.connect(base, autocommit=True) as admin:
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
