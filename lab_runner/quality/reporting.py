"""Closed public projections; private receipts and model strings stay private."""
import math
import re
import statistics
from .contracts import digest,encode,identifier,integer,sha
from .scoring import score_case
from .suite import load_suite

STATES={'passed','failed','unknown','unsupported'}
REASONS={'missingEvidence','wrongDecision','wrongFacts','wrongCitations','executionIncomplete',
         'invalidAnswer','invalidEvidence','criticMissedError'}
ROW_KEYS={'sampleId','caseId','profileFingerprint','repetition','state','reasons','counts','toolMetrics',
          'schemaRepairs','taskRepairs','firstPass','criticDetected','elapsedSeconds','inputTokens','outputTokens'}


def public_result(case,evidence,*,profile_fingerprint,repetition):
    verdict=score_case(case,evidence)
    return dict(sampleId=evidence['sampleId'],caseId=case['caseId'],profileFingerprint=sha(profile_fingerprint),
        repetition=integer(repetition,1,10),**verdict,counts=evidence['counts'],
        schemaRepairs=evidence['schemaRepairs'],taskRepairs=evidence['taskRepairs'],
        firstPass=evidence['firstPass'],criticDetected=evidence['criticDetected'],
        elapsedSeconds=evidence['elapsedSeconds'],inputTokens=evidence['inputTokens'],outputTokens=evidence['outputTokens'])


def _row(row):
    if set(row)!=ROW_KEYS or row['state'] not in STATES or not set(row['reasons'])<=REASONS:
        raise ValueError('invalid benchmark result')
    identifier(row['sampleId']);identifier(row['caseId']);sha(row['profileFingerprint']);integer(row['repetition'],1,10)
    if type(row['firstPass']) is not bool or type(row['criticDetected']) is not bool:raise ValueError('invalid result')
    if row['elapsedSeconds'] is None and row['state']=='unknown':pass
    elif type(row['elapsedSeconds']) not in (int,float) or not math.isfinite(row['elapsedSeconds']) or row['elapsedSeconds']<0:
        raise ValueError('invalid benchmark timing')
    if set(row['counts'])!={'providerRequests','toolCalls','reportedTokens'}:raise ValueError('invalid counts')
    for k,v in row['counts'].items():
        if v is None and (k=='reportedTokens' or row['state']=='unknown'):continue
        integer(v)
    if set(row['toolMetrics'])!={'totalCalls','requestedRecords','duplicateRecords','irrelevantRecords','excessCalls'}:
        raise ValueError('invalid tool metrics')
    for v in row['toolMetrics'].values():
        if v is None and row['state']=='unknown':continue
        integer(v)
    for key in ('inputTokens','outputTokens'):
        if row[key] is not None:integer(row[key])
    integer(row['schemaRepairs']);integer(row['taskRepairs'])


def estimate_cost(row,card):
    if card is None:return dict(units=None,currency=None,unitExponent=None,rateCardDigest=None)
    if (set(card)!={'version','currency','unitExponent','inputUnitsPerMillion','outputUnitsPerMillion'} or
            type(card['version']) is not int or card['version']!=1 or
            type(card['currency']) is not str or not re.fullmatch('[A-Z]{3}',card['currency'])):
        raise ValueError('invalid benchmark rate card')
    integer(card['unitExponent'],0,9)
    for k in ('inputUnitsPerMillion','outputUnitsPerMillion'):integer(card[k])
    units=None
    if row['inputTokens'] is not None and row['outputTokens'] is not None and row['counts']['reportedTokens'] is not None:
        units=(integer(row['inputTokens'])*card['inputUnitsPerMillion']+
               integer(row['outputTokens'])*card['outputUnitsPerMillion']+999999)//1000000
    return dict(units=units,currency=card['currency'],unitExponent=card['unitExponent'],rateCardDigest=digest(card))


