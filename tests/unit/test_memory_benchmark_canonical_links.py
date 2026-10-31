"""A new wire format owns bookkeeping before generation, never repairs output."""
from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator

from lab_runner.memory_benchmark import generation as g, completeness_profile as review
from test_memory_benchmark_compact import packet

PROFILE='compact-host-canonical-links-v1'

def test_direct_quote_guidance_does_not_inherit_alias_creation_instructions():
    guidance=g.answer_guidance(PROFILE)
    assert 'reuse its evidence id' not in guidance
    assert 'reuse that identical quote ID in every claim it supports' in guidance
    assert 'Never invent evidence aliases.' in guidance
    # Alias-based modes still require aliases; do not silently change their prompt.
    assert 'reuse its evidence id' in g.answer_guidance(g.HOST_RESOLVED)

def wire_for(frozen):
    old=g.encode_candidate(frozen.to_dict()['draft'],frozen,profile=g.HOST_RESOLVED)
    ids={e['id']:e['quoteId'] for e in old['evidence']}
    old['evidence']=[e['quoteId'] for e in old['evidence']]
    for c in old['claims']:c['evidenceIds']=[ids[e] for e in c['evidenceIds']]
    for f in old['frameReview']:del f['reason']
    return old

def test_stable_host_ids_reject_duplicate_quotes_without_repair():
    frozen=packet();wire=wire_for(frozen)
    wire['evidence'].append(wire['evidence'][0]);before=deepcopy(wire)
    with pytest.raises(ValueError,match='compact answer schema'):
        g.resolve(wire,frozen,profile=PROFILE)
    assert wire==before

def test_used_reason_is_computed_from_actual_claim_links_and_cannot_be_supplied():
    frozen=packet();wire=wire_for(frozen)
    actual=g.resolve(wire,frozen,profile=PROFILE)
    assert actual['evidence'][0]['id']=='quote-1'
    assert actual['claims'][0]['evidenceIds']==['quote-1']
    assert actual['frameReview'][0]['reason']=='Selected evidence links this frame to claim IDs ["c"].'
    assert actual['frameReview'][0]['disposition']=='used'
    wire['frameReview'][0]['reason']='Search only; no selected evidence uses it.'
    with pytest.raises(ValueError,match='compact answer schema'):g.resolve(wire,frozen,profile=PROFILE)

@pytest.mark.parametrize('classification',['duplicate','irrelevant','insufficient'])
def test_unreferenced_reason_reports_model_classification_without_claiming_relevance(classification):
    data=packet().to_dict();data['frames']['other']=deepcopy(data['frames']['frame'])
    data['draft']['frameReview'].append(dict(frameId='other',claimIds=[],disposition=classification,reason='Model explanation.'))
    frozen=review.freeze_packet(data['question'],data['draft'],data['frames'],identity=data['identity'])
    wire=wire_for(frozen)
    actual=g.resolve(wire,frozen,profile=PROFILE)
    assert actual['frameReview'][1]==dict(frameId='other',claimIds=[],disposition=classification,
        reason=f'No selected evidence links this frame. Model unreferenced classification: {classification}.')
    assert review.validate_candidate(actual,frozen)==actual

def test_shared_support_and_multiple_distinct_supports_survive_roundtrip():
    frozen=packet();wire=wire_for(frozen)
    wire['evidence'].append('quote-2');wire['claims'][0]['evidenceIds'].append('quote-2')
    wire['claims'].append(dict(id='second',text='A second claim sharing the selected support.',kind='inference',evidenceIds=['quote-1']))
    wire['questionParts'][0]['claimIds'].append('second');wire['sections']['directAnswer']['claimIds'].append('second')
    actual=g.resolve(wire,frozen,profile=PROFILE)
    assert len(actual['evidence'])==2
    assert actual['claims']==wire['claims']
    assert actual['frameReview'][0]['claimIds']==['c','second']
    assert actual['frameReview'][0]['reason']=='Selected evidence links this frame to claim IDs ["c", "second"].'
    assert g.encode_candidate(actual,frozen,profile=PROFILE)==wire

