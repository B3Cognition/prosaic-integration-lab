"""Real HTTP model requests and installed SDKs; SQL/replicas are acceptance-only."""
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
from prosaic_harness import FileRunStore,Harness

from lab_runner.native_scenarios import context_handoff_proposal,native_configuration
from prosaic_integration_lab.capacity import policy
from prosaic_integration_lab.native_execution import NativeExecution
from test_native_fault_transport import provider


def test_context_fact_is_consumed_through_distinct_tiers_and_exact_binding(provider,tmp_path):
    configuration=native_configuration('context-loopback')
    for bundle in configuration['bundles']:bundle['model_url']=provider+'/v1'
    host=SimpleNamespace(config={'native':configuration,'app_dsn':'unused',
        'assets':str(Path(__file__).resolve().parents[2]/'assets'),
        'fixture_events_url':provider+'/events'},capacity=policy({}))
    execution=NativeExecution(host)
    _,factory=execution.factories[('tenant-a','synthetic-v1')]
    workflow=factory.build_json(json.dumps(context_handoff_proposal()))
    httpx.post(provider+'/control',json={'scenario':'context_handoff','maximum_calls':2},timeout=2).raise_for_status()
    before=httpx.get(provider+'/stats',timeout=2).json()['calls']
    with FileRunStore(tmp_path/'state') as store:
        harness=Harness(workflow,store=store,run_id='a'*32)
        assert harness.run({'entity_id':'original-request'})['status']=='waiting'
        prepared=store.load_run('a'*32)
        pack=prepared.state['outputs']['prepare']
        binding=prepared.state['bindings']['prepare']
        assert pack['entity_id'].startswith('context-') and pack['entity_id']!='original-request'
        harness.resume(choice='accept',response={'confirmed':True},expected_revision=prepared.revision)
        consumed=store.load_run('a'*32)
        assert consumed.state['outputs']['review']=={'entity_id':pack['entity_id'],'approved':True}
        receipt=store.load_receipt('a'*32,consumed.state['bindings']['review']['id'])
        assert receipt['arguments']['artifacts']=={'prepare':pack}
        assert receipt['arguments']['artifact_bindings']=={'prepare':binding}
        first=store.load_receipt('a'*32,binding['id'])
        assert [r['result']['metadata']['request_model'] for r in (first,receipt)]==[
            'fixture-balanced','fixture-strong']
        harness.resume(choice='accept',response={'confirmed':True},expected_revision=consumed.revision)
        assert store.load_run('a'*32).state['status']=='completed'
    assert httpx.get(provider+'/stats',timeout=2).json()['calls']==before+2
