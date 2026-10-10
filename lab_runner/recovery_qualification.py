"""Consistent owned logical restore measurements, never HA or PITR evidence."""
import json
import math
import os
import subprocess
import time
import uuid

import httpx
import psycopg
from psycopg.conninfo import conninfo_to_dict,make_conninfo

from .qualification import digest,number,receipt,validate_profile
from .stack import OwnedStack,command
from .manifest import validate_resource

def refresh_replica_endpoint(stack,name):
    identifier=stack.manifest['replica_ids'][name]
    state=json.loads(command(stack.engine,'inspect',identifier))[0]
    validate_resource(state,identifier,stack.owner)
    ports=state.get('NetworkSettings',{}).get('Ports',{}).get('8080/tcp')
    if (type(ports) is not list or len(ports)!=1 or type(ports[0]) is not dict or
        ports[0].get('HostIp')!='127.0.0.1' or type(ports[0].get('HostPort')) is not str or
        not ports[0]['HostPort'].isascii() or not ports[0]['HostPort'].isdigit() or
        not 1<=int(ports[0]['HostPort'])<=65535):
        raise ValueError('owned loopback replica endpoint required')
    endpoint='http://127.0.0.1:'+ports[0]['HostPort']
    stack.manifest['endpoints'][name]=endpoint
    stack._save()
    return endpoint

def evaluate(profile,evidence):
    profile=validate_profile(profile)
    if evidence.get('suite')!=profile['suite'] or evidence.get('profile_sha256')!=digest(profile):
        return receipt(profile,qualification='not_qualified',qualified=False,fixture_passed=False,
            reason='evidence_identity_mismatch')
    markers=evidence.get('acknowledged');restored=evidence.get('restored')
    valid=(type(markers) is list and 0<len(markers)<=10000 and type(restored) is list and
        0<len(restored)<=10000 and all(type(s) is int and 1<=s<=10000 for s in restored))
    if valid:
        valid=all(type(m) is dict and set(m)=={'sequence','time'} and
            number(m['sequence'],1,10000,integer=True) and number(m['time'],0,2**53)
            for m in markers)
    loss=evidence.get('loss_at');ready=evidence.get('ready_at')
    valid=valid and number(loss,0,2**53) and number(ready,0,2**53) and ready>=loss
    if not valid:return receipt(profile,qualification='not_qualified',qualified=False,fixture_passed=False,
        reason='missing_restore_evidence',observed_rpo_s=None,observed_rto_s=None)
    sequences=[m['sequence'] for m in markers]
    valid=(len(set(sequences))==len(sequences) and sequences==sorted(sequences) and
        sorted(restored)==sequences[:len(restored)] and len(set(restored))==len(restored) and
        all(markers[i]['time']<=markers[i+1]['time'] for i in range(len(markers)-1)))
    if not valid:return receipt(profile,qualification='not_qualified',qualified=False,fixture_passed=False,
        reason='inconsistent_restore_markers',observed_rpo_s=None,observed_rto_s=None)
    last=markers[-1]['time'];present=[m['time'] for m in markers if m['sequence'] in restored]
    rpo=last-max(present);rto=ready-loss
    fixture=(valid and evidence.get('calls_before')==evidence.get('calls_after') and
        number(evidence.get('calls_before'),0,10000,integer=True) and
        all(evidence.get(key) is True for key in ('owner_verified','revision_verified','receipt_verified','unknown_usage_verified')))
    qualified=fixture and rpo<=profile['maximum_rpo_s'] and rto<=profile['maximum_rto_s']
    return receipt(profile,qualified=qualified,qualification='qualified' if qualified else 'not_qualified',
        fixture_passed=fixture,observed_rpo_s=rpo,observed_rto_s=rto,
        acknowledged_markers=len(markers),missing_markers=len(set(sequences)-set(restored)),
        logical_restore_only=True,redispatch_detected=evidence.get('calls_before')!=evidence.get('calls_after'))

