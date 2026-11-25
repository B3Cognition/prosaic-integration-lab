"""Generate authentic old receipts through public SDKs in a separate interpreter."""
from copy import deepcopy
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlsplit
import json,os,runpy,sys
from prosaic_runtime import ProsaicRuntime,RuntimeConfig,ExecutionContext
from prosaic_runtime.accounting import MemoryRecorder
from prosaic_harness import Harness,FileRunStore

assert version('b3-prosaic-runtime')=='0.9.17'
options=json.load(sys.stdin);assert urlsplit(options['url']).hostname=='127.0.0.1'
os.environ['NO_PROXY']=os.environ['no_proxy']='*'
project=Path(options['project']);host=runpy.run_path(str(project/'host.py'))
if options['kind']=='postgres':
    from prosaic_runtime_postgres import PostgresRecorder
    from prosaic_harness_postgres import PostgresRunStore
    recorder=PostgresRecorder(options['dsn'],namespace='effort',environment='test',provider_id=options['wire'])
    store_type=PostgresRunStore;location=options['dsn']
else:
    assert options['kind']=='file'
    recorder=MemoryRecorder(provider_id=options['wire']);store_type=FileRunStore;location=options['directory']
saved=[]
class LostAck(BaseException):pass
class FaultStore(store_type):
    def save_receipt(self,run_id,invocation_id,receipt,lease):
        super().save_receipt(run_id,invocation_id,receipt,lease)
        saved.append(deepcopy(receipt))
        if receipt['step']=='second':raise LostAck()

config=RuntimeConfig.load(project/'runtime.yml');name=config.default_profile
endpoint=config.profiles[name];features=dict(endpoint.features)
if options['wire']=='anthropic':features['reasoning_effort']=None
endpoint=replace(endpoint,base_url=options['url'],provider=options['wire'],features=features,
                 supported_efforts=None if options['wire']=='anthropic' else endpoint.supported_efforts)
runtime=ProsaicRuntime(replace(config,profiles={name:endpoint}),source=project/'.prosaic',accounting=recorder)
flow=host['workflow'](runtime,project=project);store=FaultStore(location,namespace='effort')
if options['kind']=='file':store.initialize()
else:store.check_ready();recorder.check_ready()
try:
    h=Harness(flow,store=store,run_id=options['run_id'],runtime=runtime,context=ExecutionContext(tenant_id='trusted'))
    assert h.run({})['status']=='waiting'
    store.close();store=FaultStore(location,namespace='effort')
    if options['kind']=='file':store.initialize()
    else:store.check_ready()
    h=Harness(flow,store=store,run_id=options['run_id'],runtime=runtime)
    try:h.resume(choice='approve',expected_revision=h.status().revision)
    except LostAck:pass
    else:raise AssertionError('lost-ack fixture did not fire')
    assert len(saved)==2 and all('reasoning_effort_v1' not in r['result']['metadata'] for r in saved)
    calls=recorder.calls() if options['kind']=='postgres' else {'intents':recorder.intents,'observations':recorder.observations}
    assert len(calls if options['kind']=='postgres' else calls['intents'])==2
    print(json.dumps({'runtimeVersion':version('b3-prosaic-runtime'),'receipts':saved,'accounting':calls}))
finally:store.close()
