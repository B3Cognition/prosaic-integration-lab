import json
import os
import pytest
from lab_runner.secret_delivery import read_runtime_config,private_file
from lab_runner import secret_delivery

def test_runtime_delivery_refuses_migration_credentials(tmp_path):
    source = tmp_path/'config.json'
    source.write_text(json.dumps({'namespace':'fixture','migration_dsn':'secret-owner'}))
    with pytest.raises(ValueError,match='runtime config'):
        read_runtime_config(source)

def test_runtime_delivery_allows_only_service_config(tmp_path):
    source = tmp_path/'config.json'
    data = {'namespace':'fixture','environment':'sandbox','assets':'/srv/lab/assets',
        'principals':{},'harness_dsn':'runtime','accounting_dsn':'runtime','app_dsn':'runtime'}
    source.write_text(json.dumps(data))
    assert read_runtime_config(source) == data

def test_final_file_ownership_is_synced_before_publication(tmp_path,monkeypatch):
    events = []
    sync = os.fsync
    monkeypatch.setattr(os,'fchown',lambda *args:events.append('owner_final'))
    def synced(descriptor):
        events.append('fsync')
        sync(descriptor)
    monkeypatch.setattr(os,'fsync',synced)
    private_file(tmp_path/'private.json','{}')
    assert events.index('owner_final') < events.index('fsync')

def test_generation_parent_entry_is_durable_before_publishing_pointer(tmp_path,monkeypatch):
    # Map the container's fixed owner to the test process at the OS boundary.
    monkeypatch.setattr(secret_delivery,'RUNTIME_UID',os.getuid())
    monkeypatch.setattr(secret_delivery,'RUNTIME_GID',os.getgid())
    source = tmp_path/'source.json'
    source.write_text(json.dumps({'namespace':'fixture','environment':'sandbox','assets':'assets',
        'principals':{},'harness_dsn':'runtime','accounting_dsn':'runtime','app_dsn':'runtime'}))
    target_directory = tmp_path/'private-volume'
    target_directory.mkdir(mode=0o700)
    synced = set()
    actual = os.fsync
    def sync(descriptor):
        synced.add(os.fstat(descriptor).st_ino)
        actual(descriptor)
    monkeypatch.setattr(os,'fsync',sync)
    def checkpoint(stage):
        if stage == 'before_publish':
            assert (target_directory/'generations').stat().st_ino in synced
    secret_delivery.install(source,target_directory/'service.json',checkpoint=checkpoint)
