import json
import pytest
from lab_runner.secret_delivery import read_runtime_config

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
