from lab_runner.memory_policy.trace import TraceRecorder
from lab_runner.quality.contracts import decode

def test_trace_classifies_only_validated_terminal_evidence(tmp_path):
    from prosaic_runtime import ToolOutcome
    trace=TraceRecorder(tmp_path/'trace.json')
    outcome=ToolOutcome('invalid_arguments').to_dict()
    trace.finish([dict(id='attempt1',result={'exit_code':0},events=[
        dict(event='tool_completed',status='error',call_id='call1',tool_outcome=outcome),
        dict(event='tool_completed',status='error',call_id='old'),
        dict(event='tool_completed',status='error',call_id='bad',tool_outcome={'code':'PRIVATE'})])])
    rows=decode(trace.path.read_bytes())['receiptFailures']
    assert rows[0]['reason']=='invalid_arguments' and rows[0]['toolOutcome']==outcome
    assert rows[1]['reason']==rows[2]['reason']=='unclassified'
    assert 'PRIVATE' not in str(rows)

def test_trace_drops_malformed_new_evidence_at_capture(tmp_path):
    trace=TraceRecorder(tmp_path/'trace.json')
    trace.event(dict(event='tool_completed',status='error',tool_outcome={'code':'PRIVATE'}))
    assert 'PRIVATE' not in trace.path.read_text()

def test_policy_opt_in_is_frozen_without_changing_default_request(tmp_path):
    import pytest
    from test_scoped_memory_recovery import policy
    from lab_runner.memory.execution import freeze
    case,corpus,_,_=policy();path=tmp_path/'prepared.json'
    original=freeze(case,corpus,'enabled',path,bounded_recovery=False)
    with pytest.raises(ValueError,match='drift'):freeze(case,corpus,'enabled',path,bounded_recovery=True)
    other=freeze(case,corpus,'enabled',tmp_path/'bounded.json',bounded_recovery=True)
    assert original['request']==other['request']
    assert other['boundedRecovery'] is True and 'boundedRecovery' not in original
