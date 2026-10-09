from prosaic_integration_lab.observability import Metrics,request_context,bind_run,correlation

def test_metric_labels_are_fixed_and_private_values_cannot_expand_series():
    metrics=Metrics('a'*64)
    for i in range(1000): metrics.request('/PRIVATE/'+str(i),503,.2)
    rendered=metrics.render()
    assert 'PRIVATE' not in rendered
    assert 'lab_http_requests_total{route="unknown",status="5xx"} 1000' in rendered
    assert len(rendered)<30000

def test_trusted_correlation_has_generated_request_id_and_keyed_references():
    metrics=Metrics('a'*64)
    with request_context(metrics) as request:
        bind_run({'run_id':'1'*32,'tenant_id':'PRIVATE-TENANT'})
        record=correlation()
        assert record['request_id'] == request['request_id']
        assert record['run_id']=='1'*32
        assert len(record['tenant_ref'])==16
        assert 'PRIVATE' not in str(record)
    assert correlation()=={}

def test_unknown_accounting_observations_are_not_zero_or_unique_invoice_counts():
    metrics=Metrics('a'*64)
    metrics.unknown(2)
    metrics.unknown(2)
    assert 'lab_accounting_unknown_observations_total 4' in metrics.render()
