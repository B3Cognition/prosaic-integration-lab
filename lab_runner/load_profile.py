"""Finite open-loop arrivals with no client queue or mutation retries."""
from concurrent.futures import ThreadPoolExecutor
import math
import time
import uuid
from decimal import Decimal
import httpx
from prosaic_runtime_postgres import PostgresRecorder

def validate(duration,rate,concurrency,p95_target,max_rejection):
    if (not all(type(value) in {int,float} and math.isfinite(value) for value in (duration,rate,p95_target,max_rejection)) or
        not 0<duration<=300 or not 0<rate<=100 or math.ceil(duration*rate)>10000 or
        type(concurrency) is not int or not 1<=concurrency<=64 or not 0<p95_target<=30 or not 0<=max_rejection<=1):
        raise ValueError('profile exceeds bounded qualification policy')

def qualify(*,offered,completed,rejected,shed,errors,latencies,observed,ledger_calls,unknown,duration,rate,p95_target,max_rejection,accepted=None):
    ordered=sorted(latencies)
    p95=ordered[max(0,math.ceil(.95*len(ordered))-1)] if ordered else None
    rejection_rate=(rejected+shed)/offered if offered else 1
    throughput=completed/duration
    reconciled=observed==ledger_calls==(completed if accepted is None else accepted) and unknown==0
    return {'p95_seconds':round(p95,4) if p95 is not None else None,'rejection_rate':round(rejection_rate,4),
        'completed_per_second':round(throughput,4),'accounting_reconciled':reconciled,
        'correctness_passed':errors==0 and reconciled,
        'slo_passed':errors==0 and reconciled and p95 is not None and p95<=p95_target and rejection_rate<=max_rejection and throughput>=rate*.9}

def capacity_response(response):
    return response.status_code==503 and response.json().get('detail') in {
        'capacity_exhausted','http_capacity_exhausted','retention_capacity_exhausted'}

def run(config,users,duration,rate,concurrency,events,*,p95_target=2,max_rejection=.05,allow_overload=False,qualification_profile=None):
    if qualification_profile is not None:
        return run_qualification(config,qualification_profile,events)
    validate(duration,rate,concurrency,p95_target,max_rejection)
    principals=list(config['principals'].items())[:users]
    if len(principals)!=users: raise ValueError('insufficient trusted identities')
    recorder=PostgresRecorder(config['accounting_dsn'],namespace=config['namespace'],environment=config['environment'])
    previous=recorder.report(application_id='integration-lab')
    with httpx.Client(timeout=10) as client: before=client.get(config['model']+'/stats').json()['calls']
    per_user={principal['actor_id']:{'offered':0,'completed':0,'rejected':0,'client_shed':0} for _,principal in principals}

    def one(index):
        token,principal=principals[index%users]; actor=principal['actor_id']; a,b=('a','b') if index%2==0 else ('b','a')
        began=time.monotonic(); accepted=completed=rejected=errors=0; latency=None
        headers={'Authorization':'Bearer '+token}
        try:
            with httpx.Client(timeout=15) as client:
                response=client.post(config[a]+'/runs',headers={**headers,'Idempotency-Key':uuid.uuid4().hex},
                    json={'workflow':'synthetic','task':'Neutral arrival-rate qualification fixture'})
                events.emit('requests',actor=actor,operation='profile_start',replica=a,status=response.status_code)
                if capacity_response(response):
                    return {'actor':actor,'accepted':0,'completed':0,'rejected':1,'errors':0,'latency':None}
                response.raise_for_status(); state=response.json(); accepted=1
                if state['status']!='waiting': raise ValueError('unexpected workflow state')
                path='/runs/'+state['run_id']
                approved=client.post(config[b]+path+'/resume',headers=headers,
                    json={'choice':'approve','expected_revision':state['revision']})
                if capacity_response(approved): rejected=1
                else:
                    approved.raise_for_status()
                    if approved.json()['status']!='completed': raise ValueError('approval did not complete')
                    completed=1; latency=time.monotonic()-began
                usage=client.get(config[b]+path+'/usage',headers=headers); usage.raise_for_status(); usage=usage.json()
                if (usage['total_calls']!=1 or usage['complete_calls']!=1 or usage['unresolved_calls']!=0 or usage['billing_eligible'] or
                    Decimal(usage['estimated_amounts'].get('USD','-1'))!=Decimal('0.00037')):
                    raise ValueError('accounting coverage mismatch')
                if users>1:
                    other=principals[(index+1)%users][0]
                    for suffix in ('','/usage'):
                        if client.get(config[a]+path+suffix,headers={'Authorization':'Bearer '+other}).status_code!=404:
                            raise ValueError('owner isolation failed')
                events.emit('accounting',actor=actor,run_id=state['run_id'],scope='profile_run',
                    calls=usage['total_calls'],complete=usage['complete_calls'],unknown=usage['unresolved_calls'],
                    usd=usage['estimated_amounts'].get('USD'),billing_eligible=usage['billing_eligible'])
        except Exception:
            errors=1
            events.emit('requests',actor=actor,operation='profile_error',error='request_failed')
        return {'actor':actor,'accepted':accepted,'completed':completed,'rejected':rejected,'errors':errors,'latency':latency}

    outcomes=[]; pending=set(); offered=shed=0; began=time.monotonic(); deadline=began+duration; next_arrival=began
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        while time.monotonic()<deadline:
            finished={future for future in pending if future.done()}
            outcomes.extend(future.result() for future in finished); pending-=finished
            now=time.monotonic()
            if offered>=math.ceil(duration*rate):
                time.sleep(min(deadline-now,.05)); continue
            if now<next_arrival:
                time.sleep(min(next_arrival-now,.05)); continue
            actor=principals[offered%users][1]['actor_id']; per_user[actor]['offered']+=1
            if len(pending)<concurrency: pending.add(pool.submit(one,offered))
            else:
                shed+=1; per_user[actor]['client_shed']+=1
                events.emit('requests',actor=actor,operation='client_shed',pending=len(pending))
            offered+=1; next_arrival+=1/rate
        outcomes.extend(future.result() for future in pending)
    elapsed=time.monotonic()-began
    for item in outcomes:
        for field in ('completed','rejected'): per_user[item['actor']][field]+=item[field]
    totals={field:sum(item[field] for item in outcomes) for field in ('accepted','completed','rejected','errors')}
    report=recorder.report(application_id='integration-lab')
    with httpx.Client(timeout=10) as client: observed=client.get(config['model']+'/stats').json()['calls']-before
    result=qualify(offered=offered,completed=totals['completed'],rejected=totals['rejected'],shed=shed,errors=totals['errors'],
        latencies=[item['latency'] for item in outcomes if item['latency'] is not None],observed=observed,
        ledger_calls=report['total_calls']-previous['total_calls'],unknown=max(0,report['unresolved_calls']-previous['unresolved_calls']),
        duration=elapsed,rate=rate,p95_target=p95_target,max_rejection=max_rejection,accepted=totals['accepted'])
    result.update(totals,offered=offered,client_shed=shed,users=users,concurrency=concurrency,duration_seconds=round(elapsed,3),
        target_arrivals_per_second=rate,p95_target_seconds=p95_target,max_rejection_rate=max_rejection,
        independent_model_calls=observed,per_user=per_user,billing_eligible=False,
        preexisting_unknown_calls=previous['unresolved_calls'])
    result['passed']=result['correctness_passed'] and (allow_overload or result['slo_passed'])
    events.emit('accounting',scope='profile_delta',calls=report['total_calls']-previous['total_calls'],
        unknown=max(0,report['unresolved_calls']-previous['unresolved_calls']),billing_eligible=False)
    return result

