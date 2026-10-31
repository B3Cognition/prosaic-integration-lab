from types import SimpleNamespace

from lab_runner.memory_benchmark.runner import _unknown


def test_known_token_usage_does_not_confirm_pending_harness_completion():
    budget=SimpleNamespace(usage_complete=True,provider_requests=1)
    result={'executionError':None,'evidence':{'recoveryStatus':'receiptAvailable',
        'checkpoint':{'status':'running','pending':{'id':'attempt'}},
        'receipts':[{'result':{'metadata':{}}}]}}
    assert _unknown(budget,[result]) is True


def test_completed_or_terminal_rejected_known_receipt_is_distinct_from_pending():
    budget=SimpleNamespace(usage_complete=True,provider_requests=1)
    for status in ('completed','blocked'):
        assert not _unknown(budget,[{'executionError':None,'evidence':{'recoveryStatus':status,
            'checkpoint':{'status':status,'pending':None},'receipts':[{'result':{'metadata':{}}}]}}])


def test_saved_outcome_binds_raw_state_before_the_final_batch_seal(tmp_path):
    import pytest
    from lab_runner.memory_benchmark.runner import _store_row,_check_saved_row
    from lab_runner.memory_benchmark.storage import exclusive
    item=dict(id='q-manual',caseId='q',arm='manual')
    manifest={'settings':{'review':False}}
    row=dict(item,path='outcomes/q-manual.json',status='blocked')
    raw=tmp_path/'samples/q-manual/inputs.json';exclusive(raw,{'question':'original'})
    _store_row(tmp_path,row,manifest)
    _check_saved_row(tmp_path,row,item,manifest,None)
    raw.write_text('{"question":"changed"}')
    with pytest.raises(ValueError):_check_saved_row(tmp_path,row,item,manifest,None)
