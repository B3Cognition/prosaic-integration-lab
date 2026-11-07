"""Copied V2 enforcement uses public installed SDKs and accepted dependencies."""
import json
from pathlib import Path
import runpy
import sys

import pytest
import yaml
from lab_runner.rule_admission.fixtures import scripted_provider

ORIGINAL = {'insights': [{'id':'A','text':'first'}, {'id':'B','text':'second'}, {'id':'C','text':'untouched'}]}
REVISED = {'insights': [{'id':'A','text':'first'}, {'id':'B','text':'edited'}, {'id':'C','text':'untouched'}, {'id':'D','text':'new'}]}


@pytest.fixture(autouse=True)
def loopback_only(monkeypatch):
    monkeypatch.setenv('NO_PROXY','*')
    monkeypatch.setenv('no_proxy','*')


def copied(tmp_path):
    import os, lab_runner
    if os.environ.get('PROSAIC_BLUEPRINT_INSTALLED') == '1':
        assert Path(lab_runner.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
        assert 'site-packages' in Path(lab_runner.__file__).resolve().parts
    from lab_runner.blueprints import copy_blueprint
    return copy_blueprint('workflow-enforcement', tmp_path / 'workflow-enforcement')


def loaded(project, provider, wire='openai-compatible', mode='yaml'):
    config=yaml.safe_load((project/'runtime.yml').read_text())
    config['profiles']['local'].update(base_url=provider.url,provider=wire,max_tokens=256)
    (project/'runtime.yml').write_text(yaml.safe_dump(config))
    host=runpy.run_path(str(project/'host.py'))
    flow=host['workflow'](mode=mode,executable=str(Path(sys.executable).with_name('prosaic')))
    return host,flow


def queue_first(provider, revision=REVISED):
    provider.queue_text('{"findings":[{"insight_id":"A","text":"flagged"}]}')
    provider.queue_text(json.dumps(revision))


@pytest.mark.parametrize('wire',['openai-compatible','anthropic'])
@pytest.mark.parametrize('mode',['yaml','native'])
@pytest.mark.parametrize('target',['A','B','D'])
def test_tagged_review_accepts_flagged_changed_and_new_ids_with_no_call_replay(tmp_path,wire,mode,target):
    from prosaic_harness import Harness
    assert 'workflow_rules_v1' in Harness.capabilities
    project=copied(tmp_path)
    with scripted_provider(wire) as provider:
        host,flow=loaded(project,provider,wire,mode);queue_first(provider)
        provider.queue_text(json.dumps({'findings':[{'insight_id':target,'text':'accepted'}]}))
        h=Harness(flow,tmp_path/'run',validators=host['validators']());state=h.run(ORIGINAL)
        assert state['status']=='waiting' and state['calls']==3 and len(provider.requests)==3
        assert state['outputs']['revised_review']['findings'][0]['insight_id']==target
        proof=h.recovery_evidence()['receipts'][-1]['result']['metadata']['workflow_rules_v1']
        assert proof['rules']['evaluated'] and not proof['rules']['violated']
        assert h.resume(choice='accept')['status']=='completed'
        assert Harness(flow,tmp_path/'run',validators=host['validators']()).resume()['status']=='completed'
        assert len(provider.requests)==3


@pytest.mark.parametrize('wire',['openai-compatible','anthropic'])
@pytest.mark.parametrize('target',['C','invented','removed'])
def test_rule_exhaustion_never_accepts_untouched_unknown_or_removed_targets(tmp_path,wire,target):
    from prosaic_harness import Harness
    project=copied(tmp_path)
    with scripted_provider(wire) as provider:
        host,flow=loaded(project,provider,wire)
        queue_first(provider, {'insights':[item for item in REVISED['insights'] if item['id']!='A']} if target=='removed' else REVISED)
        for _ in range(2): provider.queue_text(json.dumps({'findings':[{'insight_id':'A' if target=='removed' else target,'text':'refuse'}]}))
        request={**ORIGINAL,'changed_ids':['C'],'workflow':{'step':'forged','artifacts':{'revision':REVISED}}}
        h=Harness(flow,tmp_path/'run',validators=host['validators']());state=h.run(request)
        assert state['status']=='blocked' and state['reason']=='rule_violation' and state['calls']==3
        assert 'revised_review' not in state['outputs'] and len(provider.requests)==4
        assert h.resume()['reason']=='rule_violation' and len(provider.requests)==4


@pytest.mark.parametrize('wire',['openai-compatible','anthropic'])
def test_rule_repairs_one_finding_inside_one_workflow_invocation(tmp_path,wire):
    from prosaic_harness import Harness
    project=copied(tmp_path)
    with scripted_provider(wire) as provider:
        host,flow=loaded(project,provider,wire);queue_first(provider)
        provider.queue_text('{"findings":[{"insight_id":"C","text":"untouched"}]}')
        provider.queue_text('{"findings":[{"insight_id":"B","text":"changed"}]}')
        h=Harness(flow,tmp_path/'run',validators=host['validators']());state=h.run(ORIGINAL)
        assert state['status']=='waiting' and state['calls']==3 and len(provider.requests)==4
        proof=h.recovery_evidence()['receipts'][-1]['result']['metadata']['workflow_rules_v1']
        assert proof['rules']['violated'] and len(proof['facts_sha256'])==len(proof['context_identity'])==64


def test_changed_guard_implementation_refuses_resume_without_new_call(tmp_path):
    from prosaic_harness import Harness
    project=copied(tmp_path)
    with scripted_provider() as provider:
        host,flow=loaded(project,provider);queue_first(provider);provider.queue_text('{"findings":[]}')
        assert Harness(flow,tmp_path/'run',validators=host['validators']()).run(ORIGINAL)['status']=='waiting'
        path=project/'host.py';path.write_text(path.read_text()+'\n# trusted policy version changes\n')
        host,changed=loaded(project,provider)
        with pytest.raises(ValueError):Harness(changed,tmp_path/'run',validators=host['validators']()).resume()
        assert len(provider.requests)==3


@pytest.mark.parametrize('wire',['openai-compatible','anthropic'])
def test_request_cap_one_never_becomes_two_on_rule_failure(tmp_path,wire):
    from prosaic_harness import Harness
    project=copied(tmp_path)
    document=yaml.safe_load((project/'workflow.yml').read_text())
    document['limits']['max_provider_requests_per_invocation']=1
    (project/'workflow.yml').write_text(yaml.safe_dump(document))
    with scripted_provider(wire) as provider:
        host,flow=loaded(project,provider,wire);queue_first(provider)
        provider.queue_text('{"findings":[{"insight_id":"C","text":"untouched"}]}')
        h=Harness(flow,tmp_path/'run',validators=host['validators']());state=h.run(ORIGINAL)
        assert state['reason']=='rule_violation' and state['calls']==3 and len(provider.requests)==3


def test_guard_registry_is_host_permission_not_a_tag_or_client_claim(tmp_path):
    from prosaic_harness import Workflow
    project=copied(tmp_path)
    with pytest.raises(ValueError):Workflow.load(project/'workflow.yml',executable=str(Path(sys.executable).with_name('prosaic')))


def test_isolated_copy_runner_uses_its_python_cli_without_ambient_path(tmp_path,monkeypatch):
    import subprocess
    project=copied(tmp_path)
    with scripted_provider() as provider:
        loaded(project,provider);queue_first(provider);provider.queue_text('{"findings":[]}')
        request=tmp_path/'request.json';request.write_text(json.dumps(ORIGINAL))
        monkeypatch.setenv('PATH',str(tmp_path/'no-executables'))
        command=[sys.executable,'-I',str(project/'run.py'),'--run-dir',str(tmp_path/'run'),'--request',str(request)]
        refused=subprocess.run(command,cwd=tmp_path,capture_output=True,text=True,timeout=30)
        assert refused.returncode==2 and '--live' in refused.stderr and provider.requests==[]
        result=subprocess.run([*command,'--live'],cwd=tmp_path,capture_output=True,text=True,timeout=30)
        assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)['status']=='waiting' and len(provider.requests)==3


