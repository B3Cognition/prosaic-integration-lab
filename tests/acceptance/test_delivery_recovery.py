import json
from pathlib import Path
import httpx
import pytest
from lab_runner.stack import command,EngineError
from lab_runner.manifest import validate_resource
from test_scope import deliver_owned_config
from test_approval import headers,start
from test_recovery import mutate_replica,wait_for
from test_accounting import count

def published_path(lab):
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    identifier = manifest['replica_ids']['b']
    validate_resource(json.loads(command(manifest['engine'],'inspect',identifier))[0],identifier,manifest['owner'])
    return command(manifest['engine'],'exec',identifier,'python','-c',
        'import os; print(os.path.realpath("/run/secrets/service.json"))')

def test_interrupted_config_delivery_retains_previous_generation_and_can_retry(lab):
    run = start(lab).json()
    before = count(lab)
    secrets = Path(lab['fixture_manifest']).parent/'secrets'
    source,controls = secrets/'service.json',secrets/'delivery-controls.json'
    original = source.read_text()
    previous = published_path(lab)
    config = json.loads(original)
    config['namespace'] += '-unpublished'
    try:
        source.write_text(json.dumps(config))
        controls.write_text(json.dumps({'failpoint':'before_publish'}))
        with pytest.raises(EngineError): deliver_owned_config(lab)
        assert published_path(lab) == previous
        mutate_replica(lab,'kill','b')
        mutate_replica(lab,'start','b')
        wait_for(lambda:httpx.get(lab['b']+'/readyz',timeout=2).status_code == 200)
        assert httpx.get(lab['b']+'/runs/'+run['run_id'],headers=headers(lab),timeout=5).status_code == 200
        source.write_text(original)
        controls.write_text('{}')
        deliver_owned_config(lab)
        assert published_path(lab) != previous
        assert count(lab) == before
    finally:
        source.write_text(original)
        controls.write_text('{}')
        deliver_owned_config(lab)
        mutate_replica(lab,'kill','b')
        mutate_replica(lab,'start','b')
        wait_for(lambda:httpx.get(lab['b']+'/readyz',timeout=2).status_code == 200)