def run(stack,profile):
    profile=validate_profile(profile)
    if type(stack) is not OwnedStack:raise ValueError('verified OwnedStack required')
    stack.verify_owned()
    if profile['maximum_calls']<2 or profile['maximum_records']<2:raise ValueError('restore fixture requires two bounded calls/records')
    config=json.loads((stack.secrets/'host.json').read_text());config.update(stack.manifest['endpoints'])
    if len(config['principals'])<2:raise ValueError('owner isolation requires two principals')
    with psycopg.connect(config['migration_dsn'],connect_timeout=5,options='-c statement_timeout=5000') as connection:
        if connection.execute('SELECT count(*) FROM lab_app.runs').fetchone()[0]+2>profile['maximum_records']:
            raise ValueError('restore record allowance exhausted')
    token=next(iter(config['principals']));headers={'Authorization':'Bearer '+token}
    identifier=stack.manifest['database_id'];engine=stack.engine
    service=stack.secrets/'service.json';original=service.read_text();changed=False
    archived=stack.secrets/'qualification.dump'
    evidence={'suite':profile['suite'],'profile_sha256':digest(profile)};states=[]
    def count(client):
        response=client.get(config['model']+'/stats');response.raise_for_status();return response.json()['calls']
    with httpx.Client(timeout=15,follow_redirects=False) as client:
        client.post(config['model']+'/control',json={'maximum_calls':2}).raise_for_status()
        try:
            for scenario in ('normal','missing_usage'):
                client.post(config['model']+'/control',json={'scenario':scenario,'preserve_allowance':True}).raise_for_status()
                response=client.post(config['a']+'/runs',headers={**headers,'Idempotency-Key':uuid.uuid4().hex},
                    json={'workflow':'synthetic','task':'Neutral logical restore fixture'})
                response.raise_for_status();state=response.json()
                if state['status']!='waiting':raise ValueError('waiting receipt required')
                states.append(state)
            evidence['calls_before']=count(client)
            with psycopg.connect(config['migration_dsn'],connect_timeout=5,options='-c statement_timeout=5000') as connection:
                connection.execute('CREATE SCHEMA lab_qualification')
                connection.execute('CREATE TABLE lab_qualification.markers (sequence integer PRIMARY KEY, acknowledged_at double precision NOT NULL)')
                for sequence in (1,2):
                    connection.execute('INSERT INTO lab_qualification.markers VALUES (%s,%s)',(sequence,time.time()))
            # pg_dump creates one transactionally consistent database snapshot.
            exported=subprocess.run([engine,'exec',identifier,'pg_dump','-U','postgres','-Fc','lab'],
                capture_output=True,timeout=30)
            if exported.returncode or not exported.stdout or len(exported.stdout)>128*1024*1024:
                raise ValueError('bounded logical backup failed')
            descriptor=os.open(archived,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(descriptor,'wb') as output:output.write(exported.stdout)
            with psycopg.connect(config['migration_dsn'],connect_timeout=5,options='-c statement_timeout=5000') as connection:
                evidence['acknowledged']=[{'sequence':s,'time':t} for s,t in connection.execute(
                    'SELECT sequence,acknowledged_at FROM lab_qualification.markers ORDER BY sequence')]
            evidence['loss_at']=time.monotonic()
            # Simulated loss: stop only the exact owned replica; the original database remains forensic evidence.
            replica=stack.manifest['replica_ids']['b']
            command(engine,'stop','--time','10',replica)
            database='qualification_'+stack.owner
            command(engine,'exec',identifier,'createdb','-U','postgres','--owner=lab_migration',database)
            restored=subprocess.run([engine,'exec','-i',identifier,'pg_restore','-U','postgres',
                '--exit-on-error','-d',database],input=archived.read_bytes(),capture_output=True,timeout=30)
            if restored.returncode:raise ValueError('logical restore failed')
            replacement=json.loads(original)
            for key in ('harness_dsn','accounting_dsn','app_dsn'):
                parameters=conninfo_to_dict(replacement[key]);parameters['dbname']=database
                replacement[key]=make_conninfo(**parameters)
            service.write_text(json.dumps(replacement));changed=True
            command(engine,'start','-a',stack.manifest['runtime_config_job'])
            command(engine,'start',replica)
            config['b']=refresh_replica_endpoint(stack,'b')
            deadline=time.monotonic()+min(60,profile['maximum_rto_s']+1)
            while True:
                try:
                    if client.get(config['b']+'/readyz').status_code==200:break
                except httpx.HTTPError:pass
                if time.monotonic()>=deadline:raise ValueError('restored readiness timeout')
                time.sleep(.1)
            evidence['ready_at']=time.monotonic()
            parameters=conninfo_to_dict(config['migration_dsn']);parameters['dbname']=database
            with psycopg.connect(make_conninfo(**parameters),connect_timeout=5,options='-c statement_timeout=5000') as connection:
                evidence['restored']=[row[0] for row in connection.execute('SELECT sequence FROM lab_qualification.markers ORDER BY sequence')]
            evidence.update(owner_verified=True,revision_verified=True,receipt_verified=True)
            other=list(config['principals'])[1]
            for state in states:
                path='/runs/'+state['run_id']
                view=client.get(config['b']+path,headers=headers);view.raise_for_status();view=view.json()
                evidence['revision_verified'] &= view['revision']==state['revision']
                evidence['receipt_verified'] &= (view['status']=='waiting' and view['run_id']==state['run_id'] and
                    view.get('review')==state.get('review') and view.get('choices')==state.get('choices') and
                    view.get('current_step')==state.get('current_step'))
                for suffix in ('','/usage'):
                    evidence['owner_verified'] &= client.get(config['b']+path+suffix,
                        headers={'Authorization':'Bearer '+other}).status_code==404
            usage=client.get(config['b']+'/runs/'+states[1]['run_id']+'/usage',headers=headers)
            usage.raise_for_status();usage=usage.json()
            evidence['unknown_usage_verified']=usage['unresolved_calls']==1 and usage['fully_costed'] is False
            evidence['calls_after']=count(client)
            return evaluate(profile,evidence)
        finally:
            client.post(config['model']+'/control',json={'preserve_allowance':True}).raise_for_status()
            if changed:
                service.write_text(original)
                command(engine,'start','-a',stack.manifest['runtime_config_job'])
                command(engine,'stop','--time','10',stack.manifest['replica_ids']['b'])
                command(engine,'start',stack.manifest['replica_ids']['b'])
                config['b']=refresh_replica_endpoint(stack,'b')
