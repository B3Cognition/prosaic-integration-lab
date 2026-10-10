"""Credential-free synthetic model fixture; never routes to external providers."""
import threading
import json
import time
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
maximum_calls = None
allowance_start = 0
allowance_rejected = 0
provider_latency_s = 0
tool_samples = 0
receipt_gate = threading.Event()
receipt_gate.set()

class Control(BaseModel):
    model_config = ConfigDict(extra='forbid')
    scenario: str = 'normal'
    blocked: bool = False
    accepted_gate: bool = False
    result_text: str = Field(default='synthetic fixture output',max_length=256,strict=True)
    provider_latency_s: float = Field(default=0,ge=0,le=5,strict=True,allow_inf_nan=False)
    maximum_calls: int | None = Field(default=None,ge=1,le=10000,strict=True)
    preserve_allowance: bool = Field(default=False,strict=True)

class Operation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    latency_s: float = Field(default=0,ge=0,le=5,strict=True,allow_inf_nan=False)

@app.post('/operation')
def operation(body: Operation):
    global tool_samples
    began=time.monotonic()
    time.sleep(body.latency_s)
    with lock:tool_samples+=1
    return {'seconds':time.monotonic()-began}

@app.get('/stats')
def stats():
    with lock:
        return {'calls': calls, 'blocked': not gate.is_set(), 'accepted_events': accepted_events,
                'allowance_rejected':allowance_rejected,'tool_samples':tool_samples}

@app.post('/control')
def control(body: Control):
    global scenario,result_text,maximum_calls,allowance_start,allowance_rejected,provider_latency_s,tool_samples
    if body.scenario not in {'normal', 'missing_usage', 'invalid_output','large_usage'}:
        from fastapi import HTTPException
        raise HTTPException(422, 'invalid_scenario')
    with lock:
        scenario = body.scenario
        result_text = body.result_text
        if not body.preserve_allowance:
            maximum_calls=body.maximum_calls
            allowance_start=calls
            allowance_rejected=0
        provider_latency_s=body.provider_latency_s
        tool_samples=0
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
    global calls,allowance_rejected
    with lock:
        if maximum_calls is not None and calls-allowance_start>=maximum_calls:
            allowance_rejected+=1
            from fastapi import HTTPException
            raise HTTPException(429,'synthetic_allowance_exhausted')
        calls += 1
        call_id, selected, output = calls, scenario, result_text
        delay=provider_latency_s
    if not gate.wait(15):
        from fastapi import HTTPException
        raise HTTPException(504, 'fixture_gate_timeout')
    time.sleep(delay)
    result = {'id': f'fixture-{call_id}', 'object': 'chat.completion', 'created': 1,
              'model': 'test-model', 'choices': [{'index': 0, 'finish_reason': 'stop',
                'message': {'role': 'assistant', 'content': json.dumps({'result':output})
                            if selected != 'invalid_output' else 'invalid fixture output'}}]}
    if selected != 'missing_usage':
        prompt = 500 if selected == 'large_usage' else 100
        result['usage'] = {'prompt_tokens': prompt, 'completion_tokens': 25, 'total_tokens': prompt+25,
                           'prompt_tokens_details': {'cached_tokens': 20}}
    return result
