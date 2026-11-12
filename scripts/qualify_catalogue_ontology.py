"""Exercise a copied Lab blueprint with the RC or exact ontology candidate SDKs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
CASES = sorted((
    'test_discovery_and_execution_are_offline',
    'test_projection_is_opt_in_scoped_and_detached',
    'test_discovery_bounds_combined_response',
    'test_core_rejects_invalid_attachments[malformed-json]',
    'test_core_rejects_invalid_attachments[duplicate-key]',
    'test_core_rejects_invalid_attachments[unknown-concept]',
    'test_unregistered_aliases_are_rejected[agents]',
    'test_unregistered_aliases_are_rejected[tools]',
    'test_workflow_admission_ignores_ontology_authority',
    'test_exact_installed_sdk_payloads',
    'test_copied_catalogue_and_workflow',
))


def run(*arguments, **options):
    subprocess.run([str(part) for part in arguments], check=True, timeout=300, **options)


def installed(origin, export, manifest=None, wheel_dir=None):
    with tempfile.TemporaryDirectory(prefix='lab-installed-ontology-') as directory:
        work = Path(directory)
        source = ROOT
        if origin == 'sdist':
            run(sys.executable, '-m', 'build', '--no-isolation', '--sdist', '--outdir', work / 'sdist', source)
            archive, = (work / 'sdist').glob('*.tar.gz')
            extracted = work / 'extracted'
            extracted.mkdir()
            with tarfile.open(archive) as contents:
                contents.extractall(extracted, filter='data')
            source, = extracted.iterdir()
        run(sys.executable, '-m', 'build', '--no-isolation', '--wheel', '--outdir', work / 'wheel', source)
        wheel, = (work / 'wheel').glob('*.whl')

        run(sys.executable, '-m', 'venv', work / 'consumer')
        python = work / 'consumer/bin/python'
        run(python, '-m', 'pip', 'install', '--require-hashes', '-r', source / 'dependencies/requirements.lock')
        lock = source / 'dependencies/catalogue-ontology-rc.lock'
        profile = 'rc'
        if manifest is not None:
            sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
            from lab_runner.catalogue_ontology import PACKAGES, validate_manifest
            from prosaic_integration_lab.dependencies import sdk_manifest, verified_wheel_paths

            data = validate_manifest(sdk_manifest(manifest))
            paths = verified_wheel_paths(manifest, wheel_dir)
            names = set(PACKAGES.values()) | {'b3-prosaic-runtime'}
            lock = work / 'ontology-candidate.lock'
            lock.write_text(''.join(
                f'{item["distribution"]} @ {path.resolve().as_uri()} --hash=sha256:{item["sha256"]}\n'
                for item, path in zip(data['artifacts'], paths) if item['distribution'] in names))
            profile = 'candidate'
        run(python, '-m', 'pip', 'install', '--no-deps', '--require-hashes', '-r', lock)
        run(python, '-m', 'pip', 'install', '--no-deps', wheel)
        run(python, '-m', 'pip', 'check')
        report = work / 'tests.xml'
        run(python, '-I', '-m', 'pytest', '-o', 'pythonpath=', '-q',
            source / 'tests/catalogue_ontology_acceptance', f'--junitxml={report}', cwd=work,
            env={**os.environ, 'PROSAIC_LAB_ONTOLOGY_PROFILE': profile})
        raw = report.read_bytes()
        suite, = ElementTree.fromstring(raw).iter('testsuite')
        counts = {name: int(suite.attrib[name]) for name in ('tests', 'failures', 'errors', 'skipped')}
        cases = list(suite.iter('testcase'))
        if (counts != dict(tests=len(CASES), failures=0, errors=0, skipped=0)
                or sorted(case.attrib['name'] for case in cases) != CASES
                or any(case.find(tag) is not None for case in cases for tag in ('failure', 'error', 'skipped'))):
            raise ValueError('incomplete catalogue ontology acceptance')
        export.parent.mkdir(parents=True, exist_ok=True)
        export.write_text(json.dumps({
            'origin': origin, 'profile': profile, **counts, 'cases': CASES,
            'lab_wheel_sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
            'report_sha256': hashlib.sha256(raw).hexdigest(),
            **({'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest()}
               if manifest is not None else {}),
        }, sort_keys=True) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', choices=('wheel', 'sdist'), required=True)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--wheel-dir', type=Path)
    args = parser.parse_args()
    if (args.manifest is None) != (args.wheel_dir is None):
        parser.error('candidate qualification requires both manifest and wheel directory')
    installed(args.origin, args.export, args.manifest, args.wheel_dir)


if __name__ == '__main__':
    main()
