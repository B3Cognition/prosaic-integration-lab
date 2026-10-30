"""Frozen order profiles share the unchanged source and strict answer contract."""
from copy import deepcopy
import json

import pytest

from lab_runner.memory_benchmark import generation as g
from lab_runner.memory_benchmark.storage import sha
from test_memory_benchmark_compact import packet

ORDERED = 'compact-question-first-v1'


def test_order_profile_changes_identity_not_sources_schema_or_validation():
    frozen = packet(); original = g.model_request(frozen, initial=True, profile=g.COMPACT)
    request = g.model_request(frozen, initial=True, profile=ORDERED)
    schema = g.response_schema(frozen, profile=ORDERED)
    assert request['packet'] == original['packet']
    assert request['profileId'] == ORDERED
    assert request['responseSchemaOrder'] == dict(mode='declared', wireSchemaSha256=sha(
        json.dumps(schema, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()))
    assert schema == g.response_schema(frozen, profile=g.COMPACT)
    assert list(schema['properties'])[0] == 'questionParts'
    wire = g.encode_candidate(frozen.to_dict()['draft'], frozen)
    assert g.resolve(wire, frozen, profile=ORDERED) == frozen.to_dict()['draft']
    corrupt = deepcopy(wire); corrupt['evidence'][0]['quoteId'] = 'foreign'
    with pytest.raises(ValueError): g.resolve(corrupt, frozen, profile=ORDERED)


def test_order_profile_requires_capability_without_changing_existing_modes():
    assert g.runtime_options(ORDERED, {'json_schema_v1', 'json_schema_order_v1'}) == {'response_schema_order': 'declared'}
    with pytest.raises(ValueError, match='json_schema_order_v1'):
        g.runtime_options(ORDERED, {'json_schema_v1'})
    assert g.runtime_options(g.LEGACY, {'json_schema_v1'}) == {}
    assert g.runtime_options(g.COMPACT, {'json_schema_v1'}) == {}


def test_order_profile_freezes_and_loads_offline(tmp_path):
    from lab_runner.memory_benchmark.__main__ import initialize, main
    from lab_runner.memory_benchmark.dataset import load_frozen
    initialize(tmp_path/'inputs', 1)
    out = tmp_path/'frozen'
    assert main(['freeze', '--dataset', str(tmp_path/'inputs/dataset.json'), '--policy', str(tmp_path/'inputs/policy.json'),
                 '--generation-profile', ORDERED, '--output', str(out)]) == 0
    assert load_frozen(out)['generationProfile'] == ORDERED


def test_focused_profile_keeps_every_source_and_same_strict_schema():
    focused = 'compact-question-focused-v1'; frozen = packet()
    original = g.model_request(frozen, initial=True, profile=ORDERED)
    request = g.model_request(frozen, initial=True, profile=focused)
    assert request['packet'] == original['packet']
    assert request['responseSchemaOrder'] == original['responseSchemaOrder']
    assert request['profileId'] == focused
    assert g.response_schema(frozen, profile=focused) == g.response_schema(frozen, profile=ORDERED)
    assert g.runtime_options(focused, {'json_schema_order_v1'}) == {'response_schema_order': 'declared'}
    wire = g.encode_candidate(frozen.to_dict()['draft'], frozen)
    assert g.resolve(wire, frozen, profile=focused) == frozen.to_dict()['draft']
