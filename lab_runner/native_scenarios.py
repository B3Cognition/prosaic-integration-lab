"""Host-selected native fixtures and exact-owned fresh-worker controls."""
import json
from pathlib import Path
import time

import httpx

from .manifest import validate_resource
from .stack import command


def approved_proposal():
    from prosaic_integration_lab.native_execution import approved_proposal as proposal
    return proposal()


def native_configuration(namespace):
    """Fixture authority is registered by the runner, never by HTTP clients."""
    policies={'tenant-a':{'composition':True,'inline':False,'tools':['fixture_apply'],'agents':['finder','reviewer','effecter'],
                   'review_outputs':True,'response_schema':True},
              'tenant-b':{'composition':False,'inline':True,'tools':[],'agents':['finder','reviewer','effecter']}}
    bundles=[]
    for tenant,policy in policies.items():
        bundles.append({'version':'synthetic-v1','model_url':'http://model:8000/v1',
            'operation_namespace':namespace+'-'+tenant,'journal_identity':'fixture-journal-v1',
            'fixture_effects':True,'policies':{tenant:policy}})
    return {'bundles':bundles,'tenants':{tenant:{'bundle_version':'synthetic-v1',**policy}
                                       for tenant,policy in policies.items()}}


def effect_proposal():
    # Amount is an operation argument. The business key/namespace come from
    # the frozen trusted run scope in the registered contextual resolver.
    return {'definition':{'version':1,'start':'apply','steps':{
        'apply':{'kind':'agent','agent':'effecter','schema':'found',
                 'tools':['fixture_apply'],'require_tools':['fixture_apply'],'next':'done'},
        'done':{'kind':'finish','requires':['apply']}}}}


def control(lab,**settings):
    result=httpx.post(lab['model']+'/control',json=settings,timeout=5)
    result.raise_for_status()


def calls(lab):
    result=httpx.get(lab['model']+'/stats',timeout=5);result.raise_for_status()
    return result.json()['calls']


def owned(lab):
    manifest=json.loads(Path(lab['fixture_manifest']).read_text())
    for identifier in manifest.get('replica_ids',{}).values():
        validate_resource(json.loads(command(manifest['engine'],'inspect',identifier))[0],identifier,manifest['owner'])
    return manifest


def replace_worker(lab,name='b',*,native=None,config_patch=None):
    """A genuinely fresh process/image container, exact IDs and delivered config."""
    from .stack import OwnedStack
    manifest=owned(lab)
    identifier=manifest['replica_ids'][name]
    command(manifest['engine'],'stop','--time','10',identifier)
    stack=object.__new__(OwnedStack)
    stack.owner=manifest['owner'];stack.engine=manifest['engine'];stack.manifest=manifest
    stack.directory=Path(lab['fixture_manifest']).parent;stack.secrets=stack.directory/'secrets'
    if native is not None or config_patch is not None:
        path=stack.secrets/'service.json';config=json.loads(path.read_text())
        if native is not None:config['native']=native
        config.update(config_patch or {})
        path.write_text(json.dumps(config));path.chmod(0o600)
        command(stack.engine,'start','-a',manifest['runtime_config_job'])
    fresh=name+'-'+str(time.monotonic_ns())
    url=stack.start_replica(fresh)
    stack.manifest['replica_ids'][name]=stack.manifest['replica_ids'][fresh]
    stack.manifest['endpoints'][name]=url;stack._save();lab[name]=url
    return url


def provision_effects(dsn):
    import psycopg
    with psycopg.connect(dsn) as connection:
        connection.execute('CREATE SCHEMA lab_fixture')
        connection.execute('''CREATE TABLE lab_fixture.effects (
            namespace text NOT NULL,business_key text NOT NULL,amount integer NOT NULL,
            PRIMARY KEY(namespace,business_key))''')
        connection.execute('GRANT USAGE ON SCHEMA lab_fixture TO app_runtime')
        connection.execute('GRANT SELECT,INSERT ON lab_fixture.effects TO app_runtime')
