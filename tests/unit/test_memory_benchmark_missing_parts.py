"""Missing evidence owns its question membership; canonical checks stay strict."""
from copy import deepcopy
import pytest
from jsonschema import Draft202012Validator
from lab_runner.memory_benchmark import generation as g, completeness_profile as review
from test_memory_benchmark_compact import packet

PROFILE='compact-host-missing-parts-v1'

def old_wire(frozen):
    return g.encode_candidate(frozen.to_dict()['draft'],frozen,profile=g.CLAIM_PARTS)

def wire_for(frozen):
    wire=old_wire(frozen)
    wire['missingEvidence']=[dict(text=text,questionPartIds=[p['id'] for p in wire['questionParts']
        if i in p['missingEvidenceIndices']]) for i,text in enumerate(wire['missingEvidence'])]
    for p in wire['questionParts']:del p['missingEvidenceIndices']
    return wire

def test_schema_has_one_explicit_owner_for_missing_relationships():
    schema=g.response_schema(packet(),profile=PROFILE);Draft202012Validator.check_schema(schema)
    assert set(schema['properties']['questionParts']['items']['properties'])=={'id','quote'}
    entry=schema['properties']['missingEvidence']['items']
    assert set(entry['properties'])=={'text','questionPartIds'}
    assert set(entry['required'])=={'text','questionPartIds'} and entry['additionalProperties'] is False
    assert entry['properties']['questionPartIds']['minItems']==1
    assert entry['properties']['questionPartIds']['uniqueItems'] is True

@pytest.mark.parametrize('kwargs',[{},dict(castle=True),dict(empty=True)])
def test_roundtrip_keeps_exact_claims_missing_strings_sources_and_status(kwargs):
    frozen=packet(**kwargs);before=deepcopy(frozen.to_dict());wire=wire_for(frozen)
    expected=g.resolve(old_wire(frozen),frozen,profile=g.CLAIM_PARTS)
    assert g.resolve(wire,frozen,profile=PROFILE)==expected
    assert g.encode_candidate(expected,frozen,profile=PROFILE)==wire
    assert frozen.to_dict()==before

def test_mixed_missing_only_part_and_shared_missing_entries_preserve_array_order():
    frozen=packet();wire=wire_for(frozen);pid=wire['questionParts'][0]['id']
    wire['questionParts'][0]['quote']='What'
    wire['questionParts'].append(dict(id='other',quote='the default'))
    wire['missingEvidence']=[dict(text='Exact Žluťoučký 😀\r\nunknown.',questionPartIds=['other',pid]),
                             dict(text='Another unavailable detail.',questionPartIds=['other'])]
    wire['status']='partial';before=deepcopy(wire)
    actual=g.resolve(wire,frozen,profile=PROFILE)
    assert actual['missingEvidence']==[m['text'] for m in wire['missingEvidence']]
    assert actual['questionParts'][0]['missingEvidenceIndices']==[0]
    assert actual['questionParts'][1]['missingEvidenceIndices']==[0,1]
    assert actual['questionParts'][1]['claimIds']==[]
    assert actual['claims'][0]['text']==wire['claims'][0]['text'] and actual['status']=='partial'
    assert wire==before
    # Reverse canonical lists are valid; encoding declares host array order only.
    actual['questionParts'][1]['missingEvidenceIndices']=[1,0]
    encoded=g.encode_candidate(actual,frozen,profile=PROFILE)
    resolved=g.resolve(encoded,frozen,profile=PROFILE)
    assert resolved['questionParts'][1]['missingEvidenceIndices']==[0,1]
    assert resolved['missingEvidence']==actual['missingEvidence']

@pytest.mark.parametrize('mutation',['missing-membership','empty-membership','duplicate-membership','foreign-membership',
    'blank-text','missing-text','old-string','numeric-reverse','claim-reverse','duplicate-part','invented-offset',
    'answered-with-missing','no-part-disposition','orphan-claim','unsupported-absence','absence-wrong-section',
    'absence-missing-other-part'])
