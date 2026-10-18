"""An enforceable host planning domain over a qualified Runtime counter."""
from dataclasses import replace
from pathlib import Path
from threading import RLock
import hashlib
from lab_runner.quality.contracts import decode,encode,digest,integer,sha
from lab_runner.memory.corpus import fields


def make_plan(*,counter_descriptor,quote_identity,request_sha256,input_bounds,
              max_requests,output_tokens,token_ceiling,reported_tokens,inflight_tokens,
              continuation_budget=False):
    if type(continuation_budget) is not bool:raise ValueError('invalid continuation policy')
    from prosaic_runtime import TokenCounterDescriptor
    descriptor=TokenCounterDescriptor.from_dict(counter_descriptor).to_dict()
    sha(quote_identity);sha(request_sha256);integer(max_requests,1,128)
    integer(output_tokens,1);integer(token_ceiling);integer(reported_tokens);integer(inflight_tokens)
    bounds=decode(encode(input_bounds,8192),8192)
    if type(bounds) is not list or len(bounds)!=max_requests:raise ValueError('full trajectory quotation required')
    for bound in bounds:integer(bound)
    capacity_fits=all(bound+output_tokens<=descriptor['contextCapacityTokens'] for bound in bounds)
    available=token_ceiling-reported_tokens-inflight_tokens
    integer(available);required=integer(sum(bounds)+max_requests*output_tokens)
    plan=dict(version=2 if continuation_budget else 1,admitted=required<=available and capacity_fits,counterDescriptor=descriptor,
        quoteIdentity=quote_identity,requestSha256=request_sha256,inputBounds=bounds,
        maxRequests=max_requests,outputTokens=output_tokens,tokenCeiling=token_ceiling,
        reportedTokens=reported_tokens,inflightTokens=inflight_tokens,
        requiredTokens=required,availableTokens=available)
    if continuation_budget:plan['dispatchPolicy']='shared-execution-budget-v1'
    return plan


def validate_plan(plan):
    plan=decode(encode(plan,32768),32768)
    if type(plan) is not dict:raise ValueError('invalid trajectory plan')
    version=integer(plan.get('version'),1,2)
    fields(plan,('version','admitted','counterDescriptor','quoteIdentity','requestSha256',
        'inputBounds','maxRequests','outputTokens','tokenCeiling','reportedTokens',
        'inflightTokens','requiredTokens','availableTokens')+ (('dispatchPolicy',) if version==2 else ()))
    if version==2 and plan['dispatchPolicy']!='shared-execution-budget-v1':
        raise ValueError('invalid continuation policy')
    if type(plan['admitted']) is not bool:raise ValueError('invalid admission state')
    for key in ('requiredTokens','availableTokens'):integer(plan[key])
    expected=make_plan(counter_descriptor=plan['counterDescriptor'],quote_identity=plan['quoteIdentity'],
        request_sha256=plan['requestSha256'],input_bounds=plan['inputBounds'],max_requests=plan['maxRequests'],
        output_tokens=plan['outputTokens'],token_ceiling=plan['tokenCeiling'],
        reported_tokens=plan['reportedTokens'],inflight_tokens=plan['inflightTokens'],
        continuation_budget=version==2)
    if plan!=expected:raise ValueError('inconsistent trajectory plan')
    return plan


class _Guard:
    def __init__(self,base,plan,on_proposal):
        self._base,self._plan,self._on_proposal=base,plan,on_proposal
        self._lock=RLock();self._index=0;self._proposals=[];self._overflow_logged=False

    @property
    def proposals(self):
        with self._lock:return decode(encode(self._proposals))

    def count_tokens(self,native):
        with self._lock:
            index=self._index;reason=None;count=None
            dynamic=self._plan['version']==2
            ceiling=(max(0,min(self._plan['counterDescriptor']['contextCapacityTokens'],
                self._plan['tokenCeiling'])-self._plan['outputTokens']) if dynamic else
                self._plan['inputBounds'][index] if index<self._plan['maxRequests'] else None)
            owned=decode(encode(native,196608),196608)
            if type(owned) is not dict:raise ValueError('native request required')
            if index>=self._plan['maxRequests']:
                reason='proposalLimit'
                if self._overflow_logged:raise ValueError(reason)
                self._overflow_logged=True
            else:
                self._index+=1
                if not self._plan['admitted']:reason='mandatoryRejected'
                elif owned.get('model')!=self._base.descriptor.model:reason='modelMismatch'
                elif type(owned.get('max_tokens')) is not int or owned['max_tokens']!=self._plan['outputTokens']:
                    reason='outputCeiling'
                else:
                    try:
                        count=self._base.counter.count_tokens(decode(encode(owned,196608),196608))
                        integer(count)
                    except Exception:reason='counterFailure';count=None
                    else:
                        if count>ceiling:reason='inputCeiling'
            row=dict(proposal=index+1,requestSha256=digest(owned),inputBound=count,
                inputCeiling=ceiling if index<self._plan['maxRequests'] else None,
                outputCeiling=self._plan['outputTokens'],reason=reason or ('withinContext' if dynamic else 'withinPlan'))
            if dynamic:row['quotedInputBound']=self._plan['inputBounds'][index] if index<self._plan['maxRequests'] else None
            self._proposals.append(row)
            if self._on_proposal is not None:self._on_proposal(self.proposals)
            if reason:raise ValueError(reason)
            return count


def guard_registration(base,plan,*,on_proposal=None):
    """V2 counts the context domain; dispatch requires one shared ExecutionBudget.

    A successful proposal is not a reservation, dispatch or usage observation.
    Quotation slots select optional context; only Runtime may settle allowance.
    """
    from prosaic_runtime import TokenCounterRegistration
    if type(base) is not TokenCounterRegistration:raise ValueError('qualified base counter required')
    plan=validate_plan(plan)
    if base.descriptor.to_dict()!=plan['counterDescriptor']:raise ValueError('base counter drift')
    if on_proposal is not None and not callable(on_proposal):raise ValueError('invalid proposal observer')
    revision=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    binding=digest(dict(base=base.descriptor.to_dict(),plan=plan,implementation=revision))
    version=plan['version']
    descriptor=replace(base.descriptor,identity='trajectory-'+binding,
        implementation_version=f'trajectory-v{version}-'+revision,
        template_assets_digest=digest(dict(base=base.descriptor.template_assets_digest,plan=plan,implementation=revision)),
        guarantee='Qualified base counter within an enforced host input/output proposal domain. '
            'The serialized plan binds base provenance. Runtime owns actual shared allowance and unknown usage. '
            'Planning does not guarantee arbitrary continuations or semantic completion.')
    guard=_Guard(base,plan,on_proposal)
    guard.registration=TokenCounterRegistration(descriptor,guard)
    return guard
