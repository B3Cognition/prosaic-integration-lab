"""Check trusted host receipts against current sources, never against recalled notes."""
from lab_runner.quality.contracts import decode,digest,encode,identifier,integer
from lab_runner.quality.scoring import answer_issues


def score_case(case,evidence):
    reasons=[];metrics=dict(totalCalls=0,requestedRecords=0,duplicateRecords=0,irrelevantRecords=0,excessCalls=0)
    try:
        encode(evidence);identifier(evidence['sampleId'])
        if evidence['version']!=1 or evidence['caseId']!=case['caseId']:raise ValueError('identity')
        prepared=evidence['prepared']
        if digest(prepared)!=evidence['preparedDigest']:raise ValueError('prepared context')
        req=prepared['request'];retrieval=prepared['retrieval'];arm=prepared['arm']
        if arm not in {'enabled','disabled'} or req!={k:case[k] for k in ('caseId','task','recordIndex')}|{
                'draft':None,'recalledEpisodes':retrieval['episodes']}:raise ValueError('request')
        if prepared['binding']!=digest(dict(tenantId=case['tenantId'],arm=arm,request=req,retrieval=retrieval)):
            raise ValueError('scope')
        if retrieval['resultSha256']!=digest(retrieval['episodes']) or retrieval['resultBytes']!=len(encode(retrieval['episodes'])):
            raise ValueError('retrieval')
        if arm=='disabled' and retrieval['episodes']:raise ValueError('disabled memory')
        receipts=evidence['receipts']
        if evidence['receiptDigests']!=[digest(r) for r in receipts]:raise ValueError('receipt digest')
        by_id={r['id']:r for r in receipts};completions=[]
        if len(by_id)!=len(receipts):raise ValueError('duplicate receipt')
        for r in receipts:
            if r['run_id']!=digest({'sampleId':evidence['sampleId']})[:32] or r['arguments']['request']!=req:
                raise ValueError('foreign receipt')
            for ev in r['events']:
                if ev.get('event')=='tool_completed' and ev.get('status')=='ok':
                    if ev.get('name')!='lookup_records':raise ValueError('foreign tool')
                    completions.append((r['id'],ev['call_id']))
        if len(completions)!=len(set(completions)):raise ValueError('duplicate completion')
        matched=set();calls=set();read=set()
        for row in evidence['journal']:
            integer(row['callIndex']);identity=(row['invocationId'],row['callId']);call=(row['invocationId'],row['callIndex'])
            if identity in matched or call in calls or identity not in completions:raise ValueError('unmatched lookup')
            matched.add(identity);calls.add(call)
            if row['sampleId']!=evidence['sampleId'] or row['status']!='ok' or row['toolVersion']!='lookup-v1':
                raise ValueError('journal')
            ids=row['recordIds']
            if not 1<=len(ids)<=4 or len(set(ids))!=len(ids):raise ValueError('records')
            if row['signature']!=digest(dict(tool_name='lookup_records',tool_version='lookup-v1',arguments={'recordIds':ids})):
                raise ValueError('tool signature')
            if row['recordsSha256']!=digest([case['records'][key] for key in ids]):raise ValueError('source drift')
            events=[ev for ev in by_id[row['invocationId']]['events'] if ev.get('event')=='tool_completed' and
                ev.get('status')=='ok' and ev.get('name')=='lookup_records' and ev.get('tool_version')=='lookup-v1' and ev.get('call_id')==row['callId']]
            if len(events)!=1:raise ValueError('lookup event')
            metrics['totalCalls']+=1;metrics['requestedRecords']+=len(ids)
            metrics['duplicateRecords']+=len(set(ids)&read)
            metrics['irrelevantRecords']+=len(set(ids)-set(case['relevantRecords']));read.update(ids)
        if matched!=set(completions):raise ValueError('missing lookup journal')
        metrics['excessCalls']=max(0,metrics['totalCalls']-case['minimumCalls'])
        if not set(case['requiredRecords'])<=read:reasons.append('missingEvidence')
        if not receipts or receipts[-1]['result']['exit_code']!=0 or decode(receipts[-1]['result']['stdout'])!=evidence['answer']:
            raise ValueError('final answer receipt')
        reasons.extend(answer_issues(case,evidence['answer']))
        if evidence['completed'] is not True:reasons.append('executionIncomplete')
    except (ValueError,KeyError,TypeError,AttributeError,RecursionError):reasons.append('invalidEvidence')
    return dict(state='failed' if reasons else 'passed',reasons=sorted(set(reasons)),toolMetrics=metrics)
