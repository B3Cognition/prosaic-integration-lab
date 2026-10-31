"""Credential-free actual SDK transport fixture; never measures model quality."""
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading

from prosaic_runtime import EndpointConfig, RuntimeConfig

from .answer_contract import SECTIONS
from .storage import sha
from .workflow import unanswered


def fixture_answer(packet):
    question,frames=packet['question'],packet['frames']
    opened=[(fid,f,s) for fid,f in frames.items() if f['kind']=='open' for s in f['bodySpans']]
    if not opened:return unanswered(question,frames)
    fid,frame,span=opened[0];meta=frame['metadata'];rid=span.get('recordId')
    source=meta['records'][rid]['sourceIdentity'] if rid else meta['sourceIdentity']
    if rid:
        record=meta['records'][rid]
        citation={k:record[k] for k in ('textSha256','revision','startChar','endChar','startLine','endLine')}
        citation.update(path=source['path'],sourceFileSha256=source['sourceFileSha256'],recordId=rid)
    else:citation=dict(path=source['path'],sourceFileSha256=source['sourceFileSha256'],chars=[meta['startChar'],meta['endChar']])
    quote=frame['display'][span['start']:span['end']]
    return dict(questionParts=[dict(id='p',start=0,end=len(question),quote=question,claimIds=['c'],missingEvidenceIndices=[])],
        claims=[dict(id='c',text=quote,kind='observation',evidenceIds=['e'])],
        evidence=[dict(id='e',frameId=fid,displaySha256=sha(frame['display'].encode()),start=span['start'],end=span['end'],quote=quote)],
        sections={k:dict(claimIds=['c'] if k=='directAnswer' else [],reason='' if k=='directAnswer' else 'No additional fixture claim.') for k in SECTIONS},
        frameReview=[dict(frameId=f,disposition='used' if f==fid else 'irrelevant',claimIds=['c'] if f==fid else [],
            reason='Synthetic fixture selection; not semantic evaluation.') for f in frames],
        citations=[citation],missingEvidence=[],status='answered')


def compact_fixture_answer(packet):
    """Synthetic wire reply from the actual projected model inputs only."""
    question, frames = packet['question'], packet['frames']
    choice = next((q for q in packet['quoteAddresses'] if frames[q['frameId']]['kind'] == 'open'), None)
    if choice is None:
        return unanswered(question, frames)
    fid = choice['frameId']; text = frames[fid]['display'][choice['start']:choice['end']]
    return dict(questionParts=[dict(id='p', start=0, end=len(question), quote=question, claimIds=['c'], missingEvidenceIndices=[])],
        claims=[dict(id='c', text=text, kind='observation', evidenceIds=['e'])],
        evidence=[dict(id='e', quoteId=choice['id'])],
        sections={k: dict(claimIds=['c'] if k == 'directAnswer' else [], reason='' if k == 'directAnswer' else 'No additional fixture claim.') for k in SECTIONS},
        frameReview=[dict(frameId=f, disposition='used' if f == fid else 'irrelevant', claimIds=['c'] if f == fid else [],
            reason='Synthetic fixture selection; not semantic evaluation.') for f in frames],
        citations=[a['id'] for a in packet['citationAddresses'] if a['frameId'] == fid], missingEvidence=[], status='answered')


class FixtureServer:
    def __init__(self,*,missing_usage=False):self.requests=[];self.missing_usage=missing_usage
    def __enter__(self):
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                owner.requests.append(request)
                arguments=request['messages'][-1]['content'].split('Task arguments:\n',1)[-1]
                data=json.loads(arguments);packet=data['request']['packet']
                schema=request['response_format']['json_schema']['schema']
                if set(schema['properties'])=={'feedback'}:
                    value={'feedback':'Check the frozen evidence. Retain every supported fact; this fixture does not assess semantic completeness.'}
                elif 'draft' in packet:value=deepcopy(packet['draft'])
                elif 'quoteAddresses' in packet:value=compact_fixture_answer(packet)
                else:value=fixture_answer(packet)
                if set(schema['properties']) != {'feedback'} and data['request'].get('profileId') == 'compact-host-resolved-v1' and 'draft' not in packet:
                    # Synthetic generation from projected fixture input, never a live-output repair.
                    for part in value['questionParts']:
                        del part['start']; del part['end']
                    value['frameReview'] = [dict(frameId=frame['frameId'], reason=frame['reason'],
                        unreferencedDisposition='insufficient' if frame['disposition']=='used' else frame['disposition'])
                        for frame in value['frameReview']]
                if set(schema['properties']) != {'feedback'} and data['request'].get('profileId') in ('compact-host-canonical-links-v1','compact-host-claim-parts-v1','compact-host-missing-parts-v1') and 'draft' not in packet:
                    # Synthetic emission in the declared wire format, never a live-output repair.
                    ids = {e['id']:e['quoteId'] for e in value['evidence']}
                    value['evidence'] = list(ids.values())
                    for claim in value['claims']:
                        claim['evidenceIds'] = [ids[eid] for eid in claim['evidenceIds']]
                    for part in value['questionParts']:
                        del part['start']; del part['end']
                    value['frameReview'] = [dict(frameId=f['frameId'],
                        unreferencedDisposition='insufficient' if f['disposition']=='used' else f['disposition'])
                        for f in value['frameReview']]
                    if data['request']['profileId'] in ('compact-host-claim-parts-v1','compact-host-missing-parts-v1'):
                        for claim in value['claims']:
                            claim['questionPartIds'] = [p['id'] for p in value['questionParts'] if claim['id'] in p['claimIds']]
                        for part in value['questionParts']:
                            del part['claimIds']
                        if data['request']['profileId'] == 'compact-host-missing-parts-v1':
                            value['missingEvidence'] = [dict(text=text, questionPartIds=[p['id'] for p in value['questionParts']
                                if i in p['missingEvidenceIndices']]) for i, text in enumerate(value['missingEvidence'])]
                            for part in value['questionParts']:
                                del part['missingEvidenceIndices']
                reply=dict(id='synthetic-memory',object='chat.completion',model='synthetic-memory',
                    choices=[dict(index=0,message=dict(role='assistant',content=json.dumps(value,ensure_ascii=False)),finish_reason='stop')])
                if not owner.missing_usage:reply['usage']=dict(prompt_tokens=30,completion_tokens=20,total_tokens=50)
                raw=json.dumps(reply).encode();self.send_response(200)
                self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
                self.end_headers();self.wfile.write(raw)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.config=RuntimeConfig(profiles={'fixture':EndpointConfig(base_url=f'http://127.0.0.1:{self.server.server_port}/v1',
            model='synthetic-memory',max_tokens=4096,temperature=0)},routes={},default_profile='fixture')
        return self
    def __exit__(self,*args):
        self.server.shutdown();self.server.server_close();self.thread.join()
