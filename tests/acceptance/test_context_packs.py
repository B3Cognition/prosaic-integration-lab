"""Required candidate lane: actual restricted PostgreSQL, installed public SDKs.

The loopback provider is deterministic. These are disclosure/durability witnesses,
not evidence of answer-quality improvements from a live model.
"""
import json
import uuid
import pytest

from lab_runner.context_packs import endpoint,answer,read_answer
from prosaic_integration_lab.context_packs import scenario,conversation,markdown_workflow,require_context_pack_sdk


@pytest.fixture
def provider():
    with endpoint() as value: yield value


@pytest.fixture
def store(lab):
    from prosaic_harness_postgres import PostgresSessionStore
    require_context_pack_sdk()
    with PostgresSessionStore(lab['conversation']['dsn'],namespace='packs-'+uuid.uuid4().hex) as value:
        value.check_ready();yield value


def send(store,provider,*,kind='service-impact',**kwargs):
    url,requests,replies=provider
    bindings,candidates=scenario(kind,namespace=store.namespace,**kwargs)
    citation=candidates.variants[-1]['items'][0]['citationId']
    replies.append(answer('Supported observation ['+citation+']'))
    chat=conversation(bindings,store,url);session=chat.create()
    arguments=dict(message_id='question',message='Review with citations',expected_revision=session.revision,context_pack=candidates)
    reply=chat.send(session.session_id,**arguments)
    assert reply.document['status']=='completed' and citation in reply.document['answer']
    assert 'UNDECLARED-819' not in json.dumps(requests)
    return chat,session,arguments,reply


def test_markdown_nodes_select_independent_contexts(lab,provider,tmp_path):
    from prosaic_harness_postgres import PostgresRunStore
    url,requests,replies=provider;replies.extend([answer('{"ok":true}')]*2)
    with PostgresRunStore(lab['harness_dsn'],namespace='packs-'+uuid.uuid4().hex) as run_store:
        run_store.check_ready();controller=markdown_workflow(tmp_path.resolve(),url,run_store)
        result=controller.run({'task':'Review','private':'UNDECLARED-819'})
        assert result['status']=='completed'
        assert 'CONSTRAINTS-317' in json.dumps(requests[0]) and 'CONSTRAINTS-317' not in json.dumps(requests[1])
        assert all('REQUIREMENTS-214' in json.dumps(value) for value in requests)
        assert 'UNDECLARED-819' not in json.dumps(requests)
        assert 'candidate' in json.dumps(requests[1])


def test_service_context_reopens_and_replays_without_provider_work(lab,store,provider):
    chat,session,arguments,reply=send(store,provider)
    from prosaic_harness import Conversation
    reopened=Conversation(chat.bindings,store=store,scope=chat.scope)
    assert reopened.send(session.session_id,**arguments).document==reply.document
    assert len(provider[1])==1
    assert 'release-email' in json.dumps(provider[1][0])
    from prosaic_harness_postgres import PostgresRunStore
    from prosaic_integration_lab.context_packs import service_workflow
    with PostgresRunStore(lab['harness_dsn'],namespace='packs-'+uuid.uuid4().hex) as run_store:
        controller,calls=service_workflow(provider[0],run_store)
        provider[2].append(answer('{"ok":true}'))
        state=controller.run({'task':'Find service impact','private':'UNDECLARED-819'})
        assert state['status']=='completed' and calls==[{}]
        assert 'release-email' in json.dumps(provider[1][-1]) and 'UNDECLARED-819' not in json.dumps(provider[1])


def test_reader_returns_only_declared_capture_and_records_citation(store,provider):
    from prosaic_harness import ContextPackReader
    url,requests,replies=provider;reader=ContextPackReader()
    bindings,candidates=scenario('service-impact',reader=True,namespace=store.namespace)
    citation=candidates.variants[0]['index'][0]['citationId']
    replies.extend([read_answer(citation),answer('Impact ['+citation+']')])
    chat=conversation(bindings,store,url,reader=reader);session=chat.create()
    reply=chat.send(session.session_id,message_id='read',message='Read the lookup',expected_revision=session.revision,context_pack=candidates)
    assert reply.document['status']=='completed' and len(requests)==2 and reader.active_count==0
    assert 'release-email' not in json.dumps(requests[0]) and 'release-email' in json.dumps(requests[1])
    state=store.load_session(session.session_id,scope=chat.scope).state
    receipt=store.load_receipt(session.session_id,state['turns'][0]['attempts'][0],scope=chat.scope)
    assert 'read' in json.dumps(receipt) and citation in json.dumps(receipt)
    assert all(len(json.dumps(message).encode())<=24576+4096 for message in requests[1]['messages'] if message['role']=='tool')


def test_allowed_partial_context_retains_domain_completeness(store,provider):
    send(store,provider,outcome='partial',allow_partial=True)
    assert 'domainComplete' in json.dumps(provider[1]) and 'false' in json.dumps(provider[1])


