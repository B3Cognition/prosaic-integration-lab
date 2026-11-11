"""Run a new credential-free fixture matrix, or replay existing evidence offline."""

import argparse
import json
from pathlib import Path


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--fixture',action='store_true')
    modes.add_argument('--replay',action='store_true')
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(argv)
    from .runner import run_fixture, replay
    try:
        result=run_fixture(args.output) if args.fixture else replay(args.output)
        print(json.dumps(result,sort_keys=True))
        return 0 if result['passed']==result['cells']==24 else 1
    except (ValueError,TypeError,KeyError,OSError):
        print(json.dumps({'error':'invalid_or_existing_evidence',
            'additionalProviderRequests':0 if args.replay else None}))
        return 2


if __name__=='__main__':raise SystemExit(main())
