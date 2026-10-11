"""Credential-free synthetic model fixture; never routes to external providers."""
import threading
import json
import time
from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

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
barriers={name:threading.Event() for name in ('tool-claimed','tool-handler','tool-effect','tool-committed')}
for event in barriers.values():event.set()
barrier_counts={name:0 for name in barriers}
provenance_calls=0
finder_seen={}
FAULTS = ('reset', 'truncated_json', '429', '503', 'malformed_shape', 'slow')
fault = None
fault_phase = 'first'
fault_delay_s = 35.0
fault_acceptances = {name: 0 for name in FAULTS}
accepted_wait_s = 20

class Control(BaseModel):
    model_config = ConfigDict(extra='forbid')
    scenario: str = 'normal'
    blocked: bool = False
    accepted_gate: bool = False
    result_text: str = Field(default='synthetic fixture output',max_length=256,strict=True)
    provider_latency_s: float = Field(default=0,ge=0,le=5,strict=True,allow_inf_nan=False)
    maximum_calls: int | None = Field(default=None,ge=1,le=10000,strict=True)
    preserve_allowance: bool = Field(default=False,strict=True)
    effect_gate: str | None = None
    effect_amount: int = Field(default=1,ge=1,le=2,strict=True)
    fault: Literal['reset','truncated_json','429','503','malformed_shape','slow'] | None = None
    fault_phase: Literal['first','post_tool'] = 'first'
    fault_delay_s: float = Field(default=35.0,ge=0,le=40,strict=True,allow_inf_nan=False)
    accepted_wait_s: int = Field(default=20,ge=20,le=60,strict=True)

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
                'allowance_rejected':allowance_rejected,'tool_samples':tool_samples,
                'provenance_calls':provenance_calls,'barriers':dict(barrier_counts),
                'fault_acceptances':dict(fault_acceptances)}

@app.post('/control')
def control(body: Control):
    global scenario,result_text,maximum_calls,allowance_start,allowance_rejected,provider_latency_s,tool_samples
    global fault,fault_phase,fault_delay_s,accepted_wait_s
    if body.scenario not in {'normal', 'missing_usage', 'invalid_output','large_usage',
                             'native','native_rejected','native_effect','native_effect_batch','native_revisit'} or body.effect_gate not in {None,*barriers}:
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
        finder_seen.clear()
        app.state.effect_amount=body.effect_amount
        fault, fault_phase, fault_delay_s = body.fault, body.fault_phase, body.fault_delay_s
        accepted_wait_s = body.accepted_wait_s
    gate.clear() if body.blocked else gate.set()
    receipt_gate.clear() if body.accepted_gate else receipt_gate.set()
    for name,event in barriers.items():event.clear() if name==body.effect_gate else event.set()
    return {'status': 'configured'}

@app.post('/events/accepted')
def accepted():
    global accepted_events
    with lock:
        accepted_events += 1
        wait_s = accepted_wait_s
    if not receipt_gate.wait(wait_s):
        from fastapi import HTTPException
        raise HTTPException(504, 'receipt_gate_timeout')
    return {'status': 'observed'}

@app.post('/events/{name}')
def effect_event(name: str):
    from fastapi import HTTPException
    if name not in barriers:raise HTTPException(404,'unknown_fixture_event')
    with lock:barrier_counts[name]+=1
    if not barriers[name].wait(30):raise HTTPException(504,'effect_gate_timeout')
    return {'status':'observed'}


def native_arguments(messages):
    decoder=json.JSONDecoder()
    for message in messages:
        content=message.get('content')
        if not isinstance(content,str):continue
        # Runtime appends the actual public Harness arguments to specialist prose.
        content=content.split('## Arguments\n')[-1]
        try:value=decoder.raw_decode(content.strip())[0]
        except (ValueError,TypeError):continue
        if isinstance(value,dict) and 'request' in value:return value
    return {}


class LostResponse(Response):
    """Close an accepted HTTP response before its declared body arrives.

    Uvicorn closes an incomplete ASGI response. Sending no request data back
    keeps this deliberate transport fault independent of prompts and secrets.
    """
    async def __call__(self, scope, receive, send):
        await send({'type':'http.response.start','status':200,
                    'headers':[(b'content-type',b'application/json'),(b'content-length',b'128')]})
        # Deliberately omit the body; the server closes the connection here.

