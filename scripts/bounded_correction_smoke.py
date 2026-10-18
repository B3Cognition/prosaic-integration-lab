"""Installed bounded-correction proof; synthetic transports, never live models."""
import argparse
from pathlib import Path
import shutil
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--evidence-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    from lab_runner.handoffs import correction as c,correction_fixture as f
    from lab_runner.bounded_correction import compare_corrections
    from lab_runner.quality.contracts import digest
    from lab_runner.quality.allowance import private_directory,private_write
    from lab_runner.role_qualification import LIMITS
    assert not Path(c.__file__).resolve().is_relative_to(args.source_root.resolve())
    root=private_directory(args.evidence_dir);samples=[];pairs=[];recoveries=[]
    denied=[False]
    def guard(event,arguments):
        if denied[0] and event in ('socket.connect','socket.connect_ex','socket.getaddrinfo'):
            raise AssertionError('recovery attempted network access')
    sys.addaudithook(guard)
    scenarios=('correct','wrong_decision','missing','unread','critic_partial','critic_false',
        'ignore_feedback','regress','invalid_critic','critic_unknown','corrector_tools','final_breach')
    for provider in ('openai','anthropic'):
        for scenario in scenarios:
            case=f.example_case(scenario);scores=[];evidences=[]
            with f.fixture_provider(case,provider=provider,scenario=scenario) as p:
                for arm in ('no-critic','critic'):
                    sample=provider+'-'+scenario+'-'+arm;out=private_directory(root/sample)
                    evidence=c.execute_correction(case,config=p.config,output=out,sample_id=sample,arm=arm)
                    score=c.score_correction(case,evidence);scores.append(score);evidences.append((sample,out,evidence))
                    assert score['counts']['providerRequests']<=4 and score['counts']['toolCalls']<=2
                    assert score['counts']['reportedTokens'] is None or score['counts']['reportedTokens']<=8192
                    assert not score['taskAccepted'] or score['safe'] and score['finalArtifactCorrect']
                    private_write(out/'evidence.json',evidence);private_write(out/'score.json',score)
                    samples.append(dict(sample=sample,provider=provider,scenario=scenario,arm=arm,score=score))
                pair=compare_corrections(*scores);assert pair['matched']
                if scenario=='critic_unknown':assert not pair['accountingKnown'] and pair['answerGain'] is None
                elif scenario=='invalid_critic':assert pair['answerGain']==-1
                elif scenario=='corrector_tools':assert pair['answerGain']==(0 if pair['accountingKnown'] else None)
                elif scenario=='final_breach':assert pair['answerGain'] is None
                else:assert pair['answerGain']==0
                pairs.append(dict(provider=provider,scenario=scenario,comparison=pair))
                p.deny=True;requests=p.requests;denied[0]=True
                try:
                    for sample,out,evidence in evidences:
                        copied=root/(sample+'-recovered');shutil.copytree(out,copied)
                        restored=c.recover_correction(case,config=p.config,output=copied,sample_id=sample,arm=evidence['arm'])
                        assert restored==evidence and c.score_correction(case,restored)==c.score_correction(case,evidence)
                        recoveries.append(dict(sample=sample,receiptDigests=restored['receiptDigests'],networkAttempts=0))
                finally:denied[0]=False
                assert p.requests==requests and not p.errors
        # An interrupted observed request remains visible without a receipt or redispatch.
        case=f.example_case('wrong_decision');sample=provider+'-interrupted';out=private_directory(root/sample)
        def stop(event):
            if event.get('event')=='completed' and event.get('step')=='critic':raise KeyboardInterrupt
        with f.fixture_provider(case,provider=provider,scenario='wrong_decision') as p:
            try:c.execute_correction(case,config=p.config,output=out,sample_id=sample,arm='critic',on_event=stop)
            except KeyboardInterrupt:pass
            else:raise AssertionError('interruption missing')
            assert p.requests==3;p.deny=True;denied[0]=True
            try:
                evidence=c.recover_correction(case,config=p.config,output=out,sample_id=sample,arm='critic')
                score=c.score_correction(case,evidence)
            finally:denied[0]=False
            assert score['roleCosts']['critic']['unreceiptedObservations']==1
            assert score['roleCosts']['critic']['observedTokens']==150 and not score['accountingComplete']
            assert score['counts']['reportedTokens'] is None and not score['correctionCalled'] and p.requests==3
            assert not p.errors
            private_write(out/'recovered-evidence.json',evidence);private_write(out/'score.json',score)
            recoveries.append(dict(sample=sample,networkAttempts=0,score=score))
    private_write(args.output,dict(origin='synthetic',liveRequests=0,limits=LIMITS,samples=samples,pairs=pairs,
        recoveries=recoveries,causalModelBenefitEstablished=False,proofDigest=digest(samples)))
    print('Installed correction blueprint:48 scripted arms,24 matched pairs,50 network-denied recoveries; zero live requests.')


if __name__=='__main__':main()
