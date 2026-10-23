"""Synthetic operational tasks; grade factual contracts, not prose elegance."""
import json
from contextlib import closing
from pathlib import Path
import re
import sqlite3
import stat

from .cases import SOURCE, _json

CASE_IDS=('release-brief','incident-handoff','invoice-sql')
OUTPUTS={'release-brief':'brief.json','incident-handoff':'handoff.json','invoice-sql':'report.sql'}
PACKETS={
 'release-brief':{
  'candidate':{'version':'2.8.0','commit':'c42','fingerprint':'h42'},
  'policy':{'requiredChecks':['unit','migration'],'decision':'Approve only when all required checks pass for the current commit and fingerprint.'},
  'checks':[{'id':'unit-current','check':'unit','status':'PASS','commit':'c42','fingerprint':'h42','owner':'application'},
            {'id':'migration-current','check':'migration','status':'FAIL','commit':'c42','fingerprint':'h42','owner':'platform','detail':'A rollback migration dropped the customer index.'}],
  'reviews':[{'id':'review-previous','decision':'APPROVE','commit':'c41','fingerprint':'h41','note':'Previous candidate passed all checks.'}],
  'context':'The deployment window opens tomorrow. The window does not waive validation. Platform owns migration repair and revalidation; no delivery date has been committed.'},
 'incident-handoff':{
  'timeline':{'id':'timeline','events':[{'time':'09:00','event':'Deployment started'}, {'time':'09:06','event':'Errors elevated'}, {'time':'09:15','event':'Rollback completed'}, {'time':'09:22','event':'Errors returned to baseline'}]},
  'metrics':{'id':'metrics','failedRequests':216,'totalRequests':1200,'peakErrorPercent':18,'sampling':'Aggregate request counts cover the affected interval.'},
  'investigation':{'rootCauseConfirmed':False,'note':'The deployment is temporally correlated. No causal mechanism has been confirmed. Customer impact is mitigated after rollback.'},
  'followUps':[{'owner':'platform','assignment':'Investigate the causal mechanism and verify mitigation stability.'}, {'owner':'support','assignment':'Notify affected customers using the verified impact counts.'}]},
 'invoice-sql':{
  'asOf':'2026-10-23',
  'schema':{'customers':'id INTEGER PRIMARY KEY, name TEXT', 'invoices':'id INTEGER PRIMARY KEY, customer_id INTEGER, status TEXT, due_date TEXT, total_cents INTEGER', 'payments':'invoice_id INTEGER, amount_cents INTEGER'},
  'rules':['Dates are ISO YYYY-MM-DD strings.','Only OPEN invoices due strictly before asOf are eligible.','Subtract the sum of every payment for each invoice. No payments means zero paid.','Clamp each invoice balance at zero before customer aggregation.','Exclude invoices with no positive balance; count invoices, not payment rows.','Return customer_id, overdue_count, outstanding_cents ordered by customer_id.'],
  'examples':['An OPEN 10000-cent invoice due yesterday with payments 2000 and 3000 contributes one invoice and 5000 cents.','An OPEN invoice due exactly on asOf is not overdue.','A fully paid or overpaid invoice contributes nothing.','A VOID invoice contributes nothing even when old.']}}
DRAFTS={'release-brief':json.dumps({'candidate':'2.8.0','decision':'APPROVE','summary':'The previous reviewer approved this release. Ship in the next window.'}),
 'incident-handoff':json.dumps({'status':'RESOLVED','rootCause':'CONFIRMED','impact':{'failedRequests':18},'summary':'Deployment caused the incident. Rollback permanently fixed it.'}),
 'invoice-sql':"SELECT i.customer_id,COUNT(*) overdue_count,SUM(i.total_cents-COALESCE(p.amount_cents,0)) outstanding_cents FROM invoices i LEFT JOIN payments p ON p.invoice_id=i.id WHERE i.status='OPEN' AND i.due_date<='2026-10-23' GROUP BY i.customer_id ORDER BY i.customer_id;\n"}


def seed(case):
    if case not in CASE_IDS:raise ValueError('unknown realistic case')
    return {'packet.json':json.dumps(PACKETS[case],sort_keys=True,indent=2)+'\n',OUTPUTS[case]:DRAFTS[case]}


def prepare(case,workspace):
    from prosaic import parse_artifact
    from prosaic_runtime import ProsaicArtifact
    for name,body in seed(case).items():(Path(workspace)/name).write_text(body)
    identifier=f'subagents/{case}.md'
    return ProsaicArtifact.from_inspection({'id':identifier,'type':'subagent',
       **parse_artifact((SOURCE/identifier).read_text())})


def _summary(value):
    return isinstance(value,str) and 40<=len(value.split())<=100


def _action(row,keys):
    return (type(row) is dict and set(row)==keys and isinstance(row.get('action'),str)
            and 5<=len(row['action'])<=300)


