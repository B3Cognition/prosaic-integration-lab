"""Closed, request-bound handoffs for the Lab's public synthetic task grammar."""
from copy import deepcopy
from lab_runner.quality.contracts import digest, identifier
from lab_runner.quality.checks import parse_task, assess_evidence, compare_fields
from lab_runner.memory.context import current_index, current_sources
from lab_runner.memory.evidence import admit_complete_index

LIMITS = dict(providerRequests=4, toolCalls=2, reportedTokens=8192, timeoutSeconds=600)


def request_for(case):
    identifier(case['caseId'])
    parse_task(case['task'])
    snapshot = current_sources(case['records'])
    index = current_index(case['recordIndex'])
    admit_complete_index(index, snapshot)
    return dict(caseId=case['caseId'], task=case['task'], recordIndex=index, sourcesSha256=digest(snapshot))


def assignment(request):
    authority, required, _ = parse_task(request['task'])
    return dict(version=1, assignmentId=digest(request), caseId=request['caseId'],
                authority=authority, requiredFacts=required)


def object_schema(properties):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)


def schemas():
    binding = dict(type='string', pattern='^[a-f0-9]{64}$')
    name = dict(type='string', pattern='^[A-Za-z][A-Za-z0-9_-]{0,63}$')
    names = dict(type='array', items=name, uniqueItems=True, maxItems=16)
    answer = object_schema(dict(decision={'enum':['approve','reject','insufficient']}, facts=names,
        citations=dict(type='array', maxItems=16, uniqueItems=True,
            items=object_schema(dict(factId=name, recordId=name)))))
    return dict(assignment=object_schema(dict(version={'const':1}, assignmentId=binding,
                    caseId=name, authority=name, requiredFacts=names)),
        result=object_schema(dict(assignmentId=binding, status={'enum':['ready','missing','unread','conflict']},
            answer=answer, evidence=dict(type='array',maxItems=16,items=object_schema(dict(
                recordId=name,factId=name,authority=name,revision=dict(type='integer',minimum=0,maximum=1000000),
                value=dict(type='number')))))),
        review=object_schema(dict(assignmentId=binding, verdict={'enum':['accept','escalate']},
            issues=dict(type='array', uniqueItems=True, maxItems=6,
                        items={'enum':['binding','status','decision','facts','citations','evidence']}))))


def target(request, records):
    """Host evidence oracle. Never infer values from the complete index."""
    authority, _, _ = parse_task(request['task'])
    index = request['recordIndex']
    latest = {}
    for row in index:
        if row['authority'] == authority:
            latest[row['factId']] = max(latest.get(row['factId'], -1), row['revision'])
    ambiguous = any(sum(r['authority']==authority and r['factId']==fact and r['revision']==rev
                        for r in index) > 1 for fact, rev in latest.items())
    if ambiguous:
        # Colliding authoritative revisions cannot be resolved by arbitrary order.
        status='conflict';answer=dict(decision='insufficient',facts=[],citations=[])
    else:
        assessed = assess_evidence(request, records)
        status = 'unread' if assessed['missingRecords'] else 'missing' if assessed['missingFacts'] else 'ready'
        answer = assessed['answer']
    return dict(assignmentId=digest(request), status=status, answer=deepcopy(answer),evidence=deepcopy(records))


def worker_issues(expected, value):
    issues=[]
    if value['assignmentId'] != expected['assignmentId']:issues.append('binding')
    if value['status'] != expected['status']:issues.append('status')
    if value['evidence'] != expected['evidence']:issues.append('evidence')
    return issues + compare_fields(expected['answer'], value['answer'])


def review_target(expected, worker):
    issues=worker_issues(expected, worker)
    return dict(assignmentId=expected['assignmentId'],
                verdict='accept' if not issues and expected['status']=='ready' else 'escalate', issues=issues)
