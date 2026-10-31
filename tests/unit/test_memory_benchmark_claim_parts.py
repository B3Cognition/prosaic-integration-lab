"""Per-claim question membership has one owner; no future-claim prediction."""
from copy import deepcopy
import pytest
from jsonschema import Draft202012Validator
from lab_runner.memory_benchmark import generation as g, completeness_profile as review
from test_memory_benchmark_compact import packet
from test_memory_benchmark_canonical_links import wire_for as canonical_wire

PROFILE='compact-host-claim-parts-v1'

def wire_for(frozen):
    wire=canonical_wire(frozen)
    for c in wire['claims']:
        c['questionPartIds']=[p['id'] for p in wire['questionParts'] if c['id'] in p['claimIds']]
    for p in wire['questionParts']:del p['claimIds']
    return wire

def test_schema_makes_question_membership_required_on_each_claim_only():
    frozen=packet();schema=g.response_schema(frozen,profile=PROFILE)
    Draft202012Validator.check_schema(schema)
    claim=schema['properties']['claims']['items']
    assert claim['properties']['questionPartIds']['minItems']==1
    assert claim['properties']['questionPartIds']['uniqueItems'] is True
    assert 'questionPartIds' in claim['required']
    assert set(schema['properties']['questionParts']['items']['properties'])=={'id','quote','missingEvidenceIndices'}
    assert schema['properties']['evidence']['uniqueItems'] is True
    assert set(schema['properties']['frameReview']['items']['properties'])=={'frameId','unreferencedDisposition'}

@pytest.mark.parametrize('kwargs',[{},dict(castle=True),dict(empty=True)])
def test_encode_resolve_roundtrip_preserves_sources_claims_and_missing_evidence(kwargs):
    frozen=packet(**kwargs);before=deepcopy(frozen.to_dict())
    expected=g.resolve(g.encode_candidate(before['draft'],frozen,profile=g.CANONICAL_LINKS),frozen,profile=g.CANONICAL_LINKS)
    wire=g.encode_candidate(before['draft'],frozen,profile=PROFILE)
    assert all('claimIds' not in p for p in wire['questionParts'])
    assert all(c['questionPartIds'] for c in wire['claims'])
    assert g.resolve(wire,frozen,profile=PROFILE)==expected
    assert frozen.to_dict()==before

def test_later_claims_link_themselves_without_an_early_reverse_list():
    frozen=packet();wire=wire_for(frozen);part=wire['questionParts'][0]['id'];support=wire['evidence'][0]
    wire['claims']=[dict(id=f'c{i}',text=f'Distinct fixture interpretation {i}.',kind='inference',
                        evidenceIds=[support],questionPartIds=[part]) for i in range(1,9)]
    ids=[c['id'] for c in wire['claims']];wire['sections']['directAnswer']['claimIds']=ids
    actual=g.resolve(wire,frozen,profile=PROFILE)
    assert actual['questionParts'][0]['claimIds']==ids
    assert len(actual['claims'])==8 and all('questionPartIds' not in c for c in actual['claims'])
    assert [c['text'] for c in actual['claims']]==[c['text'] for c in wire['claims']]
    assert actual['frameReview'][0]['claimIds']==ids

def test_multi_part_membership_and_claim_array_order_are_preserved():
    frozen=packet();wire=wire_for(frozen);first=wire['questionParts'][0]['id']
    wire['questionParts'][0]['quote']='What'
    wire['questionParts'].append(dict(id='second',quote='the default',missingEvidenceIndices=[]))
    wire['claims'][0]['questionPartIds']=[first,'second']
    extra=deepcopy(wire['claims'][0]);extra.update(id='early',text='A separate fixture interpretation.')
    wire['claims'].insert(0,extra);ids=[c['id'] for c in wire['claims']]
    wire['sections']['directAnswer']['claimIds']=ids
    actual=g.resolve(wire,frozen,profile=PROFILE)
    assert [p['claimIds'] for p in actual['questionParts']]==[ids,ids]
    assert g.encode_candidate(actual,frozen,profile=PROFILE)==wire

@pytest.mark.parametrize('mutation',['missing','empty','duplicate-ref','unknown','duplicate-part','old-reverse',
                                    'unknown-quote','duplicate-quote','frame-reason','question','unknown-section'])
def test_invalid_declarations_fail_without_repair_or_mutation(mutation):
    frozen=packet();wire=wire_for(frozen)
    if mutation=='missing':del wire['claims'][0]['questionPartIds']
    if mutation=='empty':wire['claims'][0]['questionPartIds']=[]
    if mutation=='duplicate-ref':wire['claims'][0]['questionPartIds']*=2
    if mutation=='unknown':wire['claims'][0]['questionPartIds']=['foreign']
    if mutation=='duplicate-part':wire['questionParts'].append(deepcopy(wire['questionParts'][0]))
    if mutation=='old-reverse':wire['questionParts'][0]['claimIds']=[wire['claims'][0]['id']]
    if mutation=='unknown-quote':wire['claims'][0]['evidenceIds']=['quote-999']
    if mutation=='duplicate-quote':wire['evidence']*=2
    if mutation=='frame-reason':wire['frameReview'][0]['reason']='Not used.'
    if mutation=='question':wire['questionParts'][0]['quote']='not the frozen question'
    if mutation=='unknown-section':wire['sections']['directAnswer']['claimIds']=['foreign']
    before=deepcopy(wire)
    with pytest.raises(ValueError):g.resolve(wire,frozen,profile=PROFILE)
    assert wire==before

def test_wire_limit_scope_and_canonical_schema_are_unchanged():
    frozen=packet();wire=wire_for(frozen);before=deepcopy(review.ANSWER_SCHEMA)
    wire['claims'][0]['text']='x'*17000
    with pytest.raises(ValueError):g.resolve(wire,frozen,profile=PROFILE)
    forged=frozen.to_dict();forged['identity']['namespace']='foreign'
    payload=review._json(forged)
    from lab_runner.memory_benchmark.storage import sha
    with pytest.raises(ValueError):g.model_request(review.ReviewPacket(payload,sha(payload)),initial=True,profile=PROFILE)
    assert review.MAX_OUTPUT_BYTES==16384 and review.ANSWER_SCHEMA==before

def test_new_guidance_uses_explicit_per_claim_membership_without_predicting_ids():
    guidance=g.answer_guidance(PROFILE)
    assert 'questionPartIds' in guidance and 'Do not predict future claim IDs' in guidance
    assert 'questionPartIds' not in g.answer_guidance(g.CANONICAL_LINKS)
