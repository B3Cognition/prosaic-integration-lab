"""Copyable host accounting labels with installed public SDKs, no live calls."""
from dataclasses import replace
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
from uuid import uuid4

import pytest
from lab_runner.blueprints import copy_blueprint
from lab_runner.rule_admission.fixtures import scripted_provider


@pytest.fixture(autouse=True)
def loopback_only(monkeypatch):
    monkeypatch.setenv('NO_PROXY', '*')
    monkeypatch.setenv('no_proxy', '*')


@pytest.fixture(params=['openai-compatible', 'anthropic'])
def wire(request): return request.param


def copied(tmp_path):
    import lab_runner
    if os.environ.get('PROSAIC_BLUEPRINT_INSTALLED') == '1':
        assert Path(lab_runner.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    project = copy_blueprint('accounting-metadata', tmp_path/'metadata')
    return project, runpy.run_path(str(project/'host.py'))


def context(host, **changes):
    return host['trusted_context'](tenant_id='trusted-tenant', billing_account_id='trusted-payer',
                                   benchmark_run='benchmark-42', variant=changes.get('variant', 'PRIVATE_VARIANT'))


def test_public_sdk_ownership_and_capability():
    from importlib.metadata import version
    import prosaic_runtime, prosaic_harness, prosaic_runtime_postgres
    assert (version('b3-prosaic-runtime'),version('b3-prosaic-harness')) in {
        ('0.9.17','0.9.12'),('0.9.18','0.9.12'),('0.9.19','0.9.13'),('0.9.20','0.9.14'),('0.9.21.dev1','0.9.15.dev1'),('0.9.21','0.9.15'),('0.9.22.dev1','0.9.16.dev1')}
    assert version('b3-prosaic-runtime-postgres') == '0.3.0'
    assert 'accounting_request_metadata_v1' in prosaic_runtime.ProsaicRuntime.capabilities
    for module in (prosaic_runtime, prosaic_harness, prosaic_runtime_postgres):
        origin = Path(module.__file__).resolve()
        assert origin.is_relative_to(Path(sys.prefix).resolve()) and 'site-packages' in origin.parts


def test_empty_metadata_preserves_independent_legacy_accounting_golden():
    from prosaic_runtime import ExecutionContext, ResolvedContext
    from prosaic_runtime.accounting import fingerprint
    options = dict(application_id='app', tenant_id='tenant', billing_account_id='payer',
                   request_id='request', invocation_id='invocation', run_id='run')
    # Fixed golden from public Runtime0.9.16; no timestamps/random IDs.
    for labels in (None, {}):
        resolved = ExecutionContext(**options, request_metadata=labels).resolve()
        assert 'request_metadata' not in resolved.to_dict()
        assert fingerprint(resolved.to_dict()) == 'c022cb2f52a608e888a78f72a0dde93af4e200d3d53cb7c8edb527dcd7922aef'
        assert ResolvedContext.from_dict(resolved.to_dict()) == resolved


@pytest.mark.parametrize('entry', ['run', 'turn', 'prepared'])
def test_prepare_labels_precede_dispatch_and_never_enter_wire_or_artifact_identity(tmp_path, wire, entry):
    from prosaic_runtime.accounting import MemoryRecorder
    project, host = copied(tmp_path)
    with scripted_provider(wire) as provider:
        seen = []
        def before(labels):
            assert provider.requests == []
            seen.append(dict(labels))
            labels['variant'] = 'callback-copy-only'
        backend = MemoryRecorder(provider_id=wire)
        recorder = host['LabelingRecorder'](backend, before)
        runtime = host['build_runtime'](project=project, base_url=provider.url, provider=wire, accounting=recorder)
        agent = host['load_agent'](project)
        digest = agent.digest
        prepared = runtime.prepare_turn(agent, message='hello')
        identity = prepared.context_identity
        provider.queue_text('done')
        if entry == 'run': result = host['run_benchmark'](runtime, agent, context=context(host))
        else:
            result = runtime.turn(prepared if entry == 'prepared' else agent, context=context(host),
                **({} if entry == 'prepared' else {'message': 'hello'})).result
        assert result.exit_code == 0 and len(provider.requests) == 1
        assert seen == [{'run': 'benchmark-42', 'variant': 'PRIVATE_VARIANT'}]
        assert next(iter(backend.intents.values()))['context']['request_metadata']['labels'] == seen[0]
        assert agent.digest == digest and runtime.prepare_turn(agent, message='hello').context_identity == identity
        assert 'PRIVATE_VARIANT' not in json.dumps(provider.requests) + json.dumps(provider.captured_headers)
        assert set(host['public_view']({'status': 'completed', 'calls': 1, 'accounting_context': 'private', 'outputs': 'private'})) == {'status', 'calls'}


@pytest.mark.parametrize('kind', ['tool', 'repair'])
def test_continuation_labels_are_frozen_across_callbacks(tmp_path, wire, kind):
    from prosaic_runtime import CustomTool, ProsaicArtifact, RunPolicy, generic_guards
    from prosaic_runtime.accounting import ExecutionContext, MemoryRecorder
    project, host = copied(tmp_path)
    supplied = {'variant': 'original'}
    original = ExecutionContext(request_metadata=supplied)
    supplied['variant'] = 'caller-mutation'
    with scripted_provider(wire) as provider:
        seen = []
        backend = MemoryRecorder(provider_id=wire)
        def before(labels):
            assert len(provider.requests) == len(seen)
            seen.append(dict(labels)); labels['variant'] = 'callback-mutation'
        recorder = host['LabelingRecorder'](backend, before)
        tools = {'lookup': CustomTool('lookup', 'Synthetic lookup', {'type': 'object', 'additionalProperties': False},
                                      lambda args: {'found': True}, 'v1')} if kind == 'tool' else {}
        runtime = host['build_runtime'](project=project, base_url=provider.url, provider=wire,
                                        accounting=recorder, custom_tools=tools, guards=generic_guards())
        if kind == 'tool':
            agent = replace(host['load_agent'](project), frontmatter={'tools': ['lookup']})
            provider.queue_calls(('one', 'lookup', {})); provider.queue_text('done')
        else:
            agent = ProsaicArtifact('rules', 'subagent', {'tools': []},
                '- ALWAYS answer JSON. <!-- enforce: strict_json(stage=final, on_violation=retry) -->\n')
            provider.queue_text('not JSON'); provider.queue_text('{}')
        result = runtime.turn(agent, message='hello', context=original,
            policy=RunPolicy(allowed_tools=frozenset(tools), max_provider_requests=2, max_tool_calls=1))
        assert result.result.exit_code == 0 and len(provider.requests) == 2
        assert seen == [{'variant': 'original'}] * 2
        assert original.request_metadata == {'variant': 'original'}


def test_saved_context_wins_after_file_reopen_and_new_call(tmp_path, wire):
    from prosaic_harness import Harness, FileRunStore
    from prosaic_runtime import ExecutionContext
    from prosaic_runtime.accounting import MemoryRecorder
    project, host = copied(tmp_path)
    store = FileRunStore(tmp_path/'store', namespace='metadata'); store.initialize()
    try:
        with scripted_provider(wire) as provider:
            backend = MemoryRecorder(provider_id=wire)
            seen = []
            runtime = host['build_runtime'](project=project, base_url=provider.url, provider=wire,
                accounting=host['LabelingRecorder'](backend, lambda labels: seen.append(dict(labels))))
            flow, run_id = host['workflow'](runtime, project=project), uuid4().hex
            provider.queue_text('{"approved":true}'); provider.queue_text('{"approved":true}')
            first = Harness(flow, store=store, run_id=run_id, runtime=runtime, context=context(host))
            state = first.run({'variant': 'untrusted-model-input'})
            assert state['status'] == 'waiting' and len(provider.requests) == 1
            frozen = state['accounting_context']
            store.close(); store = FileRunStore(tmp_path/'store', namespace='metadata'); store.initialize()
            backend.defaults = ExecutionContext(tenant_id='changed', request_metadata={'variant': 'changed'})
            fresh = Harness(flow, store=store, run_id=run_id, runtime=runtime,
                            context=ExecutionContext(request_metadata={'variant': 'new-caller'}))
            final = fresh.resume(choice='approve', expected_revision=fresh.status().revision)
            assert final['status'] == 'completed' and len(provider.requests) == 2
            assert final['accounting_context'] == frozen
            assert seen == [{'run': 'benchmark-42', 'variant': 'PRIVATE_VARIANT'}] * 2
            assert all(i['context']['tenant_id'] == 'trusted-tenant' for i in backend.intents.values())
            assert {i['context']['step_id'] for i in backend.intents.values()} == {'first', 'second'}
    finally: store.close()


def test_saved_receipt_adoption_is_no_call_and_keeps_original_labels(tmp_path, wire):
    from prosaic_harness import Harness, FileRunStore
    from prosaic_runtime import ExecutionContext
    from prosaic_runtime.accounting import MemoryRecorder
    class LostAck(BaseException): pass
    class FaultStore(FileRunStore):
        def save_receipt(self, run_id, invocation_id, receipt, lease):
            super().save_receipt(run_id, invocation_id, receipt, lease)
            if receipt['step'] == 'second': raise LostAck()
    project, host = copied(tmp_path)
    store = FaultStore(tmp_path/'store', namespace='metadata'); store.initialize()
    try:
        with scripted_provider(wire) as provider:
            backend = MemoryRecorder(provider_id=wire)
            runtime = host['build_runtime'](project=project, base_url=provider.url, provider=wire,
                                           accounting=host['LabelingRecorder'](backend))
            flow, run_id = host['workflow'](runtime, project=project), uuid4().hex
            provider.queue_text('{"approved":true}'); provider.queue_text('{"approved":true}')
            original = Harness(flow, store=store, run_id=run_id, runtime=runtime, context=context(host))
            assert original.run({})['status'] == 'waiting'
            with pytest.raises(LostAck): original.resume(choice='approve', expected_revision=original.status().revision)
            store.close(); store = FileRunStore(tmp_path/'store', namespace='metadata'); store.initialize()
            fresh = Harness(flow, store=store, run_id=run_id, runtime=runtime,
                            context=ExecutionContext(request_metadata={'variant': 'replacement'}))
            assert fresh.recovery_evidence()['recoveryStatus'] == 'receiptAvailable'
            state = fresh.resume()
            assert state['status'] == 'completed' and len(provider.requests) == len(backend.intents) == 2
            assert state['accounting_context']['request_metadata']['labels']['variant'] == 'PRIVATE_VARIANT'
    finally: store.close()


@pytest.mark.parametrize('phase', ['prepare', 'observe'])
def test_recorder_failure_stops_without_retry(tmp_path, wire, phase):
    from prosaic_runtime.accounting import AccountingError, MemoryRecorder
    project, host = copied(tmp_path)
    class Broken(MemoryRecorder):
        def prepare(self, intent):
            if phase == 'prepare': raise AccountingError('private')
            return super().prepare(intent)
        def observe(self, call_id, observation): raise AccountingError('private')
    with scripted_provider(wire) as provider:
        runtime = host['build_runtime'](project=project, base_url=provider.url, provider=wire,
                                       accounting=host['LabelingRecorder'](Broken(provider_id=wire)))
        provider.queue_text('done')
        result = host['run_benchmark'](runtime, host['load_agent'](project), context=context(host))
        assert result.metadata['failure_reason'] == 'accounting_failed'
        assert len(provider.requests) == (0 if phase == 'prepare' else 1)


@pytest.mark.parametrize('bad', [{'variant': ''}, {'tenant_id': 'forged'}, {'variant': 'line\nbreak'},
                                {'variant': {'nested': 'value'}}, {'variant': 'é' * 129}])
def test_bad_labels_refuse_before_any_recorder_or_provider_effect(tmp_path, wire, bad):
    from prosaic_runtime import ExecutionContext
    project, host = copied(tmp_path)
    with scripted_provider(wire) as provider:
        with pytest.raises(ValueError): ExecutionContext(request_metadata=bad)
        assert provider.requests == []


def test_copyable_cli_refuses_contact_without_explicit_live_opt_in(tmp_path):
    project, _ = copied(tmp_path)
    result = subprocess.run([sys.executable, str(project/'host.py')], cwd=project,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 2 and '--live' in result.stderr


def test_explicit_cli_uses_configured_provider_accounting_identity(tmp_path, wire):
    import yaml
    project, _ = copied(tmp_path)
    with scripted_provider(wire) as provider:
        config = yaml.safe_load((project/'runtime.yml').read_text())
        config['profiles']['local'].update(base_url=provider.url, provider=wire)
        (project/'runtime.yml').write_text(yaml.safe_dump(config))
        provider.queue_text('done')
        # --live is the example's explicit contact switch; endpoint is owned synthetic loopback.
        result = subprocess.run([sys.executable, str(project/'host.py'), '--live'], cwd=project,
                                capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, result.stderr
        assert 'Prepared variant: baseline' in result.stdout and len(provider.requests) == 1
