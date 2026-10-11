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

NATIVE_CHECKS=('native_verified','proposal_verified','reference_verified','bundle_verified',
    'reservation_verified','snapshot_verified','receipt_document_verified','interaction_verified',
    'native_usage_verified','journal_verified','domain_verified','completed_claim_verified',
    'uncertain_claim_verified')

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

def evaluate(profile,evidence,*,native_mode=False):
    profile=validate_profile(profile)
    if type(native_mode) is not bool:raise ValueError('trusted restore mode must be boolean')
    if evidence.get('suite')!=profile['suite'] or evidence.get('profile_sha256')!=digest(profile):
        return receipt(profile,qualification='not_qualified',qualified=False,fixture_passed=False,
            reason='evidence_identity_mismatch')
    native_fields={'native_mode','native_runs','native_proposals','handlers_before','handlers_after',*NATIVE_CHECKS}
    if (native_mode and evidence.get('native_mode') is not True or
        not native_mode and any(key in evidence for key in native_fields)):
        return receipt(profile,qualification='not_qualified',qualified=False,fixture_passed=False,
            reason='restore_mode_mismatch',logical_restore_only=True)
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
    native=native_mode
    native_fields={}
    if native:
        handlers=(number(evidence.get('handlers_before'),0,10000,integer=True) and
            number(evidence.get('handlers_after'),0,10000,integer=True) and
            evidence.get('handlers_before')==evidence.get('handlers_after'))
        populated=(type(evidence.get('native_runs')) is int and evidence['native_runs']==4 and
            type(evidence.get('native_proposals')) is int and evidence['native_proposals']==3)
        verified=(all(evidence.get(key) is True for key in NATIVE_CHECKS) and handlers and populated and
            number(evidence.get('calls_before'),0,10000,integer=True) and
            number(evidence.get('calls_after'),0,10000,integer=True) and
            evidence.get('calls_before')==evidence.get('calls_after'))
        fixture=fixture and verified
        native_fields={key:evidence.get(key) is True for key in NATIVE_CHECKS}
        native_fields.update(native_verified=verified,native_runs=4 if populated else 0,
            native_proposals=3 if populated else 0)
    qualified=fixture and rpo<=profile['maximum_rpo_s'] and rto<=profile['maximum_rto_s']
    return receipt(profile,qualified=qualified,qualification='qualified' if qualified else 'not_qualified',
        fixture_passed=fixture,observed_rpo_s=rpo,observed_rto_s=rto,
        acknowledged_markers=len(markers),missing_markers=len(set(sequences)-set(restored)),
        logical_restore_only=True,redispatch_detected=(evidence.get('calls_before')!=evidence.get('calls_after') or
            native and evidence.get('handlers_before')!=evidence.get('handlers_after')),**native_fields)

