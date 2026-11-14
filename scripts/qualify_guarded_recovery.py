"""Qualify the copied recovery blueprint against the pinned released SDKs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from xml.etree import ElementTree

from conversation_distribution_smoke import extract_sdist
from qualify_catalogue_ontology import run

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    'guarded-recovery': ('guarded_recovery_acceptance/test_guarded_recovery.py',
        'test_copied_guarded_recovery', ('anthropic', 'openai-compatible')),
    'nemotron-correction': ('nemotron_correction_acceptance/test_nemotron_correction.py',
        'test_copied_nemotron_correction', ('ignored', 'optional', 'required', 'ungrounded')),
}


def qualify(origin, export, archive=None, profile="guarded-recovery"):
    test_path, test_name, modes = CASES[profile]
    with tempfile.TemporaryDirectory(prefix='lab-guarded-recovery-') as directory:
        work = Path(directory)
        source = ROOT
        build = [sys.executable, '-m', 'build', '--no-isolation']
        if origin == 'sdist':
            if archive is None:
                run(*build, '--sdist', '-o', work / 'sdist', ROOT)
                archive, = (work / 'sdist').glob('*.tar.gz')
            source = extract_sdist(archive, work / 'source')
        if origin == 'wheel' and archive is not None:
            wheel = archive
        else:
            run(*build, '--wheel', '-o', work / 'wheel', source)
            wheel, = (work / 'wheel').glob('*.whl')
        manifest = source / f'dependencies/releases-{profile}.json'
        run(sys.executable, '-m', 'venv', work / 'consumer')
        python = work / 'consumer/bin/python'
        run(python, '-m', 'pip', 'install', '--require-hashes',
            '-r', source / 'dependencies/requirements.lock')
        cache = work / 'wheels'
        run(python, source / 'scripts/prepare_dependencies.py', '--manifest', manifest, '--cache-root', cache)
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        run(python, source / 'scripts/install_dependencies.py', '--manifest', manifest,
            '--wheel-dir', cache / digest, '--expected-sha', digest)
        run(python, source / 'scripts/audit_install.py', '--manifest', manifest,
            '--wheel-dir', cache / digest, '--expected-sha', digest)
        run(python, '-m', 'pip', 'install', '--no-deps', wheel)
        run(python, '-m', 'pip', 'check')
        report = work / 'report.xml'
        run(python, '-I', '-m', 'pytest', '-o', 'pythonpath=', '-q',
            source / 'tests' / test_path,
            '--junitxml', report, cwd=work,
            env={**os.environ, 'PROSAIC_BLUEPRINT_INSTALLED': '1', 'NO_PROXY': '*', 'no_proxy': '*'})
        suite, = ElementTree.parse(report).getroot().iter('testsuite')
        counts = {key: int(suite.attrib[key]) for key in ('tests', 'failures', 'errors', 'skipped')}
        cases = sorted(case.attrib['name'] for case in suite.iter('testcase'))
        if (counts != {'tests': len(modes), 'failures': 0, 'errors': 0, 'skipped': 0}
                or cases != sorted(f'{test_name}[{mode}]' for mode in modes)):
            raise ValueError(f'incomplete {profile} acceptance')
        export.write_text(json.dumps({'version': 1, 'origin': origin, 'counts': counts,
            'cases': cases, 'manifestSha256': digest, 'liveProvider': False}, sort_keys=True) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', choices=('wheel', 'sdist'), required=True)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--archive', type=Path, help='Test an already verified release archive')
    parser.add_argument('--profile', choices=CASES, default='guarded-recovery')
    args = parser.parse_args()
    qualify(args.origin, args.export, args.archive, args.profile)
