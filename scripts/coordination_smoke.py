"""Offline public-SDK two-worker composition; never a live benchmark."""
import argparse
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',action='store_true')
    parser.add_argument('--source-root',type=Path)
    args=parser.parse_args()
    if args.source_root:sys.path[:0]=[str(args.source_root.resolve()),str(args.source_root.resolve()/'src')]
    from lab_runner.coordination_fixture import qualify,replay,PROVIDERS,MODES,SCENARIOS
    from lab_runner.quality.allowance import private_directory,private_write
    if args.replay:
        print(f'{replay(args.output)} saved coordination lanes inspected; network denied');return
    root=private_directory(args.output)
    if any(root.iterdir()):raise ValueError('fresh private qualification root required')
    proofs=[]
    for provider in PROVIDERS:
        for mode in MODES:
            for scenario in SCENARIOS:
                proofs.append(qualify(root/(provider+'-'+mode+'-'+scenario),provider=provider,scenario=scenario,mode=mode))
    lanes=replay(root)
    private_write(root/'result.json',dict(version=1,lanes=lanes,networkDeniedReplays=lanes,liveRequests=0,
        experimental=True,usageCompleteLanes=sum(p['usageComplete'] for p in proofs),
        providerRequests=sum(p['providerRequests'] for p in proofs),toolCalls=sum(p['toolCalls'] for p in proofs),
        knownReportedTokens=sum(p['reportedTokens'] for p in proofs)))
    print(f'{lanes} coordination lanes qualified; sequential and parallel; zero live requests')


if __name__=='__main__':main()