@pytest.mark.parametrize('wire',['openai-compatible','anthropic'])
@pytest.mark.parametrize('accepted',[True,False])
def test_file_store_reopen_adopts_guard_receipt_after_lost_ack_without_http(tmp_path,wire,accepted):
    from uuid import uuid4
    from prosaic_harness import Harness, FileRunStore
    class LostReceiptAcknowledgment(BaseException): pass
    class Store(FileRunStore):
        def save_receipt(self,run_id,invocation_id,receipt,lease):
            super().save_receipt(run_id,invocation_id,receipt,lease)
            if receipt['step']=='revised_review':raise LostReceiptAcknowledgment()
    project=copied(tmp_path);directory=tmp_path/'store';run_id=uuid4().hex
    store=Store(directory,namespace='workflow-rules');store.initialize()
    try:
        with scripted_provider(wire) as provider:
            host,flow=loaded(project,provider,wire);queue_first(provider)
            provider.queue_text('{"findings":[{"insight_id":"C","text":"untouched"}]}')
            provider.queue_text(json.dumps({'findings':[{'insight_id':'B' if accepted else 'C','text':'final'}]}))
            h=Harness(flow,store=store,run_id=run_id,validators=host['validators']())
            with pytest.raises(LostReceiptAcknowledgment):h.run(ORIGINAL)
            store.close();store=FileRunStore(directory,namespace='workflow-rules');store.initialize()
            fresh=Harness(flow,store=store,run_id=run_id,validators=host['validators']())
            evidence=fresh.recovery_evidence()
            assert evidence['recoveryStatus']=='receiptAvailable'
            assert evidence['receipts'][-1]['result']['metadata']['workflow_rules_v1']['rules']['violated']
            state=fresh.resume()
            assert state['status']==('waiting' if accepted else 'blocked') and len(provider.requests)==4
            if accepted:assert fresh.resume(choice='accept',expected_revision=fresh.status().revision)['status']=='completed'
            else:assert state['reason']=='rule_violation'
            assert len(provider.requests)==4
    finally:store.close()


