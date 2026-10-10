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


def load_lago():
    # The host runner consumes this repository's application source; upstream
    # Prosaic dependencies remain installed, checksummed release wheels.
    source = str(ROOT / 'src')
    if source not in sys.path:
        sys.path.insert(0,source)
    from .lago import start
    return start


def main():
    parser = argparse.ArgumentParser(description='Required owned synthetic acceptance; no paid calls')
    parser.add_argument('command', choices=['test', 'demo', 'run', 'watch','recover','metrics','retention','stress',
        'qualify','qualify-recovery','qualify-staging'])
    parser.add_argument('--profile')
    parser.add_argument('--staging-opt-in',action='store_true')
    parser.add_argument('--url',help='recovery service origin; HTTPS unless explicit loopback lab mode')
    parser.add_argument('--token-env',default='LAB_API_TOKEN')
    parser.add_argument('--run-id')
    parser.add_argument('--action',choices=['inspect','resume','approve','reject','retry'],default='inspect')
    parser.add_argument('--expected-revision')
    parser.add_argument('--acknowledge-effect-risk',action='store_true')
    parser.add_argument('--lab-http',action='store_true')
    parser.add_argument('--ca-file')
    parser.add_argument('--samples',type=int,default=1)
    parser.add_argument('--interval',type=float,default=2)
    parser.add_argument('--config')
    parser.add_argument('--archive',action='store_true')
    parser.add_argument('--destination')
    parser.add_argument('--duration',type=float,default=10)
    parser.add_argument('--rate',type=float,default=1)
    parser.add_argument('--p95-target',type=float,default=2)
    parser.add_argument('--max-rejection-rate',type=float,default=.05)
    parser.add_argument('--tenant-capacity',type=int,choices=(1,2))
    parser.add_argument('--max-reservations',type=int)
    parser.add_argument('--users', type=int, default=3)
    parser.add_argument('--runs-per-user', type=int, default=1)
    parser.add_argument('--concurrency', type=int, default=2)
    parser.add_argument('--allow-overload', action='store_true', help='allow measured capacity rejections; correctness failures still fail')
    parser.add_argument('--directory', help='exact evidence directory for watch')
    parser.add_argument('--stream', choices=['requests', 'accounting'], default='accounting')
    parser.add_argument('--open-report', action='store_true', help='open the generated demo report after cleanup')
    parser.add_argument('--mode', choices=['provisioning', 'deterministic', 'load', 'recovery', 'audit','identity','persistence','operations','budget','lago','ingress','observability','capacity'], default='deterministic')
    parser.add_argument('--engine', choices=['docker', 'podman'], default='docker')
    parser.add_argument('--postgres-version', type=int, choices=[16, 18], default=16)
    parser.add_argument('--candidate', action='store_true', help='explicitly use the checksummed unpublished accounting adapter candidate')
    parser.add_argument('--consumer-image',help='immutable consumer sha256 image ID; manifest and installed payload still verified')
    args = parser.parse_args()
    profile=None
    operational=args.command in {'qualify','qualify-recovery'}
    if operational:
        from pathlib import Path
        from .qualification import validate_profile
        try:
            if not args.profile or Path(args.profile).stat().st_size>65536:raise ValueError('bounded profile required')
            profile=validate_profile(json.loads(Path(args.profile).read_text()))
        except (OSError,ValueError):parser.error('invalid qualification profile')
        args.users=profile['users']
    if args.command=='qualify-staging':
        from .staging_qualification import load_private_config,run
        config=None
        if args.staging_opt_in and args.config:
            try:config=load_private_config(args.config)
            except (OSError,ValueError):pass
        result=run(config,enabled=args.staging_opt_in)
        print(json.dumps(result))
        return 0 if result['qualified'] else 1
    if args.consumer_image is not None:
        import re
        if not re.fullmatch('sha256:[0-9a-f]{64}',args.consumer_image):
            parser.error('immutable consumer image ID required')
    if args.command == 'recover':
        from .recovery import cli
        return cli(args)
    if args.command == 'metrics':
        from .metrics_viewer import cli
        return cli(args)
    if args.command == 'retention':
        source=str(ROOT/'src')
        if source not in sys.path: sys.path.insert(0,source)
        from prosaic_integration_lab.retention import cli
        return cli(args)
    if args.command == 'watch':
        if not args.directory or not os.path.isdir(args.directory):
            parser.error('watch requires an existing --directory from the run output')
        workload.watch(args.directory, args.stream)
        return 0
    try:
        workload.validate(args.users, args.runs_per_user, args.concurrency)
        if args.command=='stress':
            from .load_profile import validate
            validate(args.duration,args.rate,args.concurrency,args.p95_target,args.max_rejection_rate)
    except ValueError as error:
        parser.error(str(error))
    if args.open_report and args.command != 'demo':
        parser.error('--open-report requires demo')
    capacity_policy={}
    if args.tenant_capacity is not None: capacity_policy['per_tenant']=args.tenant_capacity
    if args.max_reservations is not None:
        if not 1<=args.max_reservations<=10000: parser.error('reservation ceiling must be 1..10000')
        capacity_policy['max_runs']=args.max_reservations
    if args.mode == 'identity' and args.command != 'test':
        parser.error('identity mode requires test')
    if args.mode == 'ingress' and args.command != 'test':
        parser.error('ingress mode requires test')
    if args.mode == 'lago' and args.command != 'test':
        parser.error('lago mode requires test')
    stack = OwnedStack(args.engine, args.postgres_version, users=args.users if args.command in {'run','stress'} or operational else 3,
        candidate=args.candidate,identity=args.mode in {'identity','ingress'},billing=args.mode == 'lago',consumer_image=args.consumer_image,
        observability=args.mode in {'audit','observability'},capacity_policy=capacity_policy or None)
    events = workload.Events(stack.directory) if args.command in {'run','stress','qualify'} else None
    if events:
        print(f'Accounting in another terminal: {sys.executable} -m lab_runner watch --directory {stack.directory}', flush=True)
    started = time.monotonic()
    result = {'owner': stack.owner, 'mode': args.command if args.command in {'demo', 'run','stress'} or operational else args.mode, 'host_architecture': platform.machine(),
              'python': platform.python_version(), 'passed': False, 'cleanup': 'pending',
              'dependency_mode': 'candidate' if args.candidate else 'released'}
    if operational:
        from .qualification import receipt
        result.update(receipt(profile,qualified=False,qualification='not_qualified',fixture_passed=False))
    try:
        stack.start()
        if args.command in {'demo', 'run','stress'} or operational or args.mode != 'provisioning':
            stack.start_model()
            stack.start_replica('a')
            stack.start_replica('b')
        config_path = stack.secrets / 'host.json'
        config = json.loads(config_path.read_text())
        config.update(stack.manifest['endpoints'])
        if args.mode == 'ingress':
            from .ingress import start as start_ingress
            config['ingress'] = start_ingress(stack)
        if args.mode == 'lago':
            config['lago'] = load_lago()(stack)
            from .lago import seed
            from prosaic_integration_lab.billing_store import BillingStore
            # Freeze account subscriptions and the open period before inference.
            seed(config['lago'],[{**p,'namespace':config['namespace'],'environment':config['environment']}
                for p in config['principals'].values()],BillingStore(config['billing_dsn']))
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
        if args.mode == 'identity':
            files = ['tests/acceptance/test_provisioning.py','tests/acceptance/test_approval.py',
                'tests/acceptance/test_authorization.py','tests/acceptance/test_accounting.py',
                'tests/acceptance/test_identity.py']
        if args.mode in {'audit','persistence'}:
            files += ['tests/acceptance/test_persistence.py']
        if args.mode in {'audit','operations'}:
            files += ['tests/acceptance/test_terminal_recovery.py','tests/acceptance/test_delivery_recovery.py']
        if args.mode in {'audit','budget'}:
            files += ['tests/acceptance/test_http_budget.py']
        if args.mode in {'audit','observability'}:
            files += ['tests/acceptance/test_observability.py']
        if args.mode in {'audit','capacity'}:
            files += ['tests/acceptance/test_capacity_retention.py']
        if args.mode=='capacity': files=['tests/acceptance/test_capacity_retention.py']
        if args.mode == 'ingress':
            files = ['tests/acceptance/test_ingress.py']
        if args.mode == 'lago':
            files = ['tests/acceptance/test_provisioning.py','tests/acceptance/test_lago.py',
                     'tests/acceptance/test_billing_outbox.py']
        if args.command=='qualify':
            from .qualification import run
            result.update(run(config,profile,events))
            result['passed']=result['qualified']
        elif args.command=='qualify-recovery':
            from .recovery_qualification import run
            result.update(run(stack,profile))
            result['passed']=result['qualified']
        elif args.command == 'stress':
            from .load_profile import run as profile
            result.update(profile(config,args.users,args.duration,args.rate,args.concurrency,events,
                p95_target=args.p95_target,max_rejection=args.max_rejection_rate,allow_overload=args.allow_overload))
        elif args.command == 'run':
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
                env={**os.environ, 'LAB_ACCEPTANCE_CONFIG': str(config_path)}, capture_output=True, text=True,
                timeout=600 if args.mode == 'lago' else 180)
            result['test_returncode'] = test.returncode
    except Exception as error:
        result['error'] = type(error).__name__
        if operational:result.update(qualified=False,qualification='not_qualified',reason='execution_unavailable')
        from .stack import EngineError
        if isinstance(error,EngineError) and error.diagnostic is not None:
            result['engine_diagnostic']=error.diagnostic
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
            if operational:result.update(qualified=False,qualification='not_qualified',reason='cleanup_failed')
        result['seconds'] = round(time.monotonic() - started, 2)
        result['images'] = stack.manifest['images']
        result['released_manifest_sha256'] = stack.manifest.get('released_manifest_sha256')
        result['payload_audit'] = stack.manifest.get('payload_audit')
        if args.candidate:
            result['candidate_manifest_sha256'] = stack.manifest.get('candidate_manifest_sha256')
        if operational and len(json.dumps(result).encode())>profile['maximum_report_bytes']:
            from .qualification import receipt
            result={**receipt(profile,qualified=False,qualification='not_qualified',fixture_passed=False,
                reason='report_limit'),'passed':False,'cleanup':result['cleanup']}
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
