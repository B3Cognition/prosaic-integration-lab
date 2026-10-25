"""Exercise CLI parsing, real plans/accounting and persisted receipts without inference."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from threading import Thread

import pytest


@pytest.mark.parametrize('flags,expected', [
    ([], 180),
    (['--local-timeout', '240'], 240),
    (['--local-timeout', '299.999999'], 299.999999),
])
def test_cli_timeout_reaches_commands_plan_samples_and_report(flags, expected, tmp_path, monkeypatch, capsys):
    from lab_runner.native_eval import provenance, unified_benchmark
    from lab_runner.native_eval.__main__ import main

    class Catalogue(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            assert self.path == '/v1/models' and self.headers['Authorization'] == 'Bearer fixture-token'
            body = b'{"data":[{"id":"synthetic"}]}'
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Catalogue)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    version = tmp_path / 'version-fixture'
    version.write_text(f'#!{sys.executable}\nimport sys\nassert sys.argv[1:]==["--version"]\nprint("fixture 2.1.308")\n')
    version.chmod(0o700)
    native = tmp_path / 'native.yml'
    native.write_text(json.dumps({'kind': 'native', 'default_profile': 'claude',
        'capacity_file': str(tmp_path / 'native-capacity.json'), 'profiles': {
            name: {'backend': backend, 'model': 'synthetic', 'quota_key': name,
                   'permission_mode': 'workspace-write', 'executable': str(version)}
            for name, backend in [('claude', 'claude-code'), ('codex', 'codex-cli')]}}))
    native.chmod(0o600)
    key = tmp_path / 'key'
    key.write_text('fixture-token')
    key.chmod(0o600)
    local = tmp_path / 'local.yml'
    local.write_text(json.dumps({'default_profile': 'local', 'allowed_tools': ['read_file', 'write_file'],
        'profiles': {'local': {'base_url': f'http://127.0.0.1:{server.server_port}/v1',
            'model': 'synthetic', 'api_key_file': str(key), 'max_tokens': 2048,
            'features': {'streaming': False}}}}))
    local.chmod(0o600)
    # Only external payload auditing and inference are replaced. Version/catalogue
    # readiness, config loading, scheduling, grading and durable accounting stay real.
    monkeypatch.setattr(provenance, 'audit_candidate', lambda *args: {'origin': 'synthetic-test'})
    commands = []
    def refuse(command):
        commands.append(command)
        return {'event': 'result', 'exit_code': 1, 'stdout': '', 'stderr': '', 'timed_out': False,
            'token_usage': 0, 'cost_usd': None, 'metadata': {'failure_reason': 'fixture_refusal',
                'unified_execution_v1': {'native_attempts': 0, 'api_provider_requests': 0,
                    'api_tool_calls': 0, 'api_reported_tokens': 0, 'api_usage_complete': True,
                    'attempts': [], 'duration_ms': 0, 'known_tokens': 0, 'usage_complete': True}}}, []
    monkeypatch.setattr(unified_benchmark, '_invoke', refuse)
    out = tmp_path / 'study'
    try:
        assert main(['unified-benchmark', '--live', '--manifest', 'synthetic', '--wheel-dir', 'synthetic',
            '--runtime-config', str(native), '--local-config', str(local), '--output', str(out),
            '--repetitions', '1', *flags]) == 1  # Scripted refusals are failures, never successes.
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    capsys.readouterr()
    plan = json.loads((out / 'plan.json').read_text())
    report = json.loads((out / 'report.json').read_text())
    assert len(commands) == report['sampleCount'] == 9
    assert all(float(command[command.index('--api-timeout') + 1]) == expected for command in commands)
    assert plan['localTimeoutSeconds'] == expected
    assert all(row['localTimeoutSeconds'] == expected for row in report['samples'])
    assert f'local {expected}s' in report['limitations'][1]
    assert report['cleanup'] == 'verified' and not list(out.glob('workspace-*'))
    assert report['allowance'] == {'maximum': 81, 'retained': 0, 'remaining': 81, 'unknown': 0}
