"""Bounded synthetic multiuser workloads and persistent terminal evidence."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
from pathlib import Path
import threading
import time
import uuid

import httpx
from prosaic_runtime_postgres import PostgresRecorder


def identities(users):
    if not 1 <= users <= 1000:
        raise ValueError('users must be between 1 and 1000')
    names = ['alice', 'bob', 'carol']
    return [{'tenant_id': 'tenant-' + ('b' if i % 3 == 2 else 'a'),
             'actor_id': names[i] if i < 3 else f'user-{i + 1:04}',
             'billing_account_id': 'account-' + ('b' if i % 3 == 2 else 'a')}
            for i in range(users)]


def validate(users, runs, concurrency):
    identities(users)
    if not 1 <= runs <= 1000 or users * runs > 10000 or not 1 <= concurrency <= 64:
        raise ValueError('require 1..1000 runs/user, at most 10000 runs, and 1..64 concurrency')


def approval_status(response):
    if response.status_code == 503 and response.json().get('detail') == 'capacity_exhausted':
        return 'waiting'
    response.raise_for_status()
    if response.json()['status'] != 'completed':
        raise ValueError('approval did not complete')
    return 'completed'


class Events:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.lock = threading.Lock()
        for stream in ('requests', 'accounting'):
            (self.directory / (stream + '.jsonl')).touch()

    def emit(self, stream, **fields):
        # Call sites supply only fixture identities and filtered metrics; never HTTP bodies.
        line = json.dumps({'time': round(time.time(), 3), **fields})
        with self.lock:
            with (self.directory / (stream + '.jsonl')).open('a') as output:
                output.write(line + '\n')
            if stream == 'requests':
                print(line, flush=True)

    def finish(self, result):
        temporary = self.directory / 'finished.tmp'
        temporary.write_text(json.dumps(result) + '\n')
        temporary.replace(self.directory / 'finished.json')


def watch(directory, stream):
    directory = Path(directory)
    path = directory / (stream + '.jsonl')
    position = 0
    while True:
        if path.exists():
            with path.open() as source:
                source.seek(position)
                for line in source:
                    print(line.rstrip(), flush=True)
                position = source.tell()
        if (directory / 'finished.json').exists():
            # Writer is finished before publishing this marker.
            if path.exists() and path.stat().st_size > position:
                continue
            print((directory / 'finished.json').read_text().strip(), flush=True)
            return
        time.sleep(0.2)


def run(config, users, runs, concurrency, events, allow_overload=False):
    validate(users, runs, concurrency)
    principals = list(config['principals'].items())[:users]
    if len(principals) != users:
        raise ValueError('insufficient trusted fixture identities')
    recorder = PostgresRecorder(config['accounting_dsn'], namespace=config['namespace'],
                                environment=config['environment'])
    with httpx.Client(timeout=30) as client:
        before = client.get(config['model'] + '/stats').json()['calls']

    def session(index):
        token, principal = principals[index]
        actor = principal['actor_id']
        headers = {'Authorization': 'Bearer ' + token}
        completed = rejected = errors = deferred = 0
        with httpx.Client(timeout=30) as client:
            def request(method, replica, path, operation, **kwargs):
                started = time.monotonic()
                response = client.request(method, config[replica] + path, headers=headers, **kwargs)
                events.emit('requests', actor=actor, operation=operation, replica=replica,
                            status=response.status_code, milliseconds=round((time.monotonic() - started) * 1000, 2))
                return response

            for iteration in range(runs):
                a, b = ('a', 'b') if (index + iteration) % 2 == 0 else ('b', 'a')
                try:
                    # Include the key without changing trusted authorization.
                    started = time.monotonic()
                    response = client.post(config[a] + '/runs', headers={**headers, 'Idempotency-Key': uuid.uuid4().hex},
                        json={'workflow': 'synthetic', 'task': 'Neutral multiuser load fixture'})
                    events.emit('requests', actor=actor, operation='start', replica=a, status=response.status_code,
                                milliseconds=round((time.monotonic() - started) * 1000, 2))
                    if response.status_code == 503 and response.json().get('detail') == 'capacity_exhausted':
                        rejected += 1
                        continue
                    response.raise_for_status()
                    state = response.json()
                    events.emit('requests', actor=actor, operation='waiting', replica=a, run_id=state['run_id'])
                    if state['status'] != 'waiting':
                        raise ValueError('unexpected workflow state')
                    path = '/runs/' + state['run_id']
                    response = request('POST', b, path + '/resume', 'approve',
                                       json={'choice': 'approve', 'expected_revision': state['revision']})
                    final_status = approval_status(response)
                    response = request('GET', b, path + '/usage', 'usage')
                    response.raise_for_status()
                    usage = response.json()
                    events.emit('accounting', actor=actor, tenant=principal['tenant_id'], run_id=state['run_id'], status=final_status,
                        calls=usage['total_calls'], complete=usage['complete_calls'], unknown=usage['unresolved_calls'],
                        usd=usage['estimated_amounts'].get('USD'), billing_eligible=usage['billing_eligible'])
                    if (usage['total_calls'] != 1 or usage['complete_calls'] != 1 or usage['unresolved_calls'] != 0
                        or Decimal(usage['estimated_amounts']['USD']) != Decimal('0.00037') or usage['billing_eligible']):
                        raise ValueError('accounting mismatch')
                    if users > 1:
                        other = principals[(index + 1) % users][0]
                        for suffix in ('', '/usage'):
                            denied = client.get(config[a] + path + suffix, headers={'Authorization': 'Bearer ' + other})
                            events.emit('requests', actor=actor, operation='other_user_denied', replica=a, status=denied.status_code)
                            if denied.status_code != 404:
                                raise ValueError('owner isolation failed')
                    if final_status == 'completed':
                        completed += 1
                    else:
                        deferred += 1
                except Exception as error:
                    errors += 1
                    events.emit('requests', actor=actor, operation='error', error=type(error).__name__)
        return completed, rejected, errors, deferred

    # map consumes only user sessions, bounded to 1000; each session issues sequential requests.
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        outcomes = list(pool.map(session, range(users)))
    completed, rejected, errors, deferred = (sum(item[i] for item in outcomes) for i in range(4))
    with httpx.Client(timeout=30) as client:
        observed = client.get(config['model'] + '/stats').json()['calls'] - before
    usage = recorder.report(application_id='integration-lab')
    events.emit('accounting', scope='all_fixture_users', **{key: usage[key] for key in
        ('total_calls', 'complete_calls', 'unresolved_calls', 'quarantined_calls',
         'partial_calls', 'estimated_amounts', 'fully_costed', 'billing_eligible')})
    reconciled = observed == usage['total_calls'] == completed + deferred and usage['unresolved_calls'] == 0
    return {'users': users, 'runs_per_user': runs, 'concurrency': concurrency,
            'completed': completed, 'start_capacity_rejected': rejected, 'approval_deferred': deferred,
            'capacity_rejected': rejected + deferred, 'errors': errors,
            'independent_model_calls': observed, 'accounting_reconciled': reconciled,
            'passed': errors == 0 and reconciled and (allow_overload or rejected + deferred == 0)}
