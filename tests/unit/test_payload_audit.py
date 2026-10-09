import importlib.util
import hashlib
import json
from pathlib import Path
import pytest

def implementation():
    path=Path(__file__).resolve().parents[2]/'scripts/audit_install.py'
    spec=importlib.util.spec_from_file_location('audit_install',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.audit

def test_payload_audit_rejects_manifest_forgery_before_inspecting_packages(tmp_path):
    manifest=tmp_path/'manifest.json'; manifest.write_text('{"artifacts":[]}')
    with pytest.raises(ValueError,match='manifest'):
        implementation()(manifest,tmp_path,expected_sha='0'*64)

def test_payload_audit_checks_original_wheel_hash_before_package_payload(tmp_path):
    wheel=tmp_path/'fixture.whl'; wheel.write_bytes(b'changed wheel')
    manifest=tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'artifacts':[{'filename':'fixture.whl','sha256':'0'*64,
        'distribution':'not-installed','version':'1.0'}]}))
    with pytest.raises(ValueError,match='checksum'):
        implementation()(manifest,tmp_path,expected_sha=hashlib.sha256(manifest.read_bytes()).hexdigest())
