"""Fixture-only projection of public Runtime evidence; never billing authority."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json

DIMENSIONS = ('input_tokens', 'cached_input_tokens', 'output_tokens')
ATTRIBUTION = ('tenant_id','actor_id','billing_account_id')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()).hexdigest()


def account_scope(reservation):
    return {k: reservation[k] for k in ('namespace','environment','tenant_id','billing_account_id')} | {'application_id':'integration-lab'}


def project(call, reservation, mapping):
    intent = call['intent']
    context = intent['context']
    if any(intent.get(k) != reservation[k] for k in ('namespace','environment')):
        raise ValueError('billing storage scope conflict')
    expected = {k: reservation[k] for k in ATTRIBUTION}
    expected.update(application_id='integration-lab',request_id=reservation['run_id'],run_id=reservation['run_id'])
    if any(context.get(k) != v for k,v in expected.items()):
        raise ValueError('billing attribution conflict')
    identity = {**account_scope(reservation),'provider_call_id':intent['provider_call_id']}
    source = digest(identity)
    result = dict(source=source,scope=digest(account_scope(reservation)),events=[],exclusion=None,
                  mapping=mapping, evidence_hash=digest(call),
                  unobserved_hash=digest({**call,'observation':None,'assessment':None,'measurement_state':'unresolved'}),
                  locator=dict(reservation={k:reservation[k] for k in
                      ('namespace','environment','tenant_id','actor_id','billing_account_id','run_id')},
                      provider_call_id=intent['provider_call_id'],intent_hash=digest(intent)))

    def exclude(reason):
        result['exclusion'] = reason
        result['hash'] = digest(result)
        return result

    state = call['measurement_state']
    if state != 'complete':
        return exclude(state if state in {'unresolved','unsupported','quarantined'} else 'invalid_state')
    observation = call.get('observation') or {}
    usage = observation.get('usage') or {}
    if (intent.get('requested_model') != 'test-model' or observation.get('response_model') != 'test-model'
        or intent.get('provider_id') != 'openai-compatible' or intent.get('credential_account') != 'platform'
        or observation.get('service_tier') not in (None,'default')
        or (call.get('assessment') or {}).get('normalization_version') != 1):
        return exclude('unsupported_contract')
    if usage.get('cached_input_tokens') is None:
        return exclude('unknown_cached_input')
    quantities = [usage.get(k) for k in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')]
    if usage.get('status') != 'reported' or any(type(v) is not int or not 0 <= v <= 2**63-1 for v in quantities):
        return exclude('invalid_usage')
    inp,cached,out,total = quantities
    reasoning = usage.get('reasoning_output_tokens')
    if cached > inp or inp+out != total or (reasoning is not None and
        (type(reasoning) is not int or not 0 <= reasoning <= out)):
        return exclude('invalid_usage')
    try:
        finished = datetime.fromisoformat(observation['finished_at'].replace('Z','+00:00'))
        if finished.tzinfo is None:
            return exclude('invalid_timestamp')
        epoch = (finished.astimezone(timezone.utc)-datetime(1970,1,1,tzinfo=timezone.utc))
        # Lago's event JSON serializes milliseconds; freeze that precision before
        # sending, so exact duplicate lookup can compare the full timestamp.
        seconds = Decimal(epoch.days*86400+epoch.seconds)+Decimal(epoch.microseconds//1000)/Decimal(1000)
    except (KeyError,ValueError,TypeError):
        return exclude('invalid_timestamp')
    for code,quantity in zip(DIMENSIONS,(inp-cached,cached,out)):
        result['events'].append(dict(transaction_id=digest([source,code]),
            external_subscription_id=mapping['subscription'],code=code,timestamp=format(seconds,'f'),
            properties={'tokens':quantity}))
    result['hash'] = digest(result)
    return result
