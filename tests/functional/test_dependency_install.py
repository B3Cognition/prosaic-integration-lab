"""Real script boundaries with credential-free wheel fixtures."""
import hashlib
import json
import os
from pathlib import Path
import shutil
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


@pytest.mark.parametrize(('renamed', 'expected'), [
    (False, {'prosaic': '1.0', 'prosaic-runtime': '1.0',
             'prosaic-runtime-postgres': '1.0', 'prosaic-harness': '1.0',
             'prosaic-harness-postgres': '1.0'}),
    (True, {'b3-prosaic': '1.0', 'b3-prosaic-runtime': '1.0',
            'b3-prosaic-runtime-postgres': '1.0', 'b3-prosaic-harness': '1.0',
            'b3-prosaic-harness-postgres': '1.0'}),
], ids=['legacy-only', 'b3-only'])
def test_version_cli_reports_the_actual_installed_distribution_family(tmp_path, renamed, expected):
    _, _, site = wheel_family(tmp_path, renamed=renamed, install=True)
    shutil.copytree(ROOT / 'src/prosaic_integration_lab', site / 'prosaic_integration_lab',
                    ignore=shutil.ignore_patterns('__pycache__'))
    # Use real wheel metadata and a fresh process with no host site packages,
    # editable source imports, PYTHONPATH or alternate SDK family to mask errors.
    result = subprocess.run([sys.executable, '-I', '-S', '-c',
        'import runpy, sys; sys.path.insert(0, sys.argv.pop(1)); '
        'runpy.run_module("prosaic_integration_lab", run_name="__main__")',
        str(site), '--version'], cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == expected


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
    def docker(argv, **kwargs):
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
    (checkout / 'dependencies/public-build-inputs.json').write_text(json.dumps({'version': 1, 'files': [
        'src/app.py', 'dependencies/requirements.lock', 'containers/Dockerfile',
        'scripts/install_dependencies.py', 'scripts/build_consumer.py', 'scripts/audit_install.py']}))
    monkeypatch.setattr(module, 'ROOT', checkout)
    def external(argv, **kwargs):
        context = Path(argv[-1])
        assert (context / 'src/app.py').exists()
        assert not (context / 'src/private-research.txt').exists()
        Path(argv[argv.index('--iidfile') + 1]).write_text('sha256:' + '2' * 64)
        return subprocess.CompletedProcess(argv, 0)
    monkeypatch.setattr(module.subprocess, 'run', external)
    assert module.build(manifest, cache, 'fixture:dev', 'released') == 'sha256:' + '2' * 64


def test_build_from_extracted_release_archive_excludes_extra_private_files(tmp_path, monkeypatch):
    import importlib.util
    import io
    import shutil
    import tarfile
    if (ROOT / '.git').exists():
        archive_bytes = subprocess.run(['git', 'archive', 'HEAD'], cwd=ROOT, capture_output=True, check=True).stdout
    else:
        # The same suite is usable when the caller already has a release
        # archive. Repack only its explicit public inputs for this fixture.
        buffer = io.BytesIO()
        files = json.loads((ROOT / 'dependencies/public-build-inputs.json').read_text())['files']
        with tarfile.open(fileobj=buffer, mode='w') as archive:
            for filename in [*files, 'dependencies/public-build-inputs.json']:
                archive.add(ROOT / filename, arcname=filename)
        archive_bytes = buffer.getvalue()
    checkout = tmp_path / 'source-archive'; checkout.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as archive:
        archive.extractall(checkout, filter='data')
    # Apply this release's reviewed helper/inventory to the last committed
    # source archive. After commit these copies are identical to archive bytes.
    shutil.copyfile(ROOT / 'scripts/build_consumer.py', checkout / 'scripts/build_consumer.py')
    shutil.copyfile(ROOT / 'dependencies/public-build-inputs.json', checkout / 'dependencies/public-build-inputs.json')
    # New approved runtime inputs may not be in HEAD before this change is committed.
    # Overlay only missing files from the explicit public inventory, never a directory tree.
    for filename in json.loads((ROOT / 'dependencies/public-build-inputs.json').read_text())['files']:
        destination=checkout/filename
        if not destination.exists():
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/filename,destination)
    assert not (checkout / '.git').exists()
    (checkout / 'src/private-research.txt').write_text('never upload\n')
    spec = importlib.util.spec_from_file_location('archive_build_consumer', checkout / 'scripts/build_consumer.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    manifest, cache, _ = wheel_family(tmp_path)
    original_run = subprocess.run
    def external(argv, **kwargs):
        if argv[0] == 'git': return original_run(argv, **kwargs)
        context = Path(argv[-1])
        assert (context / 'src/prosaic_integration_lab/app.py').exists()
        assert not (context / 'src/private-research.txt').exists()
        assert not (context / '.git').exists()
        Path(argv[argv.index('--iidfile') + 1]).write_text('sha256:' + '3' * 64)
        return subprocess.CompletedProcess(argv, 0)
    monkeypatch.setattr(module.subprocess, 'run', external)
    assert module.build(manifest, cache, 'archive:dev', 'released') == 'sha256:' + '3' * 64


def test_real_sdist_contains_all_public_build_inputs_and_builds_exact_snapshot(tmp_path,monkeypatch):
    import importlib.util
    import tarfile
    output=tmp_path/'sdist'
    built=subprocess.run([sys.executable,'-I','-m','build','--sdist','--outdir',str(output),str(ROOT)],
        capture_output=True,text=True,timeout=120,
        env={name:value for name,value in os.environ.items() if name!='PYTHONPATH'})
    assert built.returncode==0,built.stdout+built.stderr
    archives=list(output.glob('*.tar.gz'))
    assert len(archives)==1
    unpacked=tmp_path/'unpacked'
    unpacked.mkdir()
    with tarfile.open(archives[0]) as archive:
        archive.extractall(unpacked,filter='data')
    checkout=next(unpacked.iterdir())
    inventory=json.loads((checkout/'dependencies/public-build-inputs.json').read_text())['files']
    missing=[name for name in inventory if not (checkout/name).is_file()]
    assert missing==[],f'missing public build inputs: {missing}'
    assert (checkout/'configs/native.example.json').read_bytes()==(ROOT/'configs/native.example.json').read_bytes()
    assert not (checkout/'.git').exists()
    # New acceptance tools must start from the distributed public tree without
    # the caller's checkout or an editable app import supplying missing files.
    for script in ('prepare_sdk_candidates.py','required_acceptance.py'):
        started=subprocess.run([sys.executable,'-I',str(checkout/'scripts'/script),'--help'],
            cwd=tmp_path,capture_output=True,text=True,timeout=15,
            env={name:value for name,value in os.environ.items() if name!='PYTHONPATH'})
        assert started.returncode==0,started.stdout+started.stderr
    spec=importlib.util.spec_from_file_location('sdist_build_consumer',checkout/'scripts/build_consumer.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest,cache,_=wheel_family(tmp_path)
    def external(argv,**kwargs):
        assert argv[0]!='git'
        context=Path(argv[-1])
        for name in inventory:
            if name!='dependencies/releases.json':
                assert (context/name).read_bytes()==(checkout/name).read_bytes()
        assert not (context/'.git').exists()
        Path(argv[argv.index('--iidfile')+1]).write_text('sha256:'+'4'*64)
        return subprocess.CompletedProcess(argv,0)
    monkeypatch.setattr(module.subprocess,'run',external)
    assert module.build(manifest,cache,'sdist:dev','released')=='sha256:'+'4'*64
