import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from .stack import OwnedStack, ROOT


def main():
    parser = argparse.ArgumentParser(description='Required owned synthetic acceptance; no paid calls')
    parser.add_argument('command', choices=['test'])
    parser.add_argument('--mode', choices=['provisioning', 'deterministic', 'load', 'recovery'], default='deterministic')
    parser.add_argument('--engine', choices=['docker', 'podman'], default='docker')
    parser.add_argument('--postgres-version', type=int, choices=[16, 18], default=16)
    args = parser.parse_args()
    stack = OwnedStack(args.engine, args.postgres_version)
    started = time.monotonic()
    result = {'owner': stack.owner, 'mode': args.mode, 'host_architecture': platform.machine(),
              'python': platform.python_version(), 'passed': False, 'cleanup': 'pending'}
    try:
        stack.start()
        if args.mode != 'provisioning':
            stack.start_model()
            stack.start_replica('a')
            stack.start_replica('b')
        config_path = stack.secrets / 'host.json'
        config = json.loads(config_path.read_text())
        config.update(stack.manifest['endpoints'])
        config_path.write_text(json.dumps(config))
        files = ['tests/acceptance/test_provisioning.py']
        if args.mode != 'provisioning':
            files += ['tests/acceptance/test_approval.py', 'tests/acceptance/test_authorization.py', 'tests/acceptance/test_idempotency.py', 'tests/acceptance/test_accounting.py', 'tests/acceptance/test_coverage.py']
            files += ['tests/acceptance/test_reservations.py']
        if args.mode == 'load':
            files += ['tests/acceptance/test_load.py']
        if args.mode == 'recovery':
            files += ['tests/acceptance/test_accounting_failures.py', 'tests/acceptance/test_recovery.py']
        test = subprocess.run([sys.executable, '-m', 'pytest', *files, '-q',
            f'--junitxml={stack.directory / "junit.xml"}'], cwd=ROOT,
            env={**os.environ, 'LAB_ACCEPTANCE_CONFIG': str(config_path)}, capture_output=True, text=True, timeout=180)
        # Failure tracebacks can contain request/config values. Retain only
        # testcase identity/status and constant error text in exported JUnit.
        junit = ET.parse(stack.directory / 'junit.xml')
        skipped = 0
        result['failed_tests'] = []
        for case in junit.iter('testcase'):
            for child in list(case):
                if child.tag == 'skipped':
                    skipped += 1
                if child.tag in {'failure', 'error', 'skipped'}:
                    if child.tag != 'skipped':
                        result['failed_tests'].append(case.attrib['name'])
                    # Keep only exception type and assertion expression, not
                    # rendered locals, values or driver diagnostics.
                    child.attrib.clear()
                    child.text = 'Required acceptance assertion failed; reproduce with the owned runner'
                else:
                    case.remove(child)
        junit.write(stack.directory / 'junit.xml', encoding='unicode')
        result['test_count'] = len(list(junit.iter('testcase')))
        result['passed'] = test.returncode == 0 and skipped == 0 and result['test_count'] > 0
        result['skipped'] = skipped
    except Exception as error:
        result['error'] = type(error).__name__
    finally:
        try:
            stack.stop()
            result['cleanup'] = 'verified'
        except Exception:
            result['cleanup'] = 'failed'
            result['passed'] = False
        result['seconds'] = round(time.monotonic() - started, 2)
        result['images'] = stack.manifest['images']
        (stack.directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))
        print(f'Evidence: {stack.directory}')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
