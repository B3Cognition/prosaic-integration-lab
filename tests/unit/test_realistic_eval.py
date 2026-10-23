import json
import pytest


def test_realistic_budget_does_not_relax_legacy_pilots(tmp_path):
    from lab_runner.live_allowance import SharedLiveAllowance
    with pytest.raises(ValueError):
        SharedLiveAllowance(tmp_path/'old.json',max_calls=90)
    allowance=SharedLiveAllowance(tmp_path/'new.json',max_calls=90,ceiling=90)
    token=allowance.reserve(maximum_requests=8)
    allowance.finish(token,actual_requests=None)
    assert allowance.status()['retained']==8
    assert SharedLiveAllowance(tmp_path/'new.json',max_calls=90,ceiling=90).status()['remaining']==82


def test_sql_repair_is_graded_by_behavior_and_rejects_writes(tmp_path):
    from lab_runner.native_eval.realistic_cases import prepare,grade
    prepare('invoice-sql',tmp_path)
    good='''WITH paid AS (SELECT invoice_id,SUM(amount_cents) amount FROM payments GROUP BY invoice_id),
    overdue AS (SELECT i.customer_id,MAX(0,i.total_cents-COALESCE(p.amount,0)) balance
    FROM invoices i LEFT JOIN paid p ON p.invoice_id=i.id
    WHERE i.status='OPEN' AND i.due_date<'2026-10-23')
    SELECT customer_id,COUNT(*) overdue_count,SUM(balance) outstanding_cents
    FROM overdue WHERE balance>0 GROUP BY customer_id ORDER BY customer_id;'''
    (tmp_path/'report.sql').write_text(good)
    assert grade('invoice-sql',tmp_path)['passed']
    (tmp_path/'report.sql').write_text(good.replace("<'2026-10-23'","<='2026-10-23'"))
    assert not grade('invoice-sql',tmp_path)['passed']
    (tmp_path/'report.sql').write_text('DELETE FROM invoices')
    assert not grade('invoice-sql',tmp_path)['passed']


@pytest.mark.parametrize('evidence,accepted',[
    ('migration-current',True),
    ('migration-current: FAIL for the current candidate.',True),
    (['migration-current'],True),
    (['migration-current: failed','Current check: migration-current'],True),
    ('migration-current-stale',False),
    ('other-migration-current',False),
    ('review-previous',False),
    ([],False),
    (['migration-current','review-previous'],False),
    ([['migration-current']],False),
    (None,False),
    ({'id':'migration-current'},False),
])
def test_release_blocker_citations_follow_written_contract(evidence,accepted,tmp_path):
    from lab_runner.native_eval.realistic_cases import prepare,grade
    prepare('release-brief',tmp_path)
    response={'candidate':'2.8.0','decision':'HOLD',
      'summary':'The current candidate must remain on hold because its migration check failed. The passing unit check does not satisfy the separate migration requirement. The previous approval refers to an older candidate and cannot authorize this release. Platform must correct and rerun migration validation before this candidate can be reconsidered.',
      'blockers':[{'check':'migration','evidence':evidence}],
      'excludedEvidence':['review-previous'],'actions':[{'owner':'platform','action':'Fix and rerun the migration check','evidence':['migration-current']}]}
    (tmp_path/'brief.json').write_text(json.dumps(response))
    assert grade('release-brief',tmp_path)['passed'] is accepted


def test_release_brief_rejects_stale_approval_and_fabricated_evidence(tmp_path):
    from lab_runner.native_eval.realistic_cases import prepare,grade
    prepare('release-brief',tmp_path)
    response={'candidate':'2.8.0','decision':'HOLD',
      'summary':'The current candidate must remain on hold because its migration check failed. The passing unit check does not satisfy the separate migration requirement. The previous approval refers to an older candidate and cannot authorize this release. Platform must correct and rerun migration validation before this candidate can be reconsidered.',
      'blockers':[{'check':'migration','evidence':'migration-current'}],
      'excludedEvidence':['review-previous'],'actions':[{'owner':'platform','action':'Fix and rerun the migration check','evidence':['migration-current']}]}
    (tmp_path/'brief.json').write_text(json.dumps(response))
    assert grade('release-brief',tmp_path)['passed']
    response['decision']='APPROVE'
    (tmp_path/'brief.json').write_text(json.dumps(response))
    assert not grade('release-brief',tmp_path)['passed']
    response['decision']='HOLD';response['actions'][0]['evidence']=['imaginary-receipt']
    (tmp_path/'brief.json').write_text(json.dumps(response))
    assert not grade('release-brief',tmp_path)['passed']


