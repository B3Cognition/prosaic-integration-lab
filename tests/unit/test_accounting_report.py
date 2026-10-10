import json

from lab_runner.accounting_report import write_report


def test_report_keeps_unknown_cost_unknown_and_escapes_untrusted_text(tmp_path):
    report = {'version': 1, 'ownership_id': 'fixture', 'independent_model_calls': 1,
              'runs': [{'actor': 'bob', 'case': '<script>unsafe</script>', 'run_id': 'run',
                        'status': 'waiting', 'usage': {'total_calls': 1, 'complete_calls': 0,
                        'unresolved_calls': 1, 'estimated_amounts': {}, 'fully_costed': False,
                        'billing_eligible': False}, 'calls': [{'input_tokens': None,
                        'cached_input_tokens': None, 'output_tokens': None,
                        'measurement_state': 'unresolved', 'estimate_usd': None}]}]}
    path = write_report(report, tmp_path)
    text = path.read_text()
    assert 'Unknown' in text
    assert '<script>unsafe</script>' not in text
    assert '&lt;script&gt;unsafe&lt;/script&gt;' in text
    assert json.loads((tmp_path / 'accounting.json').read_text())['runs'][0]['calls'][0]['estimate_usd'] is None


def test_report_sums_decimal_estimates_and_counts_independent_dispatches(tmp_path):
    def row(actor, amount):
        return {'actor': actor, 'case': 'normal', 'run_id': actor, 'status': 'waiting',
                'usage': {'total_calls': 1, 'complete_calls': 1, 'unresolved_calls': 0,
                          'estimated_amounts': {'USD': amount}, 'fully_costed': True, 'billing_eligible': False},
                'calls': [{'input_tokens': 100, 'cached_input_tokens': 20, 'output_tokens': 25,
                           'measurement_state': 'complete', 'estimate_usd': amount}]}
    report = {'version': 1, 'ownership_id': 'fixture', 'independent_model_calls': 2,
              'runs': [row('alice', '0.000370000000000000'), row('carol', '0.000370000000000000')]}
    path = write_report(report, tmp_path)
    assert '$0.000740' in path.read_text()
    assert '2 / 2' in path.read_text()
def test_accounting_snapshot_preserves_all_evidence_except_report_time():
    import copy
    import pytest
    from lab_runner import accounting_report
    from prosaic_integration_lab.views import public_usage
    report=public_usage({'version':1,'total_calls':2,'complete_calls':1,'unresolved_calls':1,
        'quarantined_calls':0,'unsupported_calls':0,'partial_calls':0,
        'unavailable_assessment_calls':0,'excluded_resources':[],
        'estimated_amounts':{'USD':'0.00037'},'coverage':{'known':1},'fully_costed':False,
        'billing_eligible':False,'as_of':'2026-10-10T10:00:00+00:00'})
    later=copy.deepcopy(report);later['as_of']='2026-10-10T10:00:01+00:00'
    assert report!=later
    assert accounting_report.accounting_snapshot(report)==accounting_report.accounting_snapshot(later)
    for key,value in [('total_calls',3),('unresolved_calls',0),('estimated_amounts',{}),
                      ('fully_costed',True),('coverage',{}),('billing_eligible',True)]:
        changed=copy.deepcopy(later);changed[key]=value
        assert accounting_report.accounting_snapshot(report)!=accounting_report.accounting_snapshot(changed)
    for timestamp in (None,'private','2026-10-10T10:00:01'):
        changed=copy.deepcopy(later);changed['as_of']=timestamp
        with pytest.raises(ValueError):accounting_report.accounting_snapshot(changed)
    assert report['as_of']=='2026-10-10T10:00:00+00:00'
