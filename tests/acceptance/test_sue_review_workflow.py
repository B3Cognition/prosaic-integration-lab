"""Required installed-wheel SUE lane: loopback inference and owned PostgreSQL."""

import hashlib
import importlib.metadata
import json
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid

import pytest
from prosaic_harness import FileRunStore
from prosaic_harness_postgres import PostgresRunStore
from prosaic_runtime import RateCard
from prosaic_runtime_postgres import PostgresRecorder


SOURCE = "Only administrators may export data. 🙂\r\nConsent must be current.\r\n"
CLAIM = "Administrators export with current consent."


@pytest.fixture(params=["file", "postgres"])
def sue_case(request, tmp_path):
    try:
        installed = importlib.metadata.distribution("prosaic-integration-lab")
    except importlib.metadata.PackageNotFoundError:
        pytest.fail("required SUE qualification must execute the installed Lab wheel")
    import prosaic_integration_lab

    assert Path(prosaic_integration_lab.__file__).resolve() == installed.locate_file(
        "prosaic_integration_lab/__init__.py"
    ).resolve(), "required SUE qualification must execute the installed Lab wheel"
    path = os.environ.get("LAB_SUE_FIXTURE")
    assert path, "required SUE lane needs explicit owned PostgreSQL infrastructure"
    fixture = json.loads(Path(path).read_text())
    namespace = "sue-" + uuid.uuid4().hex
    store = (
        FileRunStore(tmp_path / "runs", namespace=namespace)
        if request.param == "file"
        else PostgresRunStore(fixture["dsn"], namespace=namespace)
    )
    recorder = PostgresRecorder(
        fixture["dsn"], namespace=namespace, environment="sandbox",
        rate_card=RateCard("sue-fixture-v1", "sue-fixture", "2", "8", "0.5"),
    )
    try:
        yield fixture, namespace, store, recorder, request.param, tmp_path
    finally:
        store.close()


def host(case, url):
    fixture, namespace, _, _, kind, root = case
    value = {
        "namespace": namespace,
        "principal": {"tenant_id": "tenant-a", "actor_id": "alice", "billing_account_id": "payer-a"},
        "store": {"kind": "file", "path": str(root / "runs")} if kind == "file"
        else {"kind": "postgres", "dsn_env": "LAB_SUE_RUNTIME_DSN"},
        "runtime": {"base_url": url, "model": "sue-fixture"},
        "review": {"enabled": True},
        "accounting": {"dsn_env": "LAB_SUE_RUNTIME_DSN"},
    }
    path = root / "host.json"
    path.write_text(json.dumps(value))
    path.chmod(0o600)
    return path, value, {**os.environ, "LAB_SUE_RUNTIME_DSN": fixture["dsn"]}


def request_file(case, max_turns=14):
    root = case[-1]
    source = root / "source.md"
    source.write_bytes(SOURCE.encode("utf-8"))
    path = root / "request.json"
    path.write_text(json.dumps({"seed": CLAIM, "sources": [{"sourceId": "spec",
        "path": str(source), "revision": "r1", "reference": "fixture://spec"}], "max_turns": max_turns}))
    return path, source


