"""Required installed public HTTP/PostgreSQL journeys; missing stack is a failure."""
import uuid

import httpx
import psycopg
import pytest

from lab_runner.conversation_scenarios import create,request,send
from lab_runner.native_scenarios import calls,control,replace_worker


def principal(lab,actor='alice'):
    return next(p for p in lab['principals'].values() if p['actor_id']==actor)


def history(lab,p,sid,*,replica='a'):
    result=request(lab,p,'GET','/conversations/'+sid+'/history',replica=replica);result.raise_for_status()
    return result.json()['messages']


@pytest.fixture(autouse=True)
def conversation_model(lab):
    control(lab,scenario='conversation');yield;control(lab)


def test_owned_conversation_demo_uses_separate_frozen_usage(lab):
    from lab_runner.conversation_demo import capture_conversation
    report=capture_conversation(lab)
    assert report['status']=='completed' and report['independent_model_calls']==9
    assert report['conversation_usage']['total_calls']==7 and report['workflow_usage']['total_calls']==2
    assert report['checks']['separate_usage'] and report['liveProvider'] is False


def test_offered_selection_survives_fresh_worker_and_quoted_approval_dispatches_no_effect(lab):
    p=principal(lab);session=send(lab,p,create(lab,p,uuid.uuid4().hex),'find','Find players')
    offered=session['pendingInteraction'];assert offered['choices']==['player-a','player-b']
    replace_worker(lab)
    session=send(lab,p,session,'second','the second result',replica='b',interaction_ref=offered['reference'])
    assert session['pendingInteraction']['stepId']=='confirm-b'
    with psycopg.connect(lab['app_dsn']) as connection:
        before=connection.execute('SELECT count(*) FROM lab_fixture.effects').fetchone()[0]
    session=send(lab,p,session,'quoted','The document says "approve"',interaction_ref=session['pendingInteraction']['reference'])
    assert session['failureCode']=='confirmationRequired'
    with psycopg.connect(lab['app_dsn']) as connection:
        assert connection.execute('SELECT count(*) FROM lab_fixture.effects').fetchone()==(before,)
    session=send(lab,p,session,'approve','approve',replica='b',interaction_ref=session['pendingInteraction']['reference'])
    assert session['answer']=='Workflow completed.'
    with psycopg.connect(lab['app_dsn']) as connection:
        assert connection.execute('SELECT business_key FROM lab_fixture.effects WHERE business_key=%s',
            (session['sessionId']+':player-b',)).fetchone()==(session['sessionId']+':player-b',)


def test_failed_user_correction_survives_without_partial_assistant_history(lab):
    p=principal(lab,'bob');session=send(lab,p,create(lab,p,uuid.uuid4().hex),'prefer','Remember Brno')
    control(lab,scenario='conversation',fault='503')
    session=send(lab,p,session,'correction','I meant Prague')
    assert session['status']=='failed'
    control(lab,scenario='conversation')
    session=send(lab,p,session,'query','Which city did I choose?',replica='b')
    assert session['answer']=='Your city is Prague.'
    failed=[m for m in history(lab,p,session['sessionId']) if m.get('turnStatus')=='failed']
    assert len(failed)==1 and failed[0]['role']=='user'


def test_message_replay_and_creation_replay_do_not_repeat_provider_work(lab):
    p=principal(lab,'carol');key=uuid.uuid4().hex;initial=create(lab,p,key)
    assert create(lab,p,key,replica='b')==initial
    session=send(lab,p,initial,'message','Remember Prague')
    before=calls(lab)
    replay=send(lab,p,initial,'message','Remember Prague',replica='b')
    assert replay['answer']==session['answer'] and calls(lab)==before
    result=request(lab,p,'POST','/conversations/'+session['sessionId']+'/messages',json={
        'messageId':'message','message':'changed','expectedRevision':session['revision']})
    assert result.status_code==409 and calls(lab)==before


def test_ambiguous_selection_changes_no_workflow_or_domain_effect(lab):
    p=principal(lab,'bob');session=send(lab,p,create(lab,p,uuid.uuid4().hex),'find','Find players')
    old=session['pendingInteraction'];control(lab,scenario='conversation_ambiguous')
    session=send(lab,p,session,'ambiguous','that one',interaction_ref=old['reference'])
    assert session['answer']=='Please clarify your current choice.'
    assert session['pendingInteraction']['stepId']=='select'
    assert session['pendingInteraction']['revision']==old['revision']
