"""Explicit CLI for the separate controlled retrieval-memory experiment."""
import argparse
import json
import sys


def main(argv=None):
    parser=argparse.ArgumentParser(description='Controlled read-only retrieval-memory comparison')
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--fixture',action='store_true');modes.add_argument('--live',action='store_true')
    parser.add_argument('--config');parser.add_argument('--output')
    parser.add_argument('--typed-evidence',action='store_true',help='classify current evidence as verified, absent or unread')
    parser.add_argument('--recover-only',action='store_true',help='adopt saved receipts/evidence without dispatching new samples')
    args=parser.parse_args(argv)
    evidence_format='typed' if args.typed_evidence else 'raw'
    try:
        from lab_runner.memory.runner import execute,preflight,live_settings
        if not args.fixture and not args.live:
            if args.config or args.output or args.recover_only:raise ValueError('execution flags without mode')
            report=preflight(evidence_format=evidence_format)
        else:
            if not args.output or args.live!=bool(args.config):raise ValueError('missing explicit memory config/output')
            if args.live:live_settings(args.config)
            report=execute(output=args.output,fixture=args.fixture,live_config=args.config,recover_only=args.recover_only,
                           evidence_format=evidence_format)
        print(json.dumps(report,sort_keys=True,allow_nan=False))
        if report['origin']=='unexecuted':return 0
        return 0 if report['baselineComplete'] and report['taskSuccess']['passed']==report['scheduledSamples'] else 1
    except (ValueError,OSError,KeyError,TypeError):
        print('retrieval-memory configuration or evidence invalid',file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())
