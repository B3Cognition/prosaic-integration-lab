"""Direct role scoring separates independent controls, quality and safe stopping."""
from jsonschema import Draft202012Validator
from lab_runner.quality.contracts import digest,decode
from .contracts import LIMITS,request_for,assignment
from .direct_contracts import output_schemas,expected_worker,worker_issues,expected_review,same_review


def score_direct(case,evidence):
    mode=evidence['mode'];control=mode=='critic';request=request_for(case)
    roles_expected=['worker','critic'] if mode=='handoff' else [mode]
    stages={r:'notRun' for r in roles_expected};first=None;clean=None;worker=None;review=None
    measured=dict(providerRequests=0,toolCalls=0,reportedTokens=0)
    state=evidence['checkpoint'];roles=[]
    for receipt in evidence['receipts']:
        role=receipt['step'];roles.append(role);result=receipt['result']
        try:value=decode(result['stdout'].encode())
        except (ValueError,TypeError):value=None
        bad=result['exit_code']!=0 or result['token_usage'] is None
        budgets=result['metadata'].get('invocation_budgets_v1',{})
        for field,key in (('providerRequests','provider_requests'),('toolCalls','tool_calls')):
            measured[field]+=budgets.get(key,0)
        if result['token_usage'] is None:measured['reportedTokens']=None
        elif measured['reportedTokens'] is not None:measured['reportedTokens']+=result['token_usage']
        schema=output_schemas().get(role)
        valid=schema is not None and Draft202012Validator(schema).is_valid(value)
        bad=bad or not valid
        if role=='worker':
            rows=[]
            for entry in evidence['journal']:
                if entry['invocationId']!=receipt['id']:continue
                fetched=[case['records'][k] for k in entry['recordIds']]
                if (entry['sampleId']!=evidence['sampleId'] or entry['assignmentId']!=assignment(request)['assignmentId']
                        or digest(fetched)!=entry['recordsSha256']):bad=True
                rows.extend(fetched)
            clean=expected_worker(request,rows);worker=value
            bad=bad or not rows or valid and (bool(worker_issues(clean,value)) or clean['status']=='unread')
        if role=='critic':
            review=value
            if control:
                ids=evidence['controlledRecordIds']
                rows=[case['records'][k] for k in (sorted(case['records']) if ids is None else ids)]
                clean=expected_worker(request,rows);worker=evidence['controlledDraft']
            try:bad=bad or not same_review(expected_review(clean,worker),value)
            except (TypeError,KeyError):bad=True
        if bad and first is None:first=role
        stages[role]='failed' if bad else 'passed'
    if roles!=roles_expected and first is None:first='trajectory'
    if evidence['hostAssignment']!=assignment(request) and first is None:first='binding'
    if evidence['counts']!=measured and first is None:first='accounting'
    bounded=all(measured[k] is not None and 0<=measured[k]<=LIMITS[k] for k in measured)
    accepted=bool(clean and Draft202012Validator(output_schemas()['worker']).is_valid(worker)
        and not worker_issues(clean,worker) and clean['status']=='ready'
        and (mode=='worker' or review and same_review(expected_review(clean,worker),review)))
    complete=state['status']=='completed'
    if first is None and (not bounded or (complete!=accepted) or
            not complete and state['status']!='waiting'):first='trajectory'
    return dict(version=2,control=control,qualityPassed=first is None and bounded,
        safe=not complete or bool(accepted and first is None and bounded),firstFailure=first,
        roles=roles,stages=stages,counts=dict(evidence['counts']),
        outcome='accepted' if complete else 'escalated' if state['status']=='waiting' else 'blocked')
