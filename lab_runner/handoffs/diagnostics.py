"""Rollout-specific example adapter for the generic consumer qualification API.

This reads saved host state only. It does not alter execution/scoring, trust a
model's source claims, disclose expected values, or replace accounting admission.
"""
from jsonschema import Draft202012Validator
import math
from lab_runner.quality.contracts import decode, digest
from lab_runner.role_qualification import FieldCheck, assess_output
from .contracts import request_for, assignment, LIMITS
from .direct_contracts import output_schemas, expected_worker, expected_review


def _unavailable(schema, code, status='failed'):
    return dict(version=1,status=status,schemaDigest=digest(schema),
                diagnostics=[dict(code=code,field='',evidenceRefs=[])])


def _sources(case, evidence):
    request=request_for(case);binding=assignment(request);receipts=evidence['receipts']
    if evidence['hostAssignment']!=binding or evidence['receiptDigests']!=[digest(r) for r in receipts]:
        raise ValueError('receipt or assignment changed')
    ids=[r['id'] for r in receipts]
    if len(set(ids))!=len(ids) or len({r['step'] for r in receipts})!=len(receipts):raise ValueError('duplicate receipt')
    expected_run=digest(dict(sampleId=evidence['sampleId']))[:32]
    if any(r['run_id']!=expected_run for r in receipts):raise ValueError('foreign run')
    by_role={r['step']:r for r in receipts};mode=evidence['mode']
    if mode not in ('worker','critic','handoff') or set(by_role)-({'worker','critic'} if mode=='handoff' else {mode}):
        raise ValueError('foreign role')
    scoped=[];subject=None;control_ids=None
    if mode=='critic':
        subject=evidence['controlledDraft'];ids=evidence['controlledRecordIds']
        ids=sorted(case['records']) if ids is None else ids
        if type(ids) is not list or not ids or len(set(ids))!=len(ids):raise ValueError('invalid control scope')
        control_ids=ids
        scoped=[case['records'][k] for k in ids]
        if not Draft202012Validator(output_schemas()['worker']).is_valid(subject):raise ValueError('invalid control draft')
    elif 'worker' in by_role:
        worker=by_role['worker']
        for entry in evidence['journal']:
            if entry['invocationId']!=worker['id']:continue
            values=[case['records'][k] for k in entry['recordIds']]
            if (entry['sampleId']!=evidence['sampleId'] or entry['assignmentId']!=binding['assignmentId']
                    or digest(values)!=entry['recordsSha256']):raise ValueError('foreign lookup')
            scoped.extend(values)
        try:subject=decode(worker['result']['stdout'])
        except (TypeError,ValueError):pass
        if worker['result']['exit_code']==0 and not scoped:raise ValueError('no scoped lookup')
    expected_request=request|dict(assignment=binding)
    if mode=='critic':expected_request['reviewDraft']=subject
    for receipt in receipts:
        if receipt['arguments']['request']!=expected_request:raise ValueError('changed request')
        adapter=receipt['result']['metadata']['runtime_adapter_v1']
        expected_version='direct-v2-'+digest(dict(request=expected_request,snapshot=case['records'],mode=mode,ids=control_ids))
        if adapter['version']!=expected_version:raise ValueError('changed execution scope')
        if receipt['step']=='critic':
            projected=receipt['arguments']|dict(currentEvidence=dict(assignmentId=binding['assignmentId'],
                origin='hostControl' if mode=='critic' else 'workerLookup',records=scoped))
            if (len(adapter['attempts'])!=1 or adapter['attempts'][0]['arguments_sha256']!=digest(projected)):
                raise ValueError('changed projected evidence')
    if mode=='handoff' and 'critic' in by_role:
        args=by_role['critic']['arguments']
        if (not Draft202012Validator(output_schemas()['worker']).is_valid(subject)
                or args['artifact_bindings']['worker']['id']!=by_role['worker']['id']
                or args['artifacts']['worker']!=subject):raise ValueError('foreign worker binding')
    return request,binding,by_role,scoped,subject


