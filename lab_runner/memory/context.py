"""Freeze host-scoped recall before inference; notes never become authority."""
from lab_runner.quality.contracts import decode,digest,encode,identifier,integer
from .corpus import timestamp,text,fields
import math


def current_index(index):
    if type(index) is not list or not 1<=len(index)<=16:raise ValueError('invalid current index')
    seen=set()
    for row in index:
        fields(row,('recordId','factId','authority','revision'))
        for k in ('recordId','factId','authority'):identifier(row[k])
        integer(row['revision'],0,1000000)
        if row['recordId'] in seen:raise ValueError('duplicate current index')
        seen.add(row['recordId'])
    return decode(encode(index))


def current_sources(records):
    if type(records) is not dict or not 1<=len(records)<=16:raise ValueError('invalid current sources')
    for key,row in records.items():
        fields(row,('recordId','factId','authority','revision','value'))
        current_index([{k:row[k] for k in ('recordId','factId','authority','revision')}])
        if key!=row['recordId'] or type(row['value']) not in (int,float) or not math.isfinite(row['value']):
            raise ValueError('invalid public source')
    return decode(encode(records))


def prepare(case,corpus,arm,*,context_builder=None):
    if context_builder is not None:return context_builder.prepare(case,arm)
    if arm not in {'enabled','disabled'}:raise ValueError('invalid memory arm')
    identifier(case['caseId']);identifier(case['tenantId']);timestamp(case['asOf'])
    query=text(case['entity']+' '+' '.join(case['topics'])+' '+case['task'],8192)
    if arm=='enabled':retrieval=corpus.retrieve(case['tenantId'],query,case['asOf'])
    else:retrieval=dict(corpusDigest=corpus.tenant_digest(case['tenantId']),querySha256=digest(query),
        asOf=case['asOf'],episodes=[],resultSha256=digest([]),resultBytes=len(encode([])),
        eligibleCount=None,candidateCount=None)
    request=dict(caseId=case['caseId'],task=case['task'],recordIndex=current_index(case['recordIndex']),
                 draft=None,recalledEpisodes=retrieval['episodes'])
    binding=digest(dict(tenantId=case['tenantId'],arm=arm,request=request,retrieval=retrieval))
    return decode(encode(dict(request=request,retrieval=retrieval,binding=binding,arm=arm)))
