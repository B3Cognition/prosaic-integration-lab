import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from lab_runner.explore.execution import Coordinator, inspect_receipt, reconcile


@pytest.fixture
def host(tmp_path, monkeypatch):
    import lab_runner.explore.execution as execution
    monkeypatch.setattr(execution, 'audit_candidate', lambda *args: {})
    api = tmp_path / 'api.yml'
    api.write_text(json.dumps({'profiles': {'local': {'base_url': 'http://127.0.0.1:1/v1', 'model': 'fixture'}}, 'default_profile': 'local'}))
    api.chmod(0o600)
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({'kind': 'unified', 'api_config': 'api.yml', 'pools': {'agents': {'profiles': ['local']}}, 'default_pool': 'agents', 'api_quota_keys': {'local': 'fixture'}, 'capacity_file': str(tmp_path / 'capacity.json')}))
    config.chmod(0o600)
    root = tmp_path / 'evidence'
    root.mkdir(mode=0o700)
    def create():
        return Coordinator(root, config, manifest=tmp_path / 'manifest', wheel_dir=tmp_path)
    def transport(code):
        monkeypatch.setattr(execution, 'cli_command', lambda *args, **kwargs: [sys.executable, '-c', code, str(args[2])])
    return root, config, create, transport


def finished(c, run):
    for _ in range(200):
        row = c.get(run['runId'])
        if row['state'] != 'running':
            return row
        time.sleep(.01)
    raise AssertionError('worker did not finish')


RESULT = {'event': 'result', 'exit_code': 0, 'metadata': {'profile': 'local', 'unified_execution_v1': {'native_attempts': 0, 'api_provider_requests': 2, 'api_tool_calls': 1, 'known_tokens': 14}}}
SQL = "SELECT i.customer_id, COUNT(*) overdue_count, SUM(MAX(i.total_cents-COALESCE(p.paid,0),0)) outstanding_cents FROM invoices i LEFT JOIN (SELECT invoice_id,SUM(amount_cents) paid FROM payments GROUP BY invoice_id) p ON p.invoice_id=i.id WHERE i.status='OPEN' AND i.due_date<'2026-10-23' AND i.total_cents>COALESCE(p.paid,0) GROUP BY i.customer_id ORDER BY i.customer_id"


def test_completion_durable_identity_and_accounting(host):
    root, config, create, transport = host
    transport(f"import pathlib,sys; pathlib.Path(sys.argv[1],'report.sql').write_text({SQL!r}); print({json.dumps(RESULT)!r})")
    c = create()
    run = c.submit('request-1', 'invoice-sql')
    row = finished(c, run)
    assert row['state'] == 'completed' and row['passed']
    assert row['usage']['apiRequests'] == 2
    assert c.status()['allowance']['retained'] == 2
    assert c.submit('request-1', 'invoice-sql') == row
    with pytest.raises(ValueError): c.submit('request-1', 'release-brief')
    with pytest.raises(ValueError): create()
    c.close()
    c = create()
    assert c.get(run['runId']) == row
    assert c.submit('request-1', 'invoice-sql') == row
    c.close()


def test_missing_receipt_blocks_restart_and_exact_offline_ack(host):
    root, config, create, transport = host
    transport("print('private-provider-secret')")
    c = create()
    row = finished(c, c.submit('request-1', 'release-brief'))
    assert row['state'] == 'uncertain' and row['recoveryRequired']
    assert 'private-provider-secret' not in json.dumps(row)
    assert c.status()['allowance']['unknown'] == 1
    c.close()
    c = create()
    assert c.status()['blocked']
    with pytest.raises(ValueError): c.submit('new', 'release-brief')
    c.close()
    with pytest.raises(ValueError): reconcile(root, row['runId'], '0'*64, 'inspected')
    reconcile(root, row['runId'], row['receiptSha256'], 'Inspected uncertain effects.')
    c = create()
    assert not c.status()['blocked']
    assert c.submit('request-1', 'release-brief') == row
    assert c.status()['allowance']['retained'] == 10
    c.close()


