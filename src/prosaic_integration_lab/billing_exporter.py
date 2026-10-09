"""One finite fixture-export pass; no inference, schema mutation or Lago setup."""
import argparse
import json
from pathlib import Path
import httpx
from prosaic_runtime_postgres import PostgresRecorder
from .billing_projection import project,account_scope,digest
from .billing_scan import scan
from .billing_store import BillingStore
from .billing_delivery import LagoClient,deliver,DeliveryError
from .metadata import Metadata


def verify_source(row,factory,store):
    r = row['locator']['reservation']
    recorder = factory(r['namespace'],r['environment'])
    filters = {k:r[k] for k in ('tenant_id','actor_id','billing_account_id')}
    filters.update(application_id='integration-lab',request_id=r['run_id'],run_id=r['run_id'])
    offset = 0
    while True:
        calls = recorder.calls(limit=1000,offset=offset,**filters)
        for call in calls:
            if call['intent']['provider_call_id'] != row['locator']['provider_call_id']: continue
            projection = project(call,r,row['mapping'])
            store.enqueue(projection)
            if projection['hash'] != row['hash'] or projection['exclusion']:
                raise DeliveryError('conflict')
            return
        if len(calls)<1000: raise DeliveryError('conflict')
        offset += len(calls)


def tick(config,limit=100):
    store = BillingStore(config['billing_dsn'])
    store.check_ready()
    metadata = Metadata(config['billing_dsn'])
    factory = lambda n,e:PostgresRecorder(config['billing_dsn'],namespace=n,environment=e)
    mappings = {}
    for r in metadata.billing_reservations():
        key = (r['namespace'],r['environment'],r['tenant_id'],r['billing_account_id'])
        mappings[key] = store.get_mapping(digest(account_scope(r)))
    scanned = scan(metadata,factory,store,mappings)
    with httpx.Client() as http:
        client = LagoClient(config['lago']['url'],config['lago']['key'],http)
        delivered = deliver(store,client,limit,verify=lambda row:verify_source(row,factory,store))
    states = store.summary()
    if states.get('failed') or states.get('conflict') or any(s['conflict'] for s in store.sources()):
        raise ValueError('billing evidence failed')
    return dict(event='billing_export_pass',scanned=scanned,processed=delivered,states=states,
                runtime_billing_eligible=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--limit',type=int,default=100)
    args = parser.parse_args()
    try:
        if not 1 <= args.limit <= 100: raise ValueError('invalid export limit')
        if args.config.stat().st_size > 1048576: raise ValueError('config too large')
        result = tick(json.loads(args.config.read_text()),args.limit)
        print(json.dumps(result))
        return 0
    except Exception:
        print(json.dumps({'event':'billing_export_failed'}))
        return 1


if __name__ == '__main__': raise SystemExit(main())
