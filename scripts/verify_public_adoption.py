"""Verify five exact releases through an isolated ordinary PyPI consumer install."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from prosaic_integration_lab.dependencies import (SDK_NAMES, manifest_bytes,
    manifest_digest, normalize_name, sdk_manifest, verified_wheel_paths)

INDEX = 'https://pypi.org/simple'
MAX_REPORT_BYTES = 4 * 1024 * 1024


def verify_report(report, manifest):
    """Pip's resolved identities must agree with the manifest's wheel archives."""
    if type(report) is not dict or report.get('version') != '1' or type(report.get('install')) is not list:
        raise ValueError('invalid pip report')
    expected = {normalize_name(item['distribution']): item for item in manifest['artifacts']}
    family = SDK_NAMES | {'b3-' + name for name in SDK_NAMES}
    found, seen = {}, set()
    for entry in report['install']:
        metadata = entry.get('metadata', {})
        name = normalize_name(metadata.get('name', ''))
        if not name or name in seen:
            raise ValueError('duplicate or invalid resolved distribution')
        seen.add(name)
        if name in family and name not in expected:
            raise ValueError('resolved SDK family mismatch')
        download = entry.get('download_info', {})
        url = urlsplit(download.get('url', ''))
        if (entry.get('is_direct') is not False or url.scheme != 'https' or
                url.hostname != 'files.pythonhosted.org' or url.username or url.password or
                url.query or url.fragment):
            raise ValueError('resolution did not use ordinary public-index archives')
        if name not in expected:
            continue
        item = expected[name]
        if (metadata.get('version') != item['version'] or entry.get('requested') is not True or
                unquote(Path(url.path).name) != item['filename'] or
                download.get('archive_info', {}).get('hashes', {}).get('sha256') != item['sha256']):
            raise ValueError('resolved release identity/archive checksum mismatch')
        found[name] = {key: item[key] for key in ('distribution', 'version', 'sha256')}
    if found.keys() != expected.keys():
        raise ValueError('resolved release family is incomplete')
    return [found[name] for name in sorted(found)]


def isolated_environment():
    # Pip --isolated also ignores user configuration; remove inherited interpreter,
    # installer, proxy and TLS overrides before creating the fresh environment.
    excluded = {'VIRTUAL_ENV', '__PYVENV_LAUNCHER__', 'REQUESTS_CA_BUNDLE',
        'CURL_CA_BUNDLE', 'SSL_CERT_FILE', 'SSL_CERT_DIR'}
    environment = {name: value for name, value in os.environ.items()
        if not name.startswith(('PYTHON', 'PIP_')) and not name.lower().endswith('_proxy')
        and name not in excluded}
    # Pip honors this special file selector even with --isolated. It disables
    # system/site configuration too, including an unexpected extra index.
    environment['PIP_CONFIG_FILE'] = os.devnull
    # Pip's session still trusts ambient Requests/urllib configuration under
    # --isolated. Explicit bypass also blocks system proxies; NETRC prevents
    # Requests and pip's own auth layer from consulting user credential files.
    environment.update(no_proxy='*', NO_PROXY='*', NETRC=os.devnull)
    return environment


def run(argv, *, directory, environment, timeout=180):
    # Raw logs are private even when pip prints credential-bearing local config.
    with tempfile.TemporaryFile(dir=directory) as stdout, tempfile.TemporaryFile(dir=directory) as stderr:
        result = subprocess.run([str(arg) for arg in argv], cwd=directory, env=environment,
            stdout=stdout, stderr=stderr, timeout=timeout, check=False)
        if result.returncode:
            raise ValueError('isolated public consumer command failed')
        stdout.seek(0)
        return stdout.read(65537)


PUBLIC_EXAMPLE = '''import importlib
from importlib.metadata import distribution, packages_distributions
import json
from pathlib import Path
import sys
from prosaic_harness import WorkflowBindings, WorkflowCatalog, WorkflowFactory, WorkflowPolicy
from prosaic_runtime import EndpointConfig, RuntimeConfig, ProsaicArtifact
data = json.loads(Path(sys.argv[1]).read_text())
owners = packages_distributions()
for item in data['artifacts']:
    name = item['distribution']
    module_name = (name[3:] if name.startswith('b3-') else name).replace('-', '_')
    dist = distribution(name)
    module = importlib.import_module(module_name)
    expected = Path(dist.locate_file(module_name + '/__init__.py')).resolve()
    assert dist.version == item['version']
    assert set(owners.get(module_name, [])) == {name}
    assert Path(module.__file__).resolve() == expected
    assert expected.is_relative_to(Path(sys.prefix).resolve())
config = RuntimeConfig({'local': EndpointConfig('http://127.0.0.1:9/v1', 'adoption-construction')}, {}, 'local')
agent = ProsaicArtifact.from_inspection({'id': 'adoption/agent.md', 'type': 'subagent',
    'frontmatter': {'name': 'example', 'description': 'Public construction', 'tools': []},
    'body': 'Return only JSON with result set to ok.'})
schema = {'type': 'object', 'properties': {'result': {'type': 'string'}},
    'required': ['result'], 'additionalProperties': False}
factory = WorkflowFactory(catalog=WorkflowCatalog(agents={'example': agent}, schemas={'result': schema}),
    bindings=WorkflowBindings(config=config), policy=WorkflowPolicy(allowed_agents=frozenset({'example'}),
    allowed_schemas=frozenset({'result'}), max_calls=1, max_attempts=1,
    max_provider_requests_per_invocation=1, max_tool_calls_per_invocation=0))
factory.build_json(json.dumps({'definition': {'version': 1, 'start': 'ask', 'steps': {
    'ask': {'kind': 'agent', 'agent': 'example', 'schema': 'result', 'next': 'done'},
    'done': {'kind': 'finish', 'requires': ['ask']}}}}))
assert factory.describe()['defaultModelTierAllowed'] is True
'''

# The existing audit helper uses packaging to parse wheel identities. Packaging
# is a test/audit dependency, so use the packaging copy shipped with fresh pip;
# do not install an extra unpinned package into the consumer's resolved graph.
AUDIT_LAUNCH = '''import runpy, sys
from pathlib import Path
import pip
sys.path.insert(0, str(Path(pip.__file__).parent / '_vendor'))
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
'''


def verify(manifest, *, export=None):
    manifest = Path(manifest).resolve()
    receipt = {'event': 'public_adoption', 'passed': False, 'index': INDEX,
        'dependencies_enabled': True, 'wheel_count': 5, 'owned_temporary_cleanup': True,
        'python_version': platform.python_version(), 'platform': platform.system(),
        'architecture': platform.machine()}
    temporary = None
    stage = 'manifest'
    try:
        before = manifest_digest(manifest)
        receipt['manifest_sha256'] = before
        data = sdk_manifest(manifest)
        if 'candidate_lineage' in data or any('qualified_run_id' in i for i in data['artifacts']):
            raise ValueError('candidate artifacts cannot claim public adoption')
        payload = manifest_bytes(manifest)
        if manifest_digest(manifest) != before:
            raise ValueError('manifest changed before installation')
        temporary = tempfile.TemporaryDirectory(prefix='lab-public-adoption-')
        directory = Path(temporary.name).resolve()
        private_manifest = directory / 'manifest.json'
        private_manifest.write_bytes(payload)
        environment = isolated_environment()
        venv = directory / 'consumer'
        stage = 'venv'
        run([sys.executable, '-I', '-m', 'venv', venv], directory=directory, environment=environment)
        python = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        pip = [python, '-I', '-m', 'pip', '--isolated', '--no-input', '--keyring-provider', 'disabled']
        pins = [f"{i['distribution']}=={i['version']}" for i in data['artifacts']]
        report = directory / 'private-pip-report.json'
        stage = 'resolve'
        run([*pip, 'install', '--no-cache-dir', '--index-url', INDEX, '--only-binary=:all:',
            '--report', report, *pins], directory=directory, environment=environment, timeout=300)
        with report.open('rb') as source:
            raw_report = source.read(MAX_REPORT_BYTES + 1)
        if len(raw_report) > MAX_REPORT_BYTES:
            raise ValueError('pip report exceeds limit')
        stage = 'pip_report'
        receipt['distributions'] = verify_report(json.loads(raw_report), data)
        wheels = directory / 'fresh-wheels'
        wheels.mkdir()
        # This independent cache-free transfer verifies actual wheel bytes. The
        # ordinary install above always resolves and installs dependencies.
        stage = 'fresh_download'
        run([*pip, 'download', '--no-cache-dir', '--index-url', INDEX, '--only-binary=:all:',
            '--no-deps', '--dest', wheels, *pins], directory=directory, environment=environment, timeout=300)
        stage = 'wheel_bytes'
        verified_wheel_paths(private_manifest, wheels)
        helper = directory / 'audit-helper'
        (helper / 'scripts').mkdir(parents=True)
        (helper / 'src/prosaic_integration_lab').mkdir(parents=True)
        shutil.copyfile(ROOT / 'scripts/audit_install.py', helper / 'scripts/audit_install.py')
        shutil.copyfile(ROOT / 'src/prosaic_integration_lab/dependencies.py',
            helper / 'src/prosaic_integration_lab/dependencies.py')
        shutil.copyfile(ROOT / 'src/prosaic_integration_lab/sdk_audit.py',
            helper / 'src/prosaic_integration_lab/sdk_audit.py')
        (helper / 'src/prosaic_integration_lab/__init__.py').write_text('')
        stage = 'installed_payloads'
        run([python, '-I', '-B', '-c', AUDIT_LAUNCH, helper / 'scripts/audit_install.py',
            '--manifest', private_manifest, '--wheel-dir', wheels, '--expected-sha', before],
            directory=directory, environment=environment)
        stage = 'pip_check'
        run([*pip, 'check'], directory=directory, environment=environment)
        bin_dir = python.parent
        stage = 'cli'
        for cli in ('prosaic', 'prosaic-runtime', 'prosaic-harness'):
            run([python, '-I', '-B', bin_dir / cli, '--help'], directory=directory, environment=environment)
        version = run([python, '-I', '-B', bin_dir / 'prosaic', '--version'],
            directory=directory, environment=environment)
        core_version = next(i['version'] for i in data['artifacts']
            if normalize_name(i['distribution']) in {'prosaic', 'b3-prosaic'})
        if version.decode('utf-8').strip() != core_version:
            raise ValueError('core CLI version differs from pinned release')
        example = directory / 'public_example.py'
        example.write_text(PUBLIC_EXAMPLE)
        stage = 'public_example'
        run([python, '-I', '-B', example, private_manifest], directory=directory, environment=environment)
        # Audit again after the public imports/CLIs; never certify altered payloads.
        stage = 'final_payload_audit'
        run([python, '-I', '-B', '-c', AUDIT_LAUNCH, helper / 'scripts/audit_install.py',
            '--manifest', private_manifest, '--wheel-dir', wheels, '--expected-sha', before],
            directory=directory, environment=environment)
        stage = 'manifest_recheck'
        if manifest_digest(manifest) != before or manifest_digest(private_manifest) != before:
            raise ValueError('manifest changed during adoption')
        receipt.update(passed=True, pip_report_verified=True, fresh_wheel_bytes_verified=True,
            installed_payloads_verified=True, import_ownership_verified=True, cli_verified=True,
            pip_check_passed=True, public_factory_constructed=True)
    except Exception:
        receipt['failure'] = 'public_adoption_failed'
        receipt['failure_stage'] = stage
    finally:
        if temporary is not None:
            try:
                temporary.cleanup()
            except Exception:
                receipt.update(passed=False, owned_temporary_cleanup=False, failure='public_adoption_failed',
                    failure_stage='cleanup')
    if export is not None:
        target = Path(export)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'dependencies/releases.json')
    parser.add_argument('--export', type=Path)
    args = parser.parse_args(argv)
    receipt = verify(args.manifest, export=args.export)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
