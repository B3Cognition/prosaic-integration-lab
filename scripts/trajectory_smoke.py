"""Credential-free public SDK trajectory example; use an installed Lab wheel."""
import argparse
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',action='store_true')
    args=parser.parse_args()
    from lab_runner.trajectory_fixture import qualify,replay,SCENARIOS
    from lab_runner.quality.allowance import private_directory,private_write
    if args.replay:
        print(f'{replay(args.output)} saved reports inspected; network denied; zero provider requests')
        return
    root=private_directory(args.output)
    if any(root.iterdir()):raise ValueError('fresh evidence directory required')
    rows=[]
    for provider in ('openai','anthropic'):
        for scenario in SCENARIOS:
            proof=qualify(root/(provider+'-'+scenario),provider=provider,scenario=scenario)
            assert proof['providerRequests']<=4 and proof['toolCalls']<=2
            want='passed' if scenario in ('ready','missing') else 'incomplete' if scenario=='provider-error' else 'failed'
            assert proof['report']['assessment']['status']==want
            rows.append(dict(provider=provider,scenario=scenario,providerRequests=proof['providerRequests']))
    inspected=replay(root)
    private_write(root/'result.json',dict(lanes=len(rows),networkDeniedReplays=inspected,
        syntheticRequests=sum(row['providerRequests'] for row in rows),liveRequests=0,experimental=True))
    print('12 both-wire parcel lanes and network-denied replays; zero live requests')


if __name__=='__main__':main()
