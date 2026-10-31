"""Bounded, optional run observations. These are not durable accounting evidence."""
from collections import OrderedDict, deque
import math
import re
import threading
import time

EVENTS = {
    'runtime': {'invocation_started', 'invocation_completed', 'provider_request_started',
                'provider_request_completed', 'tool_started', 'tool_completed'},
    'harness': {'run_started', 'transition_committed', 'waiting_committed',
                'recovery_committed', 'blocked_committed', 'run_completed'},
}
OUTCOMES = {'completed', 'cancelled', 'timed_out', 'admission_failure', 'critical_hook_error',
            'budget_failure', 'execution_failure', 'running', 'waiting', 'blocked', 'rejected'}


def _count(value):
    return type(value) is int and 0 <= value <= 2**63 - 1


def _safe(record):
    if (type(record) is not dict or record.get('source') not in EVENTS or
            record.get('event') not in EVENTS[record['source']]):
        return None
    result = {'source': record['source'], 'event': record['event']}
    for name in ('sequence', 'turn', 'calls', 'token_usage', 'provider_request_count', 'tool_call_count'):
        if _count(record.get(name)):
            result[name] = record[name]
    invocation = record.get('invocation_id')
    if type(invocation) is str and re.fullmatch(r'[A-Za-z0-9._:-]{1,128}', invocation):
        result['invocation_id'] = invocation
    if record.get('outcome') in OUTCOMES:
        result['outcome'] = record['outcome']
    if record.get('status') in {'ok', 'error', 'unknown'}:
        result['status'] = record['status']
    duration = record.get('duration_ms')
    if type(duration) in (int, float) and math.isfinite(duration) and 0 <= duration <= 2**63 - 1:
        result['duration_ms'] = duration
    if type(record.get('http_status')) is int and 100 <= record['http_status'] <= 599:
        result['http_status'] = record['http_status']
    if 'name' in record:
        name = record['name']
        result['name'] = name if type(name) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]{0,63}', name) else 'unknown'
    return result


class RunObservations:
    def __init__(self, *, max_runs=32, max_events=256, clock=time.monotonic):
        if (type(max_runs) is not int or not 1 <= max_runs <= 128 or
                type(max_events) is not int or not 1 <= max_events <= 1024):
            raise ValueError('invalid observation capacity')
        self.max_runs, self.max_events, self.clock = max_runs, max_events, clock
        self.runs = OrderedDict()
        self.lock = threading.Lock()

    def observe(self, run_id, record):
        safe = _safe(record)
        if safe is None:
            return
        with self.lock:
            now = self.clock()
            if run_id not in self.runs:
                if len(self.runs) == self.max_runs:
                    self.runs.popitem(last=False)
                self.runs[run_id] = {'start': now, 'events': deque(maxlen=self.max_events),
                    'open': set(), 'count': 0, 'truncated': False}
            run = self.runs[run_id]
            self.runs.move_to_end(run_id)
            run['count'] += 1
            if len(run['events']) == self.max_events:
                run['truncated'] = True
            safe.update(id=run['count'], at=round(max(0, now - run['start']), 6))
            invocation = safe.get('invocation_id', 'unknown')
            if safe['event'] == 'invocation_started':
                run['open'].add(invocation)
            elif safe['event'] == 'invocation_completed':
                run['open'].discard(invocation)
            run['events'].append(safe)

    def snapshot(self, run_id):
        with self.lock:
            run = self.runs.get(run_id)
            if run is None:
                return {'version': 1, 'runId': run_id, 'events': [], 'elapsed': 0,
                        'active': False, 'available': False, 'truncated': False}
            events = [dict(event) for event in run['events']]
            elapsed = max(events[-1]['at'], self.clock() - run['start']) if run['open'] else events[-1]['at']
            return {'version': 1, 'runId': run_id, 'events': events,
                    'elapsed': round(max(0, elapsed), 6), 'active': bool(run['open']),
                    'available': True, 'truncated': run['truncated']}


def usage_projection(rows):
    """Expose counts only from public recorder observations, never raw call data."""
    if rows is None:
        return {'input': None, 'output': None, 'completeCalls': 0,
                'totalCalls': None, 'unknownCalls': None, 'available': False}
    inp = out = known = unqualified_in = unqualified_out = unqualified = 0
    for row in rows:
        observation = row.get('observation') or {}
        usage = observation.get('usage') or {}
        if (row.get('measurement_state') == 'complete' and usage.get('status') == 'reported' and
                _count(usage.get('input_tokens')) and _count(usage.get('output_tokens'))):
            inp += usage['input_tokens']
            out += usage['output_tokens']
            known += 1
        elif (row.get('measurement_state') == 'unsupported' and
                observation.get('outcome') == 'completed' and usage.get('status') == 'unsupported' and
                _count(usage.get('input_tokens')) and _count(usage.get('output_tokens')) and
                _count(usage.get('total_tokens')) and
                usage['input_tokens'] + usage['output_tokens'] == usage['total_tokens']):
            unqualified_in += usage['input_tokens']
            unqualified_out += usage['output_tokens']
            unqualified += 1
    result = {'input': inp if known or not rows else None, 'output': out if known or not rows else None,
            'completeCalls': known, 'totalCalls': len(rows), 'unknownCalls': len(rows) - known,
            'available': True}
    if unqualified:
        # Diagnostic counts remain distinct from the recorder's qualified totals.
        result['providerReported'] = {'input': inp + unqualified_in, 'output': out + unqualified_out,
            'unqualifiedCalls': unqualified, 'unknownCalls': len(rows) - known - unqualified}
    return result


def install_observation_routes(app, observations):
    from fastapi import HTTPException, Request
    from fastapi.responses import JSONResponse

    @app.get('/conversations/{session_id}/observations')
    def conversation_observations(session_id: str, request: Request):
        execution = request.app.state.execution
        if execution.conversation is None:
            raise HTTPException(404, 'not_found')
        result = execution.read(execution.conversation.observation_request,
            request.state.principal, session_id, observations)
        return JSONResponse(result, headers={'Cache-Control': 'no-store'})
