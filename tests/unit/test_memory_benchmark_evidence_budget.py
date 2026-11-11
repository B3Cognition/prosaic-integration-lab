"""Advisory selection costs never truncate or relax canonical answers."""
from copy import deepcopy
import json

import pytest

from lab_runner.memory_benchmark import generation as g, completeness_profile as review
from test_memory_benchmark_compact import packet


def encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(',', ':')).encode('utf-8')


def test_host_budget_reports_exact_expansion_costs_without_filtering_sources():
    frozen = packet(castle=True)
    old = g.model_request(frozen, initial=True, profile=g.QUESTION_FOCUSED)
    request = g.model_request(frozen, initial=True, profile=g.HOST_RESOLVED)
    assert request['packet'] == old['packet']
    budget = request['evidenceBudget']
    assert budget['canonicalMaxBytes'] == review.MAX_OUTPUT_BYTES == 16384
    data, quotes, citations, _ = g._indexes(frozen)
    assert set(budget['quoteBytesWithEmptyEvidenceId']) == set(quotes)
    assert set(budget['citationBytes']) == set(citations)
    for qid, quote in quotes.items():
        for eid in ['e', 'Ž😀"\\']:
            cost = budget['quoteBytesWithEmptyEvidenceId'][qid] + len(encoded(eid)) - 2
            assert cost == len(encoded(dict(quote, id=eid)))
    assert budget['citationBytes'] == {cid:len(encoded(c)) for cid,c in citations.items()}
    assert 'evidenceBudget' not in old


def test_multiple_selected_supports_are_preserved_without_a_count_cap_or_pruning():
    frozen = packet()
    wire = g.encode_candidate(frozen.to_dict()['draft'], frozen, profile=g.HOST_RESOLVED)
    wire['evidence'].append(dict(id='second', quoteId='quote-2'))
    wire['claims'][0]['evidenceIds'].append('second')
    schema = g.response_schema(frozen, profile=g.HOST_RESOLVED)
    assert 'maxItems' not in schema['properties']['evidence']
    actual = g.resolve(wire, frozen, profile=g.HOST_RESOLVED)
    assert actual['claims'] == wire['claims']
    assert len(actual['evidence']) == 2
    assert actual['evidence'][1]['quote'] == frozen.to_dict()['quoteCandidates'][1]['quote']
    assert review.validate_candidate(actual, frozen) == actual
    assert 'evidenceBudget' in g.model_request(frozen, initial=False, profile=g.HOST_RESOLVED)


def test_twelve_distinct_supported_facts_survive_with_exact_evidence_and_no_truncation():
    from lab_runner.memory_benchmark.workflow import initial_packet
    from lab_runner.memory_benchmark.fixture import fixture_answer
    data = packet().to_dict()
    facts = [f'Feature {i} remains disabled by default.' for i in range(12)]
    frame = data['frames']['frame']
    frame['display'] = '\n\n'.join(facts)
    frame['bodySpans'] = [dict(start=0, end=len(frame['display']))]
    frame['metadata'].update(startChar=0, endChar=len(frame['display']))
    initial = initial_packet('What are all twelve feature defaults?', data['frames'], data['identity'])
    draft = fixture_answer(initial.to_dict())
    draft['claims'] = [dict(id=f'c{i}', text=text, kind='observation', evidenceIds=[f'e{i}'])
                       for i,text in enumerate(facts)]
    draft['evidence'] = [dict(q, id=f'e{i}') for i,q in enumerate(initial.to_dict()['quoteCandidates'])]
    ids = [c['id'] for c in draft['claims']]
    draft['questionParts'][0]['claimIds'] = ids
    draft['sections']['directAnswer']['claimIds'] = ids
    draft['frameReview'][0]['claimIds'] = ids
    frozen = review.freeze_packet(initial.to_dict()['question'], draft, data['frames'], identity=data['identity'])
    wire = g.encode_candidate(draft, frozen, profile=g.HOST_RESOLVED)
    actual = g.resolve(wire, frozen, profile=g.HOST_RESOLVED)
    assert actual == draft
    assert [c['text'] for c in actual['claims']] == facts
    assert [e['quote'] for e in actual['evidence']] == facts


def test_budget_does_not_weaken_limit_or_repair_overselected_evidence():
    frozen = packet()
    wire = g.encode_candidate(frozen.to_dict()['draft'], frozen, profile=g.HOST_RESOLVED)
    wire['evidence'] = [dict(id=f'e{i}', quoteId='quote-1') for i in range(90)]
    wire['claims'][0]['evidenceIds'] = [e['id'] for e in wire['evidence']]
    original = deepcopy(wire)
    assert len(encoded(wire)) < 16384
    with pytest.raises(ValueError, match='JSON byte limit'):
        g.resolve(wire, frozen, profile=g.HOST_RESOLVED)
    assert wire == original
    assert review.MAX_OUTPUT_BYTES == 16384


def test_empty_indexes_and_legacy_guidance_stay_compatible():
    frozen = packet(empty=True)
    request = g.model_request(frozen, initial=True, profile=g.HOST_RESOLVED)
    assert request['evidenceBudget']['quoteBytesWithEmptyEvidenceId'] == {}
    assert request['evidenceBudget']['citationBytes'] == {}
    for profile in (g.LEGACY, g.COMPACT, g.QUESTION_FIRST, g.QUESTION_FOCUSED):
        assert g.answer_guidance(profile) == g.ANSWER
        assert 'evidenceBudget' not in g.model_request(frozen, initial=True, profile=profile)
