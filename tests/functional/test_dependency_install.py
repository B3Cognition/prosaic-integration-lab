"""Real script boundaries with credential-free wheel fixtures."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
FAMILY = ['prosaic', 'prosaic-runtime', 'prosaic-runtime-postgres',
          'prosaic-harness', 'prosaic-harness-postgres']


def wheel_family(tmp_path, *, renamed=False, install=False):
    manifest = tmp_path / 'manifest.json'
    cache = tmp_path / 'wheels'
    cache.mkdir()
    site = tmp_path / 'site'
    site.mkdir()
    artifacts = []
    for legacy in FAMILY:
        name = ('b3-' if renamed else '') + legacy
        stem = name.replace('-', '_')
        module = legacy.replace('-', '_')
        metadata = f'{stem}-1.0.dist-info/METADATA'
        entries = {
            f'{module}/__init__.py': b'VALUE = "verified"\n',
            metadata: f'Metadata-Version: 2.1\nName: {name}\nVersion: 1.0\n'.encode(),
            f'{stem}-1.0.dist-info/WHEEL': b'Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n',
        }
        path = cache / f'{stem}-1.0-py3-none-any.whl'
        with zipfile.ZipFile(path, 'w') as archive:
            for key, value in entries.items():
                archive.writestr(key, value)
            archive.writestr(f'{stem}-1.0.dist-info/RECORD', '\n'.join(key + ',,' for key in entries) + '\n')
        if install:
            with zipfile.ZipFile(path) as archive:
                archive.extractall(site)
        artifacts.append({'distribution': name, 'version': '1.0', 'filename': path.name,
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest.write_text(json.dumps({'artifacts': artifacts}))
    return manifest, cache, site


def run_installer(manifest, cache, tmp_path, *, installed_site=None):
    hook = tmp_path / 'hook'
    hook.mkdir()
    if installed_site is None:
        installed_site = tmp_path / 'empty-site'; installed_site.mkdir()
    (hook / 'sitecustomize.py').write_text('''import json, os, subprocess
from importlib import metadata
discover = metadata.distributions
metadata.distributions = lambda: discover(path=[os.environ['SDK_TEST_SITE']])
def intercept(args, **kwargs):
    with open(os.environ['PIP_CAPTURE'], 'w') as target: json.dump(args, target)
    return subprocess.CompletedProcess(args, 0)
subprocess.run = intercept
''')
    capture = tmp_path / 'capture.json'
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/install_dependencies.py'),
                             '--manifest', str(manifest), '--wheel-dir', str(cache)],
                            env={**os.environ, 'PYTHONPATH': str(hook), 'PIP_CAPTURE': str(capture),
                                 'SDK_TEST_SITE': str(installed_site)},
                            capture_output=True, text=True)
    return result, capture


def test_installer_passes_only_manifest_wheels_to_pip(tmp_path):
    manifest, cache, _ = wheel_family(tmp_path)
    neighbor = cache / 'prosaic-0.3.1-py3-none-any.whl'
    neighbor.write_bytes(b'historical bytes')
    result, capture = run_installer(manifest, cache, tmp_path)
    assert result.returncode == 0, result.stderr
    argv = json.loads(capture.read_text())
    assert argv[:5] == [sys.executable, '-m', 'pip', 'install', '--no-deps']
    assert argv[5] == '--force-reinstall'
    assert len(argv) == 11
    assert str(neighbor) not in argv
    assert set(argv[6:]) == {str(cache / item['filename']) for item in json.loads(manifest.read_text())['artifacts']}


def test_checksum_failure_launches_no_pip(tmp_path):
    manifest, cache, _ = wheel_family(tmp_path)
    (cache / 'prosaic-1.0-py3-none-any.whl').write_bytes(b'modified')
    result, capture = run_installer(manifest, cache, tmp_path)
    assert result.returncode != 0 and 'checksum' in result.stderr
    assert not capture.exists()


def test_renamed_installer_rejects_existing_legacy_core(tmp_path):
    manifest, cache, site = wheel_family(tmp_path, renamed=True)
    alien = site / 'prosaic-999.dist-info'; alien.mkdir()
    (alien / 'METADATA').write_text('Metadata-Version: 2.1\nName: prosaic\nVersion: 999\n')
    result, capture = run_installer(manifest, cache, tmp_path, installed_site=site)
    assert result.returncode != 0 and 'distribution' in result.stderr
    assert not capture.exists()


def test_build_uses_private_exact_context_and_immutable_image_id(tmp_path, monkeypatch):
    import importlib.util
    path = ROOT / 'scripts/build_consumer.py'
    spec = importlib.util.spec_from_file_location('build_consumer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest, cache, _ = wheel_family(tmp_path)
    (cache / 'historical.whl').write_bytes(b'never copy')
    calls = []
    original_run = module.subprocess.run
    def docker(argv, **kwargs):
        if argv[0] == 'git': return original_run(argv, **kwargs)
        calls.append(argv)
        context = Path(argv[-1])
        expected = hashlib.sha256(manifest.read_bytes()).hexdigest()
        assert (context / 'dependencies/releases.json').read_bytes() == manifest.read_bytes()
        assert len(list((context / '.cache/wheels' / expected).iterdir())) == 5
        assert not (context / '.git').exists() and not (context / '.venv').exists()
        assert '--build-arg' in argv and 'SDK_MANIFEST_SHA256=' + expected in argv
        Path(argv[argv.index('--iidfile') + 1]).write_text('sha256:' + '1' * 64)
        return subprocess.CompletedProcess(argv, 0)
    monkeypatch.setattr(module.subprocess, 'run', docker)
    assert module.build(manifest, cache, 'fixture:dev', 'released') == 'sha256:' + '1' * 64
    assert len(calls) == 1


def test_manifest_change_aborts_before_build(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location('build_consumer', ROOT / 'scripts/build_consumer.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    manifest, cache, _ = wheel_family(tmp_path)
    original = module.verified_wheel_paths
    def mutate(*args):
        paths = original(*args)
        manifest.write_text(manifest.read_text() + '\n')
        return paths
    monkeypatch.setattr(module, 'verified_wheel_paths', mutate)
    def forbidden(*args, **kwargs):
        raise AssertionError('changed manifest must never reach Docker')
    monkeypatch.setattr(module.subprocess, 'run', forbidden)
    with pytest.raises(ValueError, match='manifest changed'):
        module.build(manifest, cache, 'fixture:dev', 'released')


def test_prepare_downloads_atomically_into_selected_cache(tmp_path, monkeypatch):
    import importlib.util
    import io
    spec = importlib.util.spec_from_file_location('prepare_dependencies', ROOT / 'scripts/prepare_dependencies.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    manifest, cache, _ = wheel_family(tmp_path)
    data = json.loads(manifest.read_text())
    blobs = {}
    for item in data['artifacts']:
        item['url'] = 'https://example.invalid/' + item['filename']
        blobs[item['url']] = (cache / item['filename']).read_bytes()
    manifest.write_text(json.dumps(data))
    monkeypatch.setattr(module.urllib.request, 'urlopen', lambda url, timeout: io.BytesIO(blobs[url]))
    selected = module.prepare(manifest, tmp_path / 'download-cache')
    assert selected.name == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert sorted(p.name for p in selected.iterdir()) == sorted(item['filename'] for item in data['artifacts'])
    assert all((selected / item['filename']).read_bytes() == blobs[item['url']] for item in data['artifacts'])


def test_prepare_never_retains_a_bad_or_oversized_download(tmp_path, monkeypatch):
    import importlib.util
    import io
    spec = importlib.util.spec_from_file_location('prepare_dependencies', ROOT / 'scripts/prepare_dependencies.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    manifest, cache, _ = wheel_family(tmp_path)
    data = json.loads(manifest.read_text())
    for item in data['artifacts']: item['url'] = 'https://example.invalid/' + item['filename']
    manifest.write_text(json.dumps(data))
    monkeypatch.setattr(module, 'MAX_ARTIFACT_BYTES', 16, raising=False)
    monkeypatch.setattr(module.urllib.request, 'urlopen', lambda url, timeout: io.BytesIO(b'x' * 17))
    with pytest.raises(ValueError, match='size limit'):
        module.prepare(manifest, tmp_path / 'download-cache')
    assert not list((tmp_path / 'download-cache').rglob('*.whl'))
    assert not list((tmp_path / 'download-cache').rglob('*.download'))


def test_build_excludes_untracked_files_inside_public_directories(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location('build_consumer', ROOT / 'scripts/build_consumer.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    manifest, cache, _ = wheel_family(tmp_path)
    checkout = tmp_path / 'checkout'
    (checkout / 'src').mkdir(parents=True)
    (checkout / 'src/app.py').write_text('# tracked public source\n')
    (checkout / 'src/private-research.txt').write_text('must never upload\n')
    for name in ('scripts', 'assets', 'lab_runner', 'containers', 'dependencies'):
        (checkout / name).mkdir()
    for filename in ('scripts/install_dependencies.py', 'scripts/build_consumer.py', 'scripts/audit_install.py',
                     'dependencies/requirements.lock', 'containers/Dockerfile'):
        (checkout / filename).write_text('# public\n')
    monkeypatch.setattr(module, 'ROOT', checkout)
    def external(argv, **kwargs):
        if argv[0] == 'git':
            return subprocess.CompletedProcess(argv, 0, stdout='src/app.py\0dependencies/requirements.lock\0containers/Dockerfile\0')
        context = Path(argv[-1])
        assert (context / 'src/app.py').exists()
        assert not (context / 'src/private-research.txt').exists()
        Path(argv[argv.index('--iidfile') + 1]).write_text('sha256:' + '2' * 64)
        return subprocess.CompletedProcess(argv, 0)
    monkeypatch.setattr(module.subprocess, 'run', external)
    assert module.build(manifest, cache, 'fixture:dev', 'released') == 'sha256:' + '2' * 64
