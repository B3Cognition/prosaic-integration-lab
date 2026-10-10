import json
import pytest

from lab_runner import stack as module


def test_failed_partial_start_cleans_only_recorded_owned_resources(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    stack = module.OwnedStack()
    stack._record('container', 'owned-container')
    state = {'owned-container': {'Id': 'owned-container', 'Config': {'Labels': {'io.prosaic.lab.owner': stack.owner}}}}
    def engine(_, *args):
        if args[0] == 'ps':
            return '\n'.join(state)
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
        if args[0] == 'ps':
            return 'recorded-id'
        if args == ('inspect', 'recorded-id'):
            return json.dumps([state])
        raise AssertionError('foreign resource mutation attempted')
    monkeypatch.setattr(module, 'command', engine)
    with pytest.raises(module.EngineError, match='cleanup failed'):
        stack.stop()
    assert state['Id'] == 'foreign-id'
    assert stack.manifest['cleanup'] == 'failed'


def test_cleanup_reads_child_recorded_replacements_before_removing_dependencies(tmp_path,monkeypatch):
    monkeypatch.setattr(module,'ROOT',tmp_path)
    stack=module.OwnedStack()
    for kind,identifier in [('network','network'),('volume','volume'),('container','old')]:
        stack._record(kind,identifier)
    child=object.__new__(module.OwnedStack)
    child.directory=stack.directory;child.manifest=json.loads((stack.directory/'ownership.json').read_text())
    child._record('container','fresh')
    state={'network':'network','volume':'volume','old':'container','fresh':'container','foreign':'container'}
    removed=[]
    def engine(_,*args):
        kind='container' if args[0] in {'ps','inspect','rm'} else args[0]
        if args[0]=='ps' or args[1:2]==('ls',):
            return '\n'.join(identifier for identifier,value in state.items() if value==kind)
        if args[0]=='inspect' or args[1:2]==('inspect',):
            identifier=args[-1]
            return json.dumps([{'Id':identifier,'Labels':{'io.prosaic.lab.owner':stack.owner}}])
        if args[0]=='rm' or args[1:2]==('rm',):
            identifier=args[-1]
            assert identifier!='foreign'
            if kind!='container' and any(identifier in state for identifier in ('old','fresh')):
                raise module.EngineError('owned dependencies remain attached')
            removed.append(identifier);del state[identifier];return ''
        raise AssertionError('unexpected engine operation')
    monkeypatch.setattr(module,'command',engine)
    stack.stop()
    assert removed==['fresh','old','volume','network'] and state=={'foreign':'container'}
    durable=json.loads((stack.directory/'ownership.json').read_text())
    assert durable['cleanup']=='verified' and {'kind':'container','id':'fresh'} in durable['resources']


@pytest.mark.parametrize('change',['owner','engine','omitted','invalid'])
def test_cleanup_rejects_changed_durable_authority_before_engine_mutation(tmp_path,monkeypatch,change):
    monkeypatch.setattr(module,'ROOT',tmp_path)
    stack=module.OwnedStack();stack._record('container','owned')
    path=stack.directory/'ownership.json';durable=json.loads(path.read_text())
    if change=='owner':durable['owner']='foreign'
    elif change=='engine':durable['engine']='podman'
    elif change=='omitted':durable['resources']=[]
    else:durable['resources'].append({'kind':'arbitrary','id':'private'})
    path.write_text(json.dumps(durable));original=path.read_bytes()
    def engine(*args):raise AssertionError('unvalidated authority reached engine')
    monkeypatch.setattr(module,'command',engine)
    with pytest.raises((ValueError,module.EngineError)):stack.stop()
    assert path.read_bytes()==original
