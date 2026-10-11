"""Exact-owned native fault resources; only A's Harness SQL route is replaced."""
from contextlib import contextmanager
from dataclasses import dataclass
import json
from pathlib import Path
import time

import httpx

from . import stack as stack_module
from .manifest import validate_resource


@dataclass(frozen=True)
class ProxyFixture:
    identifier: str
    control_url: str
    alias: str

    def harness_dsn(self, original):
        from psycopg.conninfo import conninfo_to_dict,make_conninfo
        fields=conninfo_to_dict(original)
        fields.update(host=self.alias,port='5433')
        return make_conninfo(**fields)

    def control(self, blocked):
        response=httpx.post(self.control_url+'/control',json={'blocked':blocked},timeout=5)
        response.raise_for_status()
        return response.json()

    def stats(self):
        response=httpx.get(self.control_url+'/stats',timeout=5)
        response.raise_for_status()
        return response.json()


def owned_stack(lab):
    path=Path(lab['fixture_manifest'])
    manifest=json.loads(path.read_text())
    stack=object.__new__(stack_module.OwnedStack)
    stack.owner=manifest['owner'];stack.engine=manifest['engine'];stack.manifest=manifest
    stack.directory=path.parent;stack.secrets=stack.directory/'secrets'
    stack.verify_owned()
    network=manifest['network_id']
    if {'kind':'network','id':network} not in manifest['resources']:
        raise ValueError('unrecorded owned network')
    validate_resource(json.loads(stack_module.command(stack.engine,'network','inspect',network))[0],
                      network,stack.owner)
    return stack


def start_proxy(lab):
    stack=owned_stack(lab)
    alias='sql-fault-'+stack.owner
    name='prosaic-lab-'+stack.owner+'-sql-fault'
    if stack.manifest.get('fault_proxy_id'):
        # An explicit later fixture invocation creates another owned resource;
        # uncertain _create outcomes remain governed by its durable intentions.
        suffix='-'+str(time.monotonic_ns());alias+=suffix;name+=suffix
    identifier=stack._create('container',name,'run','-d','--name',name,'--label',
        'io.prosaic.lab.owner='+stack.owner,'--network',stack.manifest['network_id'],
        '--network-alias',alias,'--user','10001:10001','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--memory','128m','--cpus','1','--pids-limit','64',
        '--tmpfs','/tmp:rw,noexec,nosuid,size=16m,mode=1777',
        '-p','127.0.0.1::8001',stack.manifest['images']['consumer'],
        'python','-m','lab_runner.fault_proxy')
    state=json.loads(stack_module.command(stack.engine,'inspect',identifier))[0]
    port=state['NetworkSettings']['Ports']['8001/tcp'][0]['HostPort']
    proxy=ProxyFixture(identifier,'http://127.0.0.1:'+port,alias)
    stack.manifest['fault_proxy_id']=identifier
    stack.manifest['endpoints']['sql_fault']=proxy.control_url
    stack._save()
    deadline=time.monotonic()+15
    while True:
        try:
            if proxy.stats()['blocked'] is False:return proxy
        except httpx.HTTPError:pass
        if time.monotonic()>=deadline:raise stack_module.EngineError('SQL proxy readiness timeout')
        time.sleep(.05)


@contextmanager
def partition_worker_a(lab):
    """Load A through the relay, then restore the default delivered config.

    B already loaded the original direct route. All app/accounting connections
    stay direct. A retains its loaded route through partition and recovery.
    """
    from .native_scenarios import replace_worker
    proxy=start_proxy(lab)
    stack=owned_stack(lab)
    source=stack.secrets/'service.json'
    original=json.loads(source.read_text())
    try:
        replace_worker(lab,'a',config_patch={'harness_dsn':proxy.harness_dsn(original['harness_dsn'])})
    finally:
        source.write_text(json.dumps(original));source.chmod(0o600)
        stack_module.command(stack.engine,'start','-a',stack.manifest['runtime_config_job'])
    try:yield proxy
    finally:proxy.control(False)
