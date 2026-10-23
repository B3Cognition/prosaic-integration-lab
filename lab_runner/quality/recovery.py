"""Fault probes around public stores; no model or tool effects are replayed."""
import time
from .allowance import BenchmarkAllowance,private_directory
from .contracts import digest
from .execution import CASE_LIMITS,materials
from .fixture import fixture_provider
from .suite import load_suite,public_case


class InjectedInterruption(BaseException):
    """Simulate process loss without becoming an ordinary retryable failure."""


class FaultStore:
    def __init__(self,store,phase):self.store,self.phase=store,phase
    def __getattr__(self,name):return getattr(self.store,name)
    def save_receipt(self,run_id,invocation_id,receipt,lease):
        if self.phase=='before':raise InjectedInterruption()
        self.store.save_receipt(run_id,invocation_id,receipt,lease)
        if self.phase=='after':raise InjectedInterruption()


def run_recovery_cases(output):
    from prosaic_harness import Harness,FileRunStore
    root=private_directory(output);results=[]
    case=load_suite()['cases'][0]
    for name,phase in [('saved-receipt','after'),('missing-receipt','before'),('schema-failure',None)]:
        directory=private_directory(root/name)
        allowance=BenchmarkAllowance(directory/'allowance.json',identity=digest({'case':name}),
            limits=dict(providerRequests=8,toolCalls=4,reportedTokens=16384,maxSamples=1,timeoutSeconds=60))
        allowance.reserve(name,{k:CASE_LIMITS[k] for k in ('providerRequests','toolCalls','reportedTokens')})
        with fixture_provider(scenario='invalid_json' if phase is None else 'correct') as provider:
            workflow,journal,on_event=materials(case,provider.config,'fixture',name,CASE_LIMITS)
            store=FileRunStore(directory/'store',namespace='quality-recovery');store.initialize()
            run_id=digest({'case':name})[:32]
            try:
                h=Harness(workflow,store=FaultStore(store,phase),run_id=run_id,on_event=on_event)
                try:h.run(public_case(case))
                except InjectedInterruption:pass
                before=(provider.requests,len(journal));retained=allowance.status()['retained']
                began=time.monotonic()
                restored=Harness(workflow,store=store,run_id=run_id,on_event=on_event)
                state=restored.resume()
                duration=time.monotonic()-began
                expected=('completed',None) if phase=='after' else ('blocked','interrupted_call') if phase=='before' else ('blocked','attempt_limit')
                delta=(provider.requests-before[0],len(journal)-before[1])
                results.append(dict(caseId=name,origin='fixture',passed=(state['status'],state['reason'])==expected
                    and delta==(0,0) and allowance.status()['retained']==retained,
                    additionalProviderRequests=delta[0],additionalToolCalls=delta[1],elapsedSeconds=duration,
                    allowancePreserved=allowance.status()['retained']==retained))
            finally:store.close()
    return results
