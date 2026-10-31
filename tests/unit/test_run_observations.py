import pytest

from prosaic_integration_lab.run_observations import RunObservations, usage_projection


def event(event_name, **extra):
    return {'version': 1, 'source': 'runtime', 'event': event_name,
            'invocation_id': 'attempt-1', 'sequence': 1, **extra}


def test_trace_records_actual_elapsed_time_and_redacts_non_contract_payloads():
    now = [10.0]
    sink = RunObservations(clock=lambda: now[0])
    sink.observe('run-a', event('invocation_started', prompt='private', endpoint='private'))
    now[0] = 12.5
    sink.observe('run-a', event('invocation_completed', sequence=2, outcome='completed', token_usage=12))
    result = sink.snapshot('run-a')
    assert result['elapsed'] == 2.5
    assert result['events'][1]['at'] == 2.5
    assert result['events'][1]['token_usage'] == 12
    assert 'private' not in str(result)
    assert sink.snapshot('run-b')['events'] == []


def test_open_invocation_keeps_elapsed_time_advancing_without_fabricated_events():
    now = [2.0]
    sink = RunObservations(clock=lambda: now[0])
    sink.observe('a', event('invocation_started'))
    now[0] = 8.0
    result = sink.snapshot('a')
    assert result['elapsed'] == 6
    assert len(result['events']) == 1
    assert result['active'] is True


def test_capacity_and_mutation_do_not_corrupt_other_runs():
    sink = RunObservations(max_runs=2, max_events=2)
    for name in ['a', 'b', 'c']:
        sink.observe(name, event('invocation_started'))
    assert sink.snapshot('a')['events'] == []
    for sequence in [2, 3]:
        sink.observe('c', event('provider_request_started', sequence=sequence, turn=sequence))
    snapshot = sink.snapshot('c')
    assert len(snapshot['events']) == 2 and snapshot['truncated'] is True
    snapshot['events'][0]['event'] = 'mutated'
    assert sink.snapshot('c')['events'][0]['event'] != 'mutated'


def test_invalid_events_and_nonfinite_fields_are_ignored():
    sink = RunObservations()
    sink.observe('a', event('secret_payload'))
    assert sink.snapshot('a')['events'] == []
    sink.observe('a', event('tool_started', name='../../secret', duration_ms=float('nan')))
    recorded = sink.snapshot('a')['events'][0]
    assert 'duration_ms' not in recorded
    assert recorded['name'] == 'unknown'


@pytest.mark.parametrize('field', ['max_runs', 'max_events'])
def test_invalid_capacity_is_rejected(field):
    with pytest.raises(ValueError):
        RunObservations(**{field: 0})


def test_usage_comes_from_validated_recorder_reports_and_preserves_unknown():
    complete = {'measurement_state': 'complete', 'observation': {'usage': {
        'status': 'reported', 'input_tokens': 100, 'output_tokens': 25}}}
    unknown = {'measurement_state': 'unresolved', 'observation': None}
    report = usage_projection([complete, unknown])
    assert report == {'input': 100, 'output': 25, 'completeCalls': 1,
                      'totalCalls': 2, 'unknownCalls': 1, 'available': True}
    assert usage_projection([unknown])['input'] is None
    assert usage_projection(None)['available'] is False
    assert usage_projection([])['input'] == 0


def test_unsupported_provider_counts_remain_separate_from_qualified_accounting():
    unsupported = {'measurement_state': 'unsupported', 'observation': {
        'outcome': 'completed', 'usage': {'status': 'unsupported',
        'input_tokens': 520, 'output_tokens': 31, 'total_tokens': 551}}}
    result = usage_projection([unsupported])
    assert result['input'] is None and result['unknownCalls'] == 1
    assert result['providerReported'] == {'input': 520, 'output': 31,
        'unqualifiedCalls': 1, 'unknownCalls': 0}
    mixed = usage_projection([unsupported, {'measurement_state': 'unresolved'}])
    assert mixed['providerReported']['unknownCalls'] == 1
    for status in ('untrusted', 'partial', 'unknown'):
        row = {**unsupported, 'observation': {'outcome': 'completed',
            'usage': {**unsupported['observation']['usage'], 'status': status}}}
        assert 'providerReported' not in usage_projection([row])
    invalid = {**unsupported, 'observation': {'outcome': 'completed',
        'usage': {**unsupported['observation']['usage'], 'total_tokens': 550}}}
    assert 'providerReported' not in usage_projection([invalid])
