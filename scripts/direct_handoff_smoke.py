"""Installed direct-role wire qualification. No credentials or live inference."""
import argparse
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--evidence-dir',type=Path,required=True)
    args=parser.parse_args()
    from lab_runner.handoffs import direct
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case,correct_worker
    from lab_runner.handoffs.direct_scoring import score_direct
    from lab_runner.quality.allowance import private_directory,private_write
    from lab_runner.quality.contracts import digest
    assert not Path(direct.__file__).resolve().is_relative_to(args.source_root.resolve())
    root=private_directory(args.evidence_dir);rows=[]
    def run(provider,family,mode,scenario='correct',flaw=None):
        case=example_case(family);draft=correct_worker(case,family) if mode=='critic' else None
        if flaw=='binding':draft['assignmentId']='0'*64
        if flaw=='status':draft['status']='missing'
        if flaw=='decision':draft['answer']['decision']='reject'
        if flaw in ('facts','citations'):draft['answer'][flaw]=[]
        if scenario=='missed_flaw' and mode=='critic':draft['answer']['decision']='reject'
        sample=f'{provider}-{family}-{mode}-{scenario}-{flaw or "none"}'
        out=private_directory(root/sample)
        controls=dict(draft=draft,record_ids=['metrics'] if family=='unread' else ['metrics','incident']
            if family=='extra_unread' else None) if mode=='critic' else {}
        with fixture_provider(case,provider=provider,family=family,scenario=scenario) as p:
            evidence=direct.execute_case(case,config=p.config,output=out,sample_id=sample,mode=mode,**controls)
            requests=p.requests
            assert p.contractChecks==requests and not p.errors,p.errors
            assert evidence['counts']['providerRequests']==requests<=4
            before=(out/(sample+'-context-trace.json')).read_bytes();p.deny=True
            replay=direct.recover_case(case,config=p.config,output=out,sample_id=sample,mode=mode,**controls)
            assert replay['receiptDigests']==evidence['receiptDigests'] and p.requests==requests
            assert (out/(sample+'-context-trace.json')).read_bytes()==before
        score=score_direct(case,evidence)
        quality=scenario=='correct' and (family not in ('unread','extra_unread') or mode=='critic')
        assert score['safe'] and score['qualityPassed']==quality,score
        assert all(r['step']!='planner' for r in evidence['receipts'])
        assert evidence['counts']['toolCalls']<=2
        if mode=='critic':assert requests==1 and evidence['counts']['toolCalls']==0
        if scenario=='unknown_usage':assert evidence['counts']['reportedTokens'] is None
        elif scenario=='overrun':assert evidence['counts']['reportedTokens']>8192
        else:assert evidence['counts']['reportedTokens']<=8192
        private_write(out/'evidence.json',evidence)
        rows.append(dict(sampleId=sample,provider=provider,family=family,mode=mode,scenario=scenario,
            flaw=flaw,**score,receiptDigests=evidence['receiptDigests'],evidenceSha256=digest(evidence),
            contractChecks=requests,replayAdditionalRequests=0))
    for provider in ('openai','anthropic'):
        for family in ('correct','reject','missing','conflict','unread','extra_unread'):
            for mode in ('worker','critic','handoff'):run(provider,family,mode)
        for flaw in ('binding','status','decision','facts','citations'):run(provider,'correct','critic',flaw=flaw)
        for scenario in ('wrong_worker','missed_flaw','false_critic','invalid_worker','schema_instead',
                         'wrong_binding','unknown_usage','repeat_tools','overrun','invalid_critic','wrong_critic_binding'):
            run(provider,'correct','handoff',scenario)
        for scenario in ('missed_flaw','false_critic','invalid_critic','wrong_critic_binding'):
            run(provider,'correct','critic',scenario)
    private_write(args.output,dict(origin='synthetic',liveRequests=0,scenarios=rows,
        limits=dict(providerRequests=4,toolCalls=2,reportedTokens=8192,timeoutSeconds=600,outputTokens=512)))
    print(f'Installed direct roles: {len(rows)} both-wire scenarios qualified; zero live requests.')


if __name__=='__main__':main()
