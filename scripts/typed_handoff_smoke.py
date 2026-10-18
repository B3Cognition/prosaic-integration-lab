"""Installed offline both-wire qualification. Synthetic units, no live allowance."""
import argparse
import json
from pathlib import Path
import tempfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    import lab_runner.handoffs.execution as installed
    from lab_runner.handoffs.fixture import SCENARIOS,example_case,fixture_provider
    from lab_runner.handoffs.scoring import score_trajectory
    assert not Path(installed.__file__).resolve().is_relative_to(args.source_root.resolve())
    rows=[]
    with tempfile.TemporaryDirectory(prefix='typed-handoff-installed-') as root:
        for provider in ('openai','anthropic'):
            for scenario in SCENARIOS:
                case=example_case(scenario);output=Path(root)/provider/scenario
                with fixture_provider(case,scenario=scenario,provider=provider) as p:
                    evidence=installed.execute_case(case,config=p.config,output=output,sample_id='qualification')
                    requests=p.requests;p.deny=True
                    replay=installed.recover_case(case,config=p.config,output=output,sample_id='qualification')
                    assert p.requests==requests and replay['receiptDigests']==evidence['receiptDigests']
                    assert evidence['counts']['providerRequests']==requests<=4
                score=score_trajectory(case,evidence)
                assert score['safe']
                assert score['qualityPassed']==(scenario in ('correct','reject','missing','conflict'))
                assert evidence['counts']['toolCalls']<=2
                if scenario=='unknown_usage':assert evidence['counts']['reportedTokens'] is None
                elif scenario=='overrun':assert evidence['counts']['reportedTokens']>8192
                else:assert evidence['counts']['reportedTokens']<=8192
                rows.append(dict(provider=provider,scenario=scenario,**score,replayAdditionalRequests=0))
    report=dict(origin='synthetic',liveRequests=0,scenarios=rows)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(f'Installed typed handoffs: {len(rows)} both-wire scenarios passed; zero live requests.')


if __name__=='__main__':main()
