"""Actual installed conversation engines; SQLite is only host SQL protocol evidence."""
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import socket
import sqlite3
import threading
import time
from types import SimpleNamespace

import pytest


@pytest.fixture
def chat_provider():
    import httpx
    import uvicorn
    from lab_runner.model import app
    sock=socket.socket();sock.bind(('127.0.0.1',0))
    port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='critical',access_log=False,timeout_graceful_shutdown=2))
    worker=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True)
    worker.start()
    endpoint=f'http://127.0.0.1:{port}'
    try:
        deadline=time.monotonic()+10
        while not server.started:
            if not worker.is_alive() or time.monotonic()>deadline:pytest.fail('owned provider readiness failed')
            time.sleep(.02)
        httpx.post(endpoint+'/control',json={'scenario':'conversation'},timeout=5).raise_for_status()
        yield endpoint
    finally:
        if server.started:
            try:httpx.post(endpoint+'/control',json={},timeout=5).raise_for_status()
            except httpx.HTTPError:pass
        server.should_exit=True;worker.join(timeout=5);sock.close()
        assert not worker.is_alive(), 'owned provider cleanup failed'


@pytest.fixture
def chat_client(tmp_path,monkeypatch,chat_provider):
    from fastapi.testclient import TestClient
    from prosaic_harness import FileRunStore,FileSessionStore
    from prosaic_integration_lab import app as service,tool_journal
    from prosaic_integration_lab.execution import Execution
    from prosaic_integration_lab.conversation_execution import ConversationExecution
    spec=importlib.util.spec_from_file_location('host_sql',Path(__file__).parents[1]/'unit/persistence_sql.py')
    sql=importlib.util.module_from_spec(spec);spec.loader.exec_module(sql)
    path=tmp_path/'chat.db';journal_path=tmp_path/'journal.db';effects_path=tmp_path/'effects.db'
    with sqlite3.connect(path) as db:
        db.executescript('''CREATE TABLE sessions(session_id TEXT PRIMARY KEY,tenant_id TEXT,actor_id TEXT,
            billing_account_id TEXT,idempotency_key TEXT,binding_identity TEXT,binding_version TEXT,
            namespace TEXT,environment TEXT,application TEXT,phase TEXT,
            UNIQUE(namespace,environment,tenant_id,actor_id,idempotency_key));
            CREATE TABLE workflow_links(session_id TEXT PRIMARY KEY,registration TEXT,
            source_message_id TEXT,source_revision TEXT,phase TEXT);''')
    with sqlite3.connect(journal_path) as db:
        db.execute('''CREATE TABLE tool_operations(operation_namespace TEXT,operation_key TEXT,signature TEXT,
            claim_token TEXT,state TEXT,outcome TEXT,PRIMARY KEY(operation_namespace,operation_key))''')
    with sqlite3.connect(effects_path) as db:
        db.execute('''CREATE TABLE effects(namespace TEXT,business_key TEXT,amount INTEGER,
            PRIMARY KEY(namespace,business_key))''')
    @contextmanager
    def connect():
        db=sqlite3.connect(':memory:',timeout=5);db.row_factory=sqlite3.Row
        for name,file in (('lab_chat',path),('lab_app',journal_path),('lab_fixture',effects_path)):
            db.execute('ATTACH DATABASE ? AS '+name,(str(file),))
        db.execute('BEGIN IMMEDIATE')
        try:
            with db:yield sql.Connection(db)
        finally:db.close()
    original=tool_journal.PgToolJournal
    class FixtureJournal(original):
        def connection(self):return connect()
    monkeypatch.setattr(tool_journal,'PgToolJournal',FixtureJournal)
    config={'assets':str(Path(__file__).resolve().parents[2]/'assets'),'app_dsn':'unit-sql-protocol',
        'namespace':'owned-chat','environment':'sandbox','fixture_events_url':chat_provider+'/events',
        'principals':{'alice-token':{'tenant_id':'tenant-a','actor_id':'alice','billing_account_id':'payer'},
            'bob-token':{'tenant_id':'tenant-a','actor_id':'bob','billing_account_id':'payer'},
            'other-token':{'tenant_id':'tenant-b','actor_id':'other','billing_account_id':'other-payer'}},
        'conversation':{'dsn':'unused-file-fixture','bundles':[{'version':'balanced-v1',
            'model_url':chat_provider+'/v1','model':'test-model-balanced','model_tier':'balanced',
            'fixture_effects':True,'operation_namespace':'owned-chat-operations','journal_identity':'chat-journal-v1'}],
            'tenants':{'tenant-a':{'enabled':True,'binding_version':'balanced-v1'},
                'tenant-b':{'enabled':True,'binding_version':'balanced-v1'}}}}
    run_store=FileRunStore(tmp_path/'runs',namespace='owned-chat')
    host=SimpleNamespace(config=config,store=run_store,recorder=None,observer=None,
        capacity={'per_tenant':2},metadata=None)
    def build():
        store=FileSessionStore(tmp_path/'sessions',namespace='owned-chat');store.initialize()
        execution=ConversationExecution(host,session_store=store)
        execution.registry.connection=connect
        return execution
    conversation=build()
    class Consumer(Execution):
        def __init__(self,*args,**kwargs):self.__dict__.update(vars(host));self.conversation=conversation
        def ready(self):self.conversation.store.check_ready()
        def close(self):self.conversation.close();self.store.close()
        async def admitted(self,function,*args):return function(*args)
        async def inspected(self,function,*args):return function(*args)
        def read(self,function,*args):return function(*args)
    monkeypatch.setattr(service,'Execution',Consumer);monkeypatch.setattr(service,'load_config',lambda:config)
    with TestClient(service.create_app()) as client:
        def restore():
            client.app.state.execution.conversation.close()
            client.app.state.execution.conversation=build()
        yield SimpleNamespace(client=client,host=host,path=path,journal_path=journal_path,
            effects_path=effects_path,restore=restore,provider=chat_provider)
