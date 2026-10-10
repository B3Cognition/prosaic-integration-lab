"""Bounded process observations; no request contents or dynamic metric labels."""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import hmac
import json
import logging
import math
import os
import re
import threading
import time
import uuid
from starlette.responses import JSONResponse,PlainTextResponse

_context = ContextVar('lab_request_observation',default=None)
logger = logging.getLogger('prosaic_integration_lab.observability')
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
logger.propagate = False

def route(path):
    if path in {'/healthz','/readyz'}: return path[1:]
    if path == '/runs': return 'runs_start'
    if path == '/workflow-catalogue': return 'workflow_catalogue'
    if path == '/workflow-proposals': return 'workflow_proposals'
    if path == '/native-runs': return 'native_runs_start'
    match = re.fullmatch('/runs/[0-9a-f]{32}(?:/(resume|usage))?',path)
    return ('run_'+(match.group(1) or 'status')) if match else 'unknown'

class Metrics:
    buckets = (.01,.05,.1,.5,1,2,5,10,30,float('inf'))
    def __init__(self,key=None):
        if key is not None and (not isinstance(key,str) or not re.fullmatch('[0-9a-f]{64}',key)):
            raise ValueError('invalid operator metrics credential')
        self.key = (key.encode() if key else os.urandom(32))
        self.lock = threading.Lock()
        self.requests = {}
        self.latencies = {}
        self.active = {'writes':0,'reads':0}
        self.rejected = {'writes':0,'reads':0}
        self.ready = self.ready_failures = self.unknown_observations = 0
        self.phases = {'reserved':0,'starting':0,'started':0}
        self.snapshot_ok = 0

    def reference(self,value):
        return hmac.new(self.key,str(value).encode(),hashlib.sha256).hexdigest()[:16]

    def request(self,path,status,duration):
        name = route(path)
        category = str(status//100)+'xx' if type(status) is int and 100 <= status < 600 else 'other'
        duration = max(0,duration) if math.isfinite(duration) else 0
        with self.lock:
            pair=(name,category)
            self.requests[pair]=self.requests.get(pair,0)+1
            histogram=self.latencies.setdefault(name,[0]*len(self.buckets)+[0.0,0])
            for i,bound in enumerate(self.buckets): histogram[i]+=int(duration<=bound)
            histogram[-2]+=duration; histogram[-1]+=1
            if name == 'readyz':
                self.ready=int(status==200)
                self.ready_failures+=int(status!=200)

    def admission(self,pool,delta=0,rejected=False):
        if pool not in self.active: raise ValueError('unknown admission pool')
        with self.lock:
            self.active[pool]+=delta
            self.rejected[pool]+=int(rejected)

    def unknown(self,count):
        if type(count) is int and 0 <= count <= 10000:
            with self.lock: self.unknown_observations+=count

    def reservation_snapshot(self,counts):
        if any(type(counts.get(name,0)) is not int or not 0 <= counts.get(name,0) <= 1000000000 for name in self.phases):
            raise ValueError('invalid reservation aggregate')
        with self.lock:
            self.phases={name:counts.get(name,0) for name in self.phases}
            self.snapshot_ok=1

    def render(self):
        with self.lock:
            lines=[f'lab_readiness {self.ready}',f'lab_readiness_failures_total {self.ready_failures}',
                f'lab_accounting_unknown_observations_total {self.unknown_observations}',
                f'lab_reservation_snapshot_success {self.snapshot_ok}']
            for pool in self.active:
                lines.extend((f'lab_admission_active{{pool="{pool}"}} {self.active[pool]}',
                    f'lab_admission_rejections_total{{pool="{pool}"}} {self.rejected[pool]}'))
            for phase,count in self.phases.items(): lines.append(f'lab_reservation_phase{{phase="{phase}"}} {count}')
            for (name,status),count in sorted(self.requests.items()):
                lines.append(f'lab_http_requests_total{{route="{name}",status="{status}"}} {count}')
            for name,values in sorted(self.latencies.items()):
                for bound,count in zip(self.buckets,values):
                    label='+Inf' if math.isinf(bound) else str(bound)
                    lines.append(f'lab_http_duration_seconds_bucket{{route="{name}",le="{label}"}} {count}')
                lines.extend((f'lab_http_duration_seconds_sum{{route="{name}"}} {values[-2]}',
                    f'lab_http_duration_seconds_count{{route="{name}"}} {values[-1]}'))
        return '\n'.join(lines)+'\n'

@contextmanager
def request_context(metrics):
    item={'request_id':uuid.uuid4().hex,'metrics':metrics}
    token=_context.set(item)
    try: yield item
    finally: _context.reset(token)

def correlation():
    item=_context.get() or {}
    return {key:item[key] for key in ('request_id','run_id','tenant_ref') if key in item}

def bind_run(reservation):
    item=_context.get()
    if item is not None and isinstance(reservation.get('run_id'),str) and re.fullmatch('[0-9a-f]{32}',reservation['run_id']):
        item['run_id']=reservation['run_id']
        item['tenant_ref']=item['metrics'].reference(reservation['tenant_id'])

def accounting_observation(report,calls):
    item=_context.get()
    if item is None: return
    unknown=report.get('unresolved_calls',0)
    if type(unknown) is not int or not 0 <= unknown <= 10000:
        raise ValueError('invalid accounting aggregate')
    item['metrics'].unknown(unknown)
    references=[item['metrics'].reference(call['intent']['provider_call_id']) for call in calls[:3]]
    logger.info(json.dumps({'event':'accounting_observed',**correlation(),
        'unknown_calls':unknown,'call_refs':references}))

def workflow_observation(record):
    # ObserverEmitter owns exception isolation. Keep only its closed kind/source
    # and bounded committed revision, never source exception text or payloads.
    item = _context.get()
    if item is None: return
    if type(record) is not dict or record.get('source') != 'harness': return
    kind = record.get('event')
    if kind not in {'run_started','transition_committed','waiting_committed','blocked_committed',
                    'run_completed','recovery_committed'}: return
    logger.info(json.dumps({'event':'workflow_observed',**correlation(),'kind':kind}))

class Observability:
    def __init__(self,app,*,metrics,operator_token=None):
        self.app,self.metrics,self.operator_token=app,metrics,operator_token

    async def __call__(self,scope,receive,send):
        if scope['type'] != 'http': return await self.app(scope,receive,send)
        if scope['path'] == '/metrics':
            values=[v for k,v in scope.get('headers',[]) if k.lower()==b'authorization']
            authorized=(self.operator_token is not None and len(values)==1 and
                hmac.compare_digest(values[0],('Bearer '+self.operator_token).encode()))
            if not authorized:
                return await JSONResponse({'detail':'not_found' if self.operator_token is None else 'unauthenticated'},
                    status_code=404 if self.operator_token is None else 401)(scope,receive,send)
            if scope['method'] != 'GET':
                return await JSONResponse({'detail':'method_not_allowed'},status_code=405)(scope,receive,send)
            try:
                execution=scope['app'].state.execution
                def snapshot():
                    execution.ready()
                    return execution.metadata.phase_counts(execution.config['namespace'],execution.config['environment'])
                counts=await execution.inspected(snapshot)
                self.metrics.reservation_snapshot(counts)
                with self.metrics.lock: self.metrics.ready=1
                response=PlainTextResponse(self.metrics.render(),media_type='text/plain; version=0.0.4')
            except Exception:
                with self.metrics.lock:
                    self.metrics.snapshot_ok=0
                    self.metrics.ready=0
                    self.metrics.ready_failures+=1
                response=JSONResponse({'detail':'metrics_unavailable'},status_code=503)
            return await response(scope,receive,send)
        began=time.monotonic(); status=503
        with request_context(self.metrics) as item:
            async def observed(message):
                nonlocal status
                if message['type']=='http.response.start':
                    status=message['status']
                    message={**message,'headers':[*message.get('headers',[]),(b'x-request-id',item['request_id'].encode())]}
                await send(message)
            try: return await self.app(scope,receive,observed)
            finally:
                duration=time.monotonic()-began
                self.metrics.request(scope['path'],status,duration)
                logger.info(json.dumps({'event':'request_finished',**correlation(),
                    'route':route(scope['path']),'status':status,'duration_ms':round(duration*1000,2)}))
