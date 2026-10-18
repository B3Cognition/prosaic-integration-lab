"""Installed, credential-free public Runtime approval qualification."""
import argparse
from pathlib import Path
import sys
import subprocess


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--evidence-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    from lab_runner import tool_approval,tool_approval_fixture as fixture
    from lab_runner.quality.allowance import private_directory,private_write
    assert not Path(tool_approval.__file__).resolve().is_relative_to(args.source_root.resolve()),'installed package required'
    private_directory(args.output.parent)
    root=private_directory(args.evidence_dir)
    assert not any(root.iterdir()),'fresh evidence directory required'
    reports=[]
    for provider in ('openai','anthropic'):
        for scenario in fixture.SCENARIOS:
            report=fixture.qualify(root/(provider+'-'+scenario),provider=provider,scenario=scenario)
            assert report['effects']==(1 if scenario in ('approved','unicode','duplicate') else 0),report
            assert report['providerRequests']<=4 and report['toolCalls']<=2 and report['reportedTokens']<=8192
            assert report['elapsedSeconds']<600 and report['networkDeniedRecovery'] and not report['providerErrors']
            reports.append(report)
    from lab_runner.quality.contracts import digest
    from prosaic_runtime import InvocationScope,ToolExecutionContext
    import time
    crash=private_directory(root/'process-loss')
    gate=tool_approval.ApprovalGate(crash/'approval.json',identity='a'*64,
                                  tools={'apply_change':'v1'},approvers=['operator'])
    action=dict(destination='staging',amount=1)
    scope=InvocationScope('invocation',run_id='run',step_id='apply',operation_namespace='owner-a')
    p=gate.propose('one',tool_name='apply_change',scope=scope,arguments=action,evidence_digest='b'*64)
    gate.decide('one',actor='operator',proposal_digest=p['proposalDigest'],approved=True,decision_digest='c'*64)
    code='''
import os,sys,time
from lab_runner.tool_approval import ApprovalGate
from lab_runner.quality.contracts import digest
from prosaic_runtime import InvocationScope,ToolExecutionContext
args=dict(destination='staging',amount=1)
scope=InvocationScope('invocation',run_id='run',step_id='apply',operation_namespace='owner-a')
context=ToolExecutionContext(scope,'apply_change','v1',1,digest(args),time.monotonic()+600,lambda:False)
j=ApprovalGate(sys.argv[1],identity='a'*64,tools={'apply_change':'v1'},approvers=['operator'])
assert j.authorizer('one')(args,context)
os._exit(23)
'''
    child=subprocess.run([sys.executable,'-I','-c',code,str(crash/'approval.json')],capture_output=True)
    assert child.returncode==23,child.stderr.decode()
    denied=[True]
    def guard(event,arguments):
        if denied[0] and event in ('socket.connect','socket.connect_ex','socket.getaddrinfo'):
            raise AssertionError('crash recovery attempted network access')
    sys.addaudithook(guard)
    try:
        restored=tool_approval.ApprovalGate(crash/'approval.json',identity='a'*64,
                                          tools={'apply_change':'v1'},approvers=['operator'])
        assert restored.inspect('one')['state']=='spent'
        ctx=ToolExecutionContext(scope,'apply_change','v1',1,digest(action),time.monotonic()+600,lambda:False)
        assert not restored.authorizer('one')(action,ctx)
    finally:denied[0]=False
    private_write(args.output,dict(version=1,experimental=True,liveRequests=0,lanes=reports,
        syntheticRequests=sum(r['providerRequests'] for r in reports),networkDeniedRecoveries=len(reports)+1,
        processLoss=dict(exitCode=23,state='spent',permissionReissued=False)))
    print(f'approval: {len(reports)} both-wire lanes, {len(reports)+1} network-denied recoveries, process-loss proof; zero live requests')


if __name__=='__main__':main()
