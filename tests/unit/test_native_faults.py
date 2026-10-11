"""Owned SQL fixture resources enter the same durable cleanup inventory."""
import json
from pathlib import Path

import pytest


def fixture_manifest(tmp_path):
    owner = '1' * 32
    manifest = {'owner': owner, 'engine': 'docker', 'payload_audit': 'verified',
        'database_id': 'database-id', 'network_id': 'network-id',
        'images': {'consumer': 'sha256:' + '2' * 64},
        'resources': [{'kind': 'network', 'id': 'network-id'}, {'kind': 'container', 'id': 'database-id'},
                      {'kind': 'container', 'id': 'a-id'}, {'kind': 'container', 'id': 'b-id'}],
        'replica_ids': {'a': 'a-id', 'b': 'b-id'}, 'endpoints': {}}
    path = tmp_path / 'ownership.json'
    path.write_text(json.dumps(manifest))
    return {'fixture_manifest': str(path)}, manifest


def test_owned_proxy_records_creation_before_engine_mutation(tmp_path, monkeypatch):
    from lab_runner.native_faults import start_proxy
    from lab_runner import stack
    lab, manifest = fixture_manifest(tmp_path)
    path = Path(lab['fixture_manifest'])
    observed = []
    def engine(_, *args):
        if args[0] == 'run':
            current = json.loads(path.read_text())
            assert current['pending_resources'] == [{'kind': 'container', 'name': 'prosaic-lab-' + manifest['owner'] + '-sql-fault'}]
            observed.append(args)
            return 'proxy-id'
        assert args[0] == 'inspect' or args[:2] == ('network', 'inspect')
        return json.dumps([{'Id': args[-1], 'Config': {'Labels': {'io.prosaic.lab.owner': manifest['owner']}},
            'NetworkSettings': {'Ports': {'8001/tcp': [{'HostPort': '18001'}]}}}])
    monkeypatch.setattr(stack, 'command', engine)
    class Response:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {'blocked': False, 'active': 0}
    monkeypatch.setattr('httpx.get', lambda *args, **kwargs: Response())
    proxy = start_proxy(lab)
    current = json.loads(path.read_text())
    assert {'kind': 'container', 'id': 'proxy-id'} in current['resources']
    assert current['pending_resources'] == []
    assert current['fault_proxy_id'] == 'proxy-id'
    assert proxy.control_url == 'http://127.0.0.1:18001'
    run = observed[0]
    assert '127.0.0.1::8001' in run
    assert manifest['images']['consumer'] in run
    assert run[-3:] == ('python', '-m', 'lab_runner.fault_proxy')
    assert '--read-only' in run and '--cap-drop' in run


def test_foreign_database_is_rejected_before_proxy_creation(tmp_path, monkeypatch):
    from lab_runner.native_faults import start_proxy
    from lab_runner import stack
    lab, manifest = fixture_manifest(tmp_path)
    def engine(_, *args):
        assert args[0] == 'inspect'
        return json.dumps([{'Id': args[1], 'Labels': {'io.prosaic.lab.owner': 'foreign'}}])
    monkeypatch.setattr(stack, 'command', engine)
    with pytest.raises(ValueError, match='ownership'):start_proxy(lab)
    assert json.loads(Path(lab['fixture_manifest']).read_text()) == manifest


def test_proxy_route_preserves_every_other_dsn_field():
    from lab_runner.native_faults import ProxyFixture
    from psycopg.conninfo import conninfo_to_dict
    proxy = ProxyFixture('proxy-id', 'http://127.0.0.1:8001', 'owned-sql-fault')
    original = "host=database port=5432 dbname=lab user=harness_runtime password='synthetic secret' sslmode=disable"
    changed = conninfo_to_dict(proxy.harness_dsn(original))
    assert changed == {'host': 'owned-sql-fault', 'port': '5433', 'dbname': 'lab',
        'user': 'harness_runtime', 'password': 'synthetic secret', 'sslmode': 'disable'}


def test_proxy_rejects_foreign_network_before_connecting_container(tmp_path, monkeypatch):
    from lab_runner.native_faults import start_proxy
    from lab_runner import stack
    lab, manifest = fixture_manifest(tmp_path)
    def engine(_, *args):
        if args[0] == 'run':raise AssertionError('proxy attached before network ownership validation')
        foreign = args[:2] == ('network', 'inspect')
        return json.dumps([{'Id': args[-1], 'Labels': {'io.prosaic.lab.owner':
            'foreign' if foreign else manifest['owner']}}])
    monkeypatch.setattr(stack, 'command', engine)
    with pytest.raises(ValueError, match='ownership'):start_proxy(lab)
    assert json.loads(Path(lab['fixture_manifest']).read_text()) == manifest
