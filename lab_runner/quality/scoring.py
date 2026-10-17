"""Pure scoring of trusted host evidence; does not attest arbitrary imported logs."""
from jsonschema import Draft202012Validator, ValidationError
from .contracts import decode, digest, encode,identifier,integer
from .suite import resource,public_case


def answer_issues(case,answer):
    try:Draft202012Validator(decode(resource('answer.schema.json'))).validate(answer)
    except ValidationError:return ['invalidAnswer']
    reasons=[]
    if answer['decision'] != case['expected']['decision']: reasons.append('wrongDecision')
    if set(answer['facts']) != set(case['expected']['facts']): reasons.append('wrongFacts')
    pairs=lambda a:{(c['factId'],c['recordId']) for c in a['citations']}
    if pairs(answer) != pairs(case['expected']): reasons.append('wrongCitations')
    return reasons


def score_case(case, evidence):
    reasons = []
    metrics = dict(totalCalls=0, requestedRecords=0, duplicateRecords=0,
                   irrelevantRecords=0, excessCalls=0)
    try:
        encode(evidence)
        if type(evidence['version']) is not int or evidence['version'] != 1 or evidence['caseId'] != case['caseId']:
            raise ValueError('identity')
        identifier(evidence['sampleId'])
        if type(evidence['completed']) is not bool:raise ValueError('completion')
        receipts = evidence['receipts']
        if evidence['receiptDigests'] != [digest(r) for r in receipts]:
            raise ValueError('receipt')
        by_id = {r['id']:r for r in receipts}
        if len(by_id) != len(receipts): raise ValueError('duplicate receipt')
        completions=[]
        for receipt in receipts:
            if receipt['run_id']!=digest({'sampleId':evidence['sampleId']})[:32] or receipt['arguments']['request']!=public_case(case):
                raise ValueError('foreign receipt')
            for event in receipt['events']:
                if event.get('event')=='tool_completed' and event.get('status')=='ok':
                    if event.get('name')!='lookup_records':raise ValueError('unexpected tool')
                    completions.append((receipt['id'],event['call_id']))
        if len(completions)!=len(set(completions)):raise ValueError('duplicate completion')
        read, calls, matched = set(), set(), set()
        for row in evidence['journal']:
            integer(row['callIndex'])
            call = (row['invocationId'], row['callIndex'])
            if call in calls: raise ValueError('duplicate execution')
            calls.add(call)
            identity=(row['invocationId'],row['callId'])
            if identity in matched:raise ValueError('reused completion')
            matched.add(identity)
            if row['sampleId'] != evidence['sampleId'] or row['status'] != 'ok' or row['toolVersion'] != 'lookup-v1':
                raise ValueError('journal identity')
            receipt = by_id[row['invocationId']]
            events = [e for e in receipt['events'] if e.get('event') == 'tool_completed'
                      and e.get('name') == 'lookup_records' and e.get('status') == 'ok'
                      and e.get('tool_version') == row['toolVersion'] and e.get('call_id') == row['callId']]
            if len(events) != 1: raise ValueError('missing execution')
            ids = row['recordIds']
            if not 1 <= len(ids) <= 4 or len(set(ids)) != len(ids): raise ValueError('records')
            if row['signature'] != digest(dict(tool_name='lookup_records',tool_version='lookup-v1',
                                               arguments={'recordIds':ids})):
                raise ValueError('argument identity')
            if row['recordsSha256'] != digest([case['records'][r] for r in ids]):
                raise ValueError('record digest')
            metrics['totalCalls'] += 1
            metrics['requestedRecords'] += len(ids)
            metrics['duplicateRecords'] += len(set(ids) & read)
            metrics['irrelevantRecords'] += len(set(ids) - set(case['relevantRecords']))
            read.update(ids)
        if matched!=set(completions):raise ValueError('unmatched tool execution')
        metrics['excessCalls'] = max(0, metrics['totalCalls']-case['minimumCalls'])
        if not set(case['requiredRecords']) <= read: reasons.append('missingEvidence')
        answer = evidence['answer']
        if not receipts or receipts[-1]['result']['exit_code'] != 0 or decode(receipts[-1]['result']['stdout']) != answer:
            raise ValueError('answer receipt mismatch')
        reasons.extend(answer_issues(case,answer))
        if not evidence['completed']: reasons.append('executionIncomplete')
        if case['kind']=='repair' and evidence.get('criticDetected') is not True:
            reasons.append('criticMissedError')
    except ValidationError:
        reasons.append('invalidAnswer')
    except (ValueError, KeyError, TypeError, AttributeError, RecursionError):
        reasons.append('invalidEvidence')
    return dict(state='failed' if reasons else 'passed', reasons=sorted(set(reasons)), toolMetrics=metrics)
