"""Bounded public measurements; no raw notes, source IDs, tenant or prompt text."""
from lab_runner.quality.contracts import integer
import math
from .scoring import score_case


def retrieval_metrics(gold,retrieved,available):
    gold=set(gold);retrieved=set(retrieved);available=set(available);hits=len(gold&retrieved)
    return dict(goldCount=len(gold),retrievedCount=len(retrieved),hitCount=hits,
        recallAt3=None if not gold else hits/len(gold),precisionAt3=None if not retrieved else hits/len(retrieved),
        availableGoldCount=len(gold&available),corpusCoverage=None if not gold else len(gold&available)/len(gold))


def public_result(case,evidence,row,available):
    verdict=score_case(case,evidence)
    counts={k:evidence['counts'][k] for k in ('providerRequests','toolCalls','reportedTokens')}
    for k in ('providerRequests','toolCalls') :integer(evidence['counts'][k])
    if evidence['counts']['reportedTokens'] is not None:integer(evidence['counts']['reportedTokens'])
    integer(evidence['retrievalMetrics']['hostQueries'],0,1)
    if type(evidence['firstPass']) is not bool:raise ValueError('invalid first-pass result')
    if type(evidence.get('reservationRetained',False)) is not bool:raise ValueError('invalid reservation marker')
    for key in ('schemaRepairs','taskRepairs'):integer(evidence[key])
    integer(evidence['retrievalMetrics']['resultBytes'],0,4096)
    for value in (evidence['elapsedSeconds'],evidence['retrievalMetrics']['elapsedSeconds']):
        if value is None and evidence.get('recovered') is True:continue
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:raise ValueError('invalid memory duration')
    public_row={k:row[k] for k in ('sampleId','caseId','profileFingerprint','arm')}
    return public_row|verdict|dict(family=case['family'],counts=counts,firstPass=evidence['firstPass'],
        reservationRetained=evidence.get('reservationRetained',False),
        schemaRepairs=evidence['schemaRepairs'],taskRepairs=evidence['taskRepairs'],elapsedSeconds=evidence['elapsedSeconds'],
        hostQueries=evidence['retrievalMetrics']['hostQueries'],retrievalSeconds=evidence['retrievalMetrics']['elapsedSeconds'],
        resultBytes=evidence['retrievalMetrics']['resultBytes'],
        retrieval=retrieval_metrics(case['goldEpisodes'],[e['episodeId'] for e in evidence['prepared']['retrieval']['episodes']],available))


def unknown_result(row,case=None,preparation=None,available=()):
    p=preparation['prepared'] if preparation is not None else None
    return row|dict(state='unknown',reasons=['interruptedEvidence'],reservationRetained=True,counts=dict(providerRequests=None,toolCalls=None,reportedTokens=None),
        family='unknown' if case is None else case['family'],firstPass=False,schemaRepairs=0,taskRepairs=0,elapsedSeconds=None,
        hostQueries=None if preparation is None else preparation['hostQueries'],
        retrievalSeconds=None if preparation is None else preparation['retrievalSeconds'],
        resultBytes=None if p is None else p['retrieval']['resultBytes'],
        retrieval=None if p is None or case is None else retrieval_metrics(case['goldEpisodes'],
            [e['episodeId'] for e in p['retrieval']['episodes']],available),toolMetrics={})


def summarize(rows,results,*,identity,origin,fixture_counts=None):
    passed=sum(r['state']=='passed' for r in results);attempted=len(results)
    usage=bool(results) and all(r['counts']['reportedTokens'] is not None for r in results)
    report=dict(version=1,origin=origin,identity=identity,schedule=rows,results=results,scheduledSamples=len(rows),
        executedSamples=attempted,baselineComplete=len(results)==len(rows) and usage,usageComplete=usage,
        retainedUnknownSamples=sum(r.get('reservationRetained',False) for r in results),
        taskSuccess=dict(passed=passed,attempted=attempted,rate=None if not attempted else passed/attempted),
        stateCounts={**{state:sum(r['state']==state for r in results) for state in ('passed','failed','unknown')},'notRun':len(rows)-len(results)},
        hostQueries=None if any(r['hostQueries'] is None for r in results) else sum(r['hostQueries'] for r in results),schemaRepairs=sum(r['schemaRepairs'] for r in results),
        taskRepairs=sum(r['taskRepairs'] for r in results),pairs=[],profiles={})
    for key in ('providerRequests','toolCalls','reportedTokens'):
        report[key]=None if any(r['counts'][key] is None for r in results) else sum(r['counts'][key] for r in results)
    for profile in dict.fromkeys(r['profileFingerprint'] for r in rows):
        sub=[r for r in results if r['profileFingerprint']==profile]
        arms={}
        for arm in ('enabled','disabled'):
            rs=[r for r in sub if r['arm']==arm]
            arms[arm]=dict(taskSuccess=dict(passed=sum(r['state']=='passed' for r in rs),attempted=len(rs)),
                stateCounts={**{state:sum(r['state']==state for r in rs) for state in ('passed','failed','unknown')},
                    'notRun':sum(r['profileFingerprint']==profile and r['arm']==arm for r in rows)-len(rs)},
                firstPass=sum(r['firstPass'] for r in rs),hostQueries=None if any(r['hostQueries'] is None for r in rs) else sum(r['hostQueries'] for r in rs),
                retrieval=[r['retrieval'] for r in rs])
        report['profiles'][profile]=arms
        for case_id in dict.fromkeys(r['caseId'] for r in rows):
            pair={r['arm']:r for r in sub if r['caseId']==case_id}
            transition='incomplete'
            if len(pair)==2 and all(r['state'] in {'passed','failed'} for r in pair.values()):
                a=pair['enabled']['state']=='passed';b=pair['disabled']['state']=='passed'
                transition='bothPassed' if a and b else 'enabledOnly' if a else 'disabledOnly' if b else 'bothFailed'
            report['pairs'].append(dict(profileFingerprint=profile,caseId=case_id,transition=transition))
    if fixture_counts is not None:report['fixtureCounts']=fixture_counts
    return report
