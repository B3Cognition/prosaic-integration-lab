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


@pytest.mark.parametrize('settings',['native','legacy','both'])
def test_delivery_accepts_exact_host_native_and_retained_legacy_config(tmp_path,monkeypatch,settings):
    from lab_runner.native_scenarios import native_configuration
    from lab_runner.legacy_upgrade import BASELINE_ASSETS_SHA256
    from prosaic_integration_lab.config import load_config
    data={'namespace':'fixture','environment':'sandbox','assets':'/srv/lab/assets',
        'principals':{},'harness_dsn':'runtime','accounting_dsn':'runtime','app_dsn':'runtime'}
    if settings in {'native','both'}:data['native']=native_configuration('effects-fixture')
    if settings in {'legacy','both'}:
        data['legacy_bundles']={BASELINE_ASSETS_SHA256:{'assets':'/srv/lab/assets/legacy-0.2.0'}}
    source=tmp_path/'service.json';source.write_text(json.dumps(data))
    monkeypatch.setenv('LAB_CONFIG',str(source))
    assert load_config()==data
    assert read_runtime_config(source)==data
    # Exercise the real private generation installation after initial delivery
    # and redelivery, retaining the original host settings without mutation.
    monkeypatch.setattr(secret_delivery,'RUNTIME_UID',os.getuid())
    monkeypatch.setattr(secret_delivery,'RUNTIME_GID',os.getgid())
    directory=tmp_path/'private-volume';directory.mkdir(mode=0o700)
    target=directory/'service.json'
    first=secret_delivery.install(source,target)
    assert json.loads(target.read_text())==data
    second=secret_delivery.install(source,target)
    assert first!=second and json.loads(target.read_text())==data


@pytest.mark.parametrize('field',['migration_dsn','billing_dsn','candidate_manifest','fixture_manifest','unknown'])
def test_new_host_bindings_do_not_allow_operator_or_unknown_delivery_fields(tmp_path,field):
    from lab_runner.native_scenarios import native_configuration
    data={'namespace':'fixture','environment':'sandbox','assets':'/srv/lab/assets',
        'principals':{},'harness_dsn':'runtime','accounting_dsn':'runtime','app_dsn':'runtime',
        'native':native_configuration('effects-fixture'),'legacy_bundles':{},field:'PRIVATE'}
    source=tmp_path/'service.json';source.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='^invalid runtime config$'):read_runtime_config(source)

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
