import json
import pytest
from lab_runner import stack
from pathlib import Path
import hashlib


def test_active_manifest_selects_only_the_verified_patch_sdk_family():
    from prosaic_integration_lab.dependencies import sdk_manifest
    manifest = Path(__file__).resolve().parents[2] / 'dependencies/releases.json'
    data = sdk_manifest(manifest)
    assert {(item['distribution'], item['version'], item['source_commit'], item['sha256'])
            for item in data['artifacts']} == {
        ('b3-prosaic', '0.4.1', '6ac6cfdfd47dc70ecf68e441aa004f07c3be3822',
         '07710a5b9c94e3f3877241a4f5138d9b777d724098eb8e24b9738fb3cea28c51'),
        ('b3-prosaic-runtime', '0.8.1', '3566731c39a3fff2837acd93a96baa2187764206',
         '3f74da0c7598c9e13f05de6b9080d6f1058bed3e1ca7ba0f960201bd34d3a1ae'),
        ('b3-prosaic-runtime-postgres', '0.2.1', '3566731c39a3fff2837acd93a96baa2187764206',
         'f06e6e3d95ad5c182b9b3d5329b6cff0b3e7be997168d2bed59fa37741f32a30'),
        ('b3-prosaic-harness', '0.7.1', 'cba77d09d1844ff624911295aecd58021b457c08',
         '7cb170ad52f9170221360f2d0eac868c667d9e531dd39236db0bf46987c18db2'),
        ('b3-prosaic-harness-postgres', '0.2.1', 'cba77d09d1844ff624911295aecd58021b457c08',
         'e7dfcdd04ab1105be99ed8cc26e569d3b39d962046c6dbd3d885e641f75f1008'),
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
