"""Explicit synthetic walkthrough; loopback only, no corpus or real inference."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import threading

from prosaic_runtime import EndpointConfig,RuntimeConfig
from lab_runner.memory_benchmark.completeness_profile import freeze_packet
from lab_runner.memory_benchmark.span_audit_fixture import materials as legacy_materials
from lab_runner.memory_benchmark.storage import read,require
from . import PROFILE,contracts
from .workflow import run_audit

CASES=('omitted','complete','unavailable','unknown-usage')


def materials(case):
    require(case in CASES,'unknown resolved fixture case')
    data=legacy_materials(case)[0].to_dict()
    packet=contracts.freeze_refs(freeze_packet(data['question'],data['draft'],data['frames'],identity=data['identity']))
    absent=case=='unavailable';complete=case=='complete';pid=contracts.PART_IDS[0];oid=contracts.OBLIGATION_IDS[0]
    proofs=contracts.catalog(packet,include_answer=True).to_dict()['proofs']
    source=[key for key,value in proofs.items() if value['kind']=='source']
    answers=[key for key,value in proofs.items() if value['kind']=='answer']
    limits=[key for key,value in proofs.items() if value['kind']=='limitation']
    ledger_wire=dict(version=1,questionParts=[dict(id=pid,questionRefs=['q0000'],
        answerability='unknown-in-context' if absent else 'answerable',reason='Synthetic body availability.')],
        obligations=[] if absent else [dict(id=oid,partIds=[pid],proposition='Memory is disabled by default.',sourceRefs=source)],unresolved=[])
    ledger=contracts.resolve_ledger(ledger_wire,packet)
    audit_wire=dict(version=1,
        obligations={} if absent else {oid:dict(verdict='covered' if complete else 'omitted',
            answerRefs=answers if complete else [],sourceRefs=source,reason='Synthetic required coverage.')},
        claims={claim['id']:dict(verdict='supported',answerRefs=answers,sourceRefs=source,
            citations={eid:dict(verdict='supported',sourceRefs=source,reason='Synthetic selected source.') for eid in claim['evidenceIds']},
            reason='Synthetic actual claim.') for claim in data['draft']['claims']},
        questionParts={pid:dict(verdict='appropriately-limited' if absent else 'fact-supported' if complete else 'insufficient',
            answerRefs=answers,limitationRefs=limits,sourceRefs=source,reason='Synthetic disposition.')},
        extraFindings=[],status=dict(recommendation='abstained' if absent else 'answered' if complete else 'partial',
            answerRefs=answers,limitationRefs=limits,reason='Synthetic consistent status.'),unresolved=[])
    contracts.resolve_audit(audit_wire,packet,ledger)
    return packet,ledger_wire,audit_wire


@contextmanager
def _provider(outputs,schemas,missing_usage):
    requests=[]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass

        def do_POST(self):
            length=int(self.headers.get('Content-Length','0'))
            if self.path!='/v1/chat/completions' or not 0<length<=262144 or len(requests)>=2:
                self.send_error(400);return
            request=json.loads(self.rfile.read(length));index=len(requests)
            if (request.get('model')!='synthetic-answer-span-refs' or request.get('max_tokens')!=4096
                or request.get('tools') or request.get('response_format',{}).get('json_schema',{}).get('schema')!=schemas[index]):
                self.send_error(400);return
            requests.append(request)
            reply=dict(id='synthetic-proof-refs',object='chat.completion',model='synthetic-answer-span-refs',
                choices=[dict(index=0,message=dict(role='assistant',content=json.dumps(outputs[index],ensure_ascii=False)),finish_reason='stop')])
            if not missing_usage:reply['usage']=dict(prompt_tokens=30,completion_tokens=20,total_tokens=50)
            raw=json.dumps(reply).encode();self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)

    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    config=RuntimeConfig(profiles={'fixture':EndpointConfig(base_url=f'http://127.0.0.1:{server.server_port}/v1',
        model='synthetic-answer-span-refs',max_tokens=4096,temperature=0,features={'streaming':False})},routes={},default_profile='fixture')
    try:yield config,requests
    finally:server.shutdown();server.server_close();thread.join(5)


def run_fixture(directory,*,case='omitted'):
    packet,source,audit=materials(case);ledger=contracts.resolve_ledger(source,packet)
    schemas=[contracts.ledger_schema(packet),contracts.audit_schema(packet,ledger)]
    with _provider([source,audit],schemas,case=='unknown-usage') as (config,requests):
        result=run_audit(config,packet,directory)
        again=run_audit(config,packet,directory)
        require(again['usage']['providerRequests']==0,'resolved fixture resume dispatched')
    path=Path(directory)/'transport';records=list(path.glob('*.json'))
    require(all(read(record)['result']['stdout'] for record in records),'raw native fixture capture missing')
    return dict(profileId=PROFILE,fixture=True,case=case,status=result['status'],outcome=result['outcome'],
        originalUnchanged=result['original']==contracts.canonical_packet(packet).to_dict()['draft'],
        syntheticProviderRequests=len(requests),resumeProviderRequests=again['usage']['providerRequests'],
        retainedTokens=result['retainedTokens'],rawNativeRecords=len(records),realModelCalls=0,
        semanticQuality='unmeasured',memoryDefault=False,sueDefault=False)
