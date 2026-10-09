import shutil
from pathlib import Path
import pytest
import yaml
from fastapi.testclient import TestClient
from prosaic_integration_lab import app as service
from prosaic_integration_lab import execution

def test_http_startup_refuses_missing_budget_before_database_resources(monkeypatch,tmp_path):
    assets = tmp_path/'assets'
    shutil.copytree(Path(__file__).resolve().parents[2]/'assets',assets)
    workflow = yaml.safe_load((assets/'synthetic.yml').read_text())
    del workflow['limits']['max_tokens']
    (assets/'synthetic.yml').write_text(yaml.safe_dump(workflow))
    touched = []
    def forbidden(*args):
        touched.append('database')
        raise AssertionError('unbounded policy must fail before database construction')
    monkeypatch.setattr(execution,'Metadata',forbidden)
    monkeypatch.setattr(service,'load_config',lambda:{'assets':str(assets),'principals':{}})
    with pytest.raises(RuntimeError,match='startup configuration failed'):
        with TestClient(service.create_app()): pass
    assert touched == []
