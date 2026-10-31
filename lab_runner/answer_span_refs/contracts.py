"""Host-owned exact references, resolved through unchanged canonical validators."""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

from lab_runner.memory_benchmark import span_audit_contracts as canonical
from lab_runner.memory_benchmark import completeness_profile as baseline
from lab_runner.memory_benchmark.storage import decode,encoded,require,sha,shape
from . import PROFILE

PART_IDS=tuple(f'part-{i:03}' for i in range(1,17))
OBLIGATION_IDS=tuple(f'obligation-{i:03}' for i in range(1,33))
MAX_PACKET_BYTES=262144
MAX_OUTPUT_BYTES=16384


def _binding():
    return dict(profile=PROFILE,version=1,
        sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))},
        limits=dict(packetBytes=MAX_PACKET_BYTES,wireBytes=MAX_OUTPUT_BYTES,canonicalBytes=MAX_OUTPUT_BYTES,
            envelopeBytes=MAX_OUTPUT_BYTES,calls=2,callSeconds=120,runSeconds=270,reportedTokens=65536,
            outputTokens=4096,tools=0,retries=0))


@dataclass(frozen=True)
class RefsPacket:
    payload: bytes
    sha256: str

    def to_dict(self):
        require(type(self.payload) is bytes and sha(self.payload)==self.sha256,'reference packet digest')
        return decode(self.payload,MAX_PACKET_BYTES)


def freeze_refs(review):
    base=canonical.freeze_audit(review)
    data=dict(version=1,profile=PROFILE,canonical=base.to_dict(),canonicalSha256=base.sha256,binding=_binding())
    raw=encoded(data);require(len(raw)<=MAX_PACKET_BYTES,'reference packet byte limit')
    return RefsPacket(raw,sha(raw))


def canonical_packet(packet):
    require(type(packet) is RefsPacket,'frozen reference packet required')
    data=packet.to_dict();shape(data,('version','profile','canonical','canonicalSha256','binding'))
    require(type(data['version']) is int and data['version']==1 and data['profile']==PROFILE
        and data['binding']==_binding(),'reference profile or source binding changed')
    body=data['canonical']
    base=canonical.freeze_audit(baseline.freeze_packet(body['question'],body['draft'],body['frames'],identity=body['identity']))
    require(base.to_dict()==body and base.sha256==data['canonicalSha256'],'canonical packet binding changed')
    return base


@dataclass(frozen=True)
class ProofCatalog:
    payload: bytes
    sha256: str

    def to_dict(self):
        require(type(self.payload) is bytes and sha(self.payload)==self.sha256,'proof catalog digest')
        return decode(self.payload,4194304)


