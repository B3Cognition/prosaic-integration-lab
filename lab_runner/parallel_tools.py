"""Bounded HTTP fixtures and exact candidate handoff validation."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
import json

RETAINED_WHEELS = {'b3-prosaic':'e858a853595746c6930fbe062e84bd8ece1a366aa3b126f2fe11bfb7cb2ceb81','b3-prosaic-runtime-postgres':'5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca'}

@contextmanager
def endpoint(provider):
    if provider not in {'openai-compatible','anthropic'}:raise ValueError('unsupported provider')
    requests=[];replies=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            length=int(self.headers['Content-Length'])
            if not 0<length<=1048576:self.send_error(413);return
            payload=json.loads(self.rfile.read(length));requests.append(payload)
            if not replies:self.send_error(500);return
            value=replies.pop(0);value=value(payload) if callable(value) else value
            calls=value['calls'] if type(value) is dict else None
            if provider=='anthropic':
                body=dict(id='fixture',type='message',role='assistant',model='synthetic',content=[dict(type='tool_use',**call) for call in calls] if calls else [dict(type='text',text=value)],stop_reason='tool_use' if calls else 'end_turn',usage=dict(input_tokens=2,output_tokens=3))
            else:
                message=dict(role='assistant',content=None if calls else value)
                if calls:message['tool_calls']=[dict(id=c['id'],type='function',function=dict(name=c['name'],arguments=json.dumps(c['input']))) for c in calls]
                body=dict(choices=[dict(message=message,finish_reason='tool_calls' if calls else 'stop')],usage=dict(total_tokens=5))
            data=json.dumps(body).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);worker=Thread(target=server.serve_forever,daemon=True);worker.start()
    try:yield f'http://127.0.0.1:{server.server_port}/v1',requests,replies
    finally:server.shutdown();server.server_close();worker.join(5);assert not worker.is_alive()


def validate_parallel_manifest(data):
    from prosaic_integration_lab.parallel_tools import TRAIN
    return validate_local_handoff(data, train=TRAIN, kind='local-parallel-tool-handoff',
        label='parallel-tool-consumer', witness='test_parallel_tool_installed.py')


def validate_local_handoff(data, *, train, kind, label, witness):
    import re
    actual={item.get('distribution'):item.get('version') for item in data.get('artifacts',())}
    if actual!=train or len(data['artifacts'])!=5:raise ValueError('exact parallel candidate family required')
    lineage=data.get('candidate_lineage',{})
    if lineage.get('version')!=1 or lineage.get('kind')!=kind:raise ValueError('explicit parallel source handoff required')
    paired=lineage.get('candidates',[])
    if len(paired)!=2 or [c.get('sdk') for c in paired]!=['runtime','harness']:raise ValueError('paired parallel SDKs required')
    for candidate in paired:
        receipt=candidate['receipt'];qualification=candidate['qualification'];sdk=candidate['sdk']
        if (not re.fullmatch('[0-9a-f]{40}',receipt.get('source_commit','')) or qualification.get('source_commit')!=receipt['source_commit'] or qualification.get('exit_code')!=0 or qualification.get('label')!=label or qualification.get('artifacts')!=receipt.get('artifacts') or witness not in ' '.join(qualification.get('command',[]))):raise ValueError('parallel candidate qualification mismatch')
        counts=qualification.get('result_counts',{})
        if (set(counts)!={'tests','failures','errors','skipped'} or any(type(v) is not int or v<0 for v in counts.values()) or counts['tests']<1 or any(counts[k] for k in ('failures','errors','skipped'))):raise ValueError('parallel candidate checks must pass without skips')
        names={'b3-prosaic-runtime'} if sdk=='runtime' else {'b3-prosaic-harness','b3-prosaic-harness-postgres'}
        if {d['name']:d['version'] for d in receipt['distributions']}!={k:train[k] for k in names}:raise ValueError('parallel receipt versions differ')
        for item in data['artifacts']:
            if item['distribution'] in names and (item['source_commit']!=receipt['source_commit'] or {'filename':item['filename'],'sha256':item['sha256']} not in receipt['artifacts']):raise ValueError('parallel wheel/source mismatch')
    if paired[1].get('runtime_receipt')!=paired[0]['receipt'] or paired[1].get('runtime_qualification')!=paired[0]['qualification']:raise ValueError('Harness tested different Runtime bytes')
    retained=lineage.get('retained_artifacts',[])
    if len(retained)!=2:raise ValueError('original Core and recorder required')
    for item in data['artifacts']:
        if item['distribution'] in RETAINED_WHEELS and (item['sha256']!=RETAINED_WHEELS[item['distribution']] or item not in retained):raise ValueError('original retained bytes differ')
    return data


def require_parallel_install(manifest, *, candidate):
    from .gates import supports_parallel_tools
    from pathlib import Path
    from prosaic_integration_lab.dependencies import sdk_manifest,cache_directory
    from prosaic_integration_lab.sdk_audit import audit
    root=Path(__file__).resolve().parents[1]
    data = sdk_manifest(manifest)
    if not supports_parallel_tools(data) or candidate != ('candidate_lineage' in data):
        raise ValueError('parallel SDK family does not match dependency mode')
    audit(manifest,cache_directory(manifest,root/'.cache/wheels'))
