"""Resolved references preserve exact proof checks and source independence."""
import copy
import importlib
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from lab_runner.memory_benchmark.completeness_profile import freeze_packet
from lab_runner.memory_benchmark.span_audit_fixture import materials


def api():
    assert (Path(__file__).parents[2]/'lab_runner/answer_span_refs/contracts.py').is_file(), 'host-resolved audit transport is missing'
    return importlib.import_module('lab_runner.answer_span_refs.contracts')


def packet(case='omitted'):
    m=api();data=materials(case)[0].to_dict()
    return m.freeze_refs(freeze_packet(data['question'],data['draft'],data['frames'],identity=data['identity']))


def refs(m,p,kind):
    return [key for key,value in m.catalog(p,include_answer=True).to_dict()['proofs'].items() if value['kind']==kind]


def ledger_wire(m,p,absent=False):
    return dict(version=1,questionParts=[dict(id=m.PART_IDS[0],questionRefs=['q0000'],
        answerability='unknown-in-context' if absent else 'answerable',reason='Displayed source availability.')],
        obligations=[] if absent else [dict(id=m.OBLIGATION_IDS[0],partIds=[m.PART_IDS[0]],
            proposition='Memory is disabled by default.',sourceRefs=refs(m,p,'source'))],unresolved=[])


def audit_wire(m,p,ledger,complete=False,absent=False):
    data=m.canonical_packet(p).to_dict();answers=refs(m,p,'answer');sources=refs(m,p,'source')
    limits=refs(m,p,'limitation');pid=m.PART_IDS[0];oid=m.OBLIGATION_IDS[0]
    return dict(version=1,
        obligations={} if absent else {oid:dict(verdict='covered' if complete else 'omitted',
            answerRefs=answers if complete else [],sourceRefs=sources,reason='Actual answer coverage.')},
        claims={claim['id']:dict(verdict='supported',answerRefs=answers,sourceRefs=sources,
            citations={eid:dict(verdict='supported',sourceRefs=sources,reason='Exact selected source.') for eid in claim['evidenceIds']},
            reason='Actual claim words.') for claim in data['draft']['claims']},
        questionParts={pid:dict(verdict='appropriately-limited' if absent else 'fact-supported' if complete else 'insufficient',
            answerRefs=answers,sourceRefs=sources,limitationRefs=limits,reason='Frozen question coverage.')},
        extraFindings=[],status=dict(recommendation='abstained' if absent else 'answered' if complete else 'partial',
            answerRefs=answers,limitationRefs=limits,reason='Consistent status.'),unresolved=[])


def test_reference_catalog_is_available_and_owns_data():
    m=api();p=packet();catalog=m.catalog(p);data=catalog.to_dict()
    data['proofs'].clear()
    assert m.catalog(p).to_dict()['proofs'] and catalog.to_dict()['proofs']
    assert m.canonical_packet(p).to_dict()==materials('omitted')[0].to_dict()


def test_source_projection_reconstructs_every_unicode_crlf_body_and_alias():
    m=api();data=materials('omitted')[0].to_dict()
    frame=data['frames']['body'];frame['display']=frame['display'].replace('Memory','Ž🙂 Memory').replace('default.','default.\r\nNext line.')
    frame['bodySpans'][0]['end']=len(frame['display'])
    # Rebuild canonical evidence/citations for the changed immutable body.
    from lab_runner.memory_benchmark.span_audit_contracts import sha
    body=frame['display'][frame['bodySpans'][0]['start']:]
    source=frame['metadata']['sourceIdentity'];source['sourceFileSha256']=sha(body)
    frame['metadata'].update(sourceFileSha256=sha(body),endChar=len(body))
    evidence=data['draft']['evidence'][0]
    evidence.update(displaySha256=sha(frame['display']),end=len(frame['display']),quote=body)
    data['draft']['citations'][0].update(sourceFileSha256=sha(body),chars=[0,len(body)])
    data['frames']['alias']=copy.deepcopy(frame)
    data['draft']['frameReview'].append(dict(frameId='alias',disposition='duplicate',claimIds=[],reason='Exact body alias.'))
    p=m.freeze_refs(freeze_packet(data['question'],data['draft'],data['frames'],identity=data['identity']))
    catalog=m.catalog(p).to_dict();view=catalog['sourceView']
    assert len(view['bodies'])==1 and len(view['occurrences'])==2
    for occurrence in view['occurrences']:
        reconstructed=''.join(catalog['proofs'][key]['quote'] for key in occurrence['refs'])
        assert reconstructed==body and '\r\n' in reconstructed and 'Ž🙂' in reconstructed
        assert all(catalog['proofs'][key]['id']==occurrence['frameId'] for key in occurrence['refs'])
    assert all(v['start']>=frame['bodySpans'][0]['start'] for v in catalog['proofs'].values() if v['kind']=='source')


