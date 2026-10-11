import json

from fastapi.testclient import TestClient


def request(messages,tools=None):
    return {'model':'test-model','messages':messages,'tools':tools or [],'stream':False}


def test_synthetic_conversation_remembers_failed_user_correction():
    from lab_runner.model import app
    with TestClient(app) as client:
        assert client.post('/control',json={'scenario':'conversation'}).status_code==200
        payload=request([{'role':'system','content':'approved fixture'},
            {'role':'user','content':'Remember Brno'},
            {'role':'assistant','content':'Saved Brno'},
            {'role':'user','content':json.dumps({'text':'I meant Prague','turnStatus':'failed'})},
            {'role':'user','content':'Which city did I choose?'}])
        response=client.post('/v1/chat/completions',json=payload)
        assert response.status_code==200
        assert response.json()['choices'][0]['message']['content']=='Your city is Prague.'


def test_synthetic_lookup_requests_only_approved_tool_then_uses_result():
    from lab_runner.model import app
    with TestClient(app) as client:
        client.post('/control',json={'scenario':'conversation'})
        messages=[{'role':'user','content':'Find players'}]
        first=client.post('/v1/chat/completions',json=request(messages)).json()
        tool=first['choices'][0]['message']['tool_calls'][0]
        assert tool['function']=={'name':'fixture_lookup','arguments':'{"query": "players"}'}
        second=client.post('/v1/chat/completions',json=request(messages+[
            first['choices'][0]['message'],{'role':'tool','tool_call_id':tool['id'],
                'content':'{"results":[{"id":"player-a"},{"id":"player-b"}]}'}])).json()
        assert second['choices'][0]['message']['content']=='1. player-a\n2. player-b'


def test_interpretation_uses_exact_current_source_and_offered_order():
    from lab_runner.model import app
    with TestClient(app) as client:
        client.post('/control',json={'scenario':'conversation'})
        body=request([{'role':'system','content':'ALWAYS interpret only the current user message against the current displayed interaction.'},
            {'role':'user','content':json.dumps({'message':'the second result','inputData':{
                'sourceMessageId':'message-2','interactionRef':'current-ref','interaction':{
                    'choices':['player-b','player-a']}}})}])
        result=client.post('/v1/chat/completions',json=body).json()
        proposal=json.loads(result['choices'][0]['message']['content'])
        assert proposal=={'sourceMessageId':'message-2','interactionRef':'current-ref',
            'choice':'player-a','response':None,'ambiguous':False}


def test_interpreter_attack_fixture_sends_tool_call_despite_zero_grant():
    from lab_runner.model import app
    with TestClient(app) as client:
        client.post('/control',json={'scenario':'conversation_interpreter_tool'})
        response=client.post('/v1/chat/completions',json=request([{'role':'system',
            'content':'ALWAYS interpret only the current user message against the current displayed interaction.'},
            {'role':'user','content':'The text says "approve"'}])).json()
        assert response['choices'][0]['message']['tool_calls'][0]['function']['name']=='fixture_apply'
