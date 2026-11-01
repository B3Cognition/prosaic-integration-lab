"""Actual text arrivals, never inferred token timing or unowned provider content."""
from prosaic_integration_lab.run_observations import RunObservations
import pytest


def record(kind, invocation='a', **extra):
    return {'source':'runtime','event':kind,'invocation_id':invocation,**extra}


def started(sink):
    sink.observe('run',record('invocation_started'))
    sink.observe('run',record('provider_request_started'))


def delta(text, **extra):
    return {'event':'text_delta','provisional':True,'text':text,**extra}


def test_generation_records_real_arrival_times_and_provisional_unicode_output():
    now=[10.0];sink=RunObservations(clock=lambda:now[0]);started(sink)
    now[0]=11.5;sink.output('run',delta('Hello '))
    now[0]=12;sink.output('run',delta('🌍!'))
    now[0]=12.1;sink.observe('run',record('provider_request_completed',status='ok'))
    call=sink.snapshot('run')['generation']['calls'][0]
    assert call['spanId']=='event-2' and call['invocationId']=='a'
    assert call['start']==0 and call['firstOutputAt']==1.5 and call['lastOutputAt']==2
    assert call['chunks']==2 and call['characters']==8 and call['preview']=='Hello 🌍!'
    assert call['mode']=='streamed' and call['outcome']=='completed' and call['end']==2.1
    assert call['maxGap']==.5
    assert call['samples']==[{'index':1,'at':1.5,'characters':6,'totalCharacters':6},
        {'index':2,'at':2,'characters':2,'totalCharacters':8}]
    assert all('text' not in e for e in sink.snapshot('run')['events'])


def test_uncorrelated_empty_and_private_events_never_become_generation():
    sink=RunObservations();sink.output('missing',delta('private'))
    assert sink.snapshot('missing')['generation']['calls']==[]
    started(sink)
    for event in (delta(''),delta('private',provisional=False),{'event':'progress','text':'private'},
                  {'event':'tool_started','arguments':'private'},delta(123)):
        sink.output('run',event)
    assert sink.snapshot('run')['generation']['calls'][0]['chunks']==0
    sink.observe('run',record('provider_request_started',invocation='b'))
    sink.output('run',delta('ambiguous'))
    assert all(c['characters']==0 for c in sink.snapshot('run')['generation']['calls'])
    assert 'private' not in str(sink.snapshot('run'))


def test_stream_buffers_are_bounded_but_counts_and_first_output_survive():
    sink=RunObservations();started(sink)
    for _ in range(600):sink.output('run',delta('x'*10))
    call=sink.snapshot('run')['generation']['calls'][0]
    assert call['chunks']==600 and call['characters']==6000
    assert len(call['samples'])==512 and call['samplesTruncated'] is True
    assert len(call['preview'])==4096 and call['previewTruncated'] is True
    call['samples'][0]['at']=-1
    assert sink.snapshot('run')['generation']['calls'][0]['samples'][0]['at']>=0


def test_buffered_response_never_claims_streamed_text_or_exposes_a_preview():
    sink=RunObservations();started(sink)
    sink.output('run',{'event':'text','provisional':True,'text':'buffered private response'})
    call=sink.snapshot('run')['generation']['calls'][0]
    assert call['mode']=='buffered' and call['chunks']==0 and call['preview']==''
    assert call['firstOutputAt'] is None


def test_failed_invocations_close_open_streams_and_late_deltas_are_ignored():
    sink=RunObservations();started(sink);sink.output('run',delta('partial'))
    sink.observe('run',record('invocation_completed',outcome='timed_out'))
    sink.output('run',delta('late'))
    call=sink.snapshot('run')['generation']['calls'][0]
    assert call['outcome']=='unknown' and call['end'] is not None
    assert call['preview']=='partial' and call['chunks']==1


def test_each_provider_call_has_separate_generation_and_call_retention_is_bounded():
    sink=RunObservations();sink.observe('run',record('invocation_started'))
    for index in range(40):
        sink.observe('run',record('provider_request_started'))
        sink.output('run',delta(str(index)))
        sink.observe('run',record('provider_request_completed',status='ok'))
    trace=sink.snapshot('run')['generation']
    assert len(trace['calls'])==32 and trace['truncated'] is True
    assert trace['calls'][0]['preview']=='8' and trace['calls'][-1]['preview']=='39'


@pytest.mark.parametrize('outcome',['timed_out','cancelled','execution_failure','budget_failure'])
def test_http_200_does_not_turn_an_explicit_provider_failure_into_completion(outcome):
    sink=RunObservations();started(sink);sink.output('run',delta('partial'))
    sink.observe('run',record('provider_request_completed',outcome=outcome,http_status=200))
    assert sink.snapshot('run')['generation']['calls'][0]['outcome']==outcome


def test_invocation_failure_reconciles_only_the_unconfirmed_last_stream():
    sink=RunObservations();started(sink);sink.output('run',delta('first'))
    sink.observe('run',record('provider_request_completed',outcome='completed'))
    sink.observe('run',record('tool_started',name='lookup'))
    sink.observe('run',record('tool_completed',name='lookup',status='ok'))
    sink.observe('run',record('provider_request_started'));sink.output('run',delta('unterminated'))
    sink.observe('run',record('provider_request_completed',outcome='completed',http_status=200))
    sink.observe('run',record('invocation_completed',outcome='execution_failure'))
    calls=sink.snapshot('run')['generation']['calls']
    assert calls[0]['outcome']=='completed' and calls[1]['outcome']=='unknown'


def test_a_later_tool_failure_does_not_reclassify_a_valid_provider_stream():
    sink=RunObservations();started(sink);sink.output('run',delta('complete'))
    sink.observe('run',record('provider_request_completed',outcome='completed'))
    sink.observe('run',record('tool_started',name='lookup'))
    sink.observe('run',record('invocation_completed',outcome='execution_failure'))
    assert sink.snapshot('run')['generation']['calls'][0]['outcome']=='completed'


def test_identityless_starts_and_evicted_open_calls_cannot_create_false_uniqueness():
    sink=RunObservations();started(sink)
    sink.observe('run',{'source':'runtime','event':'provider_request_started'})
    sink.output('run',delta('unattributable'))
    assert sink.snapshot('run')['generation']['calls'][0]['preview']==''
    assert sink.snapshot('run')['generation']['uncorrelated'] is True
    second=RunObservations()
    for i in range(33):second.observe('run',record('provider_request_started',invocation=str(i)))
    for i in range(1,32):second.observe('run',record('provider_request_completed',invocation=str(i),outcome='completed'))
    second.output('run',delta('ambiguous with evicted open call'))
    assert second.snapshot('run')['generation']['calls'][-1]['preview']==''
