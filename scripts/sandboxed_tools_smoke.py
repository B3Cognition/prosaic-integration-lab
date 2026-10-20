"""Offline public-SDK sandbox qualification. Missing enforcement is a failure."""
import argparse
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',action='store_true')
    parser.add_argument('--source-root',type=Path,help='Source execution only; omit for isolated installed qualification.')
    args=parser.parse_args()
    if args.source_root:
        sys.path[:0]=[str(args.source_root.resolve()),str(args.source_root.resolve()/'src')]
    from lab_runner.sandbox_fixture import qualify,replay,SCENARIOS
    from lab_runner.quality.allowance import private_directory,private_write
    if args.replay:
        print(f'{replay(args.output)} saved sandbox reports inspected; network denied');return
    root=private_directory(args.output)
    if any(root.iterdir()):raise ValueError('fresh private qualification root required')
    reports=[]
    for provider in ('openai','anthropic'):
        for scenario in SCENARIOS:
            proof=qualify(root/(provider+'-'+scenario),provider=provider,scenario=scenario)
            if proof['qualified'] is not True:raise RuntimeError('required sandbox qualification blocked')
            reports.append(proof)
    if replay(root)!=12:raise RuntimeError('saved sandbox inspection incomplete')
    private_write(root/'result.json',dict(version=1,lanes=12,networkDeniedReplays=12,
        syntheticRequests=sum(p['providerRequests'] for p in reports),liveRequests=0,experimental=True))
    print('12 sandbox lanes/replays qualified; actual OS enforcement; zero live requests')


if __name__=='__main__':main()
