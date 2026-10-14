"""Required owned-stack context evidence; only installed public SDK APIs."""
import uuid
import pytest
import httpx
import psycopg
from lab_runner.conversation_scenarios import create,send,request
from lab_runner.native_scenarios import calls,control


def principal(lab,tenant):
    return next(p for p in lab['principals'].values() if p['tenant_id']==tenant)


@pytest.fixture(autouse=True)
def context_fixture(lab):
    assert lab.get('context_assembly') is True,'required context stack is missing'
    control(lab,scenario='conversation')
    yield
    control(lab)


def test_context_quality_exposes_lost_history_and_preserves_current_authority(lab):
    from lab_runner.context_scenarios import capture_context_quality
    report=capture_context_quality(lab)
    rows={row['caseId']:row for row in report['cases']}
    assert rows['recent-preference']['omitOldestTurns']['outcome']=='completed'
    assert rows['older-preference']['fullHistory']['outcome']=='completed'
    assert rows['older-preference']['omitOldestTurns']['outcome']=='lostContext'
    assert rows['mandatory-interaction']['omitOldestTurns']['outcome']=='completed'
    assert rows['historical-injection']['omitOldestTurns']['outcome']=='safeDenial'
    assert report['productionCounterQualified'] is False


@pytest.mark.parametrize('tenant',['context-full','context-omit'])
def test_context_report_replays_on_other_replica_without_provider_dispatch(lab,tenant):
    p=principal(lab,tenant)
    current=send(lab,p,create(lab,p,uuid.uuid4().hex),'hello','Hello')
    before=calls(lab)
    recovered=request(lab,p,'POST','/conversations/'+current['sessionId']+'/recover',replica='b',json={})
    assert recovered.status_code==200 and recovered.json()==current
    assert current['contextAssembly']['evidenceKind']=='synthetic'
    assert calls(lab)==before


def test_full_history_overflow_allocates_no_call_or_accounting_intent(lab):
    p=principal(lab,'context-full')
    current=create(lab,p,uuid.uuid4().hex)
    for index in range(2):current=send(lab,p,current,str(index),'x'*12000)
    before=calls(lab)
    usage=request(lab,p,'GET','/conversations/'+current['sessionId']+'/usage').json()
    result=request(lab,p,'POST','/conversations/'+current['sessionId']+'/messages',json={
        'messageId':'overflow','message':'x'*12000,'expectedRevision':current['revision']})
    assert result.status_code==422
    assert calls(lab)==before
    after=request(lab,p,'GET','/conversations/'+current['sessionId']+'/usage').json()
    assert after['conversation']['total_calls']==usage['conversation']['total_calls']
    assert after['conversation']['complete_calls']==usage['conversation']['complete_calls']
    assert after['conversation']['unresolved_calls']==usage['conversation']['unresolved_calls']


def test_context_report_and_full_history_remain_owner_scoped(lab):
    p=principal(lab,'context-omit')
    other=principal(lab,'context-full')
    current=send(lab,p,create(lab,p,uuid.uuid4().hex),'hello','Hello')
    assert not {'sourceHistoryDigest','counterIdentity'} & current['contextAssembly'].keys()
    for suffix in ('','/history'):
        assert request(lab,other,'GET','/conversations/'+current['sessionId']+suffix).status_code==404


def test_posteffect_context_failure_keeps_sql_journal_and_known_usage(lab):
    from prosaic_runtime import (CustomTool,ProsaicArtifact,RuntimeConfig,EndpointConfig,
        RunPolicy,ContextPolicy)
    from prosaic_harness import Conversation,ConversationBindings,ConversationPolicy,ConversationScope
    from prosaic_harness_postgres import PostgresSessionStore
    from prosaic_integration_lab.tool_journal import PgToolJournal
    from prosaic_integration_lab.context_counter import synthetic_registry
    namespace='context-effect-'+uuid.uuid4().hex
    key=uuid.uuid4().hex
    def effect(arguments,context):
        with psycopg.connect(lab['app_dsn']) as connection:
            connection.execute('INSERT INTO lab_fixture.effects(namespace,business_key,amount) VALUES(%s,%s,%s)',
                (namespace,context.operation_key,1))
        return {'padding':'x'*3500}
    tool=CustomTool('fixture_lookup','Approved synthetic journal regression',
        {'type':'object','properties':{'query':{'type':'string'}},'required':['query'],'additionalProperties':False},
        effect,'ctx-v1',with_context=True,operation_key=lambda args,context:key,max_result_bytes=4096)
    config=RuntimeConfig({'fixture':EndpointConfig(lab['model']+'/v1','test-model-balanced',
        features={'streaming':False})},{},'fixture',frozenset({'fixture_lookup'}))
    binding=ConversationBindings(ProsaicArtifact('context-effect','subagent',
        {'name':'context-effect','description':'Approved synthetic journal regression','tools':['fixture_lookup']},
        'ALWAYS use the approved fixture lookup. NEVER repeat an effect.'),
        version='ctx-effect-v1',config=config,policy=ConversationPolicy(),
        run_policy=RunPolicy(allowed_tools=frozenset({'fixture_lookup'}),max_provider_requests=2,max_tool_calls=1),
        custom_tools={'fixture_lookup':tool},operation_namespace=namespace,
        tool_journal=PgToolJournal(lab['app_dsn'],identity='context-effect-journal-v1'),
        context_policy=ContextPolicy('fullHistory',2000,128,0,'lab-synthetic-byte-balanced-v1'),
        token_counters=synthetic_registry('test-model-balanced'))
    p=principal(lab,'context-omit')
    with PostgresSessionStore(lab['conversation']['dsn'],namespace=lab['namespace']) as store:
        controller=Conversation(binding,store=store,scope=ConversationScope(lab['namespace'],'sandbox',
            'context-regression',p['tenant_id'],p['actor_id'],p['billing_account_id']))
        initial=controller.create()
        before=calls(lab)
        failed=controller.send(initial.session_id,message_id='effect',message='Find players',
            expected_revision=initial.revision).document
        assert failed['status']=='failed' and failed['failureCode']=='contextLimit'
        assert calls(lab)==before+1
        state=store.load_session(initial.session_id,scope=controller.scope).state
        aid=state['turns'][0]['attempts'][0]
        receipt=store.load_receipt(initial.session_id,aid,scope=controller.scope)
        assert receipt['evidence']['knownUsage']['totalTokens']==125
        assert receipt['evidence']['toolOutcomes'][0]['status']=='completed'
    with psycopg.connect(lab['app_dsn']) as connection:
        assert connection.execute('SELECT amount FROM lab_fixture.effects WHERE namespace=%s AND business_key=%s',
            (namespace,key)).fetchone()==(1,)
        assert connection.execute('SELECT state FROM lab_app.tool_operations WHERE operation_namespace=%s AND operation_key=%s',
            (namespace,key)).fetchone()==('completed',)