def catalog(packet,*,include_answer=False):
    base=canonical_packet(packet);data=base.to_dict();proofs={};reverse={}

    def add(kind,identifier,text,start,end,name):
        key=(kind,identifier,start,end)
        if key in reverse:return reverse[key]
        require(name not in proofs,'colliding host proof reference')
        proofs[name]=dict(kind=kind,id=identifier,sha256=canonical.sha(text),start=start,end=end,quote=text[start:end])
        reverse[key]=name;return name

    question=data['question']
    full=add('question','question',question,0,len(question),'q0000')
    question_refs=[dict(id=full,text=question)]
    for i,match in enumerate(re.finditer(r'\S+',question),1):
        name=add('question','question',question,match.start(),match.end(),f'q{i:04}')
        if name!=full:question_refs.append(dict(id=name,text=match.group()))
    # Unify boundaries for equal bodies before deduplication. Every occurrence
    # retains its frame/range/ordering; model text is never normalized or clipped.
    groups={};occurrences=[]
    for fid,frame in data['frames'].items():
        for index,body in enumerate(frame['bodySpans']):
            start,end=body['start'],body['end'];text=frame['display'][start:end]
            group=groups.setdefault(text,dict(id=f'b{len(groups)+1:04}',cuts={0,len(text)},items=[]))
            item=dict(frameId=fid,bodyIndex=index,start=start,end=end,bodyId=group['id'])
            group['items'].append(item);occurrences.append(item)
            for quote in data['quoteCandidates']:
                if quote['frameId']==fid and start<=quote['start']<quote['end']<=end:
                    group['cuts'].update((quote['start']-start,quote['end']-start))
    bodies=[];source_count=0
    for text,group in groups.items():
        cuts=sorted(group['cuts']);fragments=[]
        for item in group['items']:item['refs']=[]
        for left,right in zip(cuts,cuts[1:]):
            aliases=[]
            for item in group['items']:
                fid=item['frameId'];source_count+=1
                name=add('source',fid,data['frames'][fid]['display'],item['start']+left,item['start']+right,f's{source_count:05}')
                item['refs'].append(name)
                if name not in aliases:aliases.append(name)
            fragments.append(dict(refs=aliases,text=text[left:right]))
        require(''.join(fragment['text'] for fragment in fragments)==text,'lossless body reconstruction')
        bodies.append(dict(id=group['id'],fragments=fragments))
    view=dict(question=question,questionRefs=question_refs,bodies=bodies,
        occurrences=[{k:item[k] for k in ('frameId','bodyIndex','bodyId','refs')} for item in occurrences],
        partIds=list(PART_IDS),obligationIds=list(OBLIGATION_IDS))
    value=dict(proofs=proofs,sourceView=view)
    if include_answer:
        answer=canonical.answer_view(base);claims=[];limits=[];evidence=[]
        for i,claim in enumerate(answer['claims'],1):
            name=add('answer',claim['id'],claim['text'],0,len(claim['text']),f'a{i:04}')
            claims.append(dict(id=claim['id'],text=claim['text'],kind=claim['kind'],answerRef=name,evidenceIds=claim['evidenceIds']))
        for i,limit in enumerate(answer['limitations'],1):
            name=add('limitation',limit['id'],limit['text'],0,len(limit['text']),f'l{i:04}')
            limits.append(dict(id=limit['id'],text=limit['text'],limitationRef=name))
        for i,row in enumerate(answer['evidence'],1):
            fid=row['frameId'];name=add('source',fid,data['frames'][fid]['display'],row['start'],row['end'],f'e{i:05}')
            evidence.append(dict(id=row['id'],sourceRef=name,quote=row['quote'],frameId=fid))
        value['answerView']=dict(claims=claims,limitations=limits,evidence=evidence,
            draftCoverage=answer['questionParts'],status=answer['status'])
    return ProofCatalog(encoded(value),sha(encoded(value)))


def source_view(packet):
    value=catalog(packet).to_dict()['sourceView']
    require(len(encoded(value))<=MAX_PACKET_BYTES,'source projection byte limit')
    return value


def answer_view(packet):
    return catalog(packet,include_answer=True).to_dict()['answerView']


def _obj(properties):
    return dict(type='object',properties=deepcopy(properties),required=list(properties),additionalProperties=False)


def _array(items,maximum=256,minimum=0,unique=False):
    value=dict(type='array',items=deepcopy(items),minItems=minimum,maxItems=maximum)
    if unique:value['uniqueItems']=True
    return value


TEXT=dict(type='string',minLength=1)


def _enum(*items):return dict(type='string',enum=list(items))


def _ids(items,maximum=256,minimum=0):
    items=list(items)
    return _array(_enum(*items) if items else dict(type='string'),maximum if items else 0,minimum,True)


def _ref_fields(proofs):
    return {kind:_ids(key for key,value in proofs.items() if value['kind']==kind)
            for kind in ('question','source','answer','limitation')}


def ledger_schema(packet):
    refs=_ref_fields(catalog(packet).to_dict()['proofs'])
    part=_obj(dict(id=_enum(*PART_IDS),questionRefs=refs['question'],
        answerability=_enum('answerable','partially-answerable','unknown-in-context','conflicting'),reason=TEXT))
    obligation=_obj(dict(id=_enum(*OBLIGATION_IDS),partIds=_ids(PART_IDS,16,1),proposition=TEXT,sourceRefs=refs['source']))
    return _obj(dict(version=dict(type='integer',enum=[1]),questionParts=_array(part,16,1),
        obligations=_array(obligation,32),unresolved=_array(TEXT,32)))


