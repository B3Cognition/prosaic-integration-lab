import json
import pytest
import subprocess
import sys
import httpx
from lab_runner import workload


def test_cli_starts_without_editable_consumer_install():
    result = subprocess.run([sys.executable, '-m', 'lab_runner', '--help'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_approval_capacity_preserves_waiting_state_but_other_503_fails():
    request = httpx.Request('POST', 'http://fixture/runs/example/resume')
    assert workload.approval_status(httpx.Response(503, request=request,
        json={'detail': 'capacity_exhausted'})) == 'waiting'
    assert workload.approval_status(httpx.Response(200, request=request,
        json={'status': 'completed'})) == 'completed'
    with pytest.raises(httpx.HTTPStatusError):
        workload.approval_status(httpx.Response(503, request=request, json={'detail': 'unavailable'}))


@pytest.mark.parametrize('ledger_calls,denial_status,passed', [(1, 404, True), (2, 404, False), (1, 200, False)])
def test_workload_accounts_deferred_approval_and_fails_bad_evidence_or_isolation(
        tmp_path, monkeypatch, ledger_calls, denial_status, passed):
    usage = {'version': 1, 'total_calls': ledger_calls, 'complete_calls': ledger_calls,
        'unresolved_calls': 0, 'quarantined_calls': 0, 'unsupported_calls': 0,
        'partial_calls': 0, 'unavailable_assessment_calls': 0,
        'estimated_amounts': {'USD': '0.00037'}, 'fully_costed': True,
        'billing_eligible': False, 'coverage': [], 'excluded_resources': [], 'as_of': 'fixture'}
    calls = 0
    def endpoint(request):
        nonlocal calls
        if request.url.path == '/stats':
            return httpx.Response(200, json={'calls': calls})
        if request.method == 'POST' and request.url.path == '/runs':
            calls += 1
            return httpx.Response(200, json={'run_id': 'fixture-run', 'status': 'waiting',
                'revision': 'fixture-revision', 'current_step': 'review', 'choices': ['approve', 'reject'],
                'recovery_status': None})
        if request.method == 'POST':
            return httpx.Response(503, json={'detail': 'capacity_exhausted'})
        if request.headers['Authorization'] == 'Bearer other':
            return httpx.Response(denial_status, json={'detail': 'not_found'})
        return httpx.Response(200, json=usage)
    original_client = httpx.Client
    class Recorder:
        def __init__(self, *args, **kwargs):
            pass
        def report(self, **kwargs):
            return usage
    monkeypatch.setattr(workload, 'PostgresRecorder', Recorder)
    config = {'a': 'http://a', 'b': 'http://b', 'model': 'http://model',
        'accounting_dsn': 'fixture', 'namespace': 'fixture', 'environment': 'sandbox',
        'principals': {'owner': workload.identities(2)[0], 'other': workload.identities(2)[1]}}
    # Two trusted users exist so isolation is checked; second session's start is
    # capacity-rejected before dispatch. The first retains one accounted call.
    original_endpoint = endpoint
    def bounded_endpoint(request):
        if request.method == 'POST' and request.url.path == '/runs' and request.headers['Authorization'] == 'Bearer other':
            return httpx.Response(503, json={'detail': 'capacity_exhausted'})
        return original_endpoint(request)
    monkeypatch.setattr(workload.httpx, 'Client', lambda **kwargs:
        original_client(transport=httpx.MockTransport(bounded_endpoint), **kwargs))
    result = workload.run(config, 2, 1, 1, workload.Events(tmp_path), allow_overload=True)
    assert result['passed'] is passed
    assert result['completed'] == 0
    if passed:
        assert result['approval_deferred'] == 1
        assert result['start_capacity_rejected'] == 1
        assert result['independent_model_calls'] == 1


def test_fixture_users_are_distinct_and_cross_tenant():
    identities = workload.identities(7)
    assert len({p['actor_id'] for p in identities}) == 7
    assert {p['tenant_id'] for p in identities} == {'tenant-a', 'tenant-b'}
    with pytest.raises(ValueError):
        workload.identities(0)


def test_stream_replays_accounting_separately_and_stops(tmp_path, capsys):
    events = workload.Events(tmp_path)
    events.emit('requests', operation='start', actor='alice', status=200)
    events.emit('accounting', actor='alice', calls=1, complete=1, unknown=0, usd='0.00037')
    events.finish({'passed': True, 'cleanup': 'verified'})
    capsys.readouterr()  # Observe only the second terminal's replay.
    workload.watch(tmp_path, 'accounting')
    output = capsys.readouterr().out
    assert '0.00037' in output
    assert 'operation' not in output
    assert json.loads((tmp_path / 'finished.json').read_text())['cleanup'] == 'verified'


def test_invalid_workload_bounds_fail_before_provisioning():
    with pytest.raises(ValueError):
        workload.validate(100, 101, 4)
    with pytest.raises(ValueError):
        workload.validate(3, 1, 0)


def test_watcher_waits_for_new_evidence_then_exits_after_cleanup(tmp_path):
    events = workload.Events(tmp_path)
    observer = subprocess.Popen([sys.executable, '-m', 'lab_runner', 'watch',
        '--directory', str(tmp_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            observer.communicate(timeout=0.3)
        events.emit('accounting', calls=2, unknown=1, usd=None)
        events.finish({'passed': False, 'cleanup': 'verified'})
        output, error = observer.communicate(timeout=3)
        assert observer.returncode == 0, error
        assert '"unknown": 1' in output
        assert '"usd": null' in output
        assert '"cleanup": "verified"' in output
    finally:
        if observer.poll() is None:
            observer.kill()
            observer.communicate()
