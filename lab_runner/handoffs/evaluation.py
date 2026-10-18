"""Conservative evaluation policy; model review never authorizes acceptance."""
from copy import deepcopy
from pathlib import Path
import shutil
from jsonschema import Draft202012Validator
from lab_runner.quality.allowance import counts,private_directory
from .contracts import schemas,review_target,worker_issues


def classify_review(clean,worker,critic,*,usable):
    issues=worker_issues(clean,worker) if worker is not None else None
    flawed=bool(issues)
    expected=review_target(clean,worker) if worker is not None else None
    if critic is None:category='notReviewed'
    elif (not usable or worker is None or not Draft202012Validator(schemas()['review']).is_valid(critic)
          or critic['assignmentId']!=clean['assignmentId']):category='invalidReview'
    elif critic==expected:
        category='caught' if flawed else 'correctAccept' if clean['status']=='ready' else 'correctEscalation'
    elif flawed:category='missed' if critic['verdict']=='accept' else 'incorrectEscalation'
    elif clean['status']=='ready' and (critic['verdict']=='escalate' or critic['issues']):category='falseAlarm'
    else:category='incorrectReview'
    return dict(category=category,workerIssues=issues,expectedReview=expected,observedReview=critic,
        workerFlawReviewed=flawed and critic is not None,flawCaught=category=='caught',
        flawMissed=category=='missed',falseAlarm=category=='falseAlarm',
        invalidReview=category=='invalidReview',incorrectEscalation=category=='incorrectEscalation')


def charge_for(claim):
    if claim['state'] not in ('pending','unknown','known','overrun'):raise ValueError('invalid claim state')
    return deepcopy(counts(claim['actual'] if claim['state'] in ('known','overrun') else claim['maximum']))


def coverage(aliases,schedule,rows):
    report={}
    for alias in aliases:
        selected=[r for r in rows if r['alias']==alias]
        item={key:sum(bool(r.get(key)) for r in selected) for key in ('evidenceAvailable','workerReached',
            'workerCorrect','criticReached','criticCorrect','workerFlawReviewed','flawCaught','flawMissed',
            'falseAlarm','invalidReview','incorrectEscalation')}
        unknown=sum(r['claim'] in ('unknown','pending') for r in selected)
        item.update(scheduled=sum(r['alias']==alias for r in schedule),attempted=len(selected),samples=len(selected),
            unknownSamples=unknown,criticRequests=sum(r.get('criticRequests',0) for r in selected),
            criticTokens=sum(r.get('criticTokens') or 0 for r in selected),
            criticUsageComplete=bool(selected) and not unknown and all(r.get('evidenceAvailable',False) for r in selected))
        report[alias]=item
    return report


def inspect_partial(case,*,config,source,output,sample_id):
    """Copy persisted receipts, then read/reconcile without dispatch or forgiveness."""
    from prosaic_harness import RunNotFound
    from .execution import recover_case
    source=Path(source);output=private_directory(output)
    if not (source/'store').exists():return None
    shutil.copytree(source/'store',output/'store')
    journal=source/(sample_id+'-journal.json')
    if journal.exists():shutil.copyfile(journal,output/journal.name)
    try:return recover_case(case,config=config,output=output,sample_id=sample_id)
    except RunNotFound:return None
