from copy import deepcopy
import json
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator


def inputs():
    rows = [
        dict(recordId='readiness-new', factId='readiness', authority='inspector', revision=2, value=95),
        dict(recordId='readiness-old', factId='readiness', authority='inspector', revision=1, value=10),
        dict(recordId='alerts-observer', factId='alerts', authority='observer', revision=99, value=0),
        dict(recordId='latency-current', factId='latency', authority='inspector', revision=3, value=11),
    ]
    return dict(authority='inspector', required_facts=['readiness', 'alerts', 'reliability'],
                record_index=[{k: row[k] for k in ('recordId', 'factId', 'authority', 'revision')} for row in rows],
                records=rows[1:], index_complete=True), rows


def build(**changes):
    from lab_runner.memory.evidence import build_summary
    data, _ = inputs()
    return build_summary(**(data | changes))


def test_absence_is_distinct_from_indexed_but_unread_evidence():
    result = build()
    facts = {row['factId']: row for row in result['facts']}
    assert facts['alerts'] == dict(factId='alerts', status='absent', recordId=None, revision=None, value=None)
    assert facts['reliability']['status'] == 'absent'
    assert facts['readiness'] == dict(factId='readiness', status='unread', recordId='readiness-new', revision=2, value=None)
    assert facts['latency'] == dict(factId='latency', status='verified', recordId='latency-current', revision=3, value=11)
    assert result['requiredFacts'] == ['alerts', 'readiness', 'reliability']
    assert result['version'] == 1 and result['indexComplete'] is True
    assert result['authority'] == 'inspector'


def test_authority_precedes_revision_and_excluded_records_remain_visible():
    data, rows = inputs()
    result = build(records=rows)
    assert {r['factId']: r['status'] for r in result['facts']}['readiness'] == 'verified'
    assert result['excludedRecords'] == [dict(recordId='alerts-observer', reason='wrongAuthority'),
                                         dict(recordId='readiness-old', reason='superseded')]
    assert result['records'] == rows
    result['records'][0]['value'] = 999
    assert rows[0]['value'] == 95


def test_schema_encodes_all_three_states_and_no_decision_target():
    result = build()
    schema = json.loads(files('lab_runner.memory').joinpath('data/evidence-summary.schema.json').read_text())
    assert not list(Draft202012Validator(schema).iter_errors(result))
    bad = deepcopy(result)
    next(row for row in bad['facts'] if row['status'] == 'unread')['value'] = 95
    assert list(Draft202012Validator(schema).iter_errors(bad))
    assert not {'decision', 'conditions', 'expected', 'approved', 'insufficient'} & set(result)
    assert 'recordIndex' not in result


def test_empty_complete_index_reports_policy_scope_absence_without_fabrication():
    result = build(record_index=[], records=[])
    assert all(row['status'] == 'absent' for row in result['facts'])
    assert result['excludedRecords'] == result['records'] == []


def test_summary_order_is_deterministic_except_preserved_raw_fetch_order():
    data, _ = inputs()
    first = build()
    other = build(record_index=list(reversed(data['record_index'])), required_facts=list(reversed(data['required_facts'])))
    assert first == other


@pytest.mark.parametrize('complete', [False, None, 1, 'true'])
def test_partial_or_untrusted_index_completeness_cannot_prove_absence(complete):
    with pytest.raises(ValueError):
        build(index_complete=complete)


@pytest.mark.parametrize('field,value', [('authority', 'observer'), ('factId', 'foreign'), ('revision', 42),
                                       ('recordId', 'foreign-source')])
def test_fetched_identity_must_match_the_public_index(field, value):
    data, _ = inputs()
    data['records'][0][field] = value
    with pytest.raises(ValueError):
        build(**data)


@pytest.mark.parametrize('value', [True, float('nan'), float('inf'), '95'])
def test_non_numeric_and_nonfinite_fetched_values_reject(value):
    data, _ = inputs()
    data['records'][0]['value'] = value
    with pytest.raises(ValueError):
        build(**data)


def test_duplicate_and_ambiguous_sources_fail_closed():
    data, rows = inputs()
    with pytest.raises(ValueError):
        build(record_index=data['record_index'] + [data['record_index'][0]])
    with pytest.raises(ValueError):
        build(records=[rows[0], rows[0]])
    with pytest.raises(ValueError):
        build(record_index=data['record_index'] + [data['record_index'][0] | dict(recordId='tied-latest')])


def test_rollout_adapter_reads_only_public_task_index_and_fetched_records():
    from memory_helpers import development
    from lab_runner.memory.evidence import summarize_lookup
    case, _, _, _ = development()
    class PublicOnly(dict):
        def __getitem__(self, key):
            assert key in {'task', 'recordIndex'}, key
            return super().__getitem__(key)
    request = PublicOnly(case | dict(expected='PRIVATE-CANARY', recalledEpisodes='PRIVATE-CANARY', requiredRecords='PRIVATE-CANARY'))
    rows = [case['records'][key] for key in case['requiredRecords']]
    result = summarize_lookup(request, rows)
    assert 'PRIVATE-CANARY' not in json.dumps(result)
    assert not {'decision', 'expected', 'conditions'} & set(result)


def test_lower_revision_ties_do_not_hide_a_unique_current_source():
    data, rows = inputs()
    result = build(record_index=data['record_index'] + [data['record_index'][1] | dict(recordId='other-old')], records=rows)
    assert next(r for r in result['facts'] if r['factId'] == 'readiness')['recordId'] == 'readiness-new'


@pytest.mark.parametrize('policy', [[], ['readiness'] * 2, ['a'] * 17, ['x' * 97]])
def test_required_policy_is_bounded_and_unambiguous(policy):
    with pytest.raises(ValueError):
        build(required_facts=policy)