def audit_schema(packet,ledger):
    ledger=canonical.validate_ledger(ledger,canonical_packet(packet))
    data=canonical_packet(packet).to_dict();proofs=catalog(packet,include_answer=True).to_dict()['proofs'];refs=_ref_fields(proofs)
    parts=[row['id'] for row in ledger['questionParts']]
    obligation=_obj(dict(verdict=_enum('covered','omitted','contradicted','unresolved'),
        answerRefs=refs['answer'],sourceRefs=refs['source'],reason=TEXT))
    citation=_obj(dict(verdict=_enum('supported','unsupported','contradicted','supported-elsewhere','unresolved'),
        sourceRefs=refs['source'],reason=TEXT))
    claims={}
    for claim in data['draft']['claims']:
        own=_ids(key for key,value in proofs.items() if value['kind']=='answer' and value['id']==claim['id'])
        claims[claim['id']]=_obj(dict(verdict=_enum('supported','unsupported','contradicted','appropriate-limitation','unresolved'),
            answerRefs=own,sourceRefs=refs['source'],citations=_obj({eid:citation for eid in claim['evidenceIds']}),reason=TEXT))
    part=_obj(dict(verdict=_enum('fact-supported','appropriately-limited','insufficient','unresolved'),
        answerRefs=refs['answer'],limitationRefs=refs['limitation'],sourceRefs=refs['source'],reason=TEXT))
    extra=_obj(dict(id=TEXT,partIds=_ids(parts,16,1),proposition=TEXT,questionRefs=refs['question'],
        sourceRefs=refs['source'],answerRefs=refs['answer'],verdict=_enum('omitted','contradicted','unsupported','unresolved'),reason=TEXT))
    return _obj(dict(version=dict(type='integer',enum=[1]),
        obligations=_obj({row['id']:obligation for row in ledger['obligations']}),claims=_obj(claims),
        questionParts=_obj({pid:part for pid in parts}),extraFindings=_array(extra,32),
        status=_obj(dict(recommendation=_enum('answered','partial','abstained'),answerRefs=refs['answer'],
            limitationRefs=refs['limitation'],reason=TEXT)),unresolved=_array(TEXT,32)))


def _expand(ids,proofs,kind):
    require(type(ids) is list and len(ids)==len(set(ids)),'duplicate proof reference')
    require(all(type(key) is str and key in proofs and proofs[key]['kind']==kind for key in ids),'unknown or wrong-kind proof reference')
    return [deepcopy(proofs[key]) for key in ids]


def resolve_ledger(wire,packet):
    wire=canonical.decode(wire,ledger_schema(packet))
    proofs=catalog(packet).to_dict()['proofs']
    result=dict(version=1,questionParts=[dict(id=row['id'],questionSpans=_expand(row['questionRefs'],proofs,'question'),
        answerability=row['answerability'],reason=row['reason']) for row in wire['questionParts']],
        obligations=[dict(id=row['id'],partIds=row['partIds'],proposition=row['proposition'],
            sourceSpans=_expand(row['sourceRefs'],proofs,'source')) for row in wire['obligations']],unresolved=wire['unresolved'])
    return canonical.validate_ledger(result,canonical_packet(packet))


def resolve_audit(wire,packet,ledger):
    wire=canonical.decode(wire,audit_schema(packet,ledger))
    proofs=catalog(packet,include_answer=True).to_dict()['proofs']

    def fields(row):
        result=deepcopy(row)
        for key,kind in (('answerRefs','answer'),('sourceRefs','source'),('questionRefs','question'),('limitationRefs','limitation')):
            if key in result:result[key.replace('Refs','Spans')]=_expand(result.pop(key),proofs,kind)
        return result

    claims=[]
    for cid,row in wire['claims'].items():
        row=fields(row);row['id']=cid
        row['citations']=[dict(fields(value),evidenceId=eid) for eid,value in row['citations'].items()]
        claims.append(row)
    result=dict(version=1,obligations=[dict(fields(row),id=oid) for oid,row in wire['obligations'].items()],
        claims=claims,questionParts=[dict(fields(row),id=pid) for pid,row in wire['questionParts'].items()],
        extraFindings=[fields(row) for row in wire['extraFindings']],
        status=dict(fields(wire['status']),partIds=[row['id'] for row in ledger['questionParts']]),unresolved=wire['unresolved'])
    return canonical.validate_audit(result,canonical_packet(packet),ledger)['audit']
