import importlib.util
import hashlib
import json
from pathlib import Path
import pytest
from tests.functional.test_dependency_install import wheel_family
from importlib import metadata

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


def audit_fixture(tmp_path, monkeypatch):
    manifest, cache, site = wheel_family(tmp_path, install=True)
    spec=importlib.util.spec_from_file_location('audit_install',Path(__file__).resolve().parents[2]/'scripts/audit_install.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    found = list(metadata.distributions(path=[str(site)]))
    monkeypatch.setattr(module, 'distributions', lambda: iter(found), raising=False)
    monkeypatch.syspath_prepend(str(site))
    return module.audit, manifest, cache, site


def test_correct_version_but_modified_installed_code_is_rejected(tmp_path, monkeypatch):
    audit, manifest, cache, site = audit_fixture(tmp_path, monkeypatch)
    (site / 'prosaic/__init__.py').write_text('VALUE = "tampered"\n')
    with pytest.raises(ValueError, match='payload'):
        audit(manifest, cache)


def test_audit_rejects_import_shadow_outside_verified_install(tmp_path, monkeypatch):
    audit, manifest, cache, site = audit_fixture(tmp_path, monkeypatch)
    shadow = tmp_path / 'shadow'; (shadow / 'prosaic').mkdir(parents=True)
    (shadow / 'prosaic/__init__.py').write_text('VALUE = "shadow"\n')
    monkeypatch.syspath_prepend(str(shadow))
    with pytest.raises(ValueError, match='import payload'):
        audit(manifest, cache)


def test_historical_clean_environment_is_auditable(tmp_path, monkeypatch):
    audit, manifest, cache, _ = audit_fixture(tmp_path, monkeypatch)
    audit(manifest, cache)


def test_audit_rejects_unexpected_same_module_distribution(tmp_path, monkeypatch):
    audit, manifest, cache, site = audit_fixture(tmp_path, monkeypatch)
    alien = site / 'alien-1.0.dist-info'; alien.mkdir()
    (alien / 'METADATA').write_text('Metadata-Version: 2.1\nName: alien\nVersion: 1.0\n')
    (alien / 'RECORD').write_text('prosaic/__init__.py,,\n')
    # Use real distribution discovery after the conflicting RECORD exists.
    module = audit.__globals__
    module['distributions'] = lambda: metadata.distributions(path=[str(site)])
    with pytest.raises(ValueError, match='conflicting'):
        audit(manifest, cache)


def test_audit_rejects_additional_installed_import_code(tmp_path, monkeypatch):
    audit, manifest, cache, site = audit_fixture(tmp_path, monkeypatch)
    (site / 'prosaic/injected.py').write_text('VALUE = "injected"\n')
    with pytest.raises(ValueError, match='unexpected import payload'):
        audit(manifest, cache)


def test_audit_rejects_additional_sourceless_import_code(tmp_path, monkeypatch):
    audit, manifest, cache, site = audit_fixture(tmp_path, monkeypatch)
    (site / 'prosaic/injected.pyc').write_bytes(b'unverified sourceless bytecode')
    with pytest.raises(ValueError, match='unexpected import payload'):
        audit(manifest, cache)


@pytest.mark.parametrize('optimization', [0, 1, 2])
@pytest.mark.parametrize('mode', ['TIMESTAMP', 'UNCHECKED_HASH'])
def test_audit_cannot_certify_an_altered_executable_hash_cache(tmp_path, monkeypatch, optimization, mode):
    import os
    import py_compile
    import subprocess
    import sys
    audit, manifest, cache, site = audit_fixture(tmp_path, monkeypatch)
    source = site / 'prosaic/__init__.py'
    original = source.read_bytes()
    source.write_text('VALUE = "modified"\n')
    timestamp = source.stat().st_mtime_ns
    py_compile.compile(str(source), doraise=True,
                       invalidation_mode=getattr(py_compile.PycInvalidationMode, mode),
                       optimize=optimization)
    source.write_bytes(original)
    os.utime(source, ns=(timestamp, timestamp))
    with pytest.raises(ValueError, match='cached import payload'):
        audit(manifest, cache)
    flags = ['-' + 'O' * optimization] if optimization else []
    imported = subprocess.run([sys.executable, '-B', *flags, '-c', 'import prosaic; print(prosaic.VALUE)'],
                              env={**os.environ, 'PYTHONPATH': str(site)}, cwd=tmp_path,
                              capture_output=True, text=True, check=True)
    assert imported.stdout.strip() == 'modified'


@pytest.mark.parametrize('optimization', [0, 1, 2])
@pytest.mark.parametrize('mode', ['TIMESTAMP', 'CHECKED_HASH', 'UNCHECKED_HASH'])
def test_verified_source_cache_remains_auditable_and_imports_verified_code(tmp_path, monkeypatch, optimization, mode):
    import os
    import py_compile
    import subprocess
    import sys
    audit, manifest, cache, site = audit_fixture(tmp_path, monkeypatch)
    py_compile.compile(str(site / 'prosaic/__init__.py'), doraise=True, optimize=optimization,
                       invalidation_mode=getattr(py_compile.PycInvalidationMode, mode))
    audit(manifest, cache)
    flags = ['-' + 'O' * optimization] if optimization else []
    imported = subprocess.run([sys.executable, '-B', *flags, '-c', 'import prosaic; print(prosaic.VALUE)'],
                              env={**os.environ, 'PYTHONPATH': str(site)}, cwd=tmp_path,
                              capture_output=True, text=True, check=True)
    assert imported.stdout.strip() == 'verified'


def test_audit_rejects_conflicting_import_files_between_selected_wheels(tmp_path, monkeypatch):
    import zipfile
    audit, manifest, cache, _ = audit_fixture(tmp_path, monkeypatch)
    path = cache / 'prosaic_runtime-1.0-py3-none-any.whl'
    with zipfile.ZipFile(path, 'a') as archive:
        archive.writestr('prosaic/__init__.py', 'VALUE = "conflict"\n')
    data = json.loads(manifest.read_text())
    data['artifacts'][1]['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='conflicting shared import'):
        audit.__globals__['wheel_payloads'](manifest, cache)
