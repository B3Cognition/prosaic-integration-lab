"""Installed-SDK reasoning lab. Fixtures are default; live calls require opt-in."""
import argparse
import json
import os
from pathlib import Path
import sys

_root = Path(__file__).resolve().parents[2]
if (_root / 'src' / 'prosaic_integration_lab').is_dir():
    sys.path.insert(0, str(_root / 'src'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('test', 'live'))
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--wheel-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--profile')
    parser.add_argument('--kind', choices=('api', 'native'), default='api')
    parser.add_argument('--effort', action='append', default=[])
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--max-calls', type=int)
    parser.add_argument('--allowance', type=Path)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args(argv)
    target = None
    try:
        if args.command == 'live' and (not args.live or args.config is None or args.output is None):
            raise ValueError('live mode requires opt-in, config and a receipt path')
        if args.output is not None and (args.output.exists() or args.output.is_symlink()):
            raise ValueError('receipt path already exists')
        if args.output is not None:
            # Reserve a writable exclusive receipt before any provider dispatch.
            target = os.fdopen(os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                       0o600), 'w')
        from lab_runner.native_eval.provenance import audit_candidate
        provenance = audit_candidate(args.manifest, args.wheel_dir)
        from . import run_fixtures, run_live
        if args.command == 'test':
            report = run_fixtures(provenance=provenance)
        else:
            report = run_live(kind=args.kind, config_path=args.config, profile=args.profile,
                efforts=args.effort, live=args.live, maximum=args.max_calls,
                allowance_path=args.allowance, timeout_s=args.timeout, provenance=provenance)
        encoded = json.dumps(report, indent=2, allow_nan=False) + '\n'
        if target is not None:
            target.write(encoded)
            target.flush()
        print(encoded, end='')
        return 0 if report['passed'] else 130 if report.get('failureReason') == 'cancelled' else 1
    except (OSError, ValueError, TypeError, ImportError, KeyError):
        if target is not None and target.tell() == 0:
            target.write(json.dumps({'schemaVersion': 1, 'passed': False,
                'controlsVerified': False, 'error': 'reasoning_lab_failed'}) + '\n')
            target.flush()
        print(json.dumps({'error': 'reasoning_lab_failed'}), file=sys.stderr)
        return 1
    finally:
        if target is not None:
            target.close()


if __name__ == '__main__':
    raise SystemExit(main())