def test_source_view_and_schema_do_not_depend_on_draft_or_selected_citations():
    m=api();p=packet();data=m.canonical_packet(p).to_dict()
    data['draft']['claims'][0]['text']='DRAFT_ONLY_SENTINEL'
    old=data['draft']['evidence'][0]['id'];data['draft']['evidence'][0]['id']='different-selected-id'
    data['draft']['claims'][0]['evidenceIds']=['different-selected-id' if key==old else key for key in data['draft']['claims'][0]['evidenceIds']]
    changed=m.freeze_refs(freeze_packet(data['question'],data['draft'],data['frames'],identity=data['identity']))
    assert p!=changed and m.source_view(p)==m.source_view(changed)
    assert m.ledger_schema(p)==m.ledger_schema(changed)
    assert 'DRAFT_ONLY_SENTINEL' not in str(m.source_view(changed))
    assert all(v['kind'] in ('question','source') for v in m.catalog(p).to_dict()['proofs'].values())


@pytest.mark.parametrize('case',['omitted','complete','unavailable'])
def test_wire_resolves_to_unchanged_canonical_validation(case):
    m=api();p=packet(case);absent=case=='unavailable';complete=case=='complete'
    ledger=m.resolve_ledger(ledger_wire(m,p,absent),p)
    value=m.resolve_audit(audit_wire(m,p,ledger,complete,absent),p,ledger)
    from lab_runner.memory_benchmark.span_audit_contracts import validate_audit
    checked=validate_audit(value,m.canonical_packet(p),ledger)
    assert checked['outcome']==('findings' if case=='omitted' else 'clear')
    assert value['status']['partIds']==[m.PART_IDS[0]]
    assert all(s['sha256'] and s['quote'] for row in ledger['obligations'] for s in row['sourceSpans'])


@pytest.mark.parametrize('mutation',['unknown-ref','wrong-kind','duplicate-ref','foreign-part','extra-field','boolean-version'])
def test_invalid_wire_ledger_cannot_bypass_old_proof_rules(mutation):
    m=api();p=packet();wire=ledger_wire(m,p)
    if mutation=='unknown-ref':wire['obligations'][0]['sourceRefs']=['forged']
    if mutation=='wrong-kind':wire['obligations'][0]['sourceRefs']=['q0000']
    if mutation=='duplicate-ref':wire['obligations'][0]['sourceRefs']*=2
    if mutation=='foreign-part':wire['obligations'][0]['partIds']=[m.PART_IDS[1]]
    if mutation=='extra-field':wire['approved']=True
    if mutation=='boolean-version':wire['version']=True
    with pytest.raises(ValueError):m.resolve_ledger(wire,p)


@pytest.mark.parametrize('mutation',['draft-part','foreign-claim','foreign-citation','source-as-answer','missing-claim','false-covered','status','extra-field'])
def test_audit_ids_and_semantic_guards_remain_strict(mutation):
    m=api();p=packet();ledger=m.resolve_ledger(ledger_wire(m,p),p);wire=audit_wire(m,p,ledger)
    cid=next(iter(wire['claims']));oid=m.OBLIGATION_IDS[0]
    if mutation=='draft-part':wire['questionParts']['part']=wire['questionParts'].pop(m.PART_IDS[0])
    if mutation=='foreign-claim':wire['claims']['forged']=wire['claims'].pop(cid)
    if mutation=='foreign-citation':
        citations=wire['claims'][cid]['citations'];citations['forged']=citations.pop(next(iter(citations)))
    if mutation=='source-as-answer':wire['claims'][cid]['answerRefs']=refs(m,p,'source')
    if mutation=='missing-claim':wire['claims'].clear()
    if mutation=='false-covered':wire['obligations'][oid].update(verdict='covered',answerRefs=[])
    if mutation=='status':wire['status']['recommendation']='answered'
    if mutation=='extra-field':wire['approved']=True
    assert not Draft202012Validator(m.audit_schema(p,ledger)).is_valid(wire) or mutation in ('false-covered','status')
    with pytest.raises(ValueError):m.resolve_audit(wire,p,ledger)


