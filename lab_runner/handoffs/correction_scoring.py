"""Source-bound scoring for the optional correction consumer, not model claims."""
import math
from jsonschema import Draft202012Validator
from lab_runner.quality.contracts import decode,digest
from lab_runner.quality.usage_counts import complete_counts
from lab_runner.role_qualification import LIMITS
from .contracts import request_for,assignment
from .direct_contracts import output_schemas,instructions,expected_worker,worker_issues


def _parsed(receipt,role):
    if receipt is None or receipt['result']['exit_code']!=0:return None
    try:value=decode(receipt['result']['stdout'])
    except (ValueError,TypeError):return None
    schema=output_schemas()['critic' if role=='critic' else 'worker']
    return value if Draft202012Validator(schema).is_valid(value) else None


def score(case,evidence):
    from .correction import PROTOCOL,_fetched,_diagnostics,_projection,corrector_instructions
    request=request_for(case);binding=assignment(request);prepared=request|dict(assignment=binding)
    frame=evidence['envelope']['frame'];arm=evidence['arm']
    if (arm not in ('critic','no-critic') or frame['arm']!=arm or frame['protocol']!=PROTOCOL
            or frame['caseDigest']!=digest(case) or frame['taskDigest']!=digest(request) or frame['limits']!=LIMITS
            or frame['workerContractDigest']!=digest(dict(schema=output_schemas()['worker'],instructions=instructions('worker',binding)))
            or frame['correctorContractDigest']!=digest(dict(schema=output_schemas()['worker'],instructions=corrector_instructions(binding)))):
        raise ValueError('changed correction frame')
    version='bounded-v1-'+digest(frame)
    if evidence['envelope']['adapterVersion']!=version:raise ValueError('changed adapter version')
    receipts=evidence['receipts']
    if evidence['receiptDigests']!=[digest(r) for r in receipts]:raise ValueError('changed receipt')
    roles=[r['step'] for r in receipts]
    allowed=['worker','critic','corrector'] if arm=='critic' else ['worker','corrector']
    if roles!=allowed[:len(roles)] or len(roles)>len(allowed):raise ValueError('unexpected correction trajectory')
    by_role={r['step']:r for r in receipts};worker=by_role.get('worker')
    draft=_parsed(worker,'worker');rows=[]
    if worker and any(j['invocationId']==worker['id'] for j in evidence['journal']):
        rows=_fetched(case,evidence['journal'],evidence['sampleId'],binding,worker['id'])
    if draft is not None and not rows:raise ValueError('missing worker grounding')
    counts=dict(providerRequests=0,toolCalls=0,reportedTokens=0);calls=[];known=True
    for receipt in receipts:
        result=receipt['result'];meta=result['metadata'];budget=meta['invocation_budgets_v1'];role=receipt['step']
        if (receipt['run_id']!=digest(dict(sampleId=evidence['sampleId']))[:32]
                or receipt['arguments']['request']!=prepared or meta['runtime_adapter_v1']['version']!=version):
            raise ValueError('foreign invocation')
        for field,key in [('providerRequests','provider_requests'),('toolCalls','tool_calls')]:
            value=budget[key]
            if type(value) is not int or value<0:raise ValueError('invalid counts')
            counts[field]+=value
        usage=result['token_usage']
        if usage is None or not budget['usage_complete']:known=False
        elif type(usage) is not int or usage<0 or usage!=budget['reported_tokens']:raise ValueError('invalid usage')
        else:counts['reportedTokens']+=usage
        calls.extend(meta.get('accounting_v1',{}).get('provider_call_ids',[]))
        if role!='worker':
            data=receipt['arguments']
            if (data['artifacts']['worker']!=draft or data['artifact_bindings']['worker']['id']!=worker['id']):
                raise ValueError('foreign draft binding')
            if role=='corrector' and arm=='critic':
                if (data['artifacts']['critic']!=_parsed(by_role.get('critic'),'critic')
                        or data['artifact_bindings']['critic']['id']!=by_role['critic']['id']):raise ValueError('foreign review binding')
            projected=_projection(role,data,request,rows);attempts=meta['runtime_adapter_v1']['attempts']
            if (budget['provider_requests']>1 or budget['tool_calls']!=0
                    or budget['provider_requests'] and len(attempts)!=1
                    or any(a['arguments_sha256']!=digest(projected) for a in attempts)):
                raise ValueError('changed projection or unbounded continuation')
    if not known or evidence['checkpoint']['pending'] is not None:counts['reportedTokens']=None
    if counts!=evidence['counts']:raise ValueError('unreconciled counts')
    if len(calls)!=len(set(calls)) or len(calls)!=counts['providerRequests']:raise ValueError('duplicate/missing provider calls')
    intents=evidence['callIntents'];observations=evidence['callObservations']
    if not set(calls)<=set(intents) or not set(observations)<=set(intents):raise ValueError('foreign observation')
    component=[];observed=0;all_counted=True
    for call,observation in observations.items():
        values=complete_counts(observation.get('usage'));bound=evidence['callBounds'][call]
        if values is None:
            all_counted=False;component.append(dict(callId=call,kind='usageUnavailable'));continue
        inp,out,total=values
        observed+=total
        if inp>bound['inputBound']:component.append(dict(callId=call,kind='inputBoundExceeded'))
        if out>512:component.append(dict(callId=call,kind='outputBoundExceeded'))
    accounting_complete=bool(known and all_counted and evidence['checkpoint']['pending'] is None and set(calls)==set(intents)==set(observations))
    if accounting_complete and observed!=counts['reportedTokens']:raise ValueError('observed token mismatch')
    if {(v['callId'],v['kind']) for v in component}!={(v['callId'],v['kind']) for v in evidence['componentBreaches']}:
        raise ValueError('changed component accounting')
    role_costs={}
    for role in allowed:
        role_intents={k for k,v in intents.items() if v['context']['step_id']==role}
        role_observed=role_intents&set(observations)
        receipt=by_role.get(role)
        role_receipted=set(receipt['result']['metadata'].get('accounting_v1',{}).get('provider_call_ids',[])) if receipt else set()
        if not role_receipted<=role_intents:raise ValueError('foreign role accounting')
        unresolved=role_intents-role_observed
        role_counts=[complete_counts(observations[k].get('usage')) for k in role_observed]
        known_role=not unresolved and all(value is not None for value in role_counts)
        role_costs[role]=dict(providerRequests=len(role_observed|role_receipted),observedRequests=len(role_observed),
            observedTokens=sum(value[2] for value in role_counts) if known_role else None,
            unresolvedIntents=len(unresolved),unreceiptedObservations=len(role_observed-role_receipted))
    if any(v['context']['step_id'] not in allowed for v in intents.values()):raise ValueError('foreign role intent')
    elapsed=evidence['elapsedSeconds']
    within=bool(accounting_complete and counts['reportedTokens'] is not None and not evidence['admissionViolation']
        and not component and all(0<=counts[k]<=LIMITS[k] for k in counts)
        and type(elapsed) in (int,float) and math.isfinite(elapsed) and 0<=elapsed<=600)
    clean=expected_worker(request,rows)
    initial_ok=bool(draft is not None and not worker_issues(clean,draft))
    correction_called=bool(role_costs['corrector']['providerRequests'])
    correction_reached=bool('corrector' in by_role or correction_called or role_costs['corrector']['unresolvedIntents'])
    final=_parsed(by_role.get('corrector'),'corrector') if correction_reached else draft
    final_ok=bool(final is not None and not worker_issues(clean,final))
    accepted=evidence['checkpoint']['status']=='completed'
    safe_stopped=not accepted or final_ok and clean['status']=='ready' and within
    diagnostics=_diagnostics(request,rows,draft) if draft is not None else None
    match=None
    if draft is not None:
        match=dict(taskDigest=frame['taskDigest'],profileFingerprint=frame['profileFingerprint'],
            workerContractDigest=frame['workerContractDigest'],correctorContractDigest=frame['correctorContractDigest'],
            initialDraftDigest=digest(draft),evidenceDigest=digest(rows),diagnosticsDigest=digest(diagnostics),
            policyRevision=digest(dict(protocol=PROTOCOL,counter=evidence['envelope']['counterDescriptor'])),limits=dict(LIMITS))
    initial_issues=worker_issues(clean,draft) if draft is not None else None
    final_issues=worker_issues(clean,final) if final is not None else None
    assessable=initial_issues is not None and final_issues is not None
    added=sorted(set(final_issues)-set(initial_issues)) if assessable else None
    resolved=sorted(set(initial_issues)-set(final_issues)) if assessable else None
    effect=('not_run' if not correction_reached else
        ('interrupted' if correction_called else 'unresolved') if 'corrector' not in by_role else
        'not_dispatched' if not correction_called else 'unusable' if final is None else
        'regressed' if added else 'repaired' if not initial_ok and final_ok else
        'unchanged' if draft==final else 'changed_unrepaired')
    reported_counts=dict(counts)
    if not accounting_complete:reported_counts['reportedTokens']=None
    return dict(arm=arm,match=match,matchedEligible=match is not None,
        initialArtifactCorrect=initial_ok,finalArtifactCorrect=final_ok,taskAccepted=accepted,
        safe=bool(within and safe_stopped),safeStopped=bool(safe_stopped),withinLimits=within,
        correctionReached=correction_reached,criticReached=bool(by_role.get('critic') or role_costs.get('critic',{}).get('providerRequests') or role_costs.get('critic',{}).get('unresolvedIntents')),
        correctionCalled=correction_called,criticCalled=bool(role_costs.get('critic',{}).get('providerRequests')),roleCosts=role_costs,
        correctionEffect=effect,
        initialIssueFields=initial_issues,finalIssueFields=final_issues,newIssueFields=added,resolvedIssueFields=resolved,
        counts=reported_counts,receiptCounts=counts,accountingComplete=accounting_complete,
        outcome='accepted' if accepted else 'escalated' if evidence['checkpoint']['status']=='waiting' else 'blocked')