def _accounting(evidence):
    """Reconcile public saved totals; this does not replace recorder admission."""
    codes=[]
    def add(code):
        if code not in codes:codes.append(code)
    def count(value):return type(value) is int and value>=0
    try:
        totals=evidence['counts']
        if set(totals)!= {'providerRequests','toolCalls','reportedTokens'}:raise ValueError('totals')
        if any(not count(totals[k]) for k in ('providerRequests','toolCalls')):raise ValueError('counts')
        if totals['reportedTokens'] is not None and not count(totals['reportedTokens']):raise ValueError('tokens')
        requests=tools=tokens=0;complete=True
        for receipt in evidence['receipts']:
            result=receipt['result'];budget=result['metadata']['invocation_budgets_v1'];usage=result['token_usage']
            if (any(not count(budget[k]) for k in ('provider_requests','tool_calls','reported_tokens'))
                    or type(budget['usage_complete']) is not bool or usage is not None and not count(usage)):
                raise ValueError('receipt accounting')
            requests+=budget['provider_requests'];tools+=budget['tool_calls']
            if budget['provider_requests']>2 or budget['tool_calls']>1:add('budget_violation')
            if usage is None or not budget['usage_complete']:complete=False
            elif budget['reported_tokens']!=usage:raise ValueError('receipt tokens')
            else:tokens+=usage
        if not complete or totals['reportedTokens'] is None:add('unknown_usage')
        if totals!=dict(providerRequests=requests,toolCalls=tools,reportedTokens=tokens if complete else None):
            raise ValueError('unreconciled totals')
        if any(totals[k] is not None and totals[k]>LIMITS[k] for k in totals):add('budget_violation')
    except (ValueError,KeyError,TypeError):add('unverified_accounting')
    elapsed=evidence.get('elapsedSeconds')
    if type(elapsed) not in (int,float) or not math.isfinite(elapsed) or elapsed<0:add('unknown_timing')
    elif elapsed>LIMITS['timeoutSeconds']:add('budget_violation')
    if evidence.get('admissionViolation'):add('budget_violation')
    return codes


def diagnose_direct(case, evidence):
    """Return all field failures, partial-review coverage and scoped source refs.

    Case snapshots/receipts must be loaded from trusted host storage. Hashes bind
    those inputs together; they do not authenticate a client-created snapshot.
    """
    schemas=output_schemas();mode=evidence.get('mode')
    roles=['worker','critic'] if mode=='handoff' else [mode] if mode in schemas else []
    if not roles:raise ValueError('invalid direct mode')
    try:request,binding,receipts,rows,subject=_sources(case,evidence)
    except (ValueError,KeyError,TypeError):
        return dict(version=1,roles={r:_unavailable(schemas[r],'unverified_evidence') for r in roles})
    clean=expected_worker(request,rows)
    refs=['assignment:'+binding['assignmentId']]
    index_refs=['index:'+r['recordId'] for r in request['recordIndex']]
    source_refs=['record:'+r['recordId'] for r in rows]
    # Bound references without exposing expected source values or task prose.
    support=tuple(dict.fromkeys((refs+index_refs+source_refs)))[:32]
    worker_checks=[FieldCheck(path,value,evidence_refs=support,comparison=comparison) for path,value,comparison in
        [('/assignmentId',clean['assignmentId'],'equal'),('/status',clean['status'],'equal'),
         ('/answer/decision',clean['answer']['decision'],'equal'),('/answer/facts',clean['answer']['facts'],'set'),
         ('/answer/citations',clean['answer']['citations'],'set')]]
    accounting_codes=_accounting(evidence)
    results={}
    for role in roles:
        receipt=receipts.get(role)
        if receipt is None:
            results[role]=_unavailable(schemas[role],'not_run','unavailable');continue
        result=receipt['result'];review=None;target=None
        checks=worker_checks
        if role=='critic':
            if subject is None:
                results[role]=_unavailable(schemas[role],'unverified_evidence');continue
            target=expected_review(clean,subject)
            checks=[FieldCheck('/'+field,value,evidence_refs=support,comparison='set' if field=='issues' else 'equal')
                    for field,value in target.items()]
            try:review=decode(result['stdout'])
            except (TypeError,ValueError):pass
        assessment=assess_output(result['stdout'],schemas[role],checks=checks,exit_code=result['exit_code'],
            usage_known=result['token_usage'] is not None and 'unknown_usage' not in accounting_codes,
            budget_violation='budget_violation' in accounting_codes)
        for code in accounting_codes:
            item=dict(code=code,field='',evidenceRefs=[])
            if item not in assessment['diagnostics']:assessment['diagnostics'].append(item)
        if accounting_codes:assessment['status']='failed'
        if role=='critic':
            usable=result['exit_code']==0 and Draft202012Validator(schemas['critic']).is_valid(review)
            wanted=set(target['issues']);found=set(review['issues']) if usable else set()
            assessment.update(missingIssueFields=sorted(wanted-found),unsupportedIssueFields=sorted(found-wanted),
                coarseEscalationCorrect=bool(usable and review['assignmentId']==binding['assignmentId']
                    and target['verdict']==review['verdict']=='escalate'))
        results[role]=assessment
    return dict(version=1,assignmentId=binding['assignmentId'],roles=results)
