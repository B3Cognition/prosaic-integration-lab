from copy import deepcopy
import pytest
from prosaic_integration_lab.billing_projection import project


def fixture():
    reservation = dict(namespace='lab-x', environment='sandbox', tenant_id='tenant-a',
        actor_id='alice', billing_account_id='account', run_id='run-a')
    context = {k: reservation[k] for k in ('tenant_id','actor_id','billing_account_id')}
    context.update(application_id='integration-lab', request_id='run-a', run_id='run-a')
    call = dict(intent=dict(provider_call_id='call-a', context=context, requested_model='test-model',
        namespace='lab-x',environment='sandbox',provider_id='openai-compatible',credential_account='platform'),
        observation=dict(finished_at='2026-10-09T12:00:00+00:00', response_model='test-model',
            outcome='completed', usage=dict(status='reported',input_tokens=100,output_tokens=20,
                total_tokens=120,cached_input_tokens=30,reasoning_output_tokens=5)),
        measurement_state='complete', assessment=dict(normalization_version=1,billing_eligible=False))
    mapping = dict(subscription='opaque-sub',revision='fixture-v1')
    return call,reservation,mapping


def test_exclusive_quantities_and_stable_timestamp():
    c,r,m = fixture()
    result = project(c,r,m)
    assert [e['properties']['tokens'] for e in result['events']] == [70,30,20]
    assert [e['code'] for e in result['events']] == ['input_tokens','cached_input_tokens','output_tokens']
    assert all(e['timestamp'] == '1791547200' for e in result['events'])
    changed = project(c,r,{**m,'revision':'v2','subscription':'other-sub'})
    assert [e['transaction_id'] for e in result['events']] == [e['transaction_id'] for e in changed['events']]
    assert result['hash'] != changed['hash']


@pytest.mark.parametrize('cached,reason',[(None,'unknown_cached_input'),(101,'invalid_usage'),(True,'invalid_usage')])
def test_unknown_or_invalid_cache_never_becomes_uncached(cached,reason):
    c,r,m = fixture()
    c['observation']['usage']['cached_input_tokens'] = cached
    result = project(c,r,m)
    assert result['exclusion'] == reason
    assert result['events'] == []


@pytest.mark.parametrize('state',['unresolved','quarantined','unsupported'])
def test_unusable_measurement_has_visible_exclusion(state):
    c,r,m = fixture()
    c['measurement_state'] = state
    assert project(c,r,m)['exclusion'] == state


def test_spoofed_context_is_conflict():
    c,r,m = fixture()
    c['intent']['context']['tenant_id'] = 'other'
    with pytest.raises(ValueError): project(c,r,m)


def test_storage_scope_mismatch_is_conflict():
    c,r,m = fixture()
    c['intent']['namespace'] = 'other-storage'
    with pytest.raises(ValueError): project(c,r,m)


def test_tenant_scopes_do_not_collide():
    c,r,m = fixture()
    first = project(c,r,m)
    r['tenant_id'] = c['intent']['context']['tenant_id'] = 'tenant-b'
    assert first['source'] != project(c,r,m)['source']


@pytest.mark.parametrize('outcome',['failed','cancelled'])
def test_measured_attempts_are_included_independently_of_output(outcome):
    c,r,m = fixture()
    c['observation']['outcome'] = outcome
    assert len(project(c,r,m)['events']) == 3


def test_zero_cache_is_known_and_preserved():
    c,r,m = fixture()
    c['observation']['usage']['cached_input_tokens'] = 0
    assert [e['properties']['tokens'] for e in project(c,r,m)['events']] == [100,0,20]


def test_timestamp_uses_lago_millisecond_precision_without_retry_drift():
    c,r,m = fixture()
    c['observation']['finished_at'] = '2026-10-09T12:00:00.678206Z'
    assert project(c,r,m)['events'][0]['timestamp'] == '1791547200.678'


@pytest.mark.parametrize('mutation', ['total','model','tier','normalization','provider','credential'])
def test_unsupported_contracts_are_excluded(mutation):
    c,r,m = fixture()
    if mutation == 'total': c['observation']['usage']['total_tokens'] = 121
    if mutation == 'model': c['observation']['response_model'] = 'different'
    if mutation == 'tier': c['observation']['service_tier'] = 'priority'
    if mutation == 'normalization': c['assessment']['normalization_version'] = 2
    if mutation == 'provider': c['intent']['provider_id'] = 'unsupported-provider'
    if mutation == 'credential': c['intent']['credential_account'] = 'byok'
    assert project(c,r,m)['events'] == []
