"""Eventually convergent public-recorder scans of frozen lab reservations."""
from .billing_projection import project


def scan(metadata, recorder_factory, store, mappings):
    count = 0
    for reservation in metadata.billing_reservations():
        mapping = mappings[(reservation['namespace'],reservation['environment'],
                            reservation['tenant_id'],reservation['billing_account_id'])]
        recorder = recorder_factory(reservation['namespace'],reservation['environment'])
        filters = {k:reservation[k] for k in ('tenant_id','actor_id','billing_account_id')}
        filters.update(application_id='integration-lab',request_id=reservation['run_id'],run_id=reservation['run_id'])
        offset = 0
        while True:
            rows = recorder.calls(limit=1000,offset=offset,**filters)
            for call in rows:
                store.enqueue(project(call,reservation,mapping))
                count += 1
            if len(rows) < 1000:
                break
            offset += len(rows)
    return count