def cli(config, env, action, run_id, *arguments, expected=0):
    result = subprocess.run(
        [sys.executable, "-I", "-m", "lab_runner.sue_review", action,
         "--config", str(config), "--run-id", run_id, *map(str, arguments)],
        env=env, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    return json.loads(result.stdout)


def test_cli_freezes_exact_utf8_and_resumes_with_owned_usage_after_source_deletion(sue_case):
    from lab_runner.sue_review_fixture import model_fixture

    _, namespace, store, recorder, _, _ = sue_case
    run_id = uuid.uuid4().hex
    with model_fixture() as (url, calls):
        config, value, env = host(sue_case, url)
        request, source = request_file(sue_case)
        waiting = cli(config, env, "start", run_id, "--request", request)
        assert waiting["status"] == "waiting" and waiting["attempts"] == 0
        assert calls == [] and recorder.calls(run_id=run_id) == []
        frozen = store.load_run(run_id).state["inputs"]["evidence"]
        assert frozen["sources"][0]["text"].encode("utf-8") == SOURCE.encode("utf-8")
        source.write_bytes(b"Changed after admission.")
        source.unlink()
        stale = cli(config, env, "resume", run_id, "--expected-revision", "0" * 64,
                    "--choice", "continue", expected=5)
        assert stale["error"] == "revision_conflict" and calls == []
        value["principal"]["actor_id"] = "bob"
        config.write_text(json.dumps(value))
        assert cli(config, env, "resume", run_id, "--expected-revision", waiting["revision"],
                   "--choice", "continue", expected=4) == {"error": "not_found"}
        assert calls == []
        value["principal"]["actor_id"] = "alice"
        config.write_text(json.dumps(value))
        done = cli(config, env, "resume", run_id, "--expected-revision", waiting["revision"],
                   "--choice", "continue")
        assert done["status"] == "completed" and done["terminal"] == "RESOLVED"
        assert done["acceptedTurns"] == 7 and len(calls) == 7
        assert store.load_run(run_id).state["inputs"]["evidence"] == frozen
        assert all(not call.get("tools") for call in calls)
        assert all("Changed after admission" not in json.dumps(call) for call in calls)
        assert SOURCE.splitlines()[0] in json.dumps(calls, ensure_ascii=False)
        rows = recorder.calls(run_id=run_id)
        assert len(rows) == 7
        for row in rows:
            context = row["intent"]["context"]
            assert {key: context[key] for key in ("application_id", "project_id", "tenant_id", "actor_id", "billing_account_id")} == {
                "application_id": "integration-lab-sue-review", "project_id": namespace,
                "tenant_id": "tenant-a", "actor_id": "alice", "billing_account_id": "payer-a",
            }
        cli(config, env, "resume", run_id, "--expected-revision", waiting["revision"],
            "--choice", "continue", expected=5)
        assert len(calls) == 7
        value["review"] = {"enabled": False}
        config.write_text(json.dumps(value))
        assert cli(config, env, "status", run_id)["status"] == "completed"
        report = cli(config, env, "report", run_id)
        assert report["advisory"] is True and report["acceptedTurns"] == 7
        assert report["usageComplete"] is True and report["reportedTokens"] == 105
        assert report["citations"][0]["quote"] == SOURCE.splitlines()[0]
        assert report["citations"][0]["sourceId"] == "spec"
        assert report["sources"][0]["textSha256"] == hashlib.sha256(SOURCE.encode("utf-8")).hexdigest()
        assert str(source) not in json.dumps(report)
        assert "rawResponse" not in report and "accounting_context" not in report
        assert cli(config, env, "resume", run_id, "--expected-revision", done["revision"],
                   expected=2) == {"error": "review_disabled"}
        assert len(calls) == 7


def test_rejection_and_disabled_start_dispatch_nothing(sue_case):
    from lab_runner.sue_review_fixture import model_fixture

    run_id = uuid.uuid4().hex
    with model_fixture() as (url, calls):
        config, value, env = host(sue_case, url)
        request, _ = request_file(sue_case)
        waiting = cli(config, env, "start", run_id, "--request", request)
        rejected = cli(config, env, "resume", run_id, "--expected-revision", waiting["revision"],
                       "--choice", "reject")
        assert rejected["status"] == "rejected" and rejected["acceptedTurns"] == 0
        value.pop("review")
        config.write_text(json.dumps(value))
        assert cli(config, env, "start", uuid.uuid4().hex, "--request", request,
                   expected=2) == {"error": "review_disabled"}
        assert calls == [] and sue_case[3].calls(run_id=run_id) == []


def test_unknown_usage_never_enters_accepted_history_or_authorizes_retry(sue_case):
    from lab_runner.sue_review_fixture import model_fixture

    run_id = uuid.uuid4().hex
    with model_fixture(usage=False) as (url, calls):
        config, _, env = host(sue_case, url)
        request, _ = request_file(sue_case, max_turns=1)
        waiting = cli(config, env, "start", run_id, "--request", request)
        stopped = cli(config, env, "resume", run_id, "--expected-revision", waiting["revision"],
                      "--choice", "continue")
        assert stopped["status"] == "blocked" and stopped["acceptedTurns"] == 0
        assert len(calls) == 1 and len(sue_case[3].calls(run_id=run_id)) == 1
        report = cli(config, env, "report", run_id)
        assert report["usageComplete"] is False and report["acceptedTurns"] == 0
        recovered = cli(config, env, "resume", run_id, "--expected-revision", stopped["revision"])
        assert recovered["status"] == "blocked" and len(calls) == 1


def test_absent_engine_fails_before_any_dispatch(sue_case):
    from lab_runner.sue_review_fixture import model_fixture

    with model_fixture() as (url, calls):
        config, _, env = host(sue_case, url)
        request, _ = request_file(sue_case)
        run_id = uuid.uuid4().hex
        script = """
import importlib.abc,sys
class AbsentEngine(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]=='castle_sue': raise ModuleNotFoundError(name)
sys.meta_path.insert(0,AbsentEngine())
from lab_runner.sue_review import main
raise SystemExit(main(sys.argv[1:]))
"""
        result = subprocess.run([sys.executable, "-I", "-c", script, "start", "--config", str(config),
            "--request", str(request), "--run-id", run_id], env=env, capture_output=True, text=True, timeout=20)
        assert result.returncode == 2 and json.loads(result.stdout) == {"error": "engine_unavailable"}
        assert calls == [] and sue_case[3].calls(run_id=run_id) == []


@pytest.mark.parametrize("sue_case", ["file"], indirect=True)
def test_process_loss_before_receipt_remains_unknown_without_redispatch(sue_case):
    from lab_runner.sue_review_fixture import model_fixture

    script = """
import os,sys
from lab_runner.sue_review import load_host
from lab_runner.memory_workflow import store_for
from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.sue_review.session import SueReviewSession
from prosaic_runtime import EndpointConfig,RuntimeConfig,RateCard
from prosaic_runtime_postgres import PostgresRecorder
host=load_host(sys.argv[1])
base=store_for(host)
class InterruptedStore:
    def __getattr__(self,name): return getattr(base,name)
    def save_receipt(self,*args,**kwargs): os._exit(71)
config=RuntimeConfig({'fixture':EndpointConfig(host['runtime']['base_url'],'sue-fixture',features={'streaming':False})},{},'fixture',allowed_tools=frozenset())
recorder=PostgresRecorder(os.environ[host['accounting']['dsn_env']],namespace=host['namespace'],environment='sandbox',rate_card=RateCard('sue-fixture-v1','sue-fixture','2','8','0.5'))
flow=SueReviewSession(settings=host['review'],store=InterruptedStore(),config=config,principal=Principal(**host['principal']),namespace=host['namespace'],accounting=recorder)
flow.resume(sys.argv[2],expected_revision=sys.argv[3],choice='continue')
raise SystemExit(99)
"""
    run_id = uuid.uuid4().hex
    with model_fixture() as (url, calls):
        config, _, env = host(sue_case, url)
        request, _ = request_file(sue_case, max_turns=1)
        waiting = cli(config, env, "start", run_id, "--request", request)
        lost = subprocess.run([sys.executable, "-I", "-c", script, str(config), run_id, waiting["revision"]],
            env=env, capture_output=True, text=True, timeout=30)
        assert lost.returncode == 71, lost.stdout + lost.stderr
        current = cli(config, env, "status", run_id)
        recovered = cli(config, env, "resume", run_id, "--expected-revision", current["revision"])
        assert recovered["status"] == "blocked" and recovered["reason"] == "interrupted_call"
        assert recovered["acceptedTurns"] == 0 and len(calls) == 1
        assert len(sue_case[3].calls(run_id=run_id)) == 1
        assert cli(config, env, "report", run_id)["usageComplete"] is False
        cli(config, env, "resume", run_id, "--expected-revision", recovered["revision"])
        assert len(calls) == 1


def test_concurrent_cli_decisions_accept_once_without_extra_calls_or_usage(sue_case):
    from lab_runner.sue_review_fixture import model_fixture

    run_id = uuid.uuid4().hex
    release_response = threading.Event()
    # Hold the first actual provider response until the competing CLI exits.
    # This proves overlapping executions without relying on scheduler timing.
    with model_fixture(first_response_gate=release_response) as (url, calls):
        config, _, env = host(sue_case, url)
        request, _ = request_file(sue_case)
        waiting = cli(config, env, "start", run_id, "--request", request)
        barrier = threading.Barrier(2)

        def continue_process():
            barrier.wait(timeout=10)
            return subprocess.run([
                sys.executable, "-I", "-m", "lab_runner.sue_review", "resume",
                "--config", str(config), "--run-id", run_id,
                "--expected-revision", waiting["revision"], "--choice", "continue",
            ], env=env, capture_output=True, text=True, timeout=45)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(continue_process) for _ in range(2)]
            try:
                completed, pending = wait(futures, timeout=20, return_when=FIRST_COMPLETED)
                assert len(completed) == 1 and len(pending) == 1
                loser = next(iter(completed)).result()
                assert loser.returncode == 5, loser.stdout + loser.stderr
                assert json.loads(loser.stdout) == {"error": "run_busy"}
                assert "Traceback" not in loser.stderr
            finally:
                release_response.set()
            winner = next(iter(pending)).result(timeout=30)
        assert winner.returncode == 0, winner.stdout + winner.stderr
        result = json.loads(winner.stdout)
        assert result["status"] == "completed" and result["acceptedTurns"] == 7
        assert result["terminal"] == "RESOLVED" and len(calls) == 7
        state = sue_case[2].load_run(run_id).state
        decisions = [event for event in state["history"] if event["event"] == "human_decision"]
        assert len(decisions) == 1 and decisions[0]["choice"] == "continue"
        assert len(state["outputs"]) == 7 and len(sue_case[3].calls(run_id=run_id)) == 7
        report = cli(config, env, "report", run_id)
        assert report["attempts"] == 7 and report["reportedTokens"] == 105
        assert report["usageComplete"] is True


