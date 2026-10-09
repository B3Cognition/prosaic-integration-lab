import pytest
from lab_runner.metrics_viewer import safe_metrics

def test_metrics_viewer_accepts_only_known_labels_and_finite_numbers():
    text='lab_readiness 1\nlab_admission_active{pool="writes"} 2\n'
    assert safe_metrics(text)==text

@pytest.mark.parametrize('text',['PRIVATE\n','lab_readiness PRIVATE\n','lab_readiness NaN\n',
    'lab_http_requests_total{route="PRIVATE",status="2xx"} 1\n','lab_readiness 1e999\n'])
def test_metrics_viewer_never_prints_malformed_or_private_provider_response(text):
    with pytest.raises(ValueError): safe_metrics(text)
