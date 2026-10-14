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
        ('b3-prosaic', '0.4.1', '6ac6cfdfd47dc70ecf68e441aa004f07c3be3822',
         '07710a5b9c94e3f3877241a4f5138d9b777d724098eb8e24b9738fb3cea28c51'),
        ('b3-prosaic-runtime', '0.9.4', '5f0a02b923173286debd8c2c01951aba35d84377',
         'f2f88630933217cda791792d3a3341a36485690bbb39b81890a8f22ef2c4bde3'),
        ('b3-prosaic-runtime-postgres', '0.3.0', 'a59621c5f30d766d1217b37df777d3876075dc34',
         '5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca'),
        ('b3-prosaic-harness', '0.9.0', '1db61abf1b648affe1d67a5069f15ce9c9b4c9d3',
         '6c9d2c2bcfcb6ac5720547db492d64526074431fa639ec2e030f88b2a633309c'),
        ('b3-prosaic-harness-postgres', '0.4.0', '1db61abf1b648affe1d67a5069f15ce9c9b4c9d3',
         '35b6b9c4493b13187eed070403a45abe1f47522e5e0fd563b4514b492bd1703a'),
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
