from pathlib import Path
from lab_runner.ingress import configuration

def test_ingress_policy_bounds_transport_and_never_retries_mutations():
    policy = configuration(('10.0.0.2','10.0.0.3'))
    for directive in ('client_header_timeout 2s;', 'client_body_timeout 2s;',
        'client_max_body_size 8k;', 'proxy_next_upstream off;',
        'worker_connections 128;', 'worker_shutdown_timeout 15s;',
        'proxy_connect_timeout 2s;', 'proxy_read_timeout 12s;',
        'access_log off;', 'proxy_request_buffering off;'):
        assert directive in policy
    for name in ('X-Tenant-ID','X-Actor-ID','X-Billing-Account-ID','Forwarded','X-Forwarded-For'):
        assert f'proxy_set_header {name} "";' in policy
    assert 'server 10.0.0.2:8080;' in policy and 'server 10.0.0.3:8080;' in policy
    assert 'ip_hash' not in policy

def test_ingress_configuration_rejects_injected_upstream():
    import pytest
    with pytest.raises(ValueError): configuration(('10.0.0.2; include /secret;','10.0.0.3'))

def test_proposal_route_has_exact_location_64k_ceiling_with_same_no_retry_proxy_policy():
    policy = configuration(('10.0.0.2','10.0.0.3'))
    assert 'location = /workflow-proposals {' in policy
    location = policy.split('location = /workflow-proposals {')[1].split('}',1)[0]
    assert 'client_max_body_size 64k;' in location
    assert 'proxy_next_upstream off;' in location
    assert 'proxy_request_buffering off;' in location