def test_model_does_not_supply_or_normalize_proof_quote_and_offsets():
    m=api();p=packet();wire=ledger_wire(m,p)
    wire['questionParts'][0]['questionSpans']=[dict(start=0,end=62,quote='invented')]
    with pytest.raises(ValueError):m.resolve_ledger(wire,p)
    wire=ledger_wire(m,p);key=wire['obligations'][0]['sourceRefs'][0]
    expected=m.catalog(p).to_dict()['proofs'][key]
    assert m.resolve_ledger(wire,p)['obligations'][0]['sourceSpans'][0]==expected


def test_selected_citation_cannot_escape_to_a_deduplicated_alias():
    m=api();data=materials('complete')[0].to_dict();data['frames']['alias']=copy.deepcopy(data['frames']['body'])
    data['draft']['frameReview'].append(dict(frameId='alias',disposition='duplicate',claimIds=[],reason='Same body.'))
    p=m.freeze_refs(freeze_packet(data['question'],data['draft'],data['frames'],identity=data['identity']))
    ledger=m.resolve_ledger(ledger_wire(m,p),p);wire=audit_wire(m,p,ledger,complete=True)
    proofs=m.catalog(p,include_answer=True).to_dict()['proofs'];cid=next(iter(wire['claims']))
    citation=next(iter(wire['claims'][cid]['citations'].values()))
    citation['sourceRefs']=[key for key,value in proofs.items() if value['kind']=='source' and value['id']=='body']
    assert m.resolve_audit(wire,p,ledger)
    citation['sourceRefs']=[key for key,value in proofs.items() if value['kind']=='source' and value['id']=='alias']
    with pytest.raises(ValueError,match='selected citation'):m.resolve_audit(wire,p,ledger)


def test_wire_and_expanded_canonical_limits_are_both_enforced():
    m=api();p=packet();wire=ledger_wire(m,p);wire['questionParts'][0]['reason']='🙂'*5000
    with pytest.raises(ValueError):m.resolve_ledger(wire,p)
    data=m.canonical_packet(p).to_dict();question='Q'*8192
    data['question']=question;data['draft']['questionParts'][0].update(start=0,end=len(question),quote=question)
    p=m.freeze_refs(freeze_packet(question,data['draft'],data['frames'],identity=data['identity']))
    wire=ledger_wire(m,p);other=copy.deepcopy(wire['questionParts'][0]);other['id']=m.PART_IDS[1]
    wire['questionParts'].append(other);wire['obligations'][0]['partIds'].append(m.PART_IDS[1])
    assert len(json.dumps(wire).encode())<16384
    with pytest.raises(ValueError):m.resolve_ledger(wire,p)


def test_duplicate_wire_keys_and_changed_packet_binding_fail_closed():
    m=api();p=packet();raw=json.dumps(ledger_wire(m,p));changed=raw.replace('"version": 1','"version": 1, "version": 1',1)
    assert raw!=changed
    with pytest.raises(ValueError):m.resolve_ledger(changed,p)
    data=p.to_dict();data['canonicalSha256']='0'*64
    from lab_runner.memory_benchmark.storage import encoded,sha
    raw=encoded(data);forged=m.RefsPacket(raw,sha(raw))
    with pytest.raises(ValueError):m.source_view(forged)


def test_legacy_benchmark_and_critic_packages_remain_byte_identical():
    root=Path(__file__).parents[2]
    manifest=json.loads((root/'tests/fixtures/answer_span_refs_legacy_hashes.json').read_text())
    actual={p.relative_to(root).as_posix() for family in manifest['families'] for p in (root/family).rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.json','.md','.txt')}
    assert actual==set(manifest['files'])
    for name,digest in manifest['files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest


def test_boolean_binding_cannot_alias_an_integer_version():
    m=api();p=packet();data=p.to_dict();data['binding']['version']=True
    from lab_runner.memory_benchmark.storage import encoded,sha
    raw=encoded(data)
    with pytest.raises(ValueError):m.canonical_packet(m.RefsPacket(raw,sha(raw)))


def test_cli_without_command_is_disabled_and_exposes_no_live_switch(capsys):
    cli=importlib.import_module('lab_runner.answer_span_refs.__main__')
    assert cli.main([])==0
    assert json.loads(capsys.readouterr().out)==dict(profileId=cli.PROFILE,enabled=False,executed=False,memoryDefault=False,sueDefault=False)
    with pytest.raises(SystemExit) as error:cli.main(['--live'])
    assert error.value.code==2
