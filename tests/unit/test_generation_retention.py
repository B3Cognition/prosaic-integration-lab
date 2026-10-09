import json
import os
import pytest
from lab_runner import secret_delivery as delivery

def test_generation_ceiling_preserves_current_credentials_without_deleting_orphans(tmp_path,monkeypatch):
    monkeypatch.setattr(delivery,'RUNTIME_UID',os.getuid()); monkeypatch.setattr(delivery,'RUNTIME_GID',os.getgid())
    monkeypatch.setattr(delivery,'MAX_GENERATIONS',1,raising=False)
    directory=tmp_path/'volume'; directory.mkdir(mode=0o700)
    source=tmp_path/'source.json'; source.write_text(json.dumps({'namespace':'fixture','environment':'sandbox',
        'assets':'assets','principals':{},'harness_dsn':'runtime','accounting_dsn':'runtime','app_dsn':'runtime'}))
    target=directory/'service.json'
    delivery.install(source,target)
    original=target.read_bytes(); pointer=os.readlink(target)
    with pytest.raises(ValueError,match='generation capacity'): delivery.install(source,target)
    assert target.read_bytes()==original and os.readlink(target)==pointer
    assert len(list((directory/'generations').iterdir()))==1
