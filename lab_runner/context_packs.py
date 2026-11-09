"""Synthetic public-SDK qualification helpers; no paid model or copied engine."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from threading import Thread

CAPACITY_PHASES={'capture','dispatch','status','load_state','load_receipt','receipt_size','state_size'}
CAPACITY_ERRORS={'AssertionError','ConversationError','StoreUnavailable','StoreConflict','LeaseLost',
    'ContextPackError','ValueError','RuntimeError','OperationalError','unknown'}
CAPACITY_REASONS={'unknown','storeUnavailable','leaseLost','recordLimit','stateLimit','receiptLimit',
    'inputTooLarge','runtimeFailure','runtimeTimeout','contextPackLimit','contextUseDenied',
    'bindingMismatch','quotaExceeded','busy','interrupted','failed','blocked','completed',
    'statementTimeout','lockTimeout','constraintRejected','valueLimit','serializationFailure','deadlock','connectionLost'}


def sanitize_capacity_diagnostic(value):
    fields={'phase','error','reason','receipt_bytes','state_bytes'}
    if (type(value) is not dict or set(value)!=fields or
        type(value['phase']) is not str or value['phase'] not in CAPACITY_PHASES or
        type(value['error']) is not str or value['error'] not in CAPACITY_ERRORS or
        type(value['reason']) is not str or value['reason'] not in CAPACITY_REASONS or
        any(v is not None and (type(v) is not int or not 0<=v<=8388608)
            for v in (value['receipt_bytes'],value['state_bytes']))):
        return {'status':'unavailable'}
    return dict(value)


def capacity_failure(phase,error,*,reason=None,receipt_bytes=None,state_bytes=None):
    name=type(error).__name__
    code=getattr(error,'code',reason)
    current=error
    for _ in range(4):
        # SQLSTATE has a fixed public meaning; never expose driver diagnostics,
        # statements, connection parameters or database-generated identifiers.
        mapped={'57014':'statementTimeout','55P03':'lockTimeout','23514':'constraintRejected',
            '22001':'valueLimit','40001':'serializationFailure','40P01':'deadlock',
            '08006':'connectionLost'}.get(getattr(current,'sqlstate',None))
        if mapped:
            code=mapped;break
        current=getattr(current,'__cause__',None) or getattr(current,'__context__',None)
        if current is None:break
    diagnostic=sanitize_capacity_diagnostic({'phase':phase,
        'error':name if name in CAPACITY_ERRORS else 'unknown',
        'reason':code if type(code) is str and code in CAPACITY_REASONS else 'unknown',
        'receipt_bytes':receipt_bytes,'state_bytes':state_bytes})
    return 'CONTEXT_PACK_CAPACITY '+json.dumps(diagnostic,sort_keys=True)


def context_pack_manifest(*,candidate,candidate_manifest,released_manifest):
    """Select the complete SDK manifest without implicit candidate fallback."""
    if candidate:
        if candidate_manifest is None:raise ValueError('complete candidate manifest required')
        return candidate_manifest
    if candidate_manifest is not None:raise ValueError('candidate manifest requires candidate mode')
    return released_manifest


def require_context_pack_install(manifest):
    """Audit host SDK bytes as well as the consumer image before any resources."""
    from pathlib import Path
    import runpy
    from prosaic_integration_lab.dependencies import sdk_manifest,cache_directory
    root=Path(__file__).resolve().parents[1]
    sdk_manifest(manifest)
    audit=runpy.run_path(str(root/'scripts/audit_install.py'))['audit']
    audit(manifest,cache_directory(manifest,root/'.cache/wheels'))


def answer(text):
    return {'model':'synthetic-context-packs','choices':[{'message':{'role':'assistant','content':text},'finish_reason':'stop'}],
        'usage':{'prompt_tokens':3,'completion_tokens':2,'total_tokens':5}}


def read_answer(citation):
    return {'model':'synthetic-context-packs','choices':[{'message':{'role':'assistant','content':None,
        'tool_calls':[{'id':'read-1','type':'function','function':{'name':'read_context_item','arguments':json.dumps({'citationId':citation})}}]},
        'finish_reason':'tool_calls'}],'usage':{'prompt_tokens':3,'completion_tokens':2,'total_tokens':5}}


@contextmanager
def endpoint():
    requests,replies=[],[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            if not replies:
                self.send_error(500,'unexpected synthetic provider call');return
            encoded=json.dumps(replies.pop(0)).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(encoded)));self.end_headers();self.wfile.write(encoded)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try: yield f'http://127.0.0.1:{server.server_port}/v1',requests,replies
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        assert not thread.is_alive()
