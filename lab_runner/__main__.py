import argparse
import json
import os
import platform
import subprocess
import sys
import time

from .stack import OwnedStack, ROOT
from .results import sanitize_junit
from .accounting_demo import capture_accounting
from .accounting_report import write_report
from . import workload


def main():
    parser = argparse.ArgumentParser(description='Required owned synthetic acceptance; no paid calls')
    parser.add_argument('command', choices=['test', 'demo', 'run', 'watch'])
    parser.add_argument('--users', type=int, default=3)
    parser.add_argument('--runs-per-user', type=int, default=1)
    parser.add_argument('--concurrency', type=int, default=2)
    parser.add_argument('--allow-overload', action='store_true', help='allow measured capacity rejections; correctness failures still fail')
    parser.add_argument('--directory', help='exact evidence directory for watch')
    parser.add_argument('--stream', choices=['requests', 'accounting'], default='accounting')
    parser.add_argument('--open-report', action='store_true', help='open the generated demo report after cleanup')
    parser.add_argument('--mode', choices=['provisioning', 'deterministic', 'load', 'recovery', 'audit'], default='deterministic')
    parser.add_argument('--engine', choices=['docker', 'podman'], default='docker')
    parser.add_argument('--postgres-version', type=int, choices=[16, 18], default=16)
    parser.add_argument('--candidate', action='store_true', help='explicitly use the checksummed unpublished accounting adapter candidate')
    args = parser.parse_args()
    if args.command == 'watch':
        if not args.directory or not os.path.isdir(args.directory):
            parser.error('watch requires an existing --directory from the run output')
        workload.watch(args.directory, args.stream)
        return 0
    try:
        workload.validate(args.users, args.runs_per_user, args.concurrency)
    except ValueError as error:
        parser.error(str(error))
    if args.open_report and args.command != 'demo':
        parser.error('--open-report requires demo')
    stack = OwnedStack(args.engine, args.postgres_version, users=args.users if args.command == 'run' else 3, candidate=args.candidate)
    events = workload.Events(stack.directory) if args.command == 'run' else None
    if events:
        print(f'Accounting in another terminal: {sys.executable} -m lab_runner watch --directory {stack.directory}', flush=True)
    started = time.monotonic()
    result = {'owner': stack.owner, 'mode': args.command if args.command in {'demo', 'run'} else args.mode, 'host_architecture': platform.machine(),
              'python': platform.python_version(), 'passed': False, 'cleanup': 'pending',
              'dependency_mode': 'candidate' if args.candidate else 'released'}
    try:
        stack.start()
        if args.command in {'demo', 'run'} or args.mode != 'provisioning':
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
        if args.mode in {'load', 'audit'}:
            files += ['tests/acceptance/test_load.py']
        if args.mode in {'recovery', 'audit'}:
            files += ['tests/acceptance/test_accounting_failures.py', 'tests/acceptance/test_recovery.py', 'tests/acceptance/test_scope.py']
        if args.mode == 'audit':
            files += ['tests/acceptance/test_production_audit.py']
        if args.command == 'run':
            result.update(workload.run(config, args.users, args.runs_per_user, args.concurrency, events, args.allow_overload))
        elif args.command == 'demo':
            report = capture_accounting(config, stack.owner)
            report_path = write_report(report, stack.directory / 'report')
            result.update(passed=True, report_html=str(report_path),
                          report_json=str(report_path.with_suffix('.json')),
                          independent_model_calls=report['independent_model_calls'])
        else:
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
        if args.candidate:
            result['candidate_manifest_sha256'] = stack.manifest.get('candidate_manifest_sha256')
        if events:
            events.finish(result)
        (stack.directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))
        print(f'Evidence: {stack.directory}')
        if args.command == 'demo' and result['passed']:
            for run in report['runs']:
                usage = run['usage']
                amount = usage['estimated_amounts'].get('USD', 'Unknown')
                print(f"{run['actor']:6} | {run['case']:20} | calls={usage['total_calls']} "
                      f"complete={usage['complete_calls']} unknown={usage['unresolved_calls']} "
                      f"known USD={amount}")
            print(f"Report: {result['report_html']}")
    if args.open_report and result['passed']:
        import webbrowser
        from pathlib import Path
        webbrowser.open(Path(result['report_html']).as_uri())
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
