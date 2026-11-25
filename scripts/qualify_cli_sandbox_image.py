"""Run the Linux image witness with the reviewed Docker deployment policy."""
import argparse
from contextlib import contextmanager
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid


PROFILE = 'prosaic-lab-cli-sandbox'
SECCOMP_COMMIT = 'a0fa70805f742f7da15b367770d802ea2a86c68b'
SECCOMP_SHA256 = '3320527d4568265ac97a077609b1bfd4cfd0d789eeb9239b7e094b1526675406'
SECCOMP_URL = f'https://raw.githubusercontent.com/moby/profiles/{SECCOMP_COMMIT}/seccomp/default.json'
USERNS_LIMIT = '/proc/sys/user/max_user_namespaces'
OWNER_LABEL = 'io.prosaic.lab.cli-sandbox-qualification'
TMPFS = '/tmp:rw,noexec,nosuid,size=64m,mode=1777'
PROC_INVENTORY = """import json
from pathlib import Path
root = Path('/proc/sys')
paths = [p for p in root.iterdir() if p.name != 'user']
paths += list((root / 'user').iterdir())
print(json.dumps([str(p) for p in paths]))
"""


def readonly_paths(defaults, inventory):
    if '/proc/sys' not in defaults or USERNS_LIMIT not in inventory:
        raise ValueError('incomplete proc inventory')
    for path in inventory:
        if not isinstance(path, str) or not re.fullmatch(
                r'/proc/sys/(?:user/)?[A-Za-z0-9_][A-Za-z0-9_-]*', path) or path == '/proc/sys/user':
            raise ValueError('invalid proc path')
    return [path for path in defaults if path != '/proc/sys'] + sorted(set(inventory) - {USERNS_LIMIT})


def allow_call(name, index=None, value=None, *, mask=None):
    rule = {'names': [name], 'action': 'SCMP_ACT_ALLOW'}
    if mask is not None:
        rule['args'] = [{'index': index, 'value': mask, 'valueTwo': value, 'op': 'SCMP_CMP_MASKED_EQ'}]
    elif index is not None:
        rule['args'] = [{'index': index, 'value': value, 'op': 'SCMP_CMP_EQ'}]
    return rule


def extend_seccomp(baseline):
    # Bubblewrap 0.12.0 uses clone's first argument for flags on AMD64 and ARM64.
    # Keep clone3, setns and the new mount API subject to the unmodified baseline.
    mount_flags = (
        0x6,          # MS_NOSUID | MS_NODEV (tmpfs)
        0x8c000,      # MS_SLAVE | MS_REC | MS_SILENT
        0x4c000,      # MS_PRIVATE | MS_REC | MS_SILENT
        0x9000,       # MS_BIND | MS_SILENT
        0xd000,       # MS_BIND | MS_REC | MS_SILENT
        0xc0edd000,   # MS_MGC_VAL | MS_BIND | MS_REC | MS_SILENT
    )
    # Remounts retain the source's ro, nodev, noexec and atime bits.
    retained_mount_bits = 1 | 4 | 8 | 1024 | 2048 | (1 << 21)
    rules = [
        allow_call('clone', 0, 0x7c020011),  # User, mount, PID, network, IPC and UTS; SIGCHLD.
        allow_call('unshare', 0, 0x10000000),  # Second user namespace for --disable-userns.
        allow_call('pivot_root'),
        allow_call('umount2', 1, 2),  # MNT_DETACH.
        *(allow_call('mount', 3, flags) for flags in mount_flags),
        allow_call('mount', 3, 0x9022, mask=(1 << 64) - 1 ^ retained_mount_bits),
    ]
    return {**baseline, 'syscalls': [*baseline['syscalls'], *rules]}


def docker(*args, host=None, capture=False):
    argv = ['docker']
    env = None
    if host is not None:
        argv.extend(['--host', host])
        env = {key: value for key, value in os.environ.items() if key not in ('DOCKER_CONTEXT', 'DOCKER_HOST')}
    return subprocess.run([*argv, *args], env=env, check=True, capture_output=capture,
                          text=True, timeout=120).stdout


def inspect_container(cli, container, owner):
    entry, = json.loads(cli('container', 'inspect', container, capture=True))
    if entry['Id'] != container or entry['Config']['Labels'].get(OWNER_LABEL) != owner:
        raise RuntimeError('Docker returned an unrelated container')
    return entry


@contextmanager
def owned_containers(cli, owner):
    selector = ('container', 'ls', '--all', '--no-trunc', '--quiet', '--filter', f'label={OWNER_LABEL}={owner}')
    try:
        yield
    finally:
        for container in cli(*selector, capture=True).splitlines():
            inspect_container(cli, container, owner)
            cli('container', 'rm', '--force', container, capture=True)
        if cli(*selector, capture=True).strip():
            raise RuntimeError('owned qualification container remains')


