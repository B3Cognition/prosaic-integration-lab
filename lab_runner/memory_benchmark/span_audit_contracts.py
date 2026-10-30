"""Exact, scoped audit attachment. Valid proof addresses do not prove semantics."""
from dataclasses import dataclass
import hashlib
from importlib.metadata import version
from pathlib import Path

from jsonschema import Draft202012Validator

from . import answer_contract, completeness_profile as baseline

PROFILE = 'consumer-answer-span-audit-v1'
MAX_PACKET_BYTES = 262144
MAX_OUTPUT_BYTES = 16384
MAX_OUTPUT_TOKENS = 4096


def _obj(properties):
    return dict(type='object', additionalProperties=False, required=list(properties), properties=properties)


def _array(items, maximum=256, minimum=0):
    return dict(type='array', items=items, minItems=minimum, maxItems=maximum)


def _enum(*values):
    return dict(enum=list(values))


TEXT = dict(type='string', minLength=1)
IDS = dict(type='array', items=TEXT, uniqueItems=True, maxItems=256)
SPAN = _obj(dict(kind=_enum('source', 'answer', 'limitation', 'question'), id=TEXT,
    sha256=dict(type='string', pattern='^[0-9a-f]{64}$'),
    start=dict(type='integer', minimum=0), end=dict(type='integer', minimum=1), quote=TEXT))
SPANS = _array(SPAN)
PART = _obj(dict(id=TEXT, questionSpans=SPANS,
    answerability=_enum('answerable', 'partially-answerable', 'unknown-in-context', 'conflicting'), reason=TEXT))
OBLIGATION = _obj(dict(id=TEXT, partIds=IDS, proposition=TEXT, sourceSpans=SPANS))
LEDGER_SCHEMA = _obj(dict(version=_enum(1), questionParts=_array(PART, 16, 1),
    obligations=_array(OBLIGATION, 32), unresolved=_array(TEXT, 32)))
AUDIT_SCHEMA = _obj(dict(version=_enum(1),
    obligations=_array(_obj(dict(id=TEXT, verdict=_enum('covered', 'omitted', 'contradicted', 'unresolved'),
        answerSpans=SPANS, sourceSpans=SPANS, reason=TEXT)), 32),
    claims=_array(_obj(dict(id=TEXT, verdict=_enum('supported', 'unsupported', 'contradicted', 'appropriate-limitation', 'unresolved'),
        answerSpans=SPANS, sourceSpans=SPANS, citations=_array(_obj(dict(evidenceId=TEXT,
            verdict=_enum('supported', 'unsupported', 'contradicted', 'supported-elsewhere', 'unresolved'), sourceSpans=SPANS, reason=TEXT))), reason=TEXT))),
    questionParts=_array(_obj(dict(id=TEXT, verdict=_enum('fact-supported', 'appropriately-limited', 'insufficient', 'unresolved'),
        answerSpans=SPANS, limitationSpans=SPANS, sourceSpans=SPANS, reason=TEXT)), 16, 1),
    extraFindings=_array(_obj(dict(id=TEXT, partIds=IDS, proposition=TEXT, questionSpans=SPANS,
        sourceSpans=SPANS, answerSpans=SPANS, verdict=_enum('omitted', 'contradicted', 'unsupported', 'unresolved'), reason=TEXT)), 32),
    status=_obj(dict(recommendation=_enum('answered', 'partial', 'abstained'), partIds=IDS,
        answerSpans=SPANS, limitationSpans=SPANS, reason=TEXT)), unresolved=_array(TEXT, 32)))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decode(value, schema, maximum=MAX_OUTPUT_BYTES):
    raw = value if type(value) in (str, bytes) else baseline._json(value, maximum)
    data = baseline._decode(raw, maximum)
    require(Draft202012Validator(schema).is_valid(data), 'closed audit schema')
    # JSON Schema considers True equal to 1 for an enum; the version is typed.
    require(type(data['version']) is int and data['version'] == 1, 'audit version')
    return data


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def address(kind, identifier, text):
    return dict(kind=kind, id=identifier, sha256=sha(text), start=0, end=len(text), quote=text)


def _binding():
    return dict(profile=PROFILE,
        sdk={name: version(name) for name in ('b3-prosaic-runtime', 'b3-prosaic-harness', 'prosaic-integration-lab')},
        sources={name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                 for name in ('span_audit_contracts.py', 'span_audit_workflow.py', 'completeness_profile.py', 'answer_contract.py')},
        schemas=dict(ledger=baseline._sha(LEDGER_SCHEMA), audit=baseline._sha(AUDIT_SCHEMA)),
        limits=dict(packetBytes=MAX_PACKET_BYTES, outputBytes=MAX_OUTPUT_BYTES, outputTokens=MAX_OUTPUT_TOKENS,
                    parts=16, obligations=32, extraFindings=32, calls=2, callSeconds=120, runSeconds=270, reportedTokens=65536))


@dataclass(frozen=True)
class AuditPacket:
    payload: bytes
    sha256: str

    def to_dict(self):
        require(type(self.payload) is bytes and baseline._sha(self.payload) == self.sha256, 'audit packet digest')
        return baseline._decode(self.payload, MAX_PACKET_BYTES)


