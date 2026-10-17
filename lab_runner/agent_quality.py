"""Explicit task quality: pure preflight by default, fixture/live execution opt-in."""
import argparse
import json
from pathlib import Path


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--fixture',action='store_true')
    mode.add_argument('--live',action='store_true')
    mode.add_argument('--compare',nargs='+',type=Path)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--repetitions',type=int,default=1,choices=range(1,11))
    args=parser.parse_args(argv)
    if args.live and (not args.config or not args.output):parser.error('live requires --config and --output')
    if args.fixture and (not args.output or args.config):parser.error('fixture requires --output and no private config')
    if not args.live and args.config:parser.error('private config requires --live')
    try:
        if args.compare:
            if args.output or args.config:parser.error('comparison reads reports only')
            from .quality.contracts import decode
            from .quality.reporting import compare
            reports=[]
            for path in args.compare:
                if path.stat().st_size>262144:raise ValueError('report limit')
                reports.append(decode(path.read_bytes(),262144))
            result=compare(reports)
        elif args.fixture or args.live:
            from .quality.runner import execute
            result=execute(output=args.output,repetitions=args.repetitions,live_config=args.config if args.live else None)
        else:
            if args.output:parser.error('preflight does not create output')
            from .quality.runner import preflight
            result=preflight(args.repetitions)
        print(json.dumps(result,sort_keys=True,allow_nan=False))
        if result.get('origin')=='unexecuted':return 0
        return 0 if result['baselineComplete'] and result.get('stateCounts',{}).get('failed',0)==0 else 1
    except (ValueError,OSError,KeyError,TypeError):
        print(json.dumps({'event':'agentQualityError','reason':'invalidConfigurationOrEvidence'}))
        return 2


if __name__=='__main__':raise SystemExit(main())