def run_qualification(config,profile,events):
    """Fixed arrivals with bounded admission reservations, concurrent owner reads."""
    import hashlib
    import json
    import psycopg
    from .qualification import validate_profile,digest
    profile=validate_profile(profile)
    principals=list(config['principals'].items())[:profile['users']]
    if len(principals)!=profile['users']:raise ValueError('insufficient trusted identities')
    def identity(principal):
        return json.dumps([principal['tenant_id'],principal['actor_id']],separators=(',',':'))
    # Identity includes tenant even if different tenants use the same actor name.
    actors={identity(p):{'offered':0,'completed':0} for _,p in principals}
    def growth():
        with psycopg.connect(config['migration_dsn'],connect_timeout=5,
                options='-c statement_timeout=5000') as connection:
            rows=connection.execute('SELECT count(*) FROM lab_app.runs').fetchone()[0]
            size=connection.execute('SELECT pg_database_size(current_database())').fetchone()[0]
            return rows,size
    rows_before,bytes_before=growth()
    recorder=PostgresRecorder(config['accounting_dsn'],namespace=config['namespace'],environment=config['environment'])
    previous=recorder.report(application_id='integration-lab')
    def stats(client):
        response=client.get(config['model']+'/stats');response.raise_for_status();return response.json()
    with httpx.Client(timeout=10,follow_redirects=False) as client:
        before=stats(client)['calls']
        client.post(config['model']+'/control',json={'maximum_calls':profile['maximum_calls'],
            'provider_latency_s':profile['provider_latency_s']}).raise_for_status()
    read_samples=read_failures=0
    def one(index):
        token,principal=principals[index%len(principals)];actor=identity(principal)
        headers={'Authorization':'Bearer '+token};a,b=('a','b') if index%2==0 else ('b','a')
        item=dict(actor=actor,accepted=0,completed=0,rejected=0,approval_deferred=0,errors=0,
            latency=None,read_samples=0,read_failures=0,tool_samples=0,completed_at=None,tool_latency=None)
        began=time.monotonic()
        try:
            with httpx.Client(timeout=15,follow_redirects=False) as client:
                response=client.post(config[a]+'/runs',headers={**headers,'Idempotency-Key':uuid.uuid4().hex},
                    json={'workflow':'synthetic','task':'Neutral bounded operational fixture'})
                if capacity_response(response):item['rejected']=1;return item
                response.raise_for_status();state=response.json();item['accepted']=1
                if state['status']!='waiting':raise ValueError('unexpected state')
                path='/runs/'+state['run_id']
                # Read in parallel with the resume worker, no mutation retry queue.
                with ThreadPoolExecutor(max_workers=1) as reader:
                    future=reader.submit(client.get,config[a]+path,headers=headers)
                    operation=client.post(config['model']+'/operation',json={'latency_s':profile['tool_latency_s']})
                    operation.raise_for_status();item['tool_samples']=1;item['tool_latency']=operation.json()['seconds']
                    approval=client.post(config[b]+path+'/resume',headers=headers,
                        json={'choice':'approve','expected_revision':state['revision']})
                    read=future.result();item['read_samples']=1
                    if read.status_code!=200:item['read_failures']=1
                if capacity_response(approval):item['approval_deferred']=1
                else:
                    approval.raise_for_status()
                    if approval.json()['status']!='completed':raise ValueError('unexpected completion')
                    item['completed']=1;item['latency']=time.monotonic()-began;item['completed_at']=time.monotonic()
                usage=client.get(config[b]+path+'/usage',headers=headers);usage.raise_for_status()
                usage=usage.json()
                if (usage['total_calls']!=1 or usage['complete_calls']!=1 or usage['unresolved_calls']!=0 or
                    not usage['fully_costed'] or usage['billing_eligible']):
                    raise ValueError('accounting mismatch')
                if len(principals)>1:
                    other=principals[(index+1)%len(principals)][0]
                    for suffix in ('','/usage'):
                        if client.get(config[a]+path+suffix,headers={'Authorization':'Bearer '+other}).status_code!=404:
                            raise ValueError('owner isolation failed')
        except Exception:item['errors']=1
        return item
    outcomes=[];pending=set();offered=shed=submitted=0;began=time.monotonic()
    deadline=began+profile['duration_s'];next_arrival=began;stop='duration';window_offers={}
    try:
        with ThreadPoolExecutor(max_workers=profile['concurrency']) as pool:
            while time.monotonic()<deadline:
                done={f for f in pending if f.done()};outcomes.extend(f.result() for f in done);pending-=done
                now=time.monotonic()
                # Reserve one call and one application row before scheduling each start.
                if submitted>=profile['maximum_calls']:stop='calls';break
                if rows_before+submitted>=profile['maximum_records']:stop='records';break
                if offered>=math.ceil(profile['duration_s']*profile['arrivals_per_second']):
                    time.sleep(min(.05,max(0,deadline-now)));continue
                if now<next_arrival:time.sleep(min(.05,next_arrival-now));continue
                actor=identity(principals[offered%len(principals)][1]);actors[actor]['offered']+=1
                window=int((now-began)//profile['window_s'])
                window_offers.setdefault(window,set()).add(actor)
                if len(pending)<profile['concurrency']:
                    pending.add(pool.submit(one,offered));submitted+=1
                else:shed+=1
                offered+=1;next_arrival+=1/profile['arrivals_per_second']
            outcomes.extend(f.result() for f in pending)
        rows_after,bytes_after=growth()
        report=recorder.report(application_id='integration-lab')
        with httpx.Client(timeout=10,follow_redirects=False) as client:after=stats(client)
    finally:
        # Restore fixture timing/scenario even when accounting/HTTP work fails.
        with httpx.Client(timeout=10,follow_redirects=False) as client:
            client.post(config['model']+'/control',json={'preserve_allowance':True}).raise_for_status()
    for item in outcomes:actors[item['actor']]['completed']+=item['completed']
    totals={field:sum(item[field] for item in outcomes) for field in
        ('accepted','completed','rejected','approval_deferred','errors','read_samples','read_failures','tool_samples')}
    # Only fully observed windows count; a completion outside its offered window does not hide starvation.
    elapsed=time.monotonic()-began
    full_windows=[w for w in window_offers if (w+1)*profile['window_s']<=elapsed]
    starved=sum(1 for w in full_windows for actor in window_offers[w] if not any(
        item['actor']==actor and item['completed_at'] is not None and
        w*profile['window_s']<=item['completed_at']-began<(w+1)*profile['window_s'] for item in outcomes))
    result=dict(totals,offered=offered,client_shed=shed,
        latencies_s=[i['latency'] for i in outcomes if i['latency'] is not None],tenant_counts=actors,
        starved_windows=starved,window_samples=len(full_windows),
        independent_model_calls=after['calls']-before,ledger_calls=report['total_calls']-previous['total_calls'],
        unknown_usage=max(0,report['unresolved_calls']-previous['unresolved_calls']),
        records_before=rows_before,records_after=rows_after,bytes_before=bytes_before,bytes_after=bytes_after,
        allowance_rejected=after['allowance_rejected'],stop_bound=stop)
    result['tool_latencies_s']=[i['tool_latency'] for i in outcomes if i['tool_latency'] is not None]
    result.update(suite=profile['suite'],profile_sha256=digest(profile),elapsed_s=elapsed)
    return result
