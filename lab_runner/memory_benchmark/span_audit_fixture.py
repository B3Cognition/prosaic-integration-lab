"""Explicit loopback-only audit demonstration. No corpus or real model calls."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading

from prosaic_runtime import EndpointConfig, RuntimeConfig

from . import answer_contract, completeness_profile as baseline
from . import span_audit_contracts as contract
from .span_audit_workflow import run_audit

CASES = ('omitted', 'complete', 'unavailable', 'unknown-usage')


def materials(case):
    contract.require(case in CASES, 'unknown synthetic audit case')
    question = 'What is the memory default?'
    body = 'Memory is disabled by default.'
    display = 'Synthetic body:\n'+body
    source = dict(namespace='synthetic-answer-audit-owner', sourceId='synthetic-memory',
                  sourceFileSha256=contract.sha(body), revision='fixture-r1', wing='notes', path='example.md')
    frames = {'body': dict(kind='open', display=display,
        bodySpans=[dict(start=len(display)-len(body), end=len(display))],
        metadata=dict(sourceIdentity=source, path='example.md', sourceFileSha256=source['sourceFileSha256'], startChar=0, endChar=len(body)))}
    absent = case == 'unavailable'
    text = body if case == 'complete' else 'Memory exists.'
    draft = dict(questionParts=[dict(id='part', start=0, end=len(question), quote=question,
                    claimIds=[] if absent else ['claim'], missingEvidenceIndices=[0] if absent else [])],
        claims=[] if absent else [dict(id='claim', text=text, kind='observation', evidenceIds=['evidence'])],
        evidence=[] if absent else [dict(id='evidence', frameId='body', displaySha256=contract.sha(display),
            start=len(display)-len(body), end=len(display), quote=body)],
        sections={name: dict(claimIds=['claim'] if name=='directAnswer' and not absent else [],
            reason='No additional claim.') for name in answer_contract.SECTIONS},
        frameReview=[] if absent else [dict(frameId='body', disposition='used', claimIds=['claim'], reason='Supplied synthetic support.')],
        citations=[] if absent else [dict(path='example.md',sourceFileSha256=source['sourceFileSha256'],chars=[0,len(body)])],
        missingEvidence=['The supplied context does not establish the requested memory default.'] if absent else [],
        status='abstained' if absent else 'answered')
    if absent:
        frames = {}
    identity = dict(namespace=source['namespace'], allowedWings=['notes'], arm='synthetic-fixture',
                    qid='memory-default', sourceRunBinding='synthetic-span-audit-v1')
    packet = contract.freeze_audit(baseline.freeze_packet(question,draft,frames,identity=identity))
    view = contract.source_view(packet)
    sources = [] if absent else view['quoteCandidates']
    answers = [] if absent else [contract.answer_view(packet)['claims'][0]['span']]
    limitations = [contract.answer_view(packet)['limitations'][0]['span']] if absent else []
    ledger = dict(version=1, questionParts=[dict(id='p',questionSpans=[view['questionSpan']],
        answerability='unknown-in-context' if absent else 'answerable',reason='Synthetic source availability.')],
        obligations=[] if absent else [dict(id='o',partIds=['p'],proposition=body,sourceSpans=sources)],unresolved=[])
    complete = case == 'complete'
    audit = dict(version=1,
        obligations=[] if absent else [dict(id='o',verdict='covered' if complete else 'omitted',
            answerSpans=answers if complete else [],sourceSpans=sources,reason='Synthetic expected coverage.')],
        claims=[] if absent else [dict(id='claim',verdict='supported',answerSpans=answers,sourceSpans=sources,
            citations=[dict(evidenceId='evidence',verdict='supported',sourceSpans=sources,reason='Exact synthetic source.')],reason='Synthetic claim support.')],
        questionParts=[dict(id='p',verdict='appropriately-limited' if absent else 'fact-supported' if complete else 'insufficient',
            answerSpans=answers,limitationSpans=limitations,sourceSpans=sources,reason='Synthetic disposition.')],
        extraFindings=[],status=dict(recommendation='abstained' if absent else 'answered' if complete else 'partial',
            partIds=['p'],answerSpans=answers,limitationSpans=limitations,reason='Synthetic status check.'),unresolved=[])
    return packet, ledger, audit


@contextmanager
def _provider(outputs, missing_usage):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            length = int(self.headers.get('Content-Length','0'))
            if self.path != '/v1/chat/completions' or not 0 < length <= 262144 or len(requests) >= 2:
                self.send_error(400)
                return
            request = json.loads(self.rfile.read(length))
            schema = contract.LEDGER_SCHEMA if not requests else contract.AUDIT_SCHEMA
            if (request.get('model') != 'synthetic-answer-span-audit' or request.get('max_tokens') != 4096
                    or request.get('tools') or request.get('response_format',{}).get('json_schema',{}).get('schema') != schema):
                self.send_error(400)
                return
            index = len(requests)
            requests.append(request)
            reply = dict(id='synthetic-span-audit', object='chat.completion', model='synthetic-answer-span-audit',
                choices=[dict(index=0,message=dict(role='assistant',content=json.dumps(outputs[index],ensure_ascii=False)),finish_reason='stop')])
            if not missing_usage:
                reply['usage'] = dict(prompt_tokens=30,completion_tokens=20,total_tokens=50)
            raw = json.dumps(reply).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    config = RuntimeConfig(profiles={'fixture':EndpointConfig(base_url=f'http://127.0.0.1:{server.server_port}/v1',
        model='synthetic-answer-span-audit',max_tokens=4096,temperature=0,features={'streaming':False})},routes={},default_profile='fixture')
    try:
        yield config, requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


def run_fixture(directory, *, case='omitted'):
    packet, ledger, audit = materials(case)
    with _provider([ledger,audit],case=='unknown-usage') as (config, requests):
        result = run_audit(config,packet,directory)
        again = run_audit(config,packet,directory)
        contract.require(again['usage']['providerRequests'] == 0, 'fixture resume dispatched')
    return dict(profileId=contract.PROFILE,fixture=True,case=case,status=result['status'],outcome=result['outcome'],
        originalUnchanged=result['original']==packet.to_dict()['draft'],syntheticProviderRequests=len(requests),
        realModelCalls=0,semanticQuality='unmeasured',retainedTokens=result['retainedTokens'],
        resumeProviderRequests=again['usage']['providerRequests'],memoryDefault=False,sueDefault=False)