def test_incident_handoff_preserves_uncertainty_and_metrics(tmp_path):
    from lab_runner.native_eval.realistic_cases import prepare,grade
    prepare('incident-handoff',tmp_path)
    response={'status':'MITIGATED','rootCause':'UNCONFIRMED',
      'impact':{'failedRequests':216,'totalRequests':1200,'windowMinutes':16},
      'summary':'The incident is mitigated following rollback, with request errors back at baseline. The affected window lasted sixteen minutes and included two hundred sixteen failures. Deployment timing is correlated with the incident, but a root cause has not been confirmed. Platform should investigate while support follows up with affected customers.',
      'evidence':['timeline','metrics'],'actions':[{'owner':'platform','action':'Investigate root cause'},{'owner':'support','action':'Notify affected customers'}]}
    (tmp_path/'handoff.json').write_text(json.dumps(response))
    assert grade('incident-handoff',tmp_path)['passed']
    response['rootCause']='DEPLOYMENT'
    (tmp_path/'handoff.json').write_text(json.dumps(response))
    assert not grade('incident-handoff',tmp_path)['passed']


@pytest.mark.parametrize('mutation',['source','extra','symlink'])
def test_realistic_workspace_integrity(mutation,tmp_path):
    from lab_runner.native_eval.realistic_cases import prepare,grade
    prepare('invoice-sql',tmp_path)
    if mutation=='source':(tmp_path/'packet.json').write_text('{}')
    elif mutation=='extra':(tmp_path/'extra.txt').write_text('not authorized')
    else:
        (tmp_path/'report.sql').unlink();(tmp_path/'report.sql').symlink_to(tmp_path/'packet.json')
    result=grade('invoice-sql',tmp_path)
    assert not result['checks']['workspaceIntegrity']
    assert not result['passed']


def test_realistic_summary_separates_failure_latency_from_success_latency():
    from lab_runner.native_eval.realistic import summary
    rows=[{'selector':'local','case':'a','passed':True,'completed':True,'durationMs':1000},
          {'selector':'local','case':'a','passed':False,'completed':False,'durationMs':180000}]
    r=summary(rows)['byBackend'][0]
    assert r['successRate']==.5 and r['completionRate']==.5
    assert r['successfulLatencyMs']=={'median':1000,'min':1000,'max':1000}
    assert r['allLatencyMs']=={'median':90500,'min':1000,'max':180000}


def test_realistic_plan_is_bounded_and_live_requires_opt_in(tmp_path):
    from lab_runner.native_eval.realistic import plan,run_realistic
    assert plan(3)=={'assignments':27,'maximumDispatchUnits':90,'maximumNativeAttempts':18,'maximumLocalRequests':72}
    for value in (True,0,4):
        with pytest.raises(ValueError):plan(value)
    with pytest.raises(ValueError,match='opt-in'):
        run_realistic(native_config=None,local_config=None,selectors=[],output=tmp_path/'run',provenance={})
    assert not (tmp_path/'run').exists()


def test_sql_overpayments_cannot_offset_other_positive_invoices(tmp_path):
    from lab_runner.native_eval.realistic_cases import prepare,grade
    prepare('invoice-sql',tmp_path)
    wrong='''WITH paid AS (SELECT invoice_id,SUM(amount_cents) amount FROM payments GROUP BY invoice_id),
    balances AS (SELECT i.customer_id,i.total_cents-COALESCE(p.amount,0) balance
    FROM invoices i LEFT JOIN paid p ON p.invoice_id=i.id
    WHERE i.status='OPEN' AND i.due_date<'2026-10-23')
    SELECT customer_id,SUM(CASE WHEN balance>0 THEN 1 ELSE 0 END) overdue_count,
    MAX(SUM(balance),0) outstanding_cents FROM balances GROUP BY customer_id
    HAVING SUM(balance)>0 ORDER BY customer_id;'''
    (tmp_path/'report.sql').write_text(wrong)
    assert not grade('invoice-sql',tmp_path)['passed']


def test_local_readiness_does_not_redirect_bearer_credentials(tmp_path):
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    import threading
    import urllib.error
    from prosaic_runtime import EndpointConfig
    from lab_runner.native_eval.realistic import check_local_readiness
    received=[]
    class Target(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            received.append(self.headers.get('Authorization'))
            body=b'{"data":[{"id":"synthetic"}]}'
            self.send_response(200);self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body)
    target=ThreadingHTTPServer(('127.0.0.1',0),Target)
    class Redirect(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            self.send_response(302)
            self.send_header('Location',f'http://127.0.0.1:{target.server_port}/models')
            self.end_headers()
    redirect=ThreadingHTTPServer(('127.0.0.1',0),Redirect)
    threads=[threading.Thread(target=s.serve_forever,daemon=True) for s in (target,redirect)]
    for thread in threads:thread.start()
    key=tmp_path/'key';key.write_text('synthetic-test-token');key.chmod(0o600)
    try:
        with pytest.raises(urllib.error.HTTPError):
            check_local_readiness(EndpointConfig(f'http://127.0.0.1:{redirect.server_port}/v1',
                                  'synthetic',api_key_file=str(key)))
        assert received==[]
    finally:
        for server in (redirect,target):server.shutdown();server.server_close()
        for thread in threads:thread.join(timeout=5)
