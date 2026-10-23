"""Synthetic units and public report projection cannot claim model qualification."""
import json
import pytest


def test_synthetic_counter_counts_exact_native_utf8_envelope():
    from prosaic_integration_lab.context_counter import SyntheticByteCounter
    counter = SyntheticByteCounter()
    request = {'model':'test-model-balanced','messages':[{'role':'user','content':'ž'}],
        'max_tokens':20,'tools':[{'description':'schema overhead'}]}
    assert counter.count_tokens(request) == len(json.dumps(request,allow_nan=False).encode('utf-8'))
    assert request['messages'][0]['content']=='ž'


@pytest.mark.parametrize('model', ['qwen-local','frontier-hosted','test-model-balanced-wrong'])
def test_fixture_counter_registry_refuses_live_or_unknown_models(model):
    from prosaic_integration_lab.context_counter import synthetic_registry
    with pytest.raises(ValueError): synthetic_registry(model)


def test_ordinary_and_interpreter_counters_have_distinct_model_identities():
    from prosaic_integration_lab.context_counter import synthetic_registry,counter_identity
    left=synthetic_registry('test-model-balanced')
    right=synthetic_registry('test-model-strong')
    assert counter_identity('test-model-balanced')!=counter_identity('test-model-strong')
    assert left.resolve(counter_identity('test-model-balanced')).descriptor.model=='test-model-balanced'
    assert right.resolve(counter_identity('test-model-strong')).descriptor.model=='test-model-strong'


def test_report_projection_excludes_extra_fields_and_labels_synthetic():
    from prosaic_integration_lab.views import public_context_report
    source={'mode':'omitOldestTurns','inputTokens':100,'inputCapacityTokens':200,
        'retainedTurnCount':2,'omittedTurnCount':1,
        'omittedRange':{'startTurn':1,'endTurnExclusive':2},
        'prompt':'private-sentinel','counterException':'private-sentinel',
        'sourceHistoryDigest':'f'*64,'counterIdentity':'internal-counter'}
    view=public_context_report(source)
    assert view=={'mode':'omitOldestTurns','inputTokens':100,'inputCapacityTokens':200,
        'retainedTurnCount':2,'omittedTurnCount':1,
        'omittedRange':{'startTurn':1,'endTurnExclusive':2},'evidenceKind':'synthetic'}
    assert 'private-sentinel' not in json.dumps(view)
    assert 'internal-counter' not in json.dumps(view)


@pytest.mark.parametrize('change', [{'inputTokens':True},{'inputTokens':201},
    {'omittedRange':{'startTurn':1,'endTurnExclusive':999999}},
    {'mode':'<script>alert(1)</script>'}])
def test_report_projection_rejects_malformed_numbers_or_ranges(change):
    from prosaic_integration_lab.views import public_context_report
    source={'mode':'omitOldestTurns','inputTokens':100,'inputCapacityTokens':200,
        'retainedTurnCount':2,'omittedTurnCount':1,
        'omittedRange':{'startTurn':1,'endTurnExclusive':2}}
    with pytest.raises(ValueError):public_context_report({**source,**change})
