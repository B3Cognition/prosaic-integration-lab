import json
import pytest
from lab_runner import stack

@pytest.mark.parametrize('labels',[{}, {'io.prosaic.lab.release-manifest':'wrong'},
    {'io.prosaic.lab.release-manifest':'247a2b1b1d64b2f4ec318a6b6aec51c28b691fb41018044f8bac571c089d53c7',
     'io.prosaic.lab.candidate-manifest':'3'*64}])
def test_released_stack_rejects_unverified_or_retagged_candidate_before_resource_allocation(monkeypatch,tmp_path,labels):
    monkeypatch.setattr(stack,'ROOT',tmp_path)
    dependencies=tmp_path/'dependencies'; dependencies.mkdir()
    source=__import__('pathlib').Path(__file__).resolve().parents[2]/'dependencies/releases.json'
    (dependencies/'releases.json').write_bytes(source.read_bytes())
    (dependencies/'images.json').write_text('{"postgres16":"fixture-image"}')
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