def test_required_partial_context_is_refused_without_provider(store,provider):
    from prosaic_harness import ContextPackError
    with pytest.raises(ContextPackError):scenario('service-impact',outcome='partial',namespace=store.namespace)
    assert provider[1]==[]


def test_required_missing_context_is_refused_without_provider(store,provider):
    from prosaic_harness import ContextPackError
    with pytest.raises(ContextPackError):scenario('service-impact',outcome='unavailable',namespace=store.namespace)
    assert provider[1]==[]


def test_contradictory_observations_are_preserved(store,provider):
    send(store,provider,conflict=True)
    assert all(value in json.dumps(provider[1]) for value in ('revision-a','revision-b'))


def test_retained_view_rechecks_current_permission(store,provider):
    from prosaic_harness import ConversationError
    allowed=[True]
    chat,session,_,_=send(store,provider,authorize=lambda use:allowed[0])
    allowed[0]=False
    with pytest.raises(ConversationError):chat.history(session.session_id)
    assert len(provider[1])==1


def test_foreign_scope_is_refused_before_dispatch(store,provider):
    from prosaic_harness import ConversationError
    url,requests,_=provider
    bindings,_=scenario('service-impact',namespace=store.namespace)
    _,foreign=scenario('service-impact',namespace='foreign-namespace')
    chat=conversation(bindings,store,url);session=chat.create()
    with pytest.raises(ConversationError):chat.send(session.session_id,message_id='foreign',message='Review',
        expected_revision=session.revision,context_pack=foreign)
    assert requests==[]


def test_saved_receipt_is_adopted_by_fresh_controller(lab,provider):
    from prosaic_harness_postgres import PostgresSessionStore
    from prosaic_harness import Conversation
    class Interrupted(BaseException):pass
    class InterruptStore(PostgresSessionStore):
        def save_receipt(self,*args,**kwargs):
            super().save_receipt(*args,**kwargs);raise Interrupted()
    namespace='packs-'+uuid.uuid4().hex;url,requests,replies=provider
    bindings,candidates=scenario('service-impact',namespace=namespace)
    with InterruptStore(lab['conversation']['dsn'],namespace=namespace) as original:
        chat=conversation(bindings,original,url);session=chat.create();replies.append(answer('Saved answer'))
        with pytest.raises(Interrupted):chat.send(session.session_id,message_id='saved',message='Review',
            expected_revision=session.revision,context_pack=candidates)
    with PostgresSessionStore(lab['conversation']['dsn'],namespace=namespace) as reopened:
        restored=Conversation(chat.bindings,store=reopened,scope=chat.scope)
        reply=restored.recover(session.session_id)
        assert reply.document['status']=='completed' and len(requests)==1


def test_large_captured_context_obeys_default_record_capacity(store,provider):
    from prosaic_harness import ContextPackSpec,ContextSlot,ContextPackBindings,InputSource,ContextPacker
    from prosaic_harness.context_packs import capture_sources
    url,requests,replies=provider
    bindings,_=scenario('service-impact',namespace=store.namespace)
    spec=ContextPackSpec('impact','1',[ContextSlot('task',required=True)]+[ContextSlot('fact'+str(i)) for i in range(15)],task_source='task')
    bindings=ContextPackBindings(specs={'impact':spec},sources={'task':InputSource('/task'),
        **{'fact'+str(i):InputSource('/fact'+str(i)) for i in range(15)}},scope=bindings.scope,authorizer=bindings.authorizer)
    records={'task':'Review','private':'PRIVATE-819'+'p'*65536,**{'fact'+str(i):'f'*2300 for i in range(15)}}
    candidates=ContextPacker().compose(spec,capture_sources(spec,{'request':records},{},bindings))
    assert len(candidates.snapshot.items)==16 and len(json.dumps(candidates.snapshot.to_dict()).encode())>=32768
    chat=conversation(bindings,store,url);session=chat.create();replies.append(answer('Task-only answer'))
    reply=chat.send(session.session_id,message_id='capacity',message='Review',expected_revision=session.revision,context_pack=candidates)
    assert reply.document['status']=='completed' and 'PRIVATE-819' not in json.dumps(requests)
    state=store.load_session(session.session_id,scope=chat.scope).state
    receipt=store.load_receipt(session.session_id,state['turns'][0]['attempts'][0],scope=chat.scope)
    assert len(json.dumps(receipt).encode())<=1048576 and len(json.dumps(state).encode())<=4194304


def test_runtime_role_cannot_migrate(lab):
    import psycopg
    with psycopg.connect(lab['conversation']['dsn']) as connection:
        assert connection.execute("SELECT has_schema_privilege(current_user,'public','CREATE')").fetchone()==(False,)
        assert connection.execute("SELECT has_schema_privilege(current_user,'prosaic_harness_conversations','CREATE')").fetchone()==(False,)
