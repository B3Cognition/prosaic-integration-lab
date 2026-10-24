"""Fixture-only comparison matrix and offline replay; no live authorization path."""

import hashlib
import json
from pathlib import Path

from .cases import load_cases
from .contracts import STRATEGIES, decode, digest, encoded
from .evidence import read_sample


def legacy_examples():
    from lab_runner.ship_eval.cases import load_suite
    from lab_runner.ship_eval.grader import grade
    from lab_runner.ship_eval.lookup import LookupSession
    cases,keys=load_suite();passed=unread_rejected=0
    for case_id,case in cases.items():
        key=keys[case_id]
        answer={'decision':key['decision'],'draftErrors':key['draftErrors'],'findings':[
            {'code':code,'citations':[{'recordId':r,'field':f} for r,f in alternatives[0]]}
            for code,alternatives in key['findings'].items()]}
        lookup=LookupSession(case)
        for record_id in case['records']:lookup.read(record_id)
        passed+=grade(case,key,answer,lookup.trace())['passed']
        unread_rejected+=not grade(case,key,answer,[])['passed']
    return {'origin':'host_constructed_legacy_examples','passed':passed,'unreadRejected':unread_rejected,
        'meaning':'Frozen historical scorer regression only; no legacy SDK execution or new inference.'}


def _summary(reports):
    return {'origin':'scripted_requirements_fixture','cells':len(reports),'passed':sum(r['passed'] for r in reports),
        'providerRequests':sum(r['usage']['providerRequests'] for r in reports),
        'reportedTokens':sum(r['usage']['reportedTokens'] for r in reports),'additionalProviderRequests':0,
        'strategies':{strategy:{'cells':sum(r['strategy']==strategy for r in reports),
            'passed':sum(r['strategy']==strategy and r['passed'] for r in reports),
            'providerRequests':sum(r['usage']['providerRequests'] for r in reports if r['strategy']==strategy)}
            for strategy in STRATEGIES},'legacy':legacy_examples(),
        'meaning':'24 scripted cells rehearse mechanics only. Quality/benefit requires a separately authorized blind repeated study.'}


def run_fixture(output):
    from .fixtures import run_fixture_sample
    output=Path(output);output.mkdir(mode=0o700,parents=False,exist_ok=False)
    reports=[];cells=[]
    for case_id in load_cases():
        for strategy in STRATEGIES:
            name=case_id+'--'+strategy
            report,_=run_fixture_sample(case_id,strategy,output/name)
            reports.append(report);cells.append({'directory':name,'lockSha256':hashlib.sha256((output/name/'sample-lock.json').read_bytes()).hexdigest()})
    summary=_summary(reports)
    with (output/'summary.json').open('xb') as handle:handle.write(encoded(summary))
    with (output/'matrix-lock.json').open('xb') as handle:
        handle.write(encoded({'cells':cells,'summarySha256':digest(summary)}))
    return summary


def replay(output):
    output=Path(output);lock=decode((output/'matrix-lock.json').read_text(),maximum=65536)
    expected={case+'--'+strategy for case in load_cases() for strategy in STRATEGIES}
    cells=lock['cells']
    if len(cells)!=24 or {cell['directory'] for cell in cells}!=expected:
        raise ValueError('matrix inventory mismatch')
    reports=[]
    for cell in cells:
        directory=output/cell['directory']
        if hashlib.sha256((directory/'sample-lock.json').read_bytes()).hexdigest()!=cell['lockSha256']:
            raise ValueError('sample lock changed')
        reports.append(read_sample(directory))
    summary=_summary(reports)
    if digest(summary)!=lock['summarySha256'] or decode((output/'summary.json').read_text(),maximum=65536)!=summary:
        raise ValueError('matrix summary mismatch')
    return summary
