"""Credential-free synthetic model fixture; never routes to external providers."""
import threading
import json
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI()
lock = threading.Lock()
gate = threading.Event()
gate.set()
calls = 0
scenario = 'normal'
result_text = 'synthetic fixture output'
accepted_events = 0
receipt_gate = threading.Event()
receipt_gate.set()

class Control(BaseModel):
    model_config = ConfigDict(extra='forbid')
    scenario: str = 'normal'
    blocked: bool = False
    accepted_gate: bool = False
    result_text: str = Field(default='synthetic fixture output',max_length=256,strict=True)

@app.get('/stats')
def stats():
    with lock:
        return {'calls': calls, 'blocked': not gate.is_set(), 'accepted_events': accepted_events}

@app.post('/control')
def control(body: Control):
    global scenario,result_text
    if body.scenario not in {'normal', 'missing_usage', 'invalid_output'}:
        from fastapi import HTTPException
        raise HTTPException(422, 'invalid_scenario')
    with lock:
        scenario = body.scenario
        result_text = body.result_text
    gate.clear() if body.blocked else gate.set()
    receipt_gate.clear() if body.accepted_gate else receipt_gate.set()
    return {'status': 'configured'}

@app.post('/events/accepted')
def accepted():
    global accepted_events
    with lock:
        accepted_events += 1
    if not receipt_gate.wait(20):
        from fastapi import HTTPException
        raise HTTPException(504, 'receipt_gate_timeout')
    return {'status': 'observed'}

@app.post('/v1/chat/completions')
def completions():
    global calls
    with lock:
        calls += 1
        call_id, selected, output = calls, scenario, result_text
    if not gate.wait(15):
        from fastapi import HTTPException
        raise HTTPException(504, 'fixture_gate_timeout')
    result = {'id': f'fixture-{call_id}', 'object': 'chat.completion', 'created': 1,
              'model': 'test-model', 'choices': [{'index': 0, 'finish_reason': 'stop',
                'message': {'role': 'assistant', 'content': json.dumps({'result':output})
                            if selected != 'invalid_output' else 'invalid fixture output'}}]}
    if selected != 'missing_usage':
        result['usage'] = {'prompt_tokens': 100, 'completion_tokens': 25, 'total_tokens': 125,
                           'prompt_tokens_details': {'cached_tokens': 20}}
    return result
