"""Deterministic two-provider fixture; all execution stays inside public SDKs."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
import json


@contextmanager
def endpoint(provider):
    if provider not in {'openai-compatible','anthropic'}:raise ValueError('unsupported provider fixture')
    requests,replies=[],[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            request=json.loads(self.rfile.read(int(self.headers['Content-Length'])));requests.append(request)
            if not replies:self.send_error(500);return
            value=replies.pop(0);value=value(request) if callable(value) else value
            tool=type(value) is dict
            if provider=='anthropic':
                body={'id':'fixture','type':'message','role':'assistant','model':'fixture','content':[
                    {'type':'tool_use','id':'call','name':value['name'],'input':value['input']} if tool else {'type':'text','text':value}],
                    'stop_reason':'tool_use' if tool else 'end_turn','usage':{'input_tokens':2,'output_tokens':3}}
            else:
                body={'choices':[{'message':({'role':'assistant','content':None,'tool_calls':[{'id':'call','type':'function','function':{
                    'name':value['name'],'arguments':json.dumps(value['input'])}}]} if tool else {'role':'assistant','content':value}),
                    'finish_reason':'tool_calls' if tool else 'stop'}],'usage':{'total_tokens':5}}
            content=json.dumps(body).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{server.server_port}/v1',requests,replies
    finally:server.shutdown();server.server_close();thread.join(5);assert not thread.is_alive()


def validate_tool_manifest(data,*,candidate=True):
    """Verify explicit feature handoffs or the complete released tool-evidence train."""
    import re
    from prosaic_integration_lab.tool_evidence import TRAIN,RELEASE_TRAIN
    actual={item.get('distribution'):item.get('version') for item in data.get('artifacts',())}
    if actual not in (TRAIN,RELEASE_TRAIN) or len(data['artifacts'])!=5:
        raise ValueError('exact five-SDK tool evidence candidates required')
    stable=actual==RELEASE_TRAIN
    original={'b3-prosaic':'e858a853595746c6930fbe062e84bd8ece1a366aa3b126f2fe11bfb7cb2ceb81','b3-prosaic-runtime-postgres':'5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca'}
    if any(item['sha256']!=original[item['distribution']] for item in data['artifacts'] if item['distribution'] in original):raise ValueError('original retained SDK bytes differ')
    if not candidate:
        if not stable or 'candidate_lineage' in data:raise ValueError('released tool evidence train required')
        return data
    lineage=data.get('candidate_lineage',{})
    if lineage.get('version')!=1 or lineage.get('kind') not in {'local-tool-contract-handoff','hosted-tool-contract-handoff'}:
        raise ValueError('explicit tool contract handoff required')
    candidates=lineage.get('candidates',[])
    if len(candidates)!=2 or {item.get('sdk') for item in candidates}!={'runtime','harness'}:raise ValueError('paired candidate receipts required')
    for candidate in candidates:
        receipt,qualification=candidate['receipt'],candidate['qualification']
        expected_label=('native-ubuntu-24.04-3.12-wheel' if candidate['sdk']=='runtime' else 'linux-ubuntu-24.04-3.12-wheel') if stable else 'tool-contract-consumer'
        if (not re.fullmatch('[0-9a-f]{40}',receipt.get('source_commit','')) or qualification.get('exit_code')!=0 or
                qualification.get('source_commit')!=receipt['source_commit'] or qualification.get('label')!=expected_label or
                qualification.get('artifacts')!=receipt.get('artifacts')):raise ValueError('candidate qualification differs')
        names={'b3-prosaic-runtime'} if candidate['sdk']=='runtime' else {'b3-prosaic-harness','b3-prosaic-harness-postgres'}
        expected={name:actual[name] for name in names}
        if stable and candidate['sdk']=='runtime':expected['b3-prosaic-runtime-postgres']='0.3.0'
        if stable and 'scripts/tool_contract_smoke.py' not in json.dumps(qualification.get('command',[])):raise ValueError('installed tool consumer qualification missing')
        if {item['name']:item['version'] for item in receipt['distributions']}!=expected:raise ValueError('candidate SDK versions differ')
        for item in data['artifacts']:
            if item['distribution'] not in names:continue
            if item['source_commit']!=receipt['source_commit'] or {'filename':item['filename'],'sha256':item['sha256']} not in receipt['artifacts']:
                raise ValueError('candidate wheel does not match qualified source')
        if lineage['kind']=='hosted-tool-contract-handoff':
            from scripts.prepare_sdk_candidates import validate_run
            validate_run(candidate['run'],receipt['source_commit'],tool_contracts=not stable)
    retained=lineage.get('retained_artifacts',[])
    pins={'b3-prosaic':('0.5.0','e858a853595746c6930fbe062e84bd8ece1a366aa3b126f2fe11bfb7cb2ceb81'),
        'b3-prosaic-runtime-postgres':('0.3.0','5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca')}
    if len(retained)!=2:raise ValueError('original retained SDK bytes required')
    for name,(version,sha) in pins.items():
        item=next(item for item in data['artifacts'] if item['distribution']==name)
        if (item['version'],item['sha256'])!=(version,sha) or item not in retained:raise ValueError('retained SDK differs')
    return data


def require_tool_evidence_install(manifest,*,candidate=True):
    from pathlib import Path
    from prosaic_integration_lab.dependencies import sdk_manifest,cache_directory
    from prosaic_integration_lab.sdk_audit import audit
    root=Path(__file__).resolve().parents[1]
    validate_tool_manifest(sdk_manifest(manifest),candidate=candidate)
    audit(manifest,cache_directory(manifest,root/'.cache/wheels'))