def qualify(image, seccomp, architecture, *, explicit_required=False):
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
        raise ValueError('qualification requires a local immutable image ID')
    context = os.environ.get('DOCKER_CONTEXT')
    host = None if context else os.environ.get('DOCKER_HOST')
    if not host:
        host = docker('context', 'inspect', *([context] if context else []),
                      '--format', '{{.Endpoints.docker.Host}}', capture=True).strip()
    if not host.startswith('unix:///'):
        raise ValueError('qualification requires a local Docker Unix socket')
    cli = partial(docker, host=host)
    engine_arch = cli('info', '--format', '{{.Architecture}}', capture=True).strip()
    image_arch = cli('image', 'inspect', '--format', '{{.Os}}/{{.Architecture}}', image, capture=True).strip()
    if ({'amd64': 'x86_64', 'arm64': 'aarch64'}[architecture] != engine_arch
            or image_arch != f'linux/{architecture}'):
        raise ValueError(f'required native {architecture}, found engine {engine_arch} and image {image_arch}')

    owner = uuid.uuid4().hex
    with owned_containers(cli, owner):
        probe = cli('create', '--pull', 'never', '--label', f'{OWNER_LABEL}={owner}',
                    '--network', 'none', '--user', '10001:10001', '--read-only', '--cap-drop', 'ALL',
                    '--security-opt', 'no-new-privileges', '--entrypoint', 'python', image,
                    '-I', '-c', PROC_INVENTORY, capture=True).strip()
        defaults = inspect_container(cli, probe, owner)['HostConfig']
        inventory = json.loads(cli('start', '--attach', probe, capture=True))

    cmd = ['-I', '/srv/lab/scripts/cli_sandbox_image_smoke.py', '--container-policy']
    if explicit_required:
        cmd.append('--explicit-required')
    paths = readonly_paths(defaults['ReadonlyPaths'], inventory)
    config = {
        'Image': image, 'User': '10001:10001', 'Entrypoint': ['python'], 'Cmd': cmd,
        'Labels': {OWNER_LABEL: owner},
        'HostConfig': {
            'NetworkMode': 'none', 'ReadonlyRootfs': True, 'CapDrop': ['ALL'],
            'PidsLimit': 128, 'Memory': 512 * 1024**2, 'NanoCpus': 2 * 10**9,
            'Tmpfs': dict([TMPFS.split(':', 1)]),
            'SecurityOpt': ['no-new-privileges', f'apparmor={PROFILE}', 'seccomp=' + json.dumps(seccomp)],
            'MaskedPaths': defaults['MaskedPaths'], 'ReadonlyPaths': paths,
        },
    }
    # The Docker CLI cannot set individual OCI ReadonlyPaths.
    with owned_containers(cli, owner):
        response = subprocess.run(
            ['curl', '--silent', '--show-error', '--fail-with-body', '--max-time', '30',
             '--unix-socket', host.removeprefix('unix://'), '--header', 'Content-Type: application/json',
             '--data-binary', '@-', 'http://localhost/containers/create'],
            input=json.dumps(config), capture_output=True, text=True, check=True,
        )
        result = json.loads(response.stdout)
        container = result['Id']
        actual = inspect_container(cli, container, owner)
        if actual['Image'] != image or actual['Config']['User'] != config['User']:
            raise RuntimeError('Docker changed the requested image or service user')
        for name, value in config['HostConfig'].items():
            if actual['HostConfig'][name] != value:
                raise RuntimeError(f'Docker changed the requested {name} policy')
        if result.get('Warnings'):
            raise RuntimeError(f"Docker policy warnings: {result['Warnings']}")
        cli('start', '--attach', container)
        if inspect_container(cli, container, owner)['State']['ExitCode'] != 0:
            raise RuntimeError('installed image witness failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', help='Immutable local image ID')
    parser.add_argument('baseline', type=Path, help=f'Pinned upstream profile from {SECCOMP_URL}')
    parser.add_argument('--architecture', choices=('amd64', 'arm64'), required=True)
    parser.add_argument('--explicit-required', action='store_true')
    args = parser.parse_args()
    content = args.baseline.read_bytes()
    if hashlib.sha256(content).hexdigest() != SECCOMP_SHA256:
        parser.error('upstream Docker seccomp checksum differs')
    qualify(args.image, extend_seccomp(json.loads(content)), args.architecture,
            explicit_required=args.explicit_required)


if __name__ == '__main__':
    main()