def test_saved_receipt_is_adopted_after_process_loss_without_repeating_call(sue_case):
    from lab_runner.sue_review_fixture import model_fixture

    script = """
import os,sys
from lab_runner.sue_review import load_host
from prosaic_harness import FileRunStore
from prosaic_harness_postgres import PostgresRunStore
from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.sue_review.session import SueReviewSession
from prosaic_runtime import EndpointConfig,RuntimeConfig,RateCard
from prosaic_runtime_postgres import PostgresRecorder
host=load_host(sys.argv[1])
if host['store']['kind']=='file':
    base=FileRunStore(host['store']['path'],namespace=host['namespace'])
else:
    base=PostgresRunStore(os.environ[host['store']['dsn_env']],namespace=host['namespace'],lease_s=15,renew_s=1,operation_timeout_s=2)
class InterruptedStore:
    def __getattr__(self,name): return getattr(base,name)
    def save_receipt(self,*args,**kwargs):
        base.save_receipt(*args,**kwargs)
        os._exit(72)
config=RuntimeConfig({'fixture':EndpointConfig(host['runtime']['base_url'],'sue-fixture',features={'streaming':False})},{},'fixture',allowed_tools=frozenset())
recorder=PostgresRecorder(os.environ[host['accounting']['dsn_env']],namespace=host['namespace'],environment='sandbox',rate_card=RateCard('sue-fixture-v1','sue-fixture','2','8','0.5'))
flow=SueReviewSession(settings=host['review'],store=InterruptedStore(),config=config,principal=Principal(**host['principal']),namespace=host['namespace'],accounting=recorder)
flow.resume(sys.argv[2],expected_revision=sys.argv[3],choice='continue')
raise SystemExit(99)
"""
    run_id = uuid.uuid4().hex
    with model_fixture() as (url, calls):
        config, _, env = host(sue_case, url)
        request, source = request_file(sue_case, max_turns=1)
        waiting = cli(config, env, "start", run_id, "--request", request)
        frozen = sue_case[2].load_run(run_id).state["inputs"]["evidence"]
        lost = subprocess.run([sys.executable, "-I", "-c", script, str(config), run_id, waiting["revision"]],
            env=env, capture_output=True, text=True, timeout=30)
        assert lost.returncode == 72, lost.stdout + lost.stderr
        assert len(calls) == 1 and len(sue_case[3].calls(run_id=run_id)) == 1
        # A dead PostgreSQL owner retains its database lease until expiration.
        # Use the public constructor's minimum admitted duration, never mutate
        # a lease row or patch the installed adapter to manufacture recovery.
        if sue_case[4] == "postgres":
            time.sleep(16)
        source.unlink()
        current = cli(config, env, "status", run_id)
        assert current["acceptedTurns"] == 0
        recovered = cli(config, env, "resume", run_id, "--expected-revision", current["revision"])
        assert recovered["status"] == "completed" and recovered["terminal"] == "BOUNDED_STOP"
        assert recovered["acceptedTurns"] == 1 and len(calls) == 1
        assert sue_case[2].load_run(run_id).state["inputs"]["evidence"] == frozen
        report = cli(config, env, "report", run_id)
        assert report["usageComplete"] is True and report["reportedTokens"] == 15
        assert report["citations"][0]["quote"] == SOURCE.splitlines()[0]
        cli(config, env, "resume", run_id, "--expected-revision", recovered["revision"])
        assert len(calls) == 1 and len(sue_case[3].calls(run_id=run_id)) == 1


def test_disabled_qualification_allocates_no_database_or_engine():
    script = """
import importlib.abc,sys
class Forbidden(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'psycopg','castle_sue','cognitive_castle'}: raise AssertionError(name)
sys.meta_path.insert(0,Forbidden())
from lab_runner.sue_review_fixture import main
raise SystemExit(main([]))
"""
    result = subprocess.run([sys.executable, "-I", "-c", script], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {"enabled": False, "qualified": False, "reason": "disabled"}
