"""Qualify installed Runtime CLI execution under the Linux image's deployment policy."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Thread

import yaml
from prosaic_runtime import ProsaicArtifact, ProsaicRuntime, RunPolicy, RuntimeConfig

CANARY = 'image-sandbox-canary'
WITNESS = """
import json, os, socket, sys
from pathlib import Path
evidence, secret, marker, port = sys.argv[1:]
if Path(evidence).read_text() != 'owned evidence':
    raise RuntimeError('granted evidence was not readable')
for path, operation in ((secret, 'read'), (marker, 'write')):
    try:
        if operation == 'read':
            Path(path).read_text()
        else:
            Path(path).write_text('unexpected write')
    except OSError as exc:
        if exc.errno not in (1, 2, 13, 30):
            raise
    else:
        raise RuntimeError('sandbox permitted an ungranted filesystem effect')
try:
    socket.create_connection(('127.0.0.1', int(port)), timeout=0.3).close()
except OSError:
    pass
else:
    raise RuntimeError('sandbox permitted network delivery')
Path(os.environ['TMPDIR'], 'private-scratch').write_text('scratch works')
if sys.platform == 'linux':
    try:
        os.unshare(os.CLONE_NEWUSER)
    except OSError as exc:
        if exc.errno not in (1, 13, 28, 87):
            raise
    else:
        raise RuntimeError('sandbox permitted a nested user namespace')
print(json.dumps('image-sandbox-canary'))
"""


def verify(root, expect_default):
    workspace = root / 'workspace'
    evidence = workspace / 'evidence'
    evidence.mkdir(parents=True)
    document = evidence / 'input.txt'
    document.write_text('owned evidence')
    secret = root / 'outside.txt'
    secret.write_text('owned private canary')
    marker = root / 'marker'
    tools = root / 'tools'
    tools.mkdir()
    requests = []

    class Model(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(request)
            if len(requests) == 1:
                message = {'role': 'assistant', 'content': None, 'tool_calls': [{
                    'id': 'sandbox-fixture', 'type': 'function',
                    'function': {'name': 'sandbox_probe', 'arguments': '{}'}}]}
                reason = 'tool_calls'
            elif len(requests) == 2:
                message = {'role': 'assistant', 'content': 'done'}
                reason = 'stop'
            else:
                self.send_error(400)
                return
            response = json.dumps({'choices': [{'index': 0, 'message': message,
                                                'finish_reason': reason}]}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)

    with ThreadingHTTPServer(('127.0.0.1', 0), Model) as server:
        port = server.server_port
        argv = ['-I', '-c', WITNESS, str(document), str(secret), str(marker), str(port)]
        manifest = {'schema_version': 1, 'name': 'sandbox_probe', 'description': 'Verify synthetic confinement.',
                    'tool_version': '1', 'executable': sys.executable, 'argv': argv,
                    'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False},
                    'output_format': 'json', 'version_probe': argv, 'version_contains': CANARY}
        (tools / 'probe.yml').write_text(yaml.safe_dump(manifest))
        yaml_path = root / 'runtime.yml'
        values = {'default_profile': 'fixture', 'tool_directories': ['tools'], 'allowed_tools': ['sandbox_probe'],
                  'profiles': {'fixture': {'base_url': f'http://127.0.0.1:{port}/v1', 'model': 'fixture',
                                           'features': {'streaming': False}}}}
        if not expect_default:
            values['cli_sandbox'] = {'mode': 'required'}
        yaml_path.write_text(yaml.safe_dump(values))
        config = RuntimeConfig.load(yaml_path)
        if config.cli_sandbox.mode != 'required':
            raise RuntimeError('installed Runtime does not require CLI confinement')
        runtime = ProsaicRuntime(config)
        artifact = ProsaicArtifact('sandbox-probe', 'subagent',
            {'name': 'sandbox-probe', 'description': 'Owned sandbox probe', 'tools': ['sandbox_probe']},
            'Call the synthetic sandbox probe.')
        policy = RunPolicy(allowed_tools=frozenset({'sandbox_probe'}), read_roots=('evidence',),
                           timeout_s=20, max_provider_requests=2, max_tool_calls=1)
        preflight = runtime.preflight(artifact, cwd=workspace, policy=policy)
        if not preflight['ok']:
            raise RuntimeError(preflight['checks']['sandbox_probe']['message'])
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = runtime.run(artifact, cwd=workspace, policy=policy)
        finally:
            server.shutdown()
            thread.join()
        if result.exit_code != 0 or len(requests) != 2 or marker.exists():
            raise RuntimeError('sandboxed invocation did not complete safely')
        outputs = [json.loads(message['content']) for message in requests[-1]['messages']
                   if message['role'] == 'tool']
        if outputs != [{'status': 'ok', 'result': CANARY}]:
            raise RuntimeError('sandboxed CLI result was not observed')


def require_container_policy():
    label = Path('/proc/self/attr/current').read_text().strip()
    if label != 'prosaic-lab-cli-sandbox (enforce)':
        raise RuntimeError(f'unexpected AppArmor mode: {label}')
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    if (status['NoNewPrivs'].strip() != '1' or status['Seccomp'].strip() != '2'
            or any(int(status[name], 16) for name in ('CapEff', 'CapBnd'))):
        raise RuntimeError('missing privilege or syscall restrictions')
    root = Path('/proc/sys')
    sysctls = [path for path in root.iterdir() if path.name != 'user']
    sysctls.extend((root / 'user').iterdir())
    exception = root / 'user/max_user_namespaces'
    for path in [Path('/'), *sysctls]:
        readonly = bool(os.statvfs(path).f_flag & os.ST_RDONLY)
        if readonly == (path == exception):
            raise RuntimeError(f'unexpected mount permissions on {path}')
    print('AppArmor enforcing, seccomp active, zero capabilities, scoped proc exception.', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--explicit-required', action='store_true', help='Qualify an older Runtime with explicit policy.')
    parser.add_argument('--container-policy', action='store_true', help='Check the deployed outer policy.')
    args = parser.parse_args()
    if platform.system() != 'Linux' or os.getuid() != 10001:
        raise RuntimeError('Linux image qualification requires the Lab service UID')
    backend = subprocess.check_output(['/usr/bin/bwrap', '--version'], text=True, timeout=5).strip()
    print(json.dumps({'architecture': platform.machine(), 'backend': backend, 'uid': os.getuid()}), flush=True)
    if args.container_policy:
        require_container_policy()
    with TemporaryDirectory(prefix='cli-sandbox-image-') as directory:
        verify(Path(directory), expect_default=not args.explicit_required)
    print('Installed image passed CLI and version-probe containment.')


if __name__ == '__main__':
    main()
