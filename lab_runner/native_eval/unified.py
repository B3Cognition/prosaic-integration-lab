"""Installed-public-SDK mixed-pool acceptance; fixtures never run real models."""
from contextlib import contextmanager
from dataclasses import asdict, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Thread
import time

from .cases import prepare_case, grade
from .provenance import require_native
from .runner import fixture_config


def require_unified():
    sdk = require_native()
    if any(not hasattr(sdk, name) for name in ('UnifiedRuntime', 'UnifiedRuntimeConfig', 'PoolPolicy')):
        raise ValueError('installed candidate lacks the unified pool API')
    return sdk


@contextmanager
def api_fixture(mode='pass'):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            reject = mode == 'reject' or mode == 'effect-reject' and len(requests) % 2 == 0
            write = len(requests) % 2 == 1
            message = {'content': 'fixed'}
            if write:
                message = {'content': '', 'tool_calls': [{'id': 'write', 'type': 'function', 'function': {
                    'name': 'write_file', 'arguments': json.dumps({'path': 'calculator.py',
                        'content': 'def add(a, b):\n    return a + b\n'})}}]}
            body = json.dumps({'error': 'fixture capacity'} if reject else {
                'choices': [{'message': message, 'finish_reason': 'tool_calls' if write else 'stop'}],
                'usage': {'prompt_tokens': 5, 'completion_tokens': 2, 'total_tokens': 7}}).encode()
            self.send_response(429 if reject else 200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{http.server_port}/v1', requests
    finally:
        http.shutdown()
        thread.join(timeout=2)
        http.server_close()


def fixture_policy(*, native=True, requests=3, write_paths=('calculator.py',)):
    sdk = require_unified()
    return sdk.PoolPolicy(timeout_s=10, max_attempts=3, max_native_attempts=2,
        native_policy=sdk.NativePolicy(permission_mode='workspace-write') if native else None,
        api_policy=sdk.RunPolicy(allowed_tools=frozenset({'write_file'}), write_paths=write_paths,
                                max_provider_requests=requests, max_tool_calls=1))


def mixed_config(root, url, *, scenario='quota', codex_quota=True,
                 order=('claude', 'codex', 'local'), shared=False):
    sdk = require_unified()
    native = fixture_config(root, scenario=scenario, same_quota=shared)
    if codex_quota:
        from . import fixture_cli
        Path(native.profiles['codex'].executable).write_text(f'#!{sys.executable}\n' +
            Path(fixture_cli.__file__).read_text() + '\nraise SystemExit(main("codex-cli", "quota"))\n')
    api = sdk.RuntimeConfig({'local': sdk.EndpointConfig(url, 'synthetic-local', features={'streaming': False})},
        {}, 'local', allowed_tools=frozenset({'write_file'}))
    return sdk.UnifiedRuntimeConfig(native, api, {'agents': sdk.ProfilePool(order, cooldown_s=10)},
        'agents', {'local': 'shared' if shared else 'local'}, capacity_file=str(root / 'unified-capacity.json'))


def sample(config, root, *, policy=None):
    sdk = require_unified()
    with tempfile.TemporaryDirectory(prefix='workspace-', dir=root) as temporary:
        artifact = prepare_case('repair', temporary)
        result = sdk.UnifiedRuntime(config).run(artifact, cwd=temporary,
            policy=fixture_policy() if policy is None else policy)
        passed = result.exit_code == 0 and grade('repair', temporary, result.stdout)
        original = (Path(temporary) / 'calculator.py').read_text() == 'def add(a, b):\n    return a - b\n'
    return result, passed, original


def run_unified_cli_acceptance(*, provenance=None):
    """Exercise installed CLI subprocesses, real transports and durable capacity."""
    require_unified()
    checks = {}
    with tempfile.TemporaryDirectory(prefix='lab-unified-cli-') as temporary:
        root = Path(temporary)

        def invoke(name, url, *, mode=None, extra=(), scenario='quota', order=('claude', 'codex', 'local'),
                   codex_quota=True, config_path=None, native=True, api=True):
            case = root / name
            case.mkdir()
            workspace = case / 'workspace'
            workspace.mkdir()
            artifact = prepare_case('repair', workspace)
            source = case / '.prosaic' / 'subagents'
            source.mkdir(parents=True)
            (source / 'repair.md').write_text('---\nname: repair\ndescription: Repair\nexecution: agent\n' +
                'tools: [write_file]\n---\n' + artifact.body)
            if config_path is None:
                config = mixed_config(case, url, scenario=scenario, order=order, codex_quota=codex_quota)
                (case / 'native.yml').write_text(json.dumps({'kind': 'native', 'profiles': {
                    k: asdict(v) for k, v in config.native_config.profiles.items()}, 'default_profile': 'claude'}))
                (case / 'api.yml').write_text(json.dumps({'profiles': {'local': asdict(config.api_config.profiles['local'])},
                    'default_profile': 'local', 'allowed_tools': ['write_file']}))
                config_path = case / 'unified.yml'
                config_path.write_text(json.dumps({'kind': 'unified', 'native_config': 'native.yml',
                    'api_config': 'api.yml', 'pools': {'agents': {'profiles': list(order)}},
                    'default_pool': 'agents', 'api_quota_keys': {'local': 'local'},
                    'capacity_file': config.capacity_file}))
            command = [sys.executable, '-I', '-m', 'prosaic_runtime.cli', 'subagents/repair.md',
                '--source', str(source.parent), '--config', str(config_path), '--cwd', str(workspace), '--quiet',
                '--timeout', '10', '--max-attempts', '3', '--max-native-attempts', '2',
                '--native-permissions', 'workspace-write', '--native-timeout', '5',
                '--enable-api', '--api-timeout', '5', '--max-api-requests', '3',
                '--max-api-tool-calls', '1', '--max-tool-rounds', '2',
                '--allow-tool', 'write_file', '--write-path', 'calculator.py']
            if not native:
                for flag in ('--native-permissions', '--native-timeout'):
                    index = command.index(flag)
                    del command[index:index + 2]
                command[command.index('--max-native-attempts') + 1] = '0'
            if not api:
                command.remove('--enable-api')
                for flag in ('--api-timeout', '--max-api-requests', '--max-api-tool-calls',
                             '--max-tool-rounds', '--allow-tool', '--write-path'):
                    index = command.index(flag)
                    del command[index:index + 2]
            command += list(extra)
            if mode:
                command += ['--events'] if mode == 'events' else ['--output', mode]
            child = subprocess.run(command, capture_output=True, text=True, timeout=15)
            lines = child.stdout.splitlines()
            result = json.loads(lines[-1]) if lines and mode != 'text' else {}
            return child, result, workspace, config_path

        with api_fixture() as (url, requests):
            child, result, workspace, path = invoke('fallback', url, mode='events')
            info = result.get('metadata', {}).get('unified_execution_v1', {})
            checks['three_backend_cli_fallback'] = child.returncode == 0 and [a['profile'] for a in info.get('attempts', [])] == ['claude', 'codex', 'local']
            events = [json.loads(line) for line in child.stdout.splitlines()]
            if child.returncode != 0 or not events:
                raise AssertionError('installed unified CLI failed: ' + child.stderr[:1000])
            checks['jsonl_terminal_result'] = events[-1]['event'] == 'result' and all('event' in e for e in events)
            checks['graded_output'] = grade('repair', workspace, '')
            child, result, _, _ = invoke('persisted', url, config_path=path)
            checks['cross_process_cooldown'] = child.returncode == 0 and result['metadata']['unified_execution_v1']['native_attempts'] == 0
        with api_fixture() as (url, requests):
            child, result, _, _ = invoke('zero-api', url, extra=('--max-api-requests', '0'))
            checks['zero_request_budget'] = child.returncode == 1 and not requests and result['metadata']['unified_execution_v1']['api_provider_requests'] == 0
        with api_fixture('reject') as (url, _):
            child, result, case, path = invoke('all-cooled', url)
            child, result, _, _ = invoke('all-cooled-again', url, config_path=path)
            checks['all_unavailable_no_dispatch'] = child.returncode == 1 and result['metadata']['unified_execution_v1']['attempts'] == [] and result['metadata']['retry_at'] > time.time()
        with api_fixture('effect-reject') as (url, _):
            child, result, case, _ = invoke('effect', url, order=('local', 'codex'), codex_quota=False)
            info = result['metadata']['unified_execution_v1']
            checks['no_replay_after_tool'] = child.returncode == 1 and info['native_attempts'] == 0 and result['metadata']['recovery_required'] and grade('repair', case, '')
        with api_fixture() as (url, requests):
            child, result, _, _ = invoke('native-effect', url, scenario='effect-quota')
            info = result['metadata']['unified_execution_v1']
            checks['native_effect_no_replay'] = child.returncode == 1 and info['native_attempts'] == 1 and result['metadata']['recovery_required'] and not requests
        with api_fixture() as (url, requests):
            child, result, _, _ = invoke('native-only-selection', url, order=('codex',), codex_quota=False, api=False)
            checks['native_success'] = child.returncode == 0 and result['metadata']['unified_execution_v1']['native_attempts'] == 1 and not requests
        with api_fixture() as (url, _):
            child, result, _, _ = invoke('api-only-permission', url, native=False)
            checks['explicit_backend_exclusion'] = child.returncode == 0 and result['metadata']['unified_execution_v1']['native_attempts'] == 0
        with api_fixture() as (url, _):
            child, result, case, _ = invoke('scope', url, order=('local',), extra=('--write-path', 'other', '--max-api-tool-calls', '0'))
            checks['zero_tool_budget'] = child.returncode == 1 and (case / 'calculator.py').read_text() == 'def add(a, b):\n    return a - b\n'
        with api_fixture() as (url, _):
            child, _, case, _ = invoke('text', url, mode='text')
            checks['text_output'] = child.returncode == 0 and child.stdout.strip() == 'fixed' and grade('repair', case, '')
    checks['temporary_workspace_cleanup'] = not root.exists()
    return {'suiteVersion': 'unified-cli-v1', 'origin': 'scripted_fixture', 'passed': all(checks.values()),
        'caseCount': len(checks), 'checks': checks, 'cleanup': 'verified' if not root.exists() else 'failed',
        'liveInvocations': 0, 'provenance': provenance or {}}


def run_unified_acceptance(*, provenance=None):
    sdk = require_unified()
    checks = {}
    with tempfile.TemporaryDirectory(prefix='lab-unified-acceptance-') as temporary:
        root = Path(temporary)
        def owned(name):
            path = root / name
            path.mkdir()
            return path
        with api_fixture() as (url, requests):
            case = owned('three-backends')
            config = mixed_config(case, url)
            result, passed, _ = sample(config, case)
            info = result.metadata['unified_execution_v1']
            checks['three_backend_fallback'] = (passed and [a['profile'] for a in info['attempts']] ==
                ['claude', 'codex', 'local'] and info['native_attempts'] == 2 and info['api_provider_requests'] == 2
                and result.token_usage is None and info['known_tokens'] == 14)
            # Serialize pure fixture operator config, then execute the installed
            # SDK in another interpreter. No Lab engine is imported in the child.
            (case / 'native.yml').write_text(json.dumps({'kind': 'native', 'profiles': {
                k: asdict(v) for k, v in config.native_config.profiles.items()}, 'default_profile': 'claude'}))
            (case / 'api.yml').write_text(json.dumps({'profiles': {'local': asdict(config.api_config.profiles['local'])},
                'default_profile': 'local', 'allowed_tools': ['write_file']}))
            path = case / 'unified.yml'
            path.write_text(json.dumps({'kind': 'unified', 'native_config': 'native.yml', 'api_config': 'api.yml',
                'pools': {'agents': {'profiles': ['claude', 'codex', 'local']}}, 'default_pool': 'agents',
                'api_quota_keys': {'local': 'local'}, 'capacity_file': config.capacity_file}))
            with tempfile.TemporaryDirectory(prefix='workspace-', dir=case) as workspace:
                artifact = prepare_case('repair', workspace)
                agent = case / 'artifact.json'
                agent.write_text(json.dumps({'id': artifact.id, 'type': artifact.type,
                    'frontmatter': artifact.frontmatter, 'body': artifact.body}))
                code = ('import json,sys; from pathlib import Path; from prosaic_runtime import *; '
                    'r=UnifiedRuntime(UnifiedRuntimeConfig.load(sys.argv[1])).run('
                    'ProsaicArtifact.from_inspection(json.loads(Path(sys.argv[2]).read_text())),cwd=sys.argv[3],'
                    'policy=PoolPolicy(timeout_s=10,max_attempts=3,max_native_attempts=2,'
                    'native_policy=NativePolicy(permission_mode="workspace-write"),'
                    'api_policy=RunPolicy(allowed_tools=frozenset({"write_file"}),write_paths=("calculator.py",),'
                    'max_provider_requests=3,max_tool_calls=1))); '
                    'print(json.dumps({"exit":r.exit_code,"native":r.metadata["unified_execution_v1"]["native_attempts"],'
                    '"api":r.metadata["unified_execution_v1"]["api_provider_requests"]}))')
                child = subprocess.run([sys.executable, '-I', '-c', code, str(path), str(agent), workspace],
                    capture_output=True, text=True, timeout=15)
                observed = json.loads(child.stdout) if child.returncode == 0 else {}
                checks['cross_process_cooldown'] = observed == {'exit': 0, 'native': 0, 'api': 2} and grade('repair', workspace, '')
        with api_fixture('reject') as (url, _):
            case = owned('api-first')
            result, passed, _ = sample(mixed_config(case, url, codex_quota=False, order=('local', 'codex')), case)
            checks['api_to_native_fallback'] = passed and [a['profile'] for a in result.metadata['unified_execution_v1']['attempts']] == ['local', 'codex']
        with api_fixture() as (url, requests):
            case = owned('native-effect')
            result, _, _ = sample(mixed_config(case, url, scenario='effect-quota'), case)
            checks['native_effect_no_replay'] = result.exit_code != 0 and result.metadata['recovery_required'] and not requests and result.metadata['unified_execution_v1']['native_attempts'] == 1
        with api_fixture('effect-reject') as (url, _):
            case = owned('api-effect')
            result, _, _ = sample(mixed_config(case, url, codex_quota=False, order=('local', 'codex')), case)
            checks['api_effect_no_replay'] = result.exit_code != 0 and result.metadata['recovery_required'] and result.metadata['unified_execution_v1']['native_attempts'] == 0
        with api_fixture() as (url, requests):
            case = owned('shared-quota')
            config = mixed_config(case, url, shared=True)
            result, _, _ = sample(config, case)
            checks['shared_quota_no_bypass'] = result.metadata.get('failure_reason') == 'capacity_unavailable' and not requests and result.metadata['unified_execution_v1']['native_attempts'] == 1
            again, _, _ = sample(config, case)
            checks['all_unavailable_no_dispatch'] = (again.metadata.get('failure_reason') == 'capacity_unavailable'
                and again.metadata['retry_at'] > time.time() and again.metadata['unified_execution_v1']['attempts'] == [] and not requests)
        with api_fixture() as (url, _):
            case = owned('explicit-permission')
            result, passed, _ = sample(mixed_config(case, url), case, policy=fixture_policy(native=False))
            checks['explicit_native_permission'] = passed and result.metadata['unified_execution_v1']['native_attempts'] == 0
        with api_fixture() as (url, _):
            case = owned('api-scope')
            result, _, unchanged = sample(mixed_config(case, url, order=('local', 'codex')), case,
                policy=fixture_policy(write_paths=('other',)))
            checks['api_write_scope'] = unchanged and result.metadata['unified_execution_v1']['native_attempts'] == 0
        with api_fixture() as (url, _):
            case = owned('api-budget')
            result, _, _ = sample(mixed_config(case, url), case, policy=fixture_policy(requests=1))
            checks['api_request_budget'] = (result.exit_code != 0 and result.metadata.get('failure_reason') == 'provider_request_limit'
                and result.metadata['unified_execution_v1']['api_provider_requests'] == 1)
    checks['temporary_workspace_cleanup'] = not root.exists()
    return {'suiteVersion': 'unified-pool-v1', 'origin': 'scripted_fixture', 'passed': all(checks.values()),
        'caseCount': len(checks), 'checks': checks, 'cleanup': 'verified' if checks['temporary_workspace_cleanup'] else 'failed',
        'liveInvocations': 0, 'provenance': provenance or {}}
