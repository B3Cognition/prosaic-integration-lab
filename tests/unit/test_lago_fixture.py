import pytest
from lab_runner.lago import start
from lab_runner.stack import choose_subnet


def test_fixture_failure_uses_existing_owned_manifest():
    class Stack:
        owner = 'a'*32
        manifest = {'images':{},'network_id':'network','endpoints':{}}
        def _secret(self,name,content): return '/fixture/private/'+name
        def _save(self): pass
        def _create(self,kind,name,*args):
            if kind == 'volume': return 'owned-volume'
            assert '--env-file' in args
            assert '127.0.0.1::3000' in args
            assert '--label' in args
            assert 'owned-volume:/data' in args
            raise RuntimeError('owned create failed')
    with pytest.raises(RuntimeError,match='owned create failed'):
        start(Stack(),pull=False)


def test_owned_subnet_selection_avoids_existing_network_ranges():
    existing = [{'IPAM':{'Config':None}}, {'IPAM':{'Config':[{'Subnet':'10.250.0.0/25'},{'Subnet':'10.250.1.0/24'}]}}]
    assert choose_subnet(existing,'00'*16) == '10.250.2.0/24'
    with pytest.raises(ValueError):
        choose_subnet([{'IPAM':{'Config':[{'Subnet':'10.250.0.0/16'}]}}],'00'*16)


def test_subnet_selection_understands_podman_inventory():
    assert choose_subnet([{'subnets':[{'subnet':'10.250.0.0/24'}]}],'00'*16) == '10.250.1.0/24'


def test_network_inventory_retries_only_confirmed_disappearance(monkeypatch):
    from lab_runner.stack import OwnedStack, EngineError
    stack = object.__new__(OwnedStack)
    stack.engine = 'docker'
    inventories = iter([['gone','retained'], ['retained'], ['retained']])
    monkeypatch.setattr(stack, '_ids', lambda kind: next(inventories))
    calls = []
    def inspect(engine,*args):
        calls.append(args)
        if 'gone' in args: raise EngineError('network disappeared')
        return '[{"Id":"retained"}]'
    monkeypatch.setattr('lab_runner.stack.command',inspect)
    assert stack.network_inventory() == [{'Id':'retained'}]
    assert len(calls) == 2
    monkeypatch.setattr(stack,'_ids',lambda kind:['retained'])
    def fail(*args): raise EngineError('stable engine failure')
    monkeypatch.setattr('lab_runner.stack.command',fail)
    with pytest.raises(EngineError,match='stable engine failure'):
        stack.network_inventory()
