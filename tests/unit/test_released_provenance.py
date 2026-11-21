import json
import pytest
from lab_runner import stack
from pathlib import Path
import hashlib


def test_active_manifest_selects_only_the_verified_sandbox_sdk_family():
    from prosaic_integration_lab.dependencies import sdk_manifest
    manifest = Path(__file__).resolve().parents[2] / 'dependencies/releases.json'
    data = sdk_manifest(manifest)
    assert {(item['distribution'], item['version'], item['source_commit'], item['sha256'])
            for item in data['artifacts']} == {
        ('b3-prosaic', '0.5.1', '921d828ea6bdafee46380212fc16f41d1f3faabc',
         'c7f7a3292952d70513da485bd87360e0bf94a3cc50d49b3deadb85a0e7d29a76'),
        ('b3-prosaic-runtime', '0.9.27', '9b7a285acd50a18a992c5ebb6bef409cb5a40345',
         '7889545eeaef8a92e08fc5669d07b72c33fdea7c191158a0d150e9798a0bf5df'),
        ('b3-prosaic-runtime-postgres', '0.3.0', 'a59621c5f30d766d1217b37df777d3876075dc34',
         '5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca'),
        ('b3-prosaic-harness', '0.9.20', '432ab7b45dc6ae16704c48652aa3dbcb99c08158',
         'cc6fb7275ee491a07499c7ebaec12f98341c0477fd5940f468a8a5180301358d'),
        ('b3-prosaic-harness-postgres', '0.4.5', '5cf6b08e3f181bfb368b24afbe1eadf9911b4504',
         '6a64d3276850582fbf24d6a6698d83bd0adb861bd9189f096733a3f1d28b03cc'),
    }


def test_active_manifest_preserves_all_required_stack_modes():
    from lab_runner.gates import (ALL_COUNTS, expected_test_count, required_modes,
                                 supports_consumer_blueprints, supports_context_assembly)
    from prosaic_integration_lab.dependencies import sdk_manifest

    manifest = sdk_manifest(Path(__file__).resolve().parents[2] / 'dependencies/releases.json')
    modes = required_modes(candidate=False, manifest=manifest)
    assert modes == tuple(ALL_COUNTS)
    assert supports_consumer_blueprints(manifest) and supports_context_assembly(manifest)
    assert sum(expected_test_count(mode, context_assembly=True) for mode in modes) == 450

    runtime = next(item for item in manifest['artifacts'] if item['distribution'] == 'b3-prosaic-runtime')
    runtime['sha256'] = '0' * 64
    with pytest.raises(ValueError):
        required_modes(candidate=False, manifest=manifest)


@pytest.mark.parametrize('labels',[{}, {'io.prosaic.lab.release-manifest':'wrong'},
    {'io.prosaic.lab.candidate-manifest':'3'*64}])
def test_released_stack_rejects_unverified_or_retagged_candidate_before_resource_allocation(monkeypatch,tmp_path,labels):
    monkeypatch.setattr(stack,'ROOT',tmp_path)
    dependencies=tmp_path/'dependencies'; dependencies.mkdir()
    source=__import__('pathlib').Path(__file__).resolve().parents[2]/'dependencies/releases.json'
    (dependencies/'releases.json').write_bytes(source.read_bytes())
    (dependencies/'images.json').write_text('{"postgres16":"fixture-image"}')
    if 'io.prosaic.lab.candidate-manifest' in labels:
        # Model an actually retagged candidate: every released label matches,
        # while the retained candidate label must still prevent allocation.
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        labels={**labels,'io.prosaic.lab.release-manifest':digest,
            'io.prosaic.lab.sdk-manifest':digest,'io.prosaic.lab.dependency-mode':'released'}
    fixture=stack.OwnedStack()
    mutations=[]
    def command(engine,*args):
        if args == ('info',): return ''
        if args == ('image','inspect','prosaic-integration-lab:dev'):
            return json.dumps([{'Id':'sha256:'+'1'*64,'Config':{'Labels':labels}}])
        mutations.append(args)
        raise AssertionError('unverified image must fail before mutations')
    monkeypatch.setattr(stack,'command',command)
    with pytest.raises(stack.EngineError,match='provenance'): fixture.start()
    assert mutations == [] and fixture.manifest['resources'] == []


def test_candidate_from_fresh_base_audits_selected_snapshot(monkeypatch, tmp_path):
    monkeypatch.setattr(stack, 'ROOT', tmp_path)
    dependencies = tmp_path / 'dependencies'; dependencies.mkdir()
    source = Path(__file__).resolve().parents[2] / 'dependencies/accounting-candidate.json'
    (dependencies / 'accounting-candidate.json').write_bytes(source.read_bytes())
    (dependencies / 'releases.json').write_bytes((Path(__file__).resolve().parents[2]/'dependencies/releases.json').read_bytes())
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    fixture = stack.OwnedStack(candidate=True)
    calls = []
    class AuditReached(Exception): pass
    def command(engine, *args):
        if args == ('info',): return ''
        if args == ('image', 'inspect', 'prosaic-integration-lab:candidate'):
            return json.dumps([{'Id': 'sha256:' + '1' * 64, 'Config': {'Labels': {
                'io.prosaic.lab.candidate-manifest': digest,
                'io.prosaic.lab.sdk-manifest': digest,
                'io.prosaic.lab.dependency-mode': 'candidate'}}}])
        raise AssertionError('must audit before engine mutations')
    monkeypatch.setattr(stack, 'command', command)
    def create(kind, name, *args):
        calls.append(args)
        raise AuditReached
    monkeypatch.setattr(fixture, '_create', create)
    with pytest.raises(AuditReached): fixture.start()
    argv = calls[0]
    assert argv[-3:] == ('dependencies/releases.json', '/srv/wheels', digest)
