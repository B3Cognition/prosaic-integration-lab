"""No command means no execution. Only an explicit synthetic fixture is exposed."""
import argparse
import json
from . import PROFILE


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command');fixture=sub.add_parser('fixture')
    fixture.add_argument('--case',choices=('omitted','complete','unavailable','unknown-usage'),default='omitted')
    fixture.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    if args.command is None:
        print(json.dumps(dict(profileId=PROFILE,enabled=False,executed=False,memoryDefault=False,sueDefault=False)))
        return 0
    try:
        from .fixture import run_fixture
        result=run_fixture(args.output,case=args.case)
    except (ValueError,KeyError,TypeError,OSError):
        print(json.dumps(dict(error='reference-fixture-failed',realModelCalls=0)));return 1
    print(json.dumps(result,sort_keys=True));return 0


if __name__=='__main__':raise SystemExit(main())
