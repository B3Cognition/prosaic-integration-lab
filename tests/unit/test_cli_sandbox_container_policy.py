import pytest

from scripts import qualify_cli_sandbox_image as policy


def test_proc_policy_retains_default_protections_and_opens_one_sysctl():
    defaults = ['/proc/bus', '/proc/sys', '/proc/sysrq-trigger']
    inventory = ['/proc/sys/new-family', '/proc/sys/net',
                 '/proc/sys/user/max_pid_namespaces', '/proc/sys/user/max_user_namespaces']

    assert policy.readonly_paths(defaults, inventory) == [
        '/proc/bus', '/proc/sysrq-trigger', '/proc/sys/net',
        '/proc/sys/new-family', '/proc/sys/user/max_pid_namespaces',
    ]
    with pytest.raises(ValueError, match='incomplete proc inventory'):
        policy.readonly_paths(defaults, inventory[:-1])
    with pytest.raises(ValueError, match='invalid proc path'):
        policy.readonly_paths(defaults, [*inventory, '/proc/sys/../kcore'])


def test_seccomp_keeps_default_denials_and_limits_namespace_flags():
    baseline = {'defaultAction': 'SCMP_ACT_ERRNO',
                'syscalls': [{'names': ['read'], 'action': 'SCMP_ACT_ALLOW'}]}
    result = policy.extend_seccomp(baseline)

    assert result['defaultAction'] == 'SCMP_ACT_ERRNO'
    assert baseline['syscalls'] == [{'names': ['read'], 'action': 'SCMP_ACT_ALLOW'}]
    rules = result['syscalls'][1:]
    assert {name for rule in rules for name in rule['names']} == {
        'clone', 'unshare', 'mount', 'umount2', 'pivot_root',
    }
    assert next(rule['args'] for rule in rules if rule['names'] == ['clone']) == [
        {'index': 0, 'value': 0x7c020011, 'op': 'SCMP_CMP_EQ'},
    ]
    assert next(rule['args'] for rule in rules if rule['names'] == ['unshare']) == [
        {'index': 0, 'value': 0x10000000, 'op': 'SCMP_CMP_EQ'},
    ]
    assert all(rule.get('args') for rule in rules if rule['names'] != ['pivot_root'])
