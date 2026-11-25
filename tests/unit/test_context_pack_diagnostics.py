import json
from pathlib import Path
import xml.etree.ElementTree as E

from lab_runner.results import sanitize_junit


def test_capacity_failure_exports_only_closed_diagnostics(tmp_path):
    diagnostic={'phase':'receipt_size','error':'AssertionError','reason':'unknown',
        'receipt_bytes':1048577,'state_bytes':400000}
    root=E.Element('testsuites');suite=E.SubElement(root,'testsuite')
    case=E.SubElement(suite,'testcase',name='test_large_captured_context_obeys_default_record_capacity')
    E.SubElement(case,'failure').text='CONTEXT_PACK_CAPACITY '+json.dumps(diagnostic)
    path=tmp_path/'junit.xml';E.ElementTree(root).write(path)
    result=sanitize_junit(path)
    assert result['context_pack_diagnostic']==diagnostic
    from lab_runner.gates import export
    assert export({'mode':'context-packs',**result})['context_pack_diagnostic']==diagnostic
    assert export({'mode':'context-packs',**result})['passed'] is False


def test_capacity_diagnostics_reject_private_extensions_and_unknown_values(tmp_path):
    from lab_runner.context_packs import sanitize_capacity_diagnostic
    public={'phase':'dispatch','error':'ConversationError','reason':'storeUnavailable',
        'receipt_bytes':None,'state_bytes':None}
    assert sanitize_capacity_diagnostic(public)==public
    for value in ({**public,'private':'PRIVATE-KEY'},{**public,'reason':'PRIVATE-KEY'},
                  {**public,'receipt_bytes':True},{**public,'error':'PRIVATE-KEY'}):
        assert sanitize_capacity_diagnostic(value)=={'status':'unavailable'}


def test_unrelated_failures_cannot_supply_capacity_diagnostics(tmp_path):
    root=E.Element('testsuites');suite=E.SubElement(root,'testsuite')
    case=E.SubElement(suite,'testcase',name='unrelated')
    E.SubElement(case,'failure').text='CONTEXT_PACK_CAPACITY '+json.dumps({'private':'PRIVATE-KEY'})
    path=tmp_path/'junit.xml';E.ElementTree(root).write(path)
    assert 'context_pack_diagnostic' not in sanitize_junit(path)
    assert 'PRIVATE-KEY' not in path.read_text()


def test_driver_cause_reveals_only_fixed_sqlstate_meaning():
    from lab_runner.context_packs import capacity_failure
    class DriverError(Exception):
        sqlstate='57014'
    class StoreUnavailable(Exception):pass
    error=StoreUnavailable('PRIVATE-KEY')
    error.__cause__=DriverError('PRIVATE-DSN')
    message=capacity_failure('dispatch',error)
    assert 'PRIVATE-' not in message
    assert json.loads(message.split(' ',1)[1])['reason']=='statementTimeout'