def test_malformed_ownership_and_canonical_absence_guards_reject_without_repair(mutation):
    frozen=packet(empty=True);wire=wire_for(frozen);pid=wire['questionParts'][0]['id']
    assert g.resolve(wire,frozen,profile=PROFILE)['status']=='abstained'
    if mutation=='missing-membership':del wire['missingEvidence'][0]['questionPartIds']
    if mutation=='empty-membership':wire['missingEvidence'][0]['questionPartIds']=[]
    if mutation=='duplicate-membership':wire['missingEvidence'][0]['questionPartIds']=[pid,pid]
    if mutation=='foreign-membership':wire['missingEvidence'][0]['questionPartIds']=['foreign']
    if mutation=='blank-text':wire['missingEvidence'][0]['text']=' '
    if mutation=='missing-text':del wire['missingEvidence'][0]['text']
    if mutation=='old-string':wire['missingEvidence']=['Unowned unknown.']
    if mutation=='numeric-reverse':wire['questionParts'][0]['missingEvidenceIndices']=[0]
    if mutation=='claim-reverse':wire['questionParts'][0]['claimIds']=[]
    if mutation=='duplicate-part':wire['questionParts'].append(deepcopy(wire['questionParts'][0]))
    if mutation=='invented-offset':wire['questionParts'][0]['start']=0
    if mutation=='answered-with-missing':wire['status']='answered'
    if mutation=='no-part-disposition':wire['missingEvidence']=[]
    if mutation in ['orphan-claim','unsupported-absence','absence-wrong-section','absence-missing-other-part']:
        wire['claims']=[dict(id='c',text='The supplied bodies do not identify the default.',kind='absence',
                             evidenceIds=[],questionPartIds=[pid])]
        wire['sections']['limitations']['claimIds']=['c']
        if mutation=='orphan-claim':wire['claims'][0]['questionPartIds']=[]
        if mutation=='unsupported-absence':wire['missingEvidence']=[]
        if mutation=='absence-wrong-section':
            wire['sections']['limitations']['claimIds']=[];wire['sections']['directAnswer']['claimIds']=['c']
        if mutation=='absence-missing-other-part':
            wire['questionParts'][0]['quote']='What'
            wire['questionParts'].append(dict(id='other',quote='the default'))
            wire['missingEvidence'][0]['questionPartIds']=['other']
    before=deepcopy(wire)
    with pytest.raises(ValueError):g.resolve(wire,frozen,profile=PROFILE)
    assert wire==before

def test_valid_unsupported_absence_stays_linked_limited_and_abstained():
    frozen=packet(empty=True);wire=wire_for(frozen);pid=wire['questionParts'][0]['id']
    wire['claims']=[dict(id='c',text='The supplied bodies do not identify the default.',kind='absence',
                         evidenceIds=[],questionPartIds=[pid])]
    wire['sections']['limitations']['claimIds']=['c']
    actual=g.resolve(wire,frozen,profile=PROFILE)
    assert actual['status']=='abstained' and actual['questionParts'][0]['claimIds']==['c']
    assert actual['questionParts'][0]['missingEvidenceIndices']==[0]

def test_old_dangling_wire_is_rejected_in_both_modes_never_filled_in():
    frozen=packet(empty=True);old=old_wire(frozen);old['missingEvidence']=[]
    with pytest.raises(ValueError,match='missingEvidence indices'):g.resolve(old,frozen,profile=g.CLAIM_PARTS)
    before=deepcopy(old)
    with pytest.raises(ValueError):g.resolve(old,frozen,profile=PROFILE)
    assert old==before

def test_guidance_declares_memberships_not_numeric_predictions():
    text=g.answer_guidance(PROFILE)
    assert 'missingEvidence entries have ONLY text and questionPartIds' in text
    assert 'Do not predict missingEvidenceIndices' in text
    assert 'Each questionParts entry has ONLY id and quote' in text
    assert 'Each questionParts entry has ONLY id, quote and missingEvidenceIndices' not in text

def test_raw_and_expanded_limits_and_scope_stay_strict():
    frozen=packet(empty=True);wire=wire_for(frozen)
    wire['missingEvidence'][0]['text']='x'*17000
    with pytest.raises(ValueError,match='JSON byte limit'):g.resolve(wire,frozen,profile=PROFILE)
    frozen=packet();wire=wire_for(frozen);wire['claims'][0]['text']='x'*17000
    with pytest.raises(ValueError,match='JSON byte limit'):g.resolve(wire,frozen,profile=PROFILE)
    forged=frozen.to_dict();forged['identity']['namespace']='foreign'
    raw=review._json(forged)
    from lab_runner.memory_benchmark.storage import sha
    with pytest.raises(ValueError):g.model_request(review.ReviewPacket(raw,sha(raw)),initial=True,profile=PROFILE)

def test_short_missing_parts_wire_cannot_expand_past_canonical_limit():
    from lab_runner.memory_benchmark.workflow import initial_packet
    import json
    original=packet().to_dict();frame=original['frames']['frame'];span=frame['bodySpans'][0]
    text='A'*18000;frame['display']=frame['display'][:span['start']]+text
    span['end']=len(frame['display']);frame['metadata']['endChar']=frame['metadata']['startChar']+len(text)
    frozen=initial_packet(original['question'],original['frames'],original['identity'])
    wire=dict(questionParts=[dict(id='p',quote=original['question'])],
        claims=[dict(id='c',text='The shown text contains a long fixture statement.',kind='observation',
                     evidenceIds=['quote-1'],questionPartIds=['p'])],evidence=['quote-1'],
        sections={k:dict(claimIds=['c'] if k=='directAnswer' else [],reason='No additional statement.')
                  for k in ['directAnswer','supportingDetails','chronologyAndBoundaries','limitations']},
        frameReview=[dict(frameId='frame',unreferencedDisposition='insufficient')],
        citations=[],missingEvidence=[],status='answered')
    assert len(json.dumps(wire).encode())<16384
    before=deepcopy(wire)
    with pytest.raises(ValueError,match='JSON byte limit'):g.resolve(wire,frozen,profile=PROFILE)
    assert wire==before
