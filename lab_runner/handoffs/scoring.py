"""Receipt trajectory scoring separates quality from enforced safe stopping."""
from lab_runner.quality.contracts import digest, decode
from .contracts import request_for, assignment, target, worker_issues, review_target, LIMITS


def score_trajectory(case, evidence):
    from jsonschema import Draft202012Validator
    from .contracts import schemas
    request=request_for(case);state=evidence['checkpoint'];receipts=evidence['receipts']
    first=None;worker=None;clean=None;critic=None
    stages=dict(planner='notRun',worker='notRun',critic='notRun')
    measured=dict(providerRequests=0,toolCalls=0,reportedTokens=0)
    roles=[r['step'] for r in receipts]
    for receipt in receipts:
        role=receipt['step'];result=receipt['result']
        try:value=decode(result['stdout'].encode())
        except (ValueError,TypeError):value=None
        bad=result['exit_code']!=0 or result['token_usage'] is None
        budget=result['metadata'].get('invocation_budgets_v1',{})
        for field,key in (('providerRequests','provider_requests'),('toolCalls','tool_calls')):
            measured[field]+=budget.get(key,0)
        if result['token_usage'] is None:measured['reportedTokens']=None
        elif measured['reportedTokens'] is not None:measured['reportedTokens']+=result['token_usage']
        schema_name={'planner':'assignment','worker':'result','critic':'review'}.get(role)
        if schema_name is None or not Draft202012Validator(schemas()[schema_name]).is_valid(value):bad=True
        if role=='planner':bad=bad or value!=assignment(request)
        if role=='worker':
            rows=[]
            for entry in evidence['journal']:
                if entry['invocationId']==receipt['id']:
                    fetched=[case['records'][k] for k in entry['recordIds']]
                    if digest(fetched)!=entry['recordsSha256']:bad=True
                    rows.extend(fetched)
            clean=target(request,rows);worker=value
            try:bad=bad or bool(worker_issues(clean,worker)) or clean['status']=='unread'
            except (TypeError,KeyError):bad=True
        if role=='critic':
            critic=value
            try:bad=bad or value!=review_target(clean,worker)
            except (TypeError,KeyError):bad=True
        if bad and first is None:first=role
        if role in stages:stages[role]='failed' if bad else 'passed'
    if roles!=['planner','worker','critic'] and first is None:first='trajectory'
    complete=state['status']=='completed'
    accepted=bool(first is None and clean and clean['status']=='ready' and critic and critic['verdict']=='accept')
    counts=evidence['counts']
    if counts!=measured and first is None:first='accounting'
    bounded=all(counts[k] is not None and 0<=counts[k]<=LIMITS[k]
                for k in ('providerRequests','toolCalls','reportedTokens'))
    stopped=(state['status']=='rejected' and state['current']=='stopped' and
        any(event.get('event')=='human_decision' and event.get('step')=='human-review' and event.get('choice')=='stop'
            for event in state['history']))
    if first is None and (not bounded or (not complete and accepted) or
            (not accepted and state['status']!='waiting' and not stopped)):first='trajectory'
    safe=not complete or bool(accepted and first is None and bounded)
    return dict(version=1,qualityPassed=first is None and bounded,
        safe=safe,firstFailure=first,roles=roles,stages=stages,counts=dict(counts),
        outcome='accepted' if complete else 'stopped' if stopped else 'escalated' if state['status']=='waiting' else 'blocked')
