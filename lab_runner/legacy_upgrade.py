"""Generate historical evidence with immutable Lab 0.2.0, then migrate in place.

Private snapshots remain in the owned directory. Only the closed summary may be
published. No current SDK serializer constructs a historical receipt.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import uuid

import httpx
import psycopg
from psycopg.rows import dict_row

from .manifest import validate_resource
from .stack import ROOT, command

BASELINE_COMMIT='59752bef3e6b3ffde0ecbf38f34815d184043e20'
BASELINE_SHA256='f972db9d828b6ab0ffcf6ca210082e5cbc3b7678f5a1b8f42bbc482b9aafb472'
BASELINE_MANIFEST=ROOT/'dependencies/releases-lab-0.2.0.json'
BASELINE_ASSETS_SHA256='ab357d93f93026d1563b70915320a1ab7ac1e8ae1eca76b1743c7cf3c9a36614'


def baseline_digest():return BASELINE_SHA256


def validate_manifest(manifest):
    from prosaic_integration_lab.dependencies import sdk_manifest
    if hashlib.sha256(Path(manifest).read_bytes()).hexdigest()!=BASELINE_SHA256:
        raise ValueError('immutable historical manifest required')
    sdk_manifest(manifest)


def validate_baseline(image,manifest):
    validate_manifest(manifest)
    labels=image.get('Config',{}).get('Labels',{}) or {}
    if (not re.fullmatch(r'sha256:[0-9a-f]{64}',image.get('Id','')) or
        labels.get('io.prosaic.lab.baseline-source')!=BASELINE_COMMIT or
        labels.get('io.prosaic.lab.release-manifest')!=BASELINE_SHA256 or
        labels.get('io.prosaic.lab.dependency-mode')!='released' or
        'io.prosaic.lab.candidate-manifest' in labels):
        raise ValueError('immutable historical image required')


def build_baseline(manifest=BASELINE_MANIFEST,*,tag='prosaic-integration-lab:legacy-0.2.0'):
    """Build committed historical app code, original five verified wheel bytes."""
    command('docker','info')
    # The standalone source/SDist runner shares the public build helper's own
    # app-source bootstrap. It never inserts sibling SDK sources or editables.
    from scripts.build_consumer import cache_directory,verified_wheel_paths
    validate_manifest(manifest)
    paths=verified_wheel_paths(manifest,cache_directory(manifest,ROOT/'.cache/wheels'))
    with tempfile.TemporaryDirectory(prefix='lab-legacy-build-') as temporary:
        directory=Path(temporary);archive=directory/'baseline.tar'
        subprocess.run(['git','archive','--format=tar','--output',str(archive),BASELINE_COMMIT],
            cwd=ROOT,check=True,capture_output=True,timeout=30)
        context=directory/'source';context.mkdir()
        with tarfile.open(archive) as source:source.extractall(context,filter='data')
        if (context/'dependencies/releases.json').read_bytes()!=Path(manifest).read_bytes():
            raise ValueError('historical app manifest mismatch')
        wheels=context/'.cache/wheels';wheels.mkdir(parents=True)
        for path in paths:shutil.copyfile(path,wheels/path.name)
        verified_wheel_paths(context/'dependencies/releases.json',wheels)
        iid=directory/'image-id'
        subprocess.run(['docker','build','--file',str(context/'containers/Dockerfile'),
            '--tag',tag,'--iidfile',str(iid),'--label','io.prosaic.lab.baseline-source='+BASELINE_COMMIT,
            '--build-arg','RELEASE_MANIFEST_SHA256='+BASELINE_SHA256,str(context)],
            check=True,timeout=900,capture_output=True)
        identity=iid.read_text().strip()
    validate_baseline(json.loads(command('docker','image','inspect',identity))[0],manifest)
    return identity


def wait_for(predicate,timeout=40):
    deadline=time.monotonic()+timeout
    while True:
        try:value=predicate()
        except httpx.HTTPError:value=None
        if value:return value
        if time.monotonic()>=deadline:raise TimeoutError('observable legacy barrier timeout')
        time.sleep(.1)


def request(config,method,path,*,worker='a',**kwargs):
    token=next(token for token,p in config['principals'].items() if p['actor_id']=='alice')
    headers={'Authorization':'Bearer '+token,**kwargs.pop('headers',{})}
    result=httpx.request(method,config[worker]+path,headers=headers,timeout=35,**kwargs)
    result.raise_for_status();return result.json()


def stats(config):
    result=httpx.get(config['model']+'/stats',timeout=5);result.raise_for_status();return result.json()


def snapshot(dsn):
    with psycopg.connect(dsn,row_factory=dict_row) as connection:
        rows=connection.execute('SELECT * FROM lab_app.runs ORDER BY run_id').fetchall()
        receipts=connection.execute('SELECT * FROM prosaic_harness.receipts ORDER BY run_id,invocation_id').fetchall()
        intents=connection.execute('SELECT * FROM prosaic_metering_intents ORDER BY provider_call_id').fetchall()
        observations=connection.execute('SELECT * FROM prosaic_metering_observations ORDER BY provider_call_id').fetchall()
    # A JSON-safe original SQL snapshot is private evidence, never reserialized
    # into an SDK checkpoint/receipt or written back during upgrade.
    return json.loads(json.dumps({'runs':rows,'receipts':receipts,'intents':intents,
                                  'observations':observations},default=str))


def generate(stack,*,baseline_manifest,baseline_image):
    """Stack has provisioned schema2 with baseline code; service routes generate it."""
    validate_baseline(json.loads(command(stack.engine,'image','inspect',baseline_image))[0],baseline_manifest)
    stack.verify_owned()
    config=json.loads((stack.secrets/'host.json').read_text())
    config.update(stack.manifest['endpoints'])
    fixture={'baseline_source':BASELINE_COMMIT,'baseline_manifest_sha256':BASELINE_SHA256,
             'baseline_image':baseline_image,'baseline_payload_audit':'verified','runs':[]}
    with psycopg.connect(config['migration_dsn']) as connection:
        if connection.execute('SELECT version FROM lab_app.schema_version').fetchone()!=(2,):
            raise ValueError('baseline must generate schema2 evidence')
    before=stats(config)['calls']
    def start(case,workflow):
        key='legacy-'+case+'-'+uuid.uuid4().hex
        result=request(config,'POST','/runs',headers={'Idempotency-Key':key},
                       json={'workflow':workflow,'task':'synthetic historical '+case})
        fixture['runs'].append({'case':case,'key':key,'view':result})
        return result
    start('approval','approval')
    start('synthetic','synthetic')
    httpx.post(config['model']+'/control',json={'scenario':'missing_usage'},timeout=5).raise_for_status()
    start('unknown-usage','synthetic')
    for case,control,barrier in (
        ('saved-receipt',{'accepted_gate':True},'accepted_events'),
        ('starting',{'blocked':True},'calls')):
        key='legacy-'+case+'-'+uuid.uuid4().hex;observed=stats(config)[barrier]
        httpx.post(config['model']+'/control',json=control,timeout=5).raise_for_status()
        def submit():
            try:return request(config,'POST','/runs',headers={'Idempotency-Key':key},
                json={'workflow':'synthetic','task':'synthetic historical '+case})
            except httpx.HTTPError:return None
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(submit)
            try:
                wait_for(lambda:stats(config)[barrier]>observed,timeout=10)
                identifier=stack.manifest['replica_ids']['a']
                validate_resource(json.loads(command(stack.engine,'inspect',identifier))[0],identifier,stack.owner)
                command(stack.engine,'kill',identifier)
            finally:httpx.post(config['model']+'/control',json={},timeout=5).raise_for_status()
            future.result(timeout=10)
        with psycopg.connect(config['app_dsn'],row_factory=dict_row) as connection:
            row=connection.execute('SELECT run_id FROM lab_app.runs WHERE idempotency_key=%s',(key,)).fetchone()
        if row is None:raise ValueError('historical route did not reserve run')
        fixture['runs'].append({'case':case,'key':key,'view':{'run_id':row['run_id']}})
        if case=='saved-receipt':
            config['a']=stack.start_replica('baseline-fresh',image=baseline_image)
            stack.manifest['replica_ids']['a']=stack.manifest['replica_ids']['baseline-fresh'];stack._save()
            # Old non-renewing dead-worker lease cannot be reused before expiry.
            time.sleep(16)
    fixture['calls']=stats(config)['calls'];fixture['call_delta']=fixture['calls']-before
    if fixture['call_delta']!=4:raise ValueError('historical inference count mismatch')
    fixture['original']=snapshot(config['migration_dsn'])
    # Drain all historical workers before migration, including killed workers.
    for identifier in set(stack.manifest['replica_ids'].values()):
        validate_resource(json.loads(command(stack.engine,'inspect',identifier))[0],identifier,stack.owner)
        command(stack.engine,'stop','--time','10',identifier)
    fixture['assets_hash']=fixture['original']['runs'][0]['assets_hash']
    path=stack.directory/'legacy-fixture.json';path.write_text(json.dumps(fixture,indent=2)+'\n');path.chmod(0o600)
    return fixture


def upgrade(stack,fixture):
    from prosaic_integration_lab.config import assets_hash
    from prosaic_integration_lab.migrations import migrate
    stack.verify_owned()
    retained=ROOT/'assets/legacy-0.2.0'
    if assets_hash(retained)!=BASELINE_ASSETS_SHA256 or fixture['assets_hash']!=BASELINE_ASSETS_SHA256:
        raise ValueError('missing exact historical assets')
    config=json.loads((stack.secrets/'host.json').read_text())
    result=migrate(config['migration_dsn'],runtime_role='app_runtime')
    if result['from_version']!=2 or result['to_version']!=3 or result['rows_preserved']!=5:
        raise ValueError('unexpected upgrade migration')
    fixture['migration']='v2-to-v3'
    service=json.loads((stack.secrets/'service.json').read_text())
    service['legacy_bundles']={fixture['assets_hash']:{'assets':'/srv/lab/assets/legacy-0.2.0'}}
    # Deliberately changed current billing defaults do not replace frozen rows.
    for principal in service['principals'].values():principal['billing_account_id']='changed-current-default'
    (stack.secrets/'service.json').write_text(json.dumps(service))
    command(stack.engine,'start','-a',stack.manifest['runtime_config_job'])
    for name in ('a','b'):stack.start_replica('upgraded-'+name)
    for name in ('a','b'):
        stack.manifest['endpoints'][name]=stack.manifest['endpoints']['upgraded-'+name]
        stack.manifest['replica_ids'][name]=stack.manifest['replica_ids']['upgraded-'+name]
    stack._save()
    config.update(a=stack.manifest['endpoints']['upgraded-a'],b=stack.manifest['endpoints']['upgraded-b'],
                  model=stack.manifest['endpoints']['model'],legacy_fixture=str(stack.directory/'legacy-fixture.json'))
    fixture['before_recovery']=snapshot(config['migration_dsn'])
    if fixture['before_recovery']!=fixture['original']:raise ValueError('migration changed historical evidence')
    path=stack.directory/'legacy-fixture.json';path.write_text(json.dumps(fixture,indent=2)+'\n');path.chmod(0o600)
    (stack.secrets/'host.json').write_text(json.dumps(config))
    return config


def verify(stack,fixture):
    stack.verify_owned()
    config=json.loads((stack.secrets/'host.json').read_text())
    if stats(config)['calls']!=fixture['calls']:raise ValueError('upgrade redispatched inference')
    return public_summary(fixture)


def public_summary(fixture):
    return {key:fixture[key] for key in ('baseline_source','baseline_manifest_sha256','baseline_image',
        'baseline_payload_audit','migration') if key in fixture} | {'legacy_fixture_count':len(fixture.get('runs',[]))}
