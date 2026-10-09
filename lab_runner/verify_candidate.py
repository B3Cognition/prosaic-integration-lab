"""Explicitly test an unpublished upstream adapter in an owned PostgreSQL fixture."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .results import sanitize_junit
from .stack import OwnedStack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--postgres-version', type=int, choices=[16,18], default=16)
    parser.add_argument('--library', choices=['runtime','harness'], default='runtime')
    args = parser.parse_args()
    source = args.source.resolve()
    required = 'test_readiness_postgres.py' if args.library == 'runtime' else 'test_registration.py'
    if not (source / 'adapters/postgres/tests' / required).is_file():
        parser.error('source must contain the candidate readiness regression suite')
    stack = OwnedStack('docker', args.postgres_version)
    result = {'owner':stack.owner, 'mode':f'unpublished-{args.library}-candidate', 'passed':False,
              'cleanup':'pending', 'postgres_major':args.postgres_version}
    started = time.monotonic()
    try:
        stack.start()
        config = json.loads((stack.secrets / 'host.json').read_text())
        environment = {**os.environ, 'METERING_TEST_DSN':config['migration_dsn'],
            'METERING_RUNTIME_DSN':config['accounting_dsn'], 'PROSAIC_OWNED_DB_AUDIT':'1',
            'HARNESS_EXISTING_RUNTIME_DSN':config['harness_dsn'],
            'PYTHONPATH':str(source / 'adapters/postgres/src'),
            'PATH':str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH','')}
        files = ['adapters/postgres/tests/test_readiness.py','adapters/postgres/tests/test_readiness_postgres.py',
                 'adapters/postgres/tests/test_postgres.py'] if args.library == 'runtime' else ['adapters/postgres/tests/test_registration.py']
        test = subprocess.run([sys.executable,'-m','pytest','-q',*files, '--junitxml=' + str(stack.directory / 'junit.xml')],
            cwd=source, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        result['test_returncode'] = test.returncode
    except Exception as error:
        result['error'] = type(error).__name__
    finally:
        junit = stack.directory / 'junit.xml'
        if junit.exists():
            try:
                result.update(sanitize_junit(junit))
                result['passed'] = result.get('test_returncode') == 0 and not result['failed_tests'] and result['skipped'] == 0 and result['test_count'] > 0
            except Exception:
                junit.unlink(missing_ok=True)
                result['error'] = 'InvalidJUnitExport'
        try:
            stack.stop()
            result['cleanup'] = 'verified'
        except Exception:
            result['cleanup'] = 'failed'
            result['passed'] = False
        result['seconds'] = round(time.monotonic()-started,2)
        result['images'] = stack.manifest['images']
        (stack.directory / 'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
        print('Evidence:',stack.directory)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
