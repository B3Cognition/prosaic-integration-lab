"""Ordinary-index commands and sanitized provenance without contacting PyPI."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest
from tests.functional.test_dependency_install import wheel_family

ROOT = Path(__file__).resolve().parents[2]


def implementation():
    path = ROOT / 'scripts/verify_public_adoption.py'
    assert path.is_file(), 'ordinary public-index adoption verifier is missing'
    spec = importlib.util.spec_from_file_location('verify_public_adoption', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def report_for(manifest):
    return {'version': '1', 'install': [{'metadata': {'name': item['distribution'], 'version': item['version']},
        'requested': True, 'is_direct': False, 'download_info': {
            'url': 'https://files.pythonhosted.org/packages/fixture/' + item['filename'],
            'archive_info': {'hashes': {'sha256': item['sha256']}}}}
        for item in json.loads(manifest.read_text())['artifacts']]}


def test_report_verifies_exact_five_archive_identities_and_hashes(tmp_path):
    manifest, _, _ = wheel_family(tmp_path)
    module = implementation()
    receipt = module.verify_report(report_for(manifest), json.loads(manifest.read_text()))
    assert len(receipt) == 5
    assert all(set(row) == {'distribution', 'version', 'sha256'} for row in receipt)


@pytest.mark.parametrize('tamper', ['hash', 'name', 'version', 'missing', 'duplicate', 'direct', 'host', 'old-family'])
def test_report_cannot_certify_changed_or_mixed_sdk_artifacts(tmp_path, tamper):
    manifest, _, _ = wheel_family(tmp_path, renamed=True)
    report = report_for(manifest)
    row = report['install'][0]
    if tamper == 'hash': row['download_info']['archive_info']['hashes']['sha256'] = '0' * 64
    elif tamper == 'name': row['metadata']['name'] = 'unexpected-sdk'
    elif tamper == 'version': row['metadata']['version'] = '999.0'
    elif tamper == 'missing': report['install'].pop()
    elif tamper == 'duplicate': report['install'].append(row.copy())
    elif tamper == 'direct': row['is_direct'] = True
    elif tamper == 'host': row['download_info']['url'] = 'https://secret:token@evil.invalid/wheel.whl'
    else:
        report['install'].append({'metadata': {'name': 'prosaic', 'version': '1.0'},
            'download_info': {'url': 'https://files.pythonhosted.org/old.whl'}})
    with pytest.raises(ValueError):
        implementation().verify_report(report, json.loads(manifest.read_text()))


def fake_process(manifest, cache, commands, environments, *, fail=False, mutate=None):
    def run(argv, **kwargs):
        commands.append(list(argv))
        environments.append(kwargs)
        assert Path(kwargs['cwd']).resolve() != ROOT
        assert 'PYTHONPATH' not in kwargs['env'] and 'PIP_EXTRA_INDEX_URL' not in kwargs['env']
        assert '-I' in argv
        if 'venv' in argv:
            (Path(argv[-1]) / 'bin').mkdir(parents=True)
        elif 'install' in argv:
            assert '--no-deps' not in argv
            assert '--isolated' in argv and '--no-cache-dir' in argv
            assert argv[argv.index('--index-url') + 1] == 'https://pypi.org/simple'
            assert set(arg for arg in argv if '==' in arg) == {
                f"{i['distribution']}=={i['version']}" for i in json.loads(manifest.read_text())['artifacts']}
            Path(argv[argv.index('--report') + 1]).write_text(json.dumps(report_for(manifest)))
            if fail:
                return subprocess.CompletedProcess(argv, 1, 'secret-in-stdout', 'secret-in-stderr')
        elif 'download' in argv:
            directory = Path(argv[argv.index('--dest') + 1])
            directory.mkdir(exist_ok=True)
            for wheel in cache.iterdir(): shutil.copyfile(wheel, directory / wheel.name)
        if mutate and 'check' in argv:
            mutate()
        if '--version' in argv:
            kwargs['stdout'].write(b'1.0\n')
        return subprocess.CompletedProcess(argv, 0, 'secret-in-stdout', 'secret-in-stderr')
    return run


def test_fresh_adoption_uses_normal_resolver_audits_and_cleans_only_owned_temp(tmp_path, monkeypatch):
    manifest, cache, _ = wheel_family(tmp_path)
    module = implementation()
    monkeypatch.setenv('PYTHONPATH', '/sibling/source')
    monkeypatch.setenv('PIP_EXTRA_INDEX_URL', 'https://private:secret@private.invalid/simple')
    commands, environments = [], []
    monkeypatch.setattr(module.subprocess, 'run', fake_process(manifest, cache, commands, environments))
    export = tmp_path / 'receipt.json'
    receipt = module.verify(manifest, export=export)
    assert receipt['passed'] is True
    assert receipt['manifest_sha256'] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert receipt['dependencies_enabled'] is True and receipt['wheel_count'] == 5
    assert receipt['owned_temporary_cleanup'] is True
    assert not any(Path(kwargs['cwd']).exists() for kwargs in environments)
    assert any('audit_install.py' in str(arg) for argv in commands for arg in argv)
    assert any('public_example.py' in str(arg) for argv in commands for arg in argv)
    assert any('check' in argv for argv in commands)
    assert all(any(cli in str(arg) for argv in commands for arg in argv)
        for cli in ('prosaic', 'prosaic-runtime', 'prosaic-harness'))
    assert json.loads(export.read_text()) == receipt
    assert 'secret' not in export.read_text() and '/sibling' not in export.read_text()
    assert cache.is_dir() and manifest.is_file()


def test_failed_installer_exports_no_raw_logs_or_report_and_removes_environment(tmp_path, monkeypatch):
    manifest, cache, _ = wheel_family(tmp_path)
    module = implementation()
    commands, environments = [], []
    monkeypatch.setattr(module.subprocess, 'run', fake_process(manifest, cache, commands, environments, fail=True))
    export = tmp_path / 'safe-failure.json'
    receipt = module.verify(manifest, export=export)
    assert receipt['passed'] is False and receipt['failure'] == 'public_adoption_failed'
    assert 'secret' not in export.read_text()
    assert not any(Path(kwargs['cwd']).exists() for kwargs in environments)
    assert manifest.exists() and cache.exists()


def test_manifest_change_cannot_produce_success_receipt(tmp_path, monkeypatch):
    manifest, cache, _ = wheel_family(tmp_path)
    module = implementation()
    commands, environments = [], []
    mutate = lambda: manifest.write_text(manifest.read_text() + '\n')
    monkeypatch.setattr(module.subprocess, 'run', fake_process(manifest, cache, commands, environments, mutate=mutate))
    receipt = module.verify(manifest)
    assert receipt['passed'] is False
    assert receipt['owned_temporary_cleanup'] is True


def test_candidate_manifest_rejected_before_any_external_process(tmp_path, monkeypatch):
    manifest, _, _ = wheel_family(tmp_path)
    data = json.loads(manifest.read_text()); data['candidate_lineage'] = {'version': 1}
    manifest.write_text(json.dumps(data))
    module = implementation()
    def forbidden(*_args, **_kwargs): raise AssertionError('candidate must never reach pip or venv')
    monkeypatch.setattr(module.subprocess, 'run', forbidden)
    receipt = module.verify(manifest)
    assert receipt['passed'] is False and receipt['failure'] == 'public_adoption_failed'


def test_isolation_disables_global_pip_config_and_removes_inherited_proxies(monkeypatch):
    monkeypatch.setenv('PIP_CONFIG_FILE', '/private/config')
    monkeypatch.setenv('HTTPS_PROXY', 'http://private:secret@proxy.invalid')
    environment = implementation().isolated_environment()
    assert environment['PIP_CONFIG_FILE'] == os.devnull
    assert 'HTTPS_PROXY' not in environment
