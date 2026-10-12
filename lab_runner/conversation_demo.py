"""Bounded synthetic conversation walkthrough over authenticated public HTTP."""
import uuid

import httpx

from .conversation_scenarios import create,request,send


def capture_conversation(config):
    principal=next(p for p in config['principals'].values() if p['actor_id']=='alice')
    def require(condition):
        if not condition:raise ValueError('conversation demonstration evidence mismatch')
    def stats():
        response=httpx.get(config['model']+'/stats',timeout=5);response.raise_for_status()
        return response.json()
    before=stats()
    try:
        httpx.post(config['model']+'/control',json={'scenario':'conversation','maximum_calls':9},timeout=5).raise_for_status()
        session=create(config,principal,uuid.uuid4().hex)
        session=send(config,principal,session,'preference','Remember Brno')
        session=send(config,principal,session,'correction','I meant Prague',replica='b')
        session=send(config,principal,session,'query','Which city did I choose?')
        require(session.get('answer')=='Your city is Prague.')
        session=send(config,principal,session,'find','Find players',replica='b')
        selected=session['pendingInteraction']
        require(selected['stepId']=='select' and selected['choices']==['player-a','player-b'])
        session=send(config,principal,session,'selection','the second result',interaction_ref=selected['reference'])
        require(session['pendingInteraction']['stepId']=='confirm-b')
        require(stats()['barriers']['tool-handler']==before['barriers']['tool-handler'])
        session=send(config,principal,session,'approve','approve',replica='b',
            interaction_ref=session['pendingInteraction']['reference'])
        require(session.get('answer')=='Workflow completed.' and session['pendingInteraction'] is None)
        usage=request(config,principal,'GET','/conversations/'+session['sessionId']+'/usage',replica='b')
        usage.raise_for_status();report=usage.json()
        require(report['conversation']['total_calls']==7 and report['workflow']['total_calls']==2)
        require(report['conversation']['complete_calls']==7 and report['workflow']['complete_calls']==2)
        after=stats()
        require(after['calls']-before['calls']==9)
        require(after['barriers']['tool-handler']-before['barriers']['tool-handler']==1)
        require(after['barriers']['tool-committed']-before['barriers']['tool-committed']==1)
    finally:
        httpx.post(config['model']+'/control',json={},timeout=5).raise_for_status()
    return {'version':1,'fixture':'conversation','status':'completed','liveProvider':False,
        'steps':['preference','correction','lookup','selection','confirmation','approved-operation'],
        'selectedEntity':'player-b','independent_model_calls':9,'domain_handler_calls':1,
        'conversation_usage':{'total_calls':7,'complete_calls':7,'unresolved_calls':0},
        'workflow_usage':{'total_calls':2,'complete_calls':2,'unresolved_calls':0},
        'checks':{'full_history':True,'offered_order':True,'confirmation_before_effect':True,
            'separate_usage':True,'two_workers':True}}
