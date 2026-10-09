import json
from pathlib import Path
import httpx

from test_approval import headers, start
from test_accounting import count
from test_recovery import mutate_replica, wait_for
from lab_runner.stack import command
from lab_runner.manifest import validate_resource

def deliver_owned_config(lab):
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    identifier = manifest['runtime_config_job']
    state = json.loads(command(manifest['engine'],'inspect',identifier))[0]
    validate_resource(state,identifier,manifest['owner'])
    command(manifest['engine'],'start','-a',identifier)


def test_replica_namespace_drift_cannot_turn_measured_usage_into_zero(lab):
    run = start(lab, workflow='synthetic').json()
    before = count(lab)
    path = '/runs/' + run['run_id']
    original = httpx.get(lab['a'] + path + '/usage', headers=headers(lab), timeout=5).json()
    assert original['total_calls'] == 1
    service = Path(lab['fixture_manifest']).parent / 'secrets/service.json'
    contents = service.read_text()
    config = json.loads(contents)
    config['namespace'] += '-drift'
    try:
        service.write_text(json.dumps(config))
        deliver_owned_config(lab)
        mutate_replica(lab, 'kill', 'b')
        mutate_replica(lab, 'start', 'b')
        wait_for(lambda: httpx.get(lab['b'] + '/readyz', timeout=2).status_code == 200)
        for suffix in ('', '/usage'):
            response = httpx.get(lab['b'] + path + suffix, headers=headers(lab), timeout=5)
            assert response.status_code == 409
            assert response.json() == {'detail': 'scope_conflict'}
        assert count(lab) == before
    finally:
        service.write_text(contents)
        deliver_owned_config(lab)
        mutate_replica(lab, 'kill', 'b')
        mutate_replica(lab, 'start', 'b')
        wait_for(lambda: httpx.get(lab['b'] + '/readyz', timeout=2).status_code == 200)