def summarize(schedule,results,*,identity,origin,recovery):
    encode([schedule,results,identity,recovery])
    allowed_identity={'suiteId','scorerVersion','suiteDigest','proseDigest','toolDigest','policyDigest','sdkVersions','sdkManifestDigest','workflowDigest','schemaDigest','scorerDigest'}
    if set(identity)!=allowed_identity or identity.get('suiteId')!='evidence-review-v1':
        raise ValueError('invalid public benchmark identity')
    for key,value in identity.items():
        if key.endswith('Digest'):sha(value)
        elif key=='scorerVersion' and value!='evidence-score-v1':raise ValueError('invalid scorer')
        elif key=='sdkVersions':
            if set(value)!={'b3-prosaic','b3-prosaic-runtime','b3-prosaic-harness'} or any(
                type(v) is not str or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:\+[a-z0-9]+(?:\.[a-z0-9]+)*)?',v) for v in value.values()):
                raise ValueError('invalid SDK identity')
    for row in recovery:
        if set(row)!={'caseId','origin','passed','additionalProviderRequests','additionalToolCalls','elapsedSeconds','allowancePreserved'} or row['caseId'] not in {'saved-receipt','missing-receipt','schema-failure'} or row['origin']!='fixture':
            raise ValueError('invalid recovery evidence')
        if type(row['passed']) is not bool or type(row['allowancePreserved']) is not bool:raise ValueError('invalid recovery result')
        integer(row['additionalProviderRequests']);integer(row['additionalToolCalls'])
        if type(row['elapsedSeconds']) not in (int,float) or not math.isfinite(row['elapsedSeconds']) or row['elapsedSeconds']<0:raise ValueError('invalid recovery timing')
    if origin not in {'unexecuted','fixture','live'} or len(schedule)>400:raise ValueError('invalid benchmark origin or schedule')
    expected={row['sampleId']:row for row in schedule}
    logical=set();groups={}
    inventory={c['caseId'] for c in load_suite()['cases']}
    for row in schedule:
        if set(row)!={'sampleId','caseId','profileFingerprint','repetition'}:raise ValueError('invalid schedule')
        identifier(row['sampleId']);identifier(row['caseId']);sha(row['profileFingerprint']);integer(row['repetition'],1,10)
        key=(row['profileFingerprint'],row['caseId'],row['repetition'])
        if key in logical or row['caseId'] not in inventory:raise ValueError('invalid logical sample')
        logical.add(key)
        groups.setdefault((row['profileFingerprint'],row['repetition']),set()).add(row['caseId'])
    full_inventory=bool(groups) and all(ids==inventory for ids in groups.values())
    for fp in {r['profileFingerprint'] for r in schedule}:
        repetitions={rep for profile,rep in groups if profile==fp}
        full_inventory &= repetitions==set(range(1,max(repetitions)+1))
    if len(expected)!=len(schedule):raise ValueError('duplicate scheduled sample')
    seen=set()
    for row in results:
        _row(row)
        if row['sampleId'] in seen or row['sampleId'] not in expected:raise ValueError('foreign benchmark sample')
        seen.add(row['sampleId'])
        if any(expected[row['sampleId']][k]!=row[k] for k in ('caseId','profileFingerprint','repetition')):
            raise ValueError('foreign sample binding')
    if origin=='unexecuted' and results:raise ValueError('unexecuted evidence')
    state_counts={k:sum(r['state']==k for r in results) for k in sorted(STATES)}
    state_counts['notRun']=len(schedule)-len(results)
    usage_complete=bool(results) and all(r['counts']['reportedTokens'] is not None for r in results)
    passed=state_counts['passed']
    profiles={}
    for fp in sorted({r['profileFingerprint'] for r in schedule}):
        observations=[r for r in results if r['profileFingerprint']==fp]
        ordinary=[r for r in observations if not r['caseId'].startswith('repair-')]
        repaired=[r for r in observations if r['caseId'].startswith('repair-')]
        good=sum(r['state']=='passed' for r in observations)
        profiles[fp]=dict(scheduledSamples=sum(r['profileFingerprint']==fp for r in schedule),
            taskSuccess=dict(passed=good,attempted=len(observations),rate=good/len(observations) if observations else None),
            firstPass=dict(passed=sum(r['firstPass'] for r in ordinary),attempted=len(ordinary)),
            repairCases=len(repaired),criticDetections=sum(r['criticDetected'] for r in repaired),
            correctedDraftSuccesses=sum(r['state']=='passed' for r in repaired),
            latency=_latency(observations),
            schemaRepairs=sum(r['schemaRepairs'] for r in observations),taskRepairs=sum(r['taskRepairs'] for r in observations),
            providerRequests=_sum_known(r['counts']['providerRequests'] for r in observations),
            reportedTokens=sum(r['counts']['reportedTokens'] for r in observations) if observations and all(r['counts']['reportedTokens'] is not None for r in observations) else None,
            toolMetrics={k:_sum_known(r['toolMetrics'][k] for r in observations) for k in ('totalCalls','requestedRecords','duplicateRecords','irrelevantRecords','excessCalls')})
    return dict(version=1,identity=identity,origin=origin,schedule=schedule,results=results,profiles=profiles,
        scheduledSamples=len(schedule),executedSamples=len(results),stateCounts=state_counts,
        baselineComplete=full_inventory and len(results)==len(schedule) and usage_complete and
            origin!='unexecuted' and all(r['passed'] for r in recovery),
        taskSuccess=dict(passed=passed,attempted=len(results),rate=passed/len(results) if results else None),
        usageComplete=usage_complete,reportedTokens=sum(r['counts']['reportedTokens'] for r in results) if usage_complete else None,
        providerRequests=_sum_known(r['counts']['providerRequests'] for r in results),
        toolCalls=_sum_known(r['counts']['toolCalls'] for r in results),
        firstPassSuccesses=sum(r['firstPass'] for r in results),
        schemaRepairs=sum(r['schemaRepairs'] for r in results),taskRepairs=sum(r['taskRepairs'] for r in results),
        latency=_latency(results),
        recovery=recovery)