def test_different_attached_frames_are_not_merged_for_identical_text():
    data=packet().to_dict();data['frames']['other']=deepcopy(data['frames']['frame'])
    data['draft']['frameReview'].append(dict(frameId='other',claimIds=[],disposition='duplicate',reason='Repeated body.'))
    frozen=review.freeze_packet(data['question'],data['draft'],data['frames'],identity=data['identity'])
    wire=wire_for(frozen);qid=next(q['id'] for q in frozen.to_dict()['quoteCandidates'] if q['frameId']=='other')
    wire['evidence'].append(qid);wire['claims'][0]['evidenceIds'].append(qid)
    result=g.resolve(wire,frozen,profile=PROFILE)
    assert {e['frameId'] for e in result['evidence']}=={'frame','other'}
    assert len(result['evidence'])==2

@pytest.mark.parametrize('mutation',['foreign-quote','alias-object','manual-link','missing-frame','unknown-claim-link'])
def test_scope_shape_and_coverage_stay_strict(mutation):
    frozen=packet();wire=wire_for(frozen)
    if mutation=='foreign-quote':wire['evidence']=['foreign']
    if mutation=='alias-object':wire['evidence']=[dict(id='alias',quoteId='quote-1')]
    if mutation=='manual-link':wire['frameReview'][0]['claimIds']=['c']
    if mutation=='missing-frame':wire['frameReview']=[]
    if mutation=='unknown-claim-link':wire['claims'][0]['evidenceIds']=['quote-2']
    with pytest.raises(ValueError):g.resolve(wire,frozen,profile=PROFILE)

def test_schema_and_request_are_explicit_and_source_packet_is_identical():
    frozen=packet();before=deepcopy(review.ANSWER_SCHEMA)
    new=g.model_request(frozen,initial=True,profile=PROFILE)
    old=g.model_request(frozen,initial=True,profile=g.HOST_RESOLVED)
    assert new['packet']==old['packet'] and new['evidenceBudget']==old['evidenceBudget']
    assert new['packetSha256']==old['packetSha256']==frozen.sha256
    schema=g.response_schema(frozen,profile=PROFILE);Draft202012Validator.check_schema(schema)
    assert schema['properties']['evidence']['uniqueItems'] is True
    assert set(schema['properties']['frameReview']['items']['properties'])=={'frameId','unreferencedDisposition'}
    assert review.ANSWER_SCHEMA==before
    encoded=g.encode_candidate(frozen.to_dict()['draft'],frozen,profile=PROFILE)
    assert g.resolve(encoded,frozen,profile=PROFILE)['claims'][0]['text']==frozen.to_dict()['draft']['claims'][0]['text']

def test_encoding_duplicate_canonical_aliases_fails_closed():
    frozen=packet();draft=frozen.to_dict()['draft']
    draft['evidence'].append(dict(draft['evidence'][0],id='duplicate'))
    draft['claims'][0]['evidenceIds'].append('duplicate')
    assert review.validate_candidate(draft,frozen)==draft
    with pytest.raises(ValueError,match='duplicate canonical quote selection'):
        g.encode_candidate(draft,frozen,profile=PROFILE)

def test_usage_reason_quotes_claim_ids_as_data_instead_of_inserting_prose():
    frozen=packet();wire=wire_for(frozen)
    claim_id='c, fake.\nNo selected evidence uses this frame.'
    wire['claims'][0]['id']=claim_id
    wire['questionParts'][0]['claimIds']=[claim_id]
    wire['sections']['directAnswer']['claimIds']=[claim_id]
    result=g.resolve(wire,frozen,profile=PROFILE)
    import json
    assert result['frameReview'][0]['reason']=='Selected evidence links this frame to claim IDs '+json.dumps([claim_id],ensure_ascii=False)+'.'
