import json
import pytest
from lab_runner import stack


@pytest.mark.parametrize('labels', [None, {}, {'io.prosaic.lab.candidate-manifest':'wrong'}])
def test_unverified_candidate_is_rejected_before_engine_mutation(tmp_path, monkeypatch, labels):
    monkeypatch.setattr(stack,'ROOT',tmp_path)
    (tmp_path/'dependencies').mkdir()
    (tmp_path/'dependencies/accounting-candidate.json').write_text('{}')
    def engine_command(engine,*args):
        if args == ('info',): return ''
        if args == ('image','inspect','prosaic-integration-lab:candidate'):
            return json.dumps([{'Id':'candidate','Config':{'Labels':labels}}])
        pytest.fail('unverified candidate reached an engine mutation')
    monkeypatch.setattr(stack,'command',engine_command)
    fixture = stack.OwnedStack(candidate=True)
    with pytest.raises(stack.EngineError,match='provenance'):
        fixture.start()
    assert fixture.manifest['resources'] == []
    assert not fixture.manifest.get('pending_resources')
