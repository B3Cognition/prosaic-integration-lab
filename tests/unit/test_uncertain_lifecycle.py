import json
import pytest
from lab_runner import stack as module


@pytest.mark.parametrize('resource_name', ['/owned-name', '/renamed-by-operator'])
def test_created_resource_with_lost_ack_is_reconciled_before_cleanup(tmp_path, monkeypatch, resource_name):
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    stack = module.OwnedStack()
    state = {}
    def engine(_, *args):
        if args[0] == 'create':
            state['actual-id'] = {'Id': 'actual-id', 'Name': resource_name,
                'Config': {'Labels': {'io.prosaic.lab.owner': stack.owner, 'io.prosaic.lab.resource': 'owned-name'}}}
            raise module.EngineError('lost create acknowledgement')
        if args[0] == 'ps':
            return '\n'.join(state)
        if args[0] == 'inspect':
            return json.dumps([state[args[1]]])
        if args[0] == 'rm':
            del state[args[-1]]
            return ''
        raise AssertionError('unexpected engine operation')
    monkeypatch.setattr(module, 'command', engine)
    with pytest.raises(module.EngineError):
        stack._create('container', 'owned-name', 'create', '--name', 'owned-name', 'image')
    stack.stop()
    assert state == {}, 'an acknowledged cleanup must not leave an owned resource'


def test_unknown_engine_state_after_removal_is_not_verified_absence(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    stack = module.OwnedStack()
    stack._record('container', 'owned-id')
    removed = False
    def engine(_, *args):
        nonlocal removed
        if args[0] == 'rm':
            removed = True
            return ''
        if removed:
            raise module.EngineError('daemon unavailable, absence unknown')
        if args[0] == 'ps':
            return 'owned-id'
        return json.dumps([{'Id': 'owned-id', 'Config': {'Labels': {'io.prosaic.lab.owner': stack.owner}}}])
    monkeypatch.setattr(module, 'command', engine)
    with pytest.raises(module.EngineError, match='cleanup failed'):
        stack.stop()
    assert stack.manifest['cleanup'] == 'failed'


def test_unresolved_creation_intent_is_retained_not_certified_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    stack = module.OwnedStack()
    def engine(_, *args):
        if args[0] == 'create':
            raise module.EngineError('operation outcome unknown')
        if args[0] == 'ps':
            return ''
        raise AssertionError('unexpected operation')
    monkeypatch.setattr(module, 'command', engine)
    with pytest.raises(module.EngineError):
        stack._create('container', 'pending-name', 'create', '--name', 'pending-name', 'image')
    with pytest.raises(module.EngineError, match='cleanup failed'):
        stack.stop()
    assert stack.manifest['pending_resources'] == [{'kind': 'container', 'name': 'pending-name'}]
