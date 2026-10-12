"""Session fault fixtures reuse exact-owned workers and the real SQL relay."""
from contextlib import contextmanager
import json
from copy import deepcopy

from .native_faults import owned_stack,start_proxy
from .native_scenarios import replace_worker
from .stack import command


def kill_worker(lab,name='a'):
    stack=owned_stack(lab)
    identifier=stack.manifest.get('replica_ids',{}).get(name)
    if identifier is None or {'kind':'container','id':identifier} not in stack.manifest.get('resources',[]):
        raise ValueError('verified owned conversation worker required')
    command(stack.engine,'kill',identifier)


@contextmanager
def restore_workers_after_loss(lab,*names):
    """A failed assertion must not leave the next owned case with a dead worker."""
    try:yield
    finally:
        for name in names:replace_worker(lab,name)


@contextmanager
def temporary_conversation_configuration(lab,transform):
    """Use the owned container binding, restoring its exact secret file and B."""
    stack=owned_stack(lab)
    source=stack.secrets/'service.json'
    raw=source.read_text();original=json.loads(raw)
    if type(original.get('conversation')) is not dict or not callable(transform):
        raise ValueError('owned conversation configuration required')
    changed=transform(deepcopy(original['conversation']))
    if type(changed) is not dict:raise ValueError('owned conversation configuration required')
    try:
        replace_worker(lab,'b',config_patch={'conversation':changed})
        yield changed
    finally:
        try:replace_worker(lab,'b',config_patch={'conversation':original['conversation']})
        finally:source.write_text(raw);source.chmod(0o600)


@contextmanager
def partition_session_worker_a(lab):
    """Only A's loaded session-store route changes; original delivery is restored."""
    proxy=start_proxy(lab)
    stack=owned_stack(lab)
    source=stack.secrets/'service.json'
    original=json.loads(source.read_text())
    if type(original.get('conversation')) is not dict or 'dsn' not in original['conversation']:
        raise ValueError('owned conversation store binding required')
    try:
        settings={**original['conversation'],'dsn':proxy.harness_dsn(original['conversation']['dsn'])}
        replace_worker(lab,'a',config_patch={'conversation':settings})
    finally:
        source.write_text(json.dumps(original));source.chmod(0o600)
        command(stack.engine,'start','-a',stack.manifest['runtime_config_job'])
    try:yield proxy
    finally:proxy.control(False)