@app.post('/v1/chat/completions')
def completions(body: dict | None = None):
    global calls,allowance_rejected,provenance_calls
    with lock:
        if maximum_calls is not None and calls-allowance_start>=maximum_calls:
            allowance_rejected+=1
            from fastapi import HTTPException
            raise HTTPException(429,'synthetic_allowance_exhausted')
        calls += 1
        call_id, selected, output = calls, scenario, result_text
        delay=provider_latency_s
        post_tool=any(message.get('role')=='tool' for message in (body or {}).get('messages',[]))
        selected_fault=fault if (fault_phase=='post_tool')==post_tool else None
        fault_delay=fault_delay_s
        if selected_fault is not None:fault_acceptances[selected_fault]+=1
    if not gate.wait(15):
        from fastapi import HTTPException
        raise HTTPException(504, 'fixture_gate_timeout')
    time.sleep(delay)
    if selected_fault == 'reset':return LostResponse()
    if selected_fault == 'truncated_json':return Response('{"id":',media_type='application/json')
    if selected_fault in {'429','503'}:
        return Response('{"error":"synthetic_provider_fault"}',status_code=int(selected_fault),media_type='application/json')
    if selected_fault == 'malformed_shape':return {'choices':[]}
    if selected_fault == 'slow':time.sleep(fault_delay)
    # These two explicit synthetic specialist instructions belong to this fixture.
    # All values are fixture constants; no product lookup or model-selected URL.
    prose = json.dumps((body or {}).get('messages',[]))
    arguments=native_arguments((body or {}).get('messages',[]))
    if selected in {'native','native_rejected','native_effect','native_effect_batch','native_revisit'}:
        entity=arguments.get('request',{}).get('entity_id')
        if type(entity) is not str or not 0<len(entity)<=64:
            from fastapi import HTTPException
            raise HTTPException(422,'native_input_missing')
        if 'ALWAYS review the synthetic finder input.' in prose:
            import hashlib
            artifact=arguments.get('artifacts',{}).get('find')
            binding=arguments.get('artifact_bindings',{}).get('find')
            expected=hashlib.sha256(json.dumps(artifact,sort_keys=True,allow_nan=False).encode()).hexdigest()
            if (artifact!={'entity_id':entity} or not isinstance(binding,dict) or
                not isinstance(binding.get('id'),str) or not binding['id'] or
                binding.get('sha256')!=expected or binding.get('dependencies')!={}):
                from fastapi import HTTPException
                raise HTTPException(422,'native_provenance_missing')
            with lock:provenance_calls+=1
            native_output={'entity_id':entity,'approved':selected!='native_rejected'}
        else:
            with lock:
                finder_seen[entity]=finder_seen.get(entity,0)+1
                seen=finder_seen[entity]
            native_output={'entity_id':entity+'-revisit' if selected=='native_revisit' and seen>1 else entity}
    else:native_output = ({'entity_id':'synthetic-entity','approved':True}
        if 'ALWAYS review the synthetic finder input.' in prose else
        {'entity_id':'synthetic-entity'} if 'ALWAYS use the synthetic fixture entity only.' in prose else
        {'result':output})
    result = {'id': f'fixture-{call_id}', 'object': 'chat.completion', 'created': 1,
              'model': 'test-model', 'choices': [{'index': 0, 'finish_reason': 'stop',
                'message': {'role': 'assistant', 'content': json.dumps(native_output)
                            if selected != 'invalid_output' else 'invalid fixture output'}}]}
    if selected != 'missing_usage':
        prompt = 500 if selected == 'large_usage' else 100
        result['usage'] = {'prompt_tokens': prompt, 'completion_tokens': 25, 'total_tokens': prompt+25,
                           'prompt_tokens_details': {'cached_tokens': 20}}
    if selected in {'native_effect','native_effect_batch'} and not any(message.get('role')=='tool' for message in (body or {}).get('messages',[])):
        result['choices'][0]['finish_reason']='tool_calls'
        result['choices'][0]['message']={'role':'assistant','content':None,'tool_calls':[
            {'id':f'effect-{call_id}-{index}','type':'function','function':{'name':'fixture_apply',
             'arguments':json.dumps({'amount':getattr(app.state,'effect_amount',1)})}}
            for index in range(2 if selected=='native_effect_batch' else 1)]}
    return result
