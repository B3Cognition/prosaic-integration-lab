"""Native Runtime candidate tests and benchmarks; live execution is opt-in."""
import argparse
import json
import os
from pathlib import Path
import sys

# Host runners may use an SDK-only environment. Bootstrap this consumer's source
# exactly as the existing Lab CLI does; upstream SDKs remain installed wheels.
_root = Path(__file__).resolve().parents[2]
if (_root / 'src' / 'prosaic_integration_lab').is_dir():
    sys.path.insert(0, str(_root / 'src'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'test', 'unified-test', 'unified-cli-test', 'unified-fallback-test', 'unified-benchmark', 'benchmark', 'preflight', 'live', 'compare', 'realistic'))
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--wheel-dir', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--repetitions', type=int)
    parser.add_argument('--runtime-wheel', type=Path)
    parser.add_argument('--runtime-sha256')
    parser.add_argument('--runtime-commit')
    parser.add_argument('--released-manifest', type=Path, default=Path('dependencies/releases.json'))
    parser.add_argument('--released-wheel-dir', type=Path)
    parser.add_argument('--runtime-config', type=Path)
    parser.add_argument('--local-config', type=Path)
    parser.add_argument('--selector', action='append', default=[])
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--max-native-attempts', type=int)
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--local-timeout', type=float,
                        help='local API deadline: compare 1..300 seconds; realistic requires 180')
    args = parser.parse_args(argv)
    if args.repetitions is None:
        args.repetitions = 1 if args.command == 'compare' else 3
    try:
        if args.local_timeout is not None and args.command not in ('compare','realistic','unified-benchmark'):
            raise ValueError('--local-timeout applies only to compare or realistic')
        if args.command in ('live', 'compare', 'realistic', 'unified-benchmark') and not args.live:
            raise ValueError('live execution requires explicit --live and a native-attempt allowance')
        if args.command == 'unified-benchmark' and (args.max_native_attempts is not None or args.selector):
            raise ValueError('unified benchmark uses fixed profile selection and attempt budgets; pilot flags are unsupported')
        if args.command == 'prepare':
            from .candidate import curate
            if not all((args.runtime_wheel, args.runtime_sha256, args.runtime_commit,
                        args.released_wheel_dir, args.manifest)):
                raise ValueError('prepare requires explicit source, checksum, wheel and manifest paths')
            report = curate(args.runtime_wheel, args.runtime_sha256, args.runtime_commit,
                            args.released_manifest, args.released_wheel_dir, args.manifest)
        else:
            if args.manifest is None or args.wheel_dir is None:
                raise ValueError('explicit five-wheel manifest and wheel directory required')
            from .provenance import audit_candidate
            provenance = audit_candidate(args.manifest, args.wheel_dir)
            if args.command == 'test':
                from .runner import run_acceptance
                report = run_acceptance(provenance=provenance)
            elif args.command == 'unified-test':
                from .unified import run_unified_acceptance
                report = run_unified_acceptance(provenance=provenance)
            elif args.command == 'unified-cli-test':
                from .unified import run_unified_cli_acceptance
                report = run_unified_cli_acceptance(provenance=provenance)
            elif args.command == 'unified-fallback-test':
                from .unified_fallback import run_fallback_acceptance
                report = run_fallback_acceptance(provenance=provenance)
            elif args.command == 'unified-benchmark':
                from .unified_benchmark import run_unified_benchmark
                if args.timeout != 60:
                    raise ValueError('unified benchmark fixes native timeout at 60 seconds')
                report = run_unified_benchmark(native_config=args.runtime_config, local_config=args.local_config,
                    output=args.output, provenance=provenance, live=args.live, repetitions=args.repetitions,
                    local_timeout_s=180 if args.local_timeout is None else args.local_timeout)
                print(json.dumps({k: v for k, v in report.items() if k != 'samples'}, allow_nan=False))
                return 0 if report['passed'] else 1
            elif args.command == 'benchmark':
                from .runner import fixture_benchmark
                report = fixture_benchmark(repetitions=args.repetitions, provenance=provenance)
            elif args.command == 'realistic':
                from .realistic import run_realistic
                report=run_realistic(native_config=args.runtime_config,local_config=args.local_config,
                    selectors=args.selector,output=args.output,provenance=provenance,live=args.live,
                    repetitions=args.repetitions,timeout_s=args.timeout,
                    local_timeout_s=180 if args.local_timeout is None else args.local_timeout)
                print(json.dumps({k:v for k,v in report.items() if k!='samples'},allow_nan=False))
                return 0 if report['passed'] else 1
            elif args.command == 'compare':
                from .compare import run_comparison
                report = run_comparison(native_config=args.runtime_config, local_config=args.local_config,
                    selectors=args.selector, output=args.output, provenance=provenance, live=args.live,
                    repetitions=args.repetitions, timeout_s=args.timeout, local_timeout_s=args.local_timeout)
                print(json.dumps(report, allow_nan=False))
                return 0 if report['passed'] else 1
            else:
                from .live import preflight, run_live
                options = dict(config_path=args.runtime_config, selectors=args.selector,
                    repetitions=args.repetitions, maximum=args.max_native_attempts, timeout_s=args.timeout)
                if args.command == 'preflight':
                    report = preflight(**options)
                    report['provenance'] = provenance
                else:
                    report = run_live(**options, output=args.output, provenance=provenance)
                    # Live mode writes its own exclusive private directory.
                    print(json.dumps(report, allow_nan=False))
                    return 0 if report['passed'] else 1
        encoded = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n'
        if args.output is not None:
            with os.fdopen(os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as target:
                target.write(encoded)
        print(encoded, end='')
        return 0 if report.get('passed', True) else 1
    except (OSError, ValueError, TypeError, ImportError, KeyError):
        # Public reports never include raw exceptions/configuration or model text.
        print(json.dumps({'error': 'native_eval_setup_failed'}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
