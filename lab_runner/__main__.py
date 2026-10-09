import argparse
import json
import os
import platform
import subprocess
import sys
import time

from .stack import OwnedStack, ROOT
from .results import sanitize_junit


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
            files += ['tests/acceptance/test_accounting_failures.py', 'tests/acceptance/test_recovery.py', 'tests/acceptance/test_scope.py']
        test = subprocess.run([sys.executable, '-m', 'pytest', *files, '-q',
            f'--junitxml={stack.directory / "junit.xml"}'], cwd=ROOT,
            env={**os.environ, 'LAB_ACCEPTANCE_CONFIG': str(config_path)}, capture_output=True, text=True, timeout=180)
        result['test_returncode'] = test.returncode
    except Exception as error:
        result['error'] = type(error).__name__
    finally:
        junit = stack.directory / 'junit.xml'
        if junit.exists():
            try:
                result.update(sanitize_junit(junit))
                result['passed'] = (result.get('test_returncode') == 0 and 'error' not in result
                    and result['skipped'] == 0 and result['test_count'] > 0 and not result['failed_tests'])
            except Exception:
                # Never leave a raw/incomplete export after timeout or errors.
                junit.unlink(missing_ok=True)
                result['error'] = 'InvalidJUnitExport'
                result['passed'] = False
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