def freeze_audit(packet):
    require(type(packet) is baseline.ReviewPacket, 'validated review packet required')
    data = packet.to_dict()
    checked = baseline.freeze_packet(data['question'], data['draft'], data['frames'], identity=data['identity'])
    require(checked == packet, 'review packet binding mismatch')
    data['auditBinding'] = _binding()
    data['originalPacketSha256'] = packet.sha256
    payload = baseline._json(data, MAX_PACKET_BYTES)
    return AuditPacket(payload, baseline._sha(payload))


def checked(packet):
    require(type(packet) is AuditPacket, 'frozen AuditPacket required')
    data = packet.to_dict()
    original = baseline.freeze_packet(data['question'], data['draft'], data['frames'], identity=data['identity'])
    require(freeze_audit(original) == packet, 'frozen audit input or version mismatch')
    return data


def source_view(packet):
    data = checked(packet)
    # Authorization/provenance is frozen by the host; model output cannot alter it.
    return dict(question=data['question'], questionSpan=address('question', 'question', data['question']),
        frames=data['frames'], quoteCandidates=[dict(kind='source', id=q['frameId'], sha256=q['displaySha256'],
            start=q['start'], end=q['end'], quote=q['quote']) for q in data['quoteCandidates']])


def answer_view(packet):
    data = checked(packet)
    answer = data['draft']
    claims = {c['id']: c for c in answer['claims']}
    ordered = [claims[cid] for name in answer_contract.SECTIONS for cid in answer['sections'][name]['claimIds']]
    return dict(claims=[dict(c, sha256=sha(c['text']), span=address('answer', c['id'], c['text'])) for c in ordered],
        limitations=[dict(id=f'missing-{i}', text=text, sha256=sha(text), span=address('limitation', f'missing-{i}', text))
                     for i, text in enumerate(answer['missingEvidence'])],
        questionParts=answer['questionParts'], evidence=answer['evidence'], citations=answer['citations'], status=answer['status'])


def _rows(rows, expected=None):
    ids = [r['id'] for r in rows]
    require(len(ids) == len(set(ids)), 'duplicate audit identity')
    if expected is not None:
        require(set(ids) == set(expected), 'incomplete or foreign audit identity set')
    return {r['id']: r for r in rows}


def _spans(spans, packet, kind, *, allowed=None, required=False):
    data = checked(packet)
    require(type(spans) is list and (not required or bool(spans)), 'required exact proof missing')
    claims = {c['id']: c['text'] for c in data['draft']['claims']}
    limits = {f'missing-{i}': text for i, text in enumerate(data['draft']['missingEvidence'])}
    identities = {'question': {'question': data['question']}, 'answer': claims, 'limitation': limits,
                  'source': {fid: f['display'] for fid, f in data['frames'].items()}}
    seen = set()
    for span in spans:
        require(span['kind'] == kind and span['id'] in identities[kind], 'wrong proof view or identity')
        require(allowed is None or span['id'] in allowed, 'foreign proof membership')
        text = identities[kind][span['id']]
        require(span['sha256'] == sha(text), 'proof text digest')
        answer_contract.exact_range(span, text, 'audit proof')
        key = (span['id'], span['start'], span['end'])
        require(key not in seen, 'duplicate proof span')
        seen.add(key)
        if kind == 'source':
            require(any(b['start'] <= span['start'] < span['end'] <= b['end'] for b in data['frames'][span['id']]['bodySpans']),
                    'proof outside authorized body')


def _part_ids(ids, parts, required=True):
    require((not required or bool(ids)) and len(ids) == len(set(ids)) and set(ids) <= set(parts), 'question part membership')


def validate_ledger(value, packet):
    data = checked(packet)
    result = decode(value, LEDGER_SCHEMA)
    parts = _rows(result['questionParts'])
    coverage = set()
    for part in parts.values():
        _spans(part['questionSpans'], packet, 'question', required=True)
        for span in part['questionSpans']:
            coverage.update(range(span['start'], span['end']))
    require(all(i in coverage for i, c in enumerate(data['question']) if not c.isspace()), 'disconnected question coverage')
    obligations = _rows(result['obligations'])
    for row in obligations.values():
        _part_ids(row['partIds'], parts)
        _spans(row['sourceSpans'], packet, 'source', required=True)
        require(all(parts[p]['answerability'] != 'unknown-in-context' for p in row['partIds']), 'unknown fact cannot invent an obligation')
    for part in parts.values():
        if part['answerability'] in ('answerable', 'partially-answerable', 'conflicting'):
            require(any(part['id'] in row['partIds'] for row in obligations.values()), 'answerable part requires source obligation')
    return result


