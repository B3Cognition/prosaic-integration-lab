"""SQL protocol checks; PostgreSQL locking/grants remain required stack evidence."""
from contextlib import contextmanager
import sqlite3

import pytest
from fastapi import HTTPException

from prosaic_integration_lab.identity import Principal


@pytest.fixture
def registry(tmp_path):
    from prosaic_integration_lab.conversation_registry import ConversationRegistry
    path = tmp_path / 'registry.db'
    with sqlite3.connect(path) as db:
        db.execute('''CREATE TABLE sessions(session_id TEXT PRIMARY KEY,tenant_id TEXT,
            actor_id TEXT,billing_account_id TEXT,idempotency_key TEXT,binding_identity TEXT,
            binding_version TEXT,namespace TEXT,environment TEXT,application TEXT,phase TEXT,
            UNIQUE(namespace,environment,tenant_id,actor_id,idempotency_key))''')
    class Connection:
        def __init__(self, db): self.db = db
        def execute(self, statement, params=()):
            if statement.startswith('SELECT pg_advisory_xact_lock'):
                return self.db.execute('SELECT 1')
            return self.db.execute(statement.replace('%s','?'),params)
    @contextmanager
    def connect():
        db=sqlite3.connect(':memory:')
        db.row_factory=sqlite3.Row
        db.execute('ATTACH DATABASE ? AS lab_chat',(str(path),))
        db.execute('BEGIN IMMEDIATE')
        try:
            with db: yield Connection(db)
        finally: db.close()
    value=ConversationRegistry('unused',namespace='chat',environment='sandbox')
    value.connection=connect
    return value


ALICE=Principal('one','alice','payer-one')
BOB=Principal('one','bob','payer-one')


def reserve(registry,key='one',**kwargs):
    return registry.reserve_creation(ALICE,key,'a'*64,'chat-v1',**kwargs)


def test_reservation_preallocates_and_exact_replay_survives_capacity(registry):
    first=reserve(registry,max_sessions=1,max_owner_sessions=1)
    assert len(first['session_id'])==32 and first['phase']=='reserved'
    assert reserve(registry,max_sessions=1,max_owner_sessions=1)==first
    with pytest.raises(HTTPException) as error:
        reserve(registry,'two',max_sessions=1,max_owner_sessions=1)
    assert error.value.status_code==422
    assert error.value.detail=={'code':'sessionLimit'}


def test_adoption_preserves_rows_at_capacity_and_is_idempotent(registry):
    row=reserve(registry,max_sessions=1,max_owner_sessions=1)
    registry.adopt_creation(row,row['session_id'])
    registry.adopt_creation(row,row['session_id'])
    assert reserve(registry,max_sessions=1,max_owner_sessions=1)['phase']=='created'
    with pytest.raises(HTTPException):reserve(registry,'next',max_sessions=1,max_owner_sessions=1)


def test_adoption_cannot_switch_session_or_binding(registry):
    row=reserve(registry)
    with pytest.raises(ValueError):registry.adopt_creation(row,'f'*32)
    forged={**row,'binding_identity':'b'*64}
    with pytest.raises(HTTPException):registry.adopt_creation(forged,row['session_id'])
    assert reserve(registry)['phase']=='reserved'


def test_replay_rejects_binding_and_frozen_payer_drift(registry):
    reserve(registry)
    with pytest.raises(HTTPException):registry.reserve_creation(ALICE,'one','b'*64,'chat-v1')
    with pytest.raises(HTTPException):
        registry.reserve_creation(Principal('one','alice','changed'),'one','a'*64,'chat-v1')


def test_owned_lookup_filters_actor_and_tenant(registry):
    row=reserve(registry)
    assert registry.owned(ALICE,row['session_id'])==row
    assert registry.owned(BOB,row['session_id']) is None
    assert registry.owned(Principal('two','alice','payer-two'),row['session_id']) is None


def test_creation_lookup_returns_original_binding_before_new_default(registry):
    first=reserve(registry)
    assert registry.creation(ALICE,'one')==first
    assert registry.creation(BOB,'one') is None
    assert registry.creation(ALICE,'unseen') is None


@pytest.mark.parametrize('key',['', 'x'*129, 'bad\nkey'])
def test_keys_are_bounded_before_storage(registry,key):
    with pytest.raises(ValueError):reserve(registry,key)


@pytest.mark.parametrize('maximum',[True,0,129])
def test_quota_bounds_are_finite(registry,maximum):
    with pytest.raises(ValueError):reserve(registry,max_sessions=maximum)
