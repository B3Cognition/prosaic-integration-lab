"""The optional wire profile removes arithmetic, never the canonical gate."""
from copy import deepcopy
import json

import pytest

from lab_runner.memory_benchmark import generation as g, completeness_profile as review
from test_memory_benchmark_compact import packet

PROFILE = 'compact-host-resolved-v1'

def host_wire(frozen):
    wire = g.encode_candidate(frozen.to_dict()['draft'], frozen)
    for part in wire['questionParts']:
        del part['start']; del part['end']
    for frame in wire['frameReview']:
        frame['unreferencedDisposition'] = 'insufficient' if frame['disposition'] == 'used' else frame['disposition']
        del frame['disposition']; del frame['claimIds']
    return wire

@pytest.mark.parametrize('castle', [False, True])
def test_host_offsets_and_frame_links_reach_unchanged_validator(castle):
    frozen = packet(castle=castle)
    wire = host_wire(frozen)
    schema_before = deepcopy(review.ANSWER_SCHEMA)
    actual = g.resolve(wire, frozen, profile=PROFILE)
    assert actual == frozen.to_dict()['draft']
    assert actual['questionParts'][0]['start'] == 0
    assert actual['questionParts'][0]['end'] == 20
    assert actual['frameReview'][0]['disposition'] == 'used'
    assert actual['frameReview'][0]['claimIds'] == [actual['claims'][0]['id']]
    assert review.validate_candidate(actual, frozen) == actual
    assert review.ANSWER_SCHEMA == schema_before

@pytest.mark.parametrize('question,quote,start,end', [('Žluťoučký 😀: what?', '😀: what?', 10, 18), ('ababa', 'ababa', 0, 5)])
def test_offsets_use_exact_unicode_character_positions(question, quote, start, end):
    base = packet(); data = base.to_dict(); draft = data['draft']
    draft['questionParts'][0].update(start=0, end=len(question), quote=question)
    frozen = review.freeze_packet(question, draft, data['frames'], identity=data['identity'])
    wire = host_wire(frozen); wire['questionParts'][0]['quote'] = quote
    part = g.resolve(wire, frozen, profile=PROFILE)['questionParts'][0]
    assert (part['start'], part['end'], part['quote']) == (start, end, quote)

@pytest.mark.parametrize('question,quote', [('ababa','aba'), ('foo foo','foo'), ('café','cafe\u0301'), ('what?','What?'), ('what?','foreign'), ('what?','')])
def test_question_spans_fail_closed_on_ambiguity_or_nonexact_text(question, quote):
    base = packet(); data = base.to_dict(); draft = data['draft']
    draft['questionParts'][0].update(start=0,end=len(question),quote=question)
    frozen = review.freeze_packet(question,draft,data['frames'],identity=data['identity'])
    wire=host_wire(frozen);wire['questionParts'][0]['quote']=quote
    with pytest.raises(ValueError):g.resolve(wire,frozen,profile=PROFILE)

@pytest.mark.parametrize('mutation', ['offset', 'manual-links', 'manual-disposition', 'unknown-evidence', 'foreign-quote', 'foreign-frame', 'missing-frame', 'duplicate-evidence', 'duplicate-frame'])
def test_canonical_scope_coverage_and_reference_checks_still_reject(mutation):
    frozen=packet();wire=host_wire(frozen)
    if mutation=='offset':wire['questionParts'][0]['end']=62
    if mutation=='manual-links':wire['frameReview'][0]['claimIds']=[]
    if mutation=='manual-disposition':wire['frameReview'][0]['disposition']='used'
    if mutation=='unknown-evidence':wire['claims'][0]['evidenceIds']=['foreign']
    if mutation=='foreign-quote':wire['evidence'][0]['quoteId']='foreign'
    if mutation=='foreign-frame':wire['frameReview'][0]['frameId']='foreign'
    if mutation=='missing-frame':wire['frameReview']=[]
    if mutation=='duplicate-evidence':wire['evidence'].append(deepcopy(wire['evidence'][0]))
    if mutation=='duplicate-frame':wire['frameReview'].append(deepcopy(wire['frameReview'][0]))
    with pytest.raises(ValueError):g.resolve(wire,frozen,profile=PROFILE)

def test_unreferenced_frames_keep_explicit_nonused_dispositions():
    base=packet();data=base.to_dict();extra=deepcopy(data['frames']['frame']);frames={**data['frames'],'unreferenced':extra}
    draft=data['draft'];draft['frameReview'].append(dict(frameId='unreferenced',disposition='duplicate',claimIds=[],reason='Repeated source.'))
    frozen=review.freeze_packet(data['question'],draft,frames,identity=data['identity'])
    wire=host_wire(frozen)
    result=g.resolve(wire,frozen,profile=PROFILE)
    assert result['frameReview'][1]==dict(frameId='unreferenced',disposition='duplicate',claimIds=[],reason='Repeated source.')

def test_new_profile_request_and_draft_roundtrip_preserve_all_sources():
    frozen=packet();old=g.model_request(frozen,initial=True,profile=g.QUESTION_FOCUSED)
    new=g.model_request(frozen,initial=True,profile=PROFILE)
    assert new['packet']==old['packet'] and new['packetSha256']==old['packetSha256']
    assert new['profileId']==PROFILE and new['responseSchemaOrder']!=old['responseSchemaOrder']
    draft=g.model_request(frozen,initial=False,profile=PROFILE)['packet']['draft']
    assert g.resolve(draft,frozen,profile=PROFILE)==frozen.to_dict()['draft']
    assert 'start' not in draft['questionParts'][0] and 'claimIds' not in draft['frameReview'][0]
    assert g.encode_candidate(frozen.to_dict()['draft'],frozen,profile=PROFILE)==draft

def test_mutating_generated_schema_cannot_mutate_canonical_validator():
    before=deepcopy(review.ANSWER_SCHEMA)
    schema=g.response_schema(packet(),profile=PROFILE)
    quote=schema['properties']['questionParts']['items']['properties']['quote']
    try:
        quote['type']='integer'
        assert review.ANSWER_SCHEMA==before
    finally:
        quote['type']='string'