def run(stack,profile):
    profile=validate_profile(profile)
    if type(stack) is not OwnedStack:raise ValueError('verified OwnedStack required')
    stack.verify_owned()
    native=getattr(stack,'native_fixture',False)
    required_calls,required_records=(8,6) if native else (2,2)
    if native and (profile['maximum_calls']<8 or profile['maximum_records']<6):
        raise ValueError('native restore fixture requires eight bounded calls/six records')
    if profile['maximum_calls']<2 or profile['maximum_records']<2:raise ValueError('restore fixture requires two bounded calls/records')
    config=json.loads((stack.secrets/'host.json').read_text());config.update(stack.manifest['endpoints'])
    if len(config['principals'])<2:raise ValueError('owner isolation requires two principals')
    with psycopg.connect(config['migration_dsn'],connect_timeout=5,options='-c statement_timeout=5000') as connection:
        if connection.execute('SELECT count(*) FROM lab_app.runs').fetchone()[0]+required_records>profile['maximum_records']:
            raise ValueError('restore record allowance exhausted')
    token=next(iter(config['principals']));headers={'Authorization':'Bearer '+token}
    identifier=stack.manifest['database_id'];engine=stack.engine
    service=stack.secrets/'service.json';original=service.read_text();changed=False
    b_stopped=False;fresh=None
    archived=stack.secrets/'qualification.dump'
    evidence={'suite':profile['suite'],'profile_sha256':digest(profile)};states=[]
    def count(client):
        response=client.get(config['model']+'/stats');response.raise_for_status();return response.json()['calls']
    with httpx.Client(timeout=15,follow_redirects=False) as client:
        client.post(config['model']+'/control',json={'maximum_calls':required_calls}).raise_for_status()
        current_phase='legacy_seed'
        try:
            for scenario,status in (('normal','waiting'),('missing_usage','blocked')):
                client.post(config['model']+'/control',json={'scenario':scenario,'preserve_allowance':True}).raise_for_status()
                response=client.post(config['a']+'/runs',headers={**headers,'Idempotency-Key':uuid.uuid4().hex},
                    json={'workflow':'synthetic','task':'Neutral logical restore fixture'})
                response.raise_for_status();state=response.json()
                if (state['status']!=status or scenario=='missing_usage' and
                    state.get('recovery_status')!='usage_reconciliation_required'):
                    raise ValueError('expected frozen recovery state required')
                states.append(state)
            fixture=None
            if native:
                from .native_restore import seed
                current_phase='native_seed'
                fixture=seed(stack,config,client)
                evidence['native_mode']=True
            evidence['calls_before']=count(client)
            with psycopg.connect(config['migration_dsn'],connect_timeout=5,options='-c statement_timeout=5000') as connection:
                connection.execute('CREATE SCHEMA lab_qualification')
                connection.execute('CREATE TABLE lab_qualification.markers (sequence integer PRIMARY KEY, acknowledged_at double precision NOT NULL)')
                for sequence in (1,2):
                    connection.execute('INSERT INTO lab_qualification.markers VALUES (%s,%s)',(sequence,time.time()))
            # pg_dump creates one transactionally consistent database snapshot.
            current_phase='logical_backup'
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
            b_stopped=True
            database='qualification_'+stack.owner
            current_phase='new_database'
            command(engine,'exec',identifier,'createdb','-U','postgres','--owner=lab_migration',database)
            current_phase='logical_restore'
            restored=subprocess.run([engine,'exec','-i',identifier,'pg_restore','-U','postgres',
                '--exit-on-error','-d',database],input=archived.read_bytes(),capture_output=True,timeout=30)
            if restored.returncode:raise ValueError('logical restore failed')
            replacement=json.loads(original)
            for key in ('harness_dsn','accounting_dsn','app_dsn'):
                parameters=conninfo_to_dict(replacement[key]);parameters['dbname']=database
                replacement[key]=make_conninfo(**parameters)
            service.write_text(json.dumps(replacement));changed=True
            current_phase='deliver_configuration'
            command(engine,'start','-a',stack.manifest['runtime_config_job'])
            if native:
                current_phase='fresh_replica'
                fresh='restored-'+uuid.uuid4().hex
                config['b']=stack.start_replica(fresh)
            else:
                command(engine,'start',replica)
                config['b']=refresh_replica_endpoint(stack,'b')
            current_phase='readiness'
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
            current_phase='legacy_verification'
            other=list(config['principals'])[1]
            for state in states:
                path='/runs/'+state['run_id']
                view=client.get(config['b']+path,headers=headers);view.raise_for_status();view=view.json()
                evidence['revision_verified'] &= view['revision']==state['revision']
                evidence['receipt_verified'] &= (view['status']==state['status'] and view['run_id']==state['run_id'] and
                    view.get('recovery_status')==state.get('recovery_status') and
                    view.get('review')==state.get('review') and view.get('choices')==state.get('choices') and
                    view.get('current_step')==state.get('current_step'))
                for suffix in ('','/usage'):
                    evidence['owner_verified'] &= client.get(config['b']+path+suffix,
                        headers={'Authorization':'Bearer '+other}).status_code==404
            usage=client.get(config['b']+'/runs/'+states[1]['run_id']+'/usage',headers=headers)
            usage.raise_for_status();usage=usage.json()
            evidence['unknown_usage_verified']=usage['unresolved_calls']==1 and usage['fully_costed'] is False
            if native:
                from .native_restore import verify
                current_phase='native_verification'
                restored_config=dict(config)
                for key in ('migration_dsn','harness_dsn','accounting_dsn','app_dsn'):
                    parameters=conninfo_to_dict(config[key]);parameters['dbname']=database
                    restored_config[key]=make_conninfo(**parameters)
                native_evidence=verify(restored_config,fixture,client)
                native_evidence['owner_verified'] &= evidence['owner_verified']
                evidence.update(native_evidence)
            evidence['calls_after']=count(client)
            current_phase='evaluation'
            return evaluate(profile,evidence,native_mode=native)
        except Exception as error:
            if not native:raise
            from .native_restore import failure
            diagnostic=failure(current_phase,error).diagnostic
            return receipt(profile,qualified=False,qualification='not_qualified',fixture_passed=False,
                reason='native_restore_failed',logical_restore_only=True,native_restore_diagnostic=diagnostic)
        finally:
            try:
                client.post(config['model']+'/control',json={'preserve_allowance':True}).raise_for_status()
            finally:
                if changed:
                    service.write_text(original)
                    command(engine,'start','-a',stack.manifest['runtime_config_job'])
                    if native and fresh in stack.manifest['replica_ids']:
                        command(engine,'stop','--time','10',stack.manifest['replica_ids'][fresh])
                    elif not native:
                        command(engine,'stop','--time','10',stack.manifest['replica_ids']['b'])
                if b_stopped:
                    command(engine,'start',stack.manifest['replica_ids']['b'])
                    config['b']=refresh_replica_endpoint(stack,'b')