def test_cancel_retains_unknown_and_config_changes_rejected(host):
    root, config, create, transport = host
    transport('import time; time.sleep(60)')
    c = create()
    row = c.submit('request-1', 'release-brief')
    c.cancel(row['runId'])
    row = finished(c, row)
    assert row['state'] == 'cancelled' and row['recoveryRequired']
    assert c.status()['allowance']['retained'] == 10
    c.close()
    c = create()
    config.write_text(config.read_text() + '\n')
    with pytest.raises(ValueError): c.submit('new', 'release-brief')
    c.close()


@pytest.mark.parametrize('task,timeout', [('other',180), ('invoice-sql',True), ('invoice-sql',181)])
def test_strict_admission(host, task, timeout):
    _, _, create, _ = host
    c = create()
    with pytest.raises(ValueError): c.submit('request', task, timeout)
    assert c.status()['runs'] == []
    c.close()


def test_symlink_output_never_graded_or_exposed(host):
    _, config, create, transport = host
    transport(f"import pathlib,sys; p=pathlib.Path(sys.argv[1],'brief.json'); p.unlink(); p.symlink_to({str(config)!r}); print({json.dumps(RESULT)!r})")
    c = create()
    row = finished(c, c.submit('request', 'release-brief'))
    assert not row['passed'] and row['output'] == ''
    assert 'api_config' not in json.dumps(row)
    c.close()


def test_partial_work_keeps_known_usage_and_blocks(host):
    _, _, create, transport = host
    result = json.loads(json.dumps(RESULT))
    result['exit_code'] = 1
    result['metadata'].update(recovery_required=True, failure_reason='private-secret')
    transport(f"print({json.dumps({'event':'profile_fallback','profile':'local','reason':'private-secret'})!r}); print({json.dumps(result)!r}); raise SystemExit(1)")
    c = create()
    row = finished(c, c.submit('request', 'invoice-sql'))
    assert row['state'] == 'uncertain'
    assert row['events'] == [{'event':'profile_fallback', 'profile':'local'}]
    assert 'private-secret' not in json.dumps(row)
    assert c.status()['blocked'] and c.status()['allowance']['retained'] == 2
    c.close()


def test_output_flood_is_bounded_and_charged(host):
    _, _, create, transport = host
    transport("import sys; sys.stdout.write('x'*1100000)")
    c = create()
    row = finished(c, c.submit('request', 'invoice-sql'))
    assert row['state'] == 'uncertain' and len(json.dumps(row)) < 4096
    assert c.status()['allowance']['unknown'] == 1
    c.close()


def test_pending_admission_survives_process_loss_without_redispatch(host):
    root, _, create, transport = host
    transport("raise AssertionError('must never dispatch')")
    c = create()
    c.close()
    state_path = root / 'state.json'
    state = json.loads(state_path.read_text())
    state['runs'].append({'timeout':180, 'reservation':None, 'receipt':dict(
        runId='a'*32, requestId='crashed', task='invoice-sql', state='running', passed=False,
        durationMs=0, selectedProfile=None, events=[], output='', failureReason=None,
        recoveryRequired=False, usage={}, startedAt=0)})
    state_path.write_text(json.dumps(state))
    c = create()
    row = c.submit('crashed', 'invoice-sql')
    assert row['state'] == 'uncertain' and c.status()['blocked']
    with pytest.raises(ValueError): c.submit('new', 'invoice-sql')
    c.close()


def test_busy_and_exhausted_never_add_authority(host):
    _, _, create, transport = host
    transport('import time; time.sleep(60)')
    c = create()
    run = c.submit('first', 'invoice-sql')
    with pytest.raises(ValueError, match='busy'): c.submit('second', 'invoice-sql')
    assert len(c.status()['runs']) == 1
    c.cancel(run['runId'])
    finished(c, run)
    c.close()


def test_receipt_is_durable_before_allowance_settlement(host, monkeypatch):
    root, _, create, transport = host
    from lab_runner.live_allowance import SharedLiveAllowance
    original = SharedLiveAllowance.finish
    checked = []
    def finish(allowance, token, *, actual_requests):
        state = json.loads((root / 'state.json').read_text())
        row = state['runs'][0]
        checked.append(row['receipt']['state'] != 'running' and row.get('settledActual') == actual_requests)
        return original(allowance, token, actual_requests=actual_requests)
    monkeypatch.setattr(SharedLiveAllowance, 'finish', finish)
    transport(f"print({json.dumps(RESULT)!r})")
    c = create()
    finished(c, c.submit('first', 'invoice-sql'))
    c.close()
    assert checked == [True]


