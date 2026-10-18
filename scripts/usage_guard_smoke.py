"""Installed, offline usage-guard fault qualification; synthetic loopback only."""
import argparse
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--evidence-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    from lab_runner.handoffs import correction as c,correction_fixture as f
    from lab_runner.quality.allowance import private_directory,private_write
    assert not Path(c.__file__).resolve().is_relative_to(args.source_root.resolve())
    root=private_directory(args.evidence_dir);samples=[];denied=[False]
    def guard(event,arguments):
        if denied[0] and event in ('socket.connect','socket.connect_ex','socket.getaddrinfo'):
            raise AssertionError('recovery attempted network access')
    sys.addaudithook(guard)
    for provider in ('openai','anthropic'):
        lanes=[(stage,fault,'critic','wrong_decision',requests) for stage,requests in
            [('lookup',1),('worker',2),('critic',3),('corrector',4)] for fault in
            ('input','output','missing','partial','invalid')]
        lanes += [('all','complete',arm,'wrong_decision',requests) for arm,requests in [('no-critic',3),('critic',4)]]
        lanes += [('worker',fault,'no-critic','correct',2) for fault in ('input','output')]
        for stage,fault,arm,scenario,requests in lanes:
            sample='-'.join((provider,stage,fault,arm));out=private_directory(root/sample)
            case=f.example_case(scenario)
            with f.fixture_provider(case,provider=provider,scenario=scenario,usage_fault=fault,usage_stage=stage) as p:
                evidence=c.execute_correction(case,config=p.config,output=out,sample_id=sample,arm=arm)
                score=c.score_correction(case,evidence)
                assert not p.errors and p.requests==requests
                if fault=='complete':
                    assert score['taskAccepted'] and score['safe'] and score['accountingComplete']
                    assert score['roleCosts']['worker']['observedTokens']==300
                    assert score['roleCosts']['corrector']['observedTokens']==150
                    if arm=='critic':assert score['roleCosts']['critic']['observedTokens']==150
                    assert all(o['usage']['status']=='unsupported' for o in evidence['callObservations'].values())
                else:
                    assert not score['taskAccepted'] and not score['withinLimits'] and score['safeStopped']
                    assert evidence['admissionViolation'] and evidence['componentBreaches']
                    if fault in ('input','output'):
                        assert evidence['componentBreaches'][-1]['kind']==('inputBoundExceeded' if fault=='input' else 'outputBoundExceeded')
                    else:
                        assert score['counts']['reportedTokens'] is None
                        assert score['roleCosts']['worker' if stage=='lookup' else stage]['observedTokens'] is None
                private_write(out/'score.json',score)
                p.deny=True;denied[0]=True
                try:
                    restored=c.recover_correction(case,config=p.config,output=out,sample_id=sample,arm=arm)
                    assert restored==evidence and c.score_correction(case,restored)==score
                finally:denied[0]=False
                assert p.requests==requests
                samples.append(dict(sample=sample,syntheticRequests=requests,score=score,networkDeniedRecovery=True))
    report=dict(version=1,protocol=c.PROTOCOL,liveRequests=0,samples=samples,
        arms=len(samples),networkDeniedRecoveries=len(samples),syntheticRequests=sum(s['syntheticRequests'] for s in samples))
    private_write(args.output,report)
    print(f"usage guard: {len(samples)} synthetic arms and network-denied recoveries; 0 live requests")


if __name__=='__main__':main()