def _migration_blocker(value):
    if type(value) is not list or len(value)!=1:return False
    blocker=value[0]
    if type(blocker) is not dict or set(blocker)!={'check','evidence'} or blocker['check']!='migration':return False
    evidence=blocker['evidence']
    citations=[evidence] if isinstance(evidence,str) else evidence
    return (type(citations) is list and bool(citations)
            and all(isinstance(c,str) and re.search(r'(?<![\w-])migration-current(?![\w-])',c)
                    for c in citations))


def _sql(query):
    fixtures=[(
      [(1,1,'OPEN','2026-10-20',10000),(2,1,'OPEN','2026-10-21',4000),(3,2,'OPEN','2026-10-23',9000),(4,2,'VOID','2026-10-01',9000),(5,2,'OPEN','2026-10-01',5000),(6,1,'OPEN','2026-10-01',1000)],
      [(1,2000),(1,3000),(2,4000),(5,6000),(6,2000)],[(1,1,5000)]),
      ([(10,2,'OPEN','2026-10-22',3000),(11,2,'OPEN','2026-10-01',2000),(12,3,'OPEN','2026-10-24',5000),(13,3,'PAID','2026-10-01',7000)],
       [(11,500),(11,200)],[(2,2,4300)]),
      ([(21,1,'OPEN','2026-10-23',1),(22,3,'OPEN','2026-10-22',100)],[(22,100)],[])]
    for invoices,payments,expected in fixtures:
        with closing(sqlite3.connect(':memory:')) as db:
            db.executescript('CREATE TABLE customers(id INTEGER PRIMARY KEY,name TEXT); CREATE TABLE invoices(id INTEGER PRIMARY KEY,customer_id INTEGER,status TEXT,due_date TEXT,total_cents INTEGER); CREATE TABLE payments(invoice_id INTEGER,amount_cents INTEGER);')
            db.executemany('INSERT INTO customers VALUES(?,?)',[(1,'A'),(2,'B'),(3,'C')])
            db.executemany('INSERT INTO invoices VALUES(?,?,?,?,?)',invoices)
            db.executemany('INSERT INTO payments VALUES(?,?)',payments)
            db.commit()
            def authorize(op,a,b,*unused):
                if op in (sqlite3.SQLITE_SELECT,sqlite3.SQLITE_READ):return sqlite3.SQLITE_OK
                if op==sqlite3.SQLITE_FUNCTION and b.lower() in {'sum','count','coalesce','max','min','ifnull','nullif','date'}:return sqlite3.SQLITE_OK
                return sqlite3.SQLITE_DENY
            db.set_authorizer(authorize)
            db.set_progress_handler(lambda:1,20000)
            cursor=db.execute(query)
            if [x[0] for x in cursor.description]!=['customer_id','overdue_count','outstanding_cents']:return False
            if cursor.fetchmany(20)!=expected:return False
    return True


def grade(case,workspace):
    checks={'workspaceIntegrity':False,'factualContract':False}
    try:
        root=Path(workspace);files=seed(case)
        if {p.name for p in root.iterdir()}!=set(files):return {'passed':False,'checks':checks}
        for name in files:
            p=root/name
            if p.is_symlink() or not stat.S_ISREG(p.stat().st_mode) or p.stat().st_size>32768:return {'passed':False,'checks':checks}
        if (root/'packet.json').read_bytes()!=files['packet.json'].encode():return {'passed':False,'checks':checks}
        checks['workspaceIntegrity']=True
        text=(root/OUTPUTS[case]).read_text()
        if case=='invoice-sql':checks['factualContract']=_sql(text)
        else:
            r=_json(text)
            if type(r) is not dict or not _summary(r.get('summary')):return {'passed':False,'checks':checks}
            if case=='release-brief':
                keys={'candidate','decision','summary','blockers','excludedEvidence','actions'}
                actions=r.get('actions')
                checks['factualContract']=(set(r)==keys and r['candidate']=='2.8.0' and r['decision']=='HOLD'
                  and _migration_blocker(r['blockers'])
                  and r['excludedEvidence']==['review-previous'] and type(actions) is list and len(actions)==1
                  and _action(actions[0],{'owner','action','evidence'}) and actions[0]['owner']=='platform'
                  and actions[0]['evidence']==['migration-current'])
            else:
                impact=r.get('impact');actions=r.get('actions')
                checks['factualContract']=(set(r)=={'status','rootCause','impact','summary','evidence','actions'}
                  and r['status']=='MITIGATED' and r['rootCause']=='UNCONFIRMED'
                  and impact=={'failedRequests':216,'totalRequests':1200,'windowMinutes':16}
                  and all(type(v) is int for v in impact.values())
                  and type(r['evidence']) is list and sorted(r['evidence'])==['metrics','timeline']
                  and type(actions) is list and len(actions)==2
                  and all(_action(a,{'owner','action'}) for a in actions)
                  and sorted(a['owner'] for a in actions)==['platform','support'])
    except (OSError,ValueError,TypeError,KeyError,AttributeError,sqlite3.Error,RecursionError):pass
    return {'passed':all(checks.values()),'checks':checks}