def test_replaced_root_lock_denies_new_authority(host):
    root, _, create, _ = host
    c = create()
    (root / 'explorer.lock').unlink()
    (root / 'explorer.lock').write_text('')
    (root / 'explorer.lock').chmod(0o600)
    try:
        with pytest.raises(ValueError): c.submit('new', 'invoice-sql')
    finally:
        c.close()


def test_offline_inspection_filters_and_requires_exclusive_root(host):
    root, _, create, transport = host
    transport("print('no terminal result')")
    c = create()
    run = finished(c, c.submit('first', 'release-brief'))
    with pytest.raises(ValueError, match='root_locked'): inspect_receipt(root, run['runId'])
    c.close()
    assert inspect_receipt(root, run['runId']) == run


def test_installed_runtime_cli_actual_http_tool_execution(host):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread
    root, config, create, _ = host
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_POST(self):
            calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            message = {'content':'Fixture completed.'}
            if len(calls) == 1:
                message = {'content':'', 'tool_calls':[{'id':'fixture-write', 'type':'function',
                    'function':{'name':'write_file', 'arguments':json.dumps({'path':'report.sql', 'content':SQL})}}]}
            body = json.dumps({'choices':[{'message':message, 'finish_reason':'tool_calls' if len(calls)==1 else 'stop'}],
                               'usage':{'prompt_tokens':5,'completion_tokens':2,'total_tokens':7}}).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers(); self.wfile.write(body)
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = Thread(target=server.serve_forever,daemon=True); thread.start()
    api = config.parent / 'api.yml'
    api.write_text(json.dumps({'profiles':{'local':{'base_url':f'http://127.0.0.1:{server.server_port}/v1',
                           'model':'fixture','features':{'streaming':False}}},
                           'default_profile':'local','allowed_tools':['read_file','write_file','edit_file']}))
    c = None
    try:
        c = create()
        row = finished(c,c.submit('actual-cli','invoice-sql',240))
        assert row['state'] == 'completed' and row['passed'], row
        assert row['usage'] == {'nativeAttempts':0,'apiRequests':2,'apiToolCalls':1,'knownTokens':14}
        assert len(calls) == 2
        assert c.status()['allowance']['retained'] == 2
    finally:
        if c: c.close()
        server.shutdown(); thread.join(2); server.server_close()


def test_uncertain_transport_retains_bounded_task_output(host):
    _, _, create, transport = host
    transport("import pathlib,sys; pathlib.Path(sys.argv[1],'brief.json').write_text('Retained partial task output.'); print('no receipt')")
    c = create()
    row = finished(c, c.submit('first','release-brief'))
    assert row['state'] == 'uncertain' and row['output'] == 'Retained partial task output.'
    c.close()


def test_known_allowance_limit_never_admits_excess(host):
    _, _, create, transport = host
    transport(f"print({json.dumps(RESULT)!r})")
    c = create()
    try:
        for i in range(6): finished(c, c.submit(f'run-{i}','invoice-sql'))
        with pytest.raises(ValueError, match='allowance_exhausted'): c.submit('excess','invoice-sql')
        assert len(c.status()['runs']) == 6 and c.status()['allowance']['retained'] == 12
    finally: c.close()


def test_hardlinked_output_is_not_exposed(host):
    _, config, create, transport = host
    transport(f"import pathlib,sys,os; p=pathlib.Path(sys.argv[1],'brief.json'); p.unlink(); os.link({str(config)!r},p); print({json.dumps(RESULT)!r})")
    c = create()
    try:
        row = finished(c,c.submit('first','release-brief'))
        assert row['output'] == '' and not row['passed']
    finally: c.close()


