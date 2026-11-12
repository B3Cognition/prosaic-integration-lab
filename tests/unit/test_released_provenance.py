import json
import pytest
from lab_runner import stack
from pathlib import Path
import hashlib


def test_active_manifest_selects_only_the_verified_conversation_sdk_family():
    from prosaic_integration_lab.dependencies import sdk_manifest
    manifest = Path(__file__).resolve().parents[2] / 'dependencies/releases.json'
    data = sdk_manifest(manifest)
    assert {(item['distribution'], item['version'], item['source_commit'], item['sha256'])
            for item in data['artifacts']} == {
        ('b3-prosaic', '0.5.0', '67b3807281ed0cdfd345fff84c56b236ec82cfb1',
         'e858a853595746c6930fbe062e84bd8ece1a366aa3b126f2fe11bfb7cb2ceb81'),
        ('b3-prosaic-runtime', '0.9.23', '48c10ac9aeb18bd06f53015df0624b35d5254646',
         '5caab59f6d0ffd14299ee0840dd5f9b58b4e4f4a1b724ff6e3e2fa1699f08fd8'),
        ('b3-prosaic-runtime-postgres', '0.3.0', 'a59621c5f30d766d1217b37df777d3876075dc34',
         '5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca'),
        ('b3-prosaic-harness', '0.9.17', '5cf6b08e3f181bfb368b24afbe1eadf9911b4504',
         'c65c932798cc7e52e7e9659e43e72cc5f2e48feee9b889b5593e80e9e241c0fb'),
        ('b3-prosaic-harness-postgres', '0.4.5', '5cf6b08e3f181bfb368b24afbe1eadf9911b4504',
         '6a64d3276850582fbf24d6a6698d83bd0adb861bd9189f096733a3f1d28b03cc'),
    }


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