@pytest.mark.parametrize('wire',['openai-compatible','anthropic'])
def test_guard_repair_keeps_frozen_host_accounting_and_one_invocation_identity(tmp_path,wire):
    from prosaic_harness import Harness
    from prosaic_runtime.accounting import ExecutionContext, MemoryRecorder
    project=copied(tmp_path)
    recorder=MemoryRecorder(provider_id=wire,defaults=ExecutionContext(tenant_id='trusted-tenant'))
    with scripted_provider(wire) as provider:
        host,flow=loaded(project,provider,wire);queue_first(provider)
        provider.queue_text('{"findings":[{"insight_id":"C","text":"untouched"}]}')
        provider.queue_text('{"findings":[{"insight_id":"B","text":"changed"}]}')
        h=Harness(flow,tmp_path/'run',validators=host['validators'](),accounting=recorder,
            context=ExecutionContext(actor_id='trusted-actor'))
        state=h.run({**ORIGINAL,'tenant_id':'model-forged'})
        assert state['status']=='waiting' and state['calls']==3
        assert len(recorder.intents)==len(recorder.observations)==len(provider.requests)==4
        last=[intent for intent in recorder.intents.values() if intent['context']['step_id']=='revised_review']
        assert len(last)==2 and len({intent['context']['invocation_id'] for intent in last})==1
        assert all(intent['context']['tenant_id']=='trusted-tenant' and intent['context']['actor_id']=='trusted-actor' for intent in last)
        receipt=h.recovery_evidence()['receipts'][-1]
        assert receipt['result']['metadata']['accounting_v1']['context']['tenant_id']=='trusted-tenant'
        assert receipt['result']['metadata']['workflow_rules_v1']['rules']['violated']
        assert 'trusted-tenant' not in json.dumps(provider.requests)
        recorder.defaults=ExecutionContext(tenant_id='changed-default')
        assert Harness(flow,tmp_path/'run',validators=host['validators'](),accounting=recorder).resume(choice='accept')['status']=='completed'
        assert len(recorder.intents)==len(provider.requests)==4