@pytest.mark.parametrize('reason,timed_out', [('timeout',False), ('native_timeout',False), ('api_timeout',False), ('pool_timeout',False), (None,True)])
def test_known_timeout_receipt_keeps_durable_recovery_barrier(host, reason, timed_out):
    root, _, create, transport = host
    result = json.loads(json.dumps(RESULT))
    result.update(exit_code=1, timed_out=timed_out)
    if reason: result['metadata']['failure_reason'] = reason
    transport(f"print({json.dumps(result)!r}); raise SystemExit(1)")
    c = create()
    try:
        row = finished(c,c.submit('timed-out','invoice-sql'))
        assert row['state'] == 'uncertain' and row['recoveryRequired']
        assert c.status()['blocked'] and c.status()['allowance']['retained'] == 2
        assert c.status()['allowance']['unknown'] == 0
    finally: c.close()
    c = create()
    try:
        assert c.status()['blocked']
        assert c.submit('timed-out','invoice-sql') == row
    finally: c.close()


@pytest.mark.parametrize('tokens,expected', [(70000,70000), (9007199254740991,9007199254740991), (9007199254740992,None), ('unsupported',None)])
def test_native_token_observation_is_not_an_api_cap(host, tokens, expected):
    _, _, create, transport = host
    result = json.loads(json.dumps(RESULT))
    result['metadata']['unified_execution_v1'].update(native_attempts=1,known_tokens=tokens)
    transport(f"import pathlib,sys; pathlib.Path(sys.argv[1],'report.sql').write_text({SQL!r}); print({json.dumps(result)!r})")
    c = create()
    try:
        row = finished(c,c.submit('known-native','invoice-sql'))
        assert row['state'] == 'completed' and row['passed']
        assert row['usage']['knownTokens'] == expected
        assert c.status()['allowance']['retained'] == 3
    finally: c.close()


def test_symlink_parent_before_dotdot_cannot_hide_configuration_reference(host):
    root, config, create, _ = host
    outside = config.parent / 'outside'
    outside.mkdir(mode=0o700)
    (outside/'nested').mkdir(mode=0o700)
    (config.parent/'link').symlink_to(outside/'nested',target_is_directory=True)
    (outside/'api.yml').write_text((config.parent/'api.yml').read_text())
    (outside/'api.yml').chmod(0o600)
    raw = json.loads(config.read_text())
    raw['api_config'] = 'link/../api.yml'
    config.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match='config_invalid'): create()


@pytest.mark.parametrize('stop', ['cancel', 'close', 'leader-exited'])
def test_owned_descendant_is_stopped_after_leader_exits(host, stop):
    root, _, create, transport = host
    child = ("import os,pathlib,signal,sys,time; "
             "signal.signal(signal.SIGINT,signal.SIG_IGN); "
             "pathlib.Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(60)")
    leader = ("import pathlib,signal,subprocess,sys,time; "
              "signal.signal(signal.SIGINT,lambda *args:sys.exit(0)); "
              "marker=pathlib.Path(sys.argv[1],'descendant.pid'); "
              f"subprocess.Popen([sys.executable,'-c',{child!r},str(marker)], "
              "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); "
              "\nwhile not marker.exists(): time.sleep(.01)\n")
    leader += f"print({json.dumps(RESULT)!r})\n" if stop == 'leader-exited' else 'time.sleep(60)\n'
    transport(leader)
    c = create()
    pid = None
    try:
        run = c.submit('descendant','invoice-sql')
        marker = root / ('workspace-'+run['runId']) / 'descendant.pid'
        for _ in range(200):
            if marker.exists(): break
            time.sleep(.01)
        pid = int(marker.read_text())
        if stop == 'cancel':
            c.cancel(run['runId']); finished(c,run)
        elif stop == 'close': c.close()
        else: finished(c,run)
        # A killed orphan can briefly be a zombie awaiting the OS reaper. A
        # running/sleeping descendant is a leaked owned process, even if its
        # original CLI leader exited successfully or promptly on SIGINT.
        for _ in range(100):
            state = subprocess.run(['ps','-p',str(pid),'-o','stat='],capture_output=True,text=True).stdout.strip()
            if not state or state.startswith('Z'): break
            time.sleep(.01)
        assert not state or state.startswith('Z'), f'owned descendant remains live: {state}'
    finally:
        c.close()
        if pid is not None:
            try: os.kill(pid,signal.SIGKILL)
            except ProcessLookupError: pass