def validate_audit(value, packet, ledger):
    data = checked(packet)
    ledger = validate_ledger(ledger, packet)
    result = decode(value, AUDIT_SCHEMA)
    obligations = _rows(ledger['obligations'])
    parts = _rows(ledger['questionParts'])
    claims = _rows(data['draft']['claims'])
    obligation_checks = _rows(result['obligations'], obligations)
    claim_checks = _rows(result['claims'], claims)
    part_checks = _rows(result['questionParts'], parts)
    findings = bool(result['extraFindings'])
    unresolved = bool(ledger['unresolved'] or result['unresolved'])
    for row in obligation_checks.values():
        _spans(row['sourceSpans'], packet, 'source', required=True)
        _spans(row['answerSpans'], packet, 'answer', required=row['verdict'] in ('covered', 'contradicted'))
        findings |= row['verdict'] in ('omitted', 'contradicted')
        unresolved |= row['verdict'] == 'unresolved'
    evidence = {e['id']: e for e in data['draft']['evidence']}
    for cid, row in claim_checks.items():
        claim = claims[cid]
        _spans(row['answerSpans'], packet, 'answer', allowed={cid}, required=True)
        _spans(row['sourceSpans'], packet, 'source', required=row['verdict'] in ('supported', 'contradicted'))
        if row['verdict'] == 'appropriate-limitation':
            require(claim['kind'] == 'absence' and cid in data['draft']['sections']['limitations']['claimIds']
                    and bool(data['draft']['missingEvidence']) and data['draft']['status'] != 'answered', 'invalid limitation claim')
            require(any(cid in p['claimIds'] and p['missingEvidenceIndices'] for p in data['draft']['questionParts']), 'unlinked limitation claim')
        citations = row['citations']
        require(len(citations) == len({c['evidenceId'] for c in citations}) and {c['evidenceId'] for c in citations} == set(claim['evidenceIds']), 'selected citation membership')
        for citation in citations:
            _spans(citation['sourceSpans'], packet, 'source', required=citation['verdict'] in ('supported', 'contradicted', 'supported-elsewhere'))
            if citation['verdict'] == 'supported':
                selected = evidence[citation['evidenceId']]
                require(all(s['id'] == selected['frameId'] and selected['start'] <= s['start'] < s['end'] <= selected['end'] for s in citation['sourceSpans']), 'support outside selected citation')
            findings |= citation['verdict'] not in ('supported', 'unresolved')
            unresolved |= citation['verdict'] == 'unresolved'
        findings |= row['verdict'] in ('unsupported', 'contradicted')
        unresolved |= row['verdict'] == 'unresolved'
    for pid, row in part_checks.items():
        matching = [p for p in data['draft']['questionParts'] if any(
            s['start'] < p['end'] and p['start'] < s['end'] for s in parts[pid]['questionSpans'])]
        allowed_claims = {cid for p in matching for cid in p['claimIds']}
        allowed_limits = {f'missing-{i}' for p in matching for i in p['missingEvidenceIndices']}
        _spans(row['answerSpans'], packet, 'answer', allowed=allowed_claims)
        _spans(row['limitationSpans'], packet, 'limitation', allowed=allowed_limits)
        _spans(row['sourceSpans'], packet, 'source')
        linked = [o['id'] for o in obligations.values() if pid in o['partIds']]
        if row['verdict'] == 'fact-supported':
            require(parts[pid]['answerability'] == 'answerable' and bool(row['answerSpans'])
                    and all(obligation_checks[oid]['verdict'] == 'covered' for oid in linked), 'unproved fact-supported part')
        elif row['verdict'] == 'appropriately-limited':
            require(parts[pid]['answerability'] != 'answerable' and data['draft']['status'] != 'answered', 'unjustified limited question part')
            absence_ids = {cid for cid, c in claims.items() if c['kind'] == 'absence' and claim_checks[cid]['verdict'] == 'appropriate-limitation'}
            require(bool(row['limitationSpans']) or any(s['id'] in absence_ids for s in row['answerSpans']), 'explicit limitation proof required')
            if parts[pid]['answerability'] == 'conflicting':
                require(len(row['sourceSpans']) >= 2 and bool(row['answerSpans']), 'conflict requires opposing source and answer proof')
        findings |= row['verdict'] == 'insufficient'
        unresolved |= row['verdict'] == 'unresolved'
    extras = _rows(result['extraFindings'])
    require(not (set(extras) & (set(obligations) | set(parts) | set(claims))), 'colliding extra finding identity')
    for row in extras.values():
        _part_ids(row['partIds'], parts)
        _spans(row['questionSpans'], packet, 'question', required=True)
        _spans(row['sourceSpans'], packet, 'source', required=row['verdict'] in ('omitted', 'contradicted'))
        _spans(row['answerSpans'], packet, 'answer', required=row['verdict'] in ('contradicted', 'unsupported'))
        unresolved |= row['verdict'] == 'unresolved'
    status = result['status']
    _part_ids(status['partIds'], parts)
    require(set(status['partIds']) == set(parts), 'status must address every question part')
    _spans(status['answerSpans'], packet, 'answer')
    _spans(status['limitationSpans'], packet, 'limitation')
    require(bool(status['answerSpans'] or status['limitationSpans']), 'status explanation requires actual answer or limitation proof')
    findings |= status['recommendation'] != data['draft']['status']
    return dict(audit=result, outcome='unresolved' if unresolved else 'findings' if findings else 'clear')
