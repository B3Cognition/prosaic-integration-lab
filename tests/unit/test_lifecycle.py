import json
import pytest

from lab_runner import stack as module


def test_failed_partial_start_cleans_only_recorded_owned_resources(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    stack = module.OwnedStack()
    stack._record('container', 'owned-container')
    state = {'owned-container': {'Id': 'owned-container', 'Config': {'Labels': {'io.prosaic.lab.owner': stack.owner}}}}
    def engine(_, *args):
        if args[0] == 'inspect':
            if args[1] not in state:
                raise module.EngineError('absent')
            return json.dumps([state[args[1]]])
        if args[0] == 'rm':
            del state[args[-1]]
            return ''
        raise AssertionError('unexpected global engine operation')
    monkeypatch.setattr(module, 'command', engine)
    stack.stop()
    assert state == {}
    assert json.loads((stack.directory / 'ownership.json').read_text())['cleanup'] == 'verified'


def test_replaced_container_is_preserved_and_cleanup_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    stack = module.OwnedStack()
    stack._record('container', 'recorded-id')
    state = {'Id': 'foreign-id', 'Config': {'Labels': {'io.prosaic.lab.owner': 'someone-else'}}}
    def engine(_, *args):
        if args == ('inspect', 'recorded-id'):
            return json.dumps([state])
        raise AssertionError('foreign resource mutation attempted')
    monkeypatch.setattr(module, 'command', engine)
    with pytest.raises(module.EngineError, match='cleanup failed'):
        stack.stop()
    assert state['Id'] == 'foreign-id'
    assert stack.manifest['cleanup'] == 'failed'