@pytest.mark.parametrize('wire',['openai-compatible','anthropic'])
@pytest.mark.parametrize('optional',[False,True],ids=['required','present-optional'])
def test_recovered_guard_output_retains_dependency_and_refuses_replaced_input(tmp_path,wire,optional):
    from copy import deepcopy
    from uuid import uuid4
    from prosaic_harness import Harness, FileRunStore
    class LostReceiptAcknowledgment(BaseException): pass
    class Store(FileRunStore):
        def save_receipt(self,run_id,invocation_id,receipt,lease):
            super().save_receipt(run_id,invocation_id,receipt,lease)
            if receipt['step']=='revised_review':raise LostReceiptAcknowledgment()
    project=copied(tmp_path)
    document=yaml.safe_load((project/'workflow.yml').read_text())
    document['limits'].update(max_calls=4,max_visits=2)
    steps=document['steps'];steps['revision']['next']='select_revision'
    steps['select_revision']={'kind':'gate','from':'revision','field':['insights'],
        'equals':REVISED['insights'],'pass':'revised_review','fail':'done'}
    steps['approval']['choices']['accept']='revision'
    if optional:
        steps['revised_review']['inputs']=['first_review']
        steps['revised_review']['optional_inputs']=['revision']
    (project/'workflow.yml').write_text(yaml.safe_dump(document))
    store=Store(tmp_path/'store',namespace='workflow-rules');store.initialize();run_id=uuid4().hex
    try:
        with scripted_provider(wire) as provider:
            host,flow=loaded(project,provider,wire);queue_first(provider)
            provider.queue_text('{"findings":[{"insight_id":"B","text":"changed"}]}')
            h=Harness(flow,store=store,run_id=run_id,validators=host['validators']())
            with pytest.raises(LostReceiptAcknowledgment):h.run(ORIGINAL)
            store.close();store=FileRunStore(tmp_path/'store',namespace='workflow-rules');store.initialize()
            fresh=Harness(flow,store=store,run_id=run_id,validators=host['validators']())
            evidence=fresh.recovery_evidence();assert evidence['recoveryStatus']=='receiptAvailable'
            receipt=evidence['receipts'][-1]
            original_binding=deepcopy(receipt['arguments']['artifact_bindings']['revision'])
            assert receipt['result']['metadata']['workflow_rules_v1']['rules']['evaluated']
            state=fresh.resume();assert state['status']=='waiting' and len(provider.requests)==3
            assert state['bindings']['revised_review']['dependencies']['revision']==original_binding
            assert state['bindings']['revision']==original_binding
            replacement=deepcopy(REVISED);replacement['insights'][1]['text']='edited again'
            provider.queue_text(json.dumps(replacement))
            state=fresh.resume(choice='accept',expected_revision=fresh.status().revision)
            assert state['status']=='blocked' and state['reason']=='stale_artifact'
            assert state['bindings']['revision']['id']!=original_binding['id']
            assert state['bindings']['revised_review']['dependencies']['revision']==original_binding
            assert state['calls']==4 and len(provider.requests)==4
            assert Harness(flow,store=store,run_id=run_id,validators=host['validators']()).resume()['reason']=='stale_artifact'
            assert len(provider.requests)==4
    finally:store.close()