def _sum_known(values):
    values=list(values)
    return None if any(v is None for v in values) else sum(values)


def _latency(rows):
    durations=sorted(r['elapsedSeconds'] for r in rows if r['elapsedSeconds'] is not None)
    return dict(observations=len(durations),unknownObservations=len(rows)-len(durations),
        medianSeconds=statistics.median(durations) if durations else None,
        minSeconds=min(durations) if durations else None,maxSeconds=max(durations) if durations else None,
        p95Seconds=durations[math.ceil(.95*len(durations))-1] if len(durations)>=20 else None)


def unknown_result(row):
    return dict(**row,state='unknown',reasons=['executionIncomplete'],
        counts=dict(providerRequests=None,toolCalls=None,reportedTokens=None),
        toolMetrics={k:None for k in ('totalCalls','requestedRecords','duplicateRecords','irrelevantRecords','excessCalls')},
        schemaRepairs=0,taskRepairs=0,firstPass=False,criticDetected=False,elapsedSeconds=None,
        inputTokens=None,outputTokens=None)


def compare(reports):
    if not 2<=len(reports)<=8:raise ValueError('two to eight reports required')
    origin=reports[0]['origin'];identity=reports[0]['identity'];shape=None;seen=set();groups=[]
    for report in reports:
        rebuilt=summarize(report['schedule'],report['results'],identity=report['identity'],
                          origin=report['origin'],recovery=report['recovery'])
        if report!=rebuilt or report['identity']!=identity or report['origin']!=origin or origin=='unexecuted':
            raise ValueError('incompatible benchmark reports')
        current=sorted((r['caseId'],r['repetition']) for r in report['schedule'])
        if shape is not None and current!=shape:raise ValueError('incompatible benchmark schedules')
        shape=current
        for row in report['results']:
            key=(row['profileFingerprint'],row['caseId'],row['repetition'])
            if key in seen:raise ValueError('duplicate benchmark observation')
            seen.add(key)
        groups.append(dict(profiles=sorted({r['profileFingerprint'] for r in report['schedule']}),
            taskSuccess=report['taskSuccess'],latency=report['latency'],
            providerRequests=report['providerRequests'],reportedTokens=report['reportedTokens']))
    return dict(version=1,event='agentQualityComparison',identity=identity,origin=origin,
                baselineComplete=all(r['baselineComplete'] for r in reports),groups=groups)
