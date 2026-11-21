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


def test_image_publication_qualifies_native_builds_and_fresh_registry_pulls():
    from pathlib import Path
    import yaml

    root = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load((root / '.github/workflows/publish-linux-images.yml').read_bytes())
    assert set(workflow[True]) == {'workflow_dispatch'}
    assert workflow['permissions'] == {'contents': 'read'}
    build, index, verify = (workflow['jobs'][name] for name in ('build', 'index', 'verify'))
    assert build['if'] == "github.ref == 'refs/heads/main' && github.repository == 'B3Cognition/prosaic-integration-lab'"
    assert index['needs'] == 'build' and verify['needs'] == 'index'
    assert build['strategy']['matrix'] == verify['strategy']['matrix']
    assert {entry['architecture'] for entry in build['strategy']['matrix']['include']} == {'amd64', 'arm64'}
    assert verify['permissions']['packages'] == 'read'
    for job, operation in ((build, 'docker push'), (verify, 'docker pull')):
        steps = job['steps']
        image = next(step for step in steps if step.get('id') == 'image')
        witness = next(step for step in steps if step.get('name') == 'Qualify default CLI confinement')
        assert steps.index(image) < steps.index(witness)
        assert 'scripts/qualify_cli_sandbox_image.py' in witness['run']
        assert '--explicit-required' not in witness['run']
        assert 'steps.image.outputs.id' in witness['env']['IMAGE_ID']
        operators = [step for step in steps if operation in step.get('run', '')]
        assert len(operators) == 1
        assert (steps.index(operators[0]) > steps.index(witness)) == (job is build)
        assert any("always()" in step.get('if', '') and 'apparmor_parser -R' in step.get('run', '')
                   for step in steps)
