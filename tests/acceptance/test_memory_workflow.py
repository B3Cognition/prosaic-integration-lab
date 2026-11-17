"""Required explicit lane: real worker, installed SDKs, loopback model and SQL."""

import json
import importlib.metadata
from contextlib import closing
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest
from prosaic_harness import FileRunStore, RunNotFound
from prosaic_harness_postgres import PostgresRunStore
from prosaic_runtime import EndpointConfig, RateCard, RuntimeConfig
from prosaic_runtime_postgres import PostgresRecorder

from lab_runner.memory_fixture import memory_settings, model_fixture, prepare_castle
from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.memory_provider import MemoryProviders, MemoryUnavailable
from prosaic_integration_lab.memory_workflow import MemoryWorkflowSession


OWNER = Principal("tenant-a", "alice", "payer-a")


@pytest.fixture(params=["file", "postgres"])
def memory_case(request, tmp_path):
    import prosaic_integration_lab

    installed = importlib.metadata.distribution("prosaic-integration-lab")
    assert (
        Path(prosaic_integration_lab.__file__).resolve()
        == installed.locate_file("prosaic_integration_lab/__init__.py").resolve()
    ), "explicit memory qualification must execute the installed Lab wheel"
    path = os.environ.get("LAB_MEMORY_FIXTURE")
    assert path, "required memory lane needs explicit owned fixture infrastructure"
    fixture = json.loads(Path(path).read_text())
    namespace = "memory-" + uuid.uuid4().hex
    store = (
        FileRunStore(tmp_path / "runs", namespace=namespace)
        if request.param == "file"
        else PostgresRunStore(fixture["dsn"], namespace=namespace)
    )
    recorder = PostgresRecorder(
        fixture["dsn"],
        namespace=namespace,
        environment="sandbox",
        rate_card=RateCard("memory-fixture-v1", "memory-fixture", "2", "8", "0.5"),
    )
    try:
        yield fixture, namespace, store, recorder, request.param, tmp_path
    finally:
        store.close()


def flow(case, providers, url):
    _, namespace, store, recorder, _, _ = case
    return MemoryWorkflowSession(
        providers=providers,
        store=store,
        accounting=recorder,
        config=RuntimeConfig(
            {
                "fixture": EndpointConfig(
                    url, "memory-fixture", features={"streaming": False}
                )
            },
            {},
            "fixture",
        ),
        principal=OWNER,
        namespace=namespace,
    )


def resume_process(case, url, run_id, revision, status):
    fixture, namespace, store, _, kind, root = case
    host = {
        "namespace": namespace,
        "principal": dict(vars(OWNER)),
        "memory": {"enabled": False},
        "runtime": {"base_url": url, "model": "memory-fixture"},
        "store": {"kind": "file", "path": str(root / "runs")}
        if kind == "file"
        else {"kind": "postgres", "dsn_env": "LAB_MEMORY_RUNTIME_DSN"},
        "accounting": {"dsn_env": "LAB_MEMORY_RUNTIME_DSN"},
    }
    path = root / "host.json"
    path.write_text(json.dumps(host))
    path.chmod(0o600)
    command = [
        sys.executable,
        "-I",
        "-m",
        "lab_runner.memory_workflow",
        "resume",
        "--config",
        str(path),
        "--run-id",
        run_id,
        "--expected-revision",
        revision,
        "--choice",
        "continue",
    ]
    result = subprocess.run(
        command,
        env={**os.environ, "LAB_MEMORY_RUNTIME_DSN": fixture["dsn"]},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    value = json.loads(result.stdout)
    assert value["status"] == "completed" and value["memory_status"] == status
    return command, host, path


def test_actual_castle_snapshot_survives_changed_source_and_cross_process_resume(
    memory_case,
):
    fixture, _, store, recorder, _, root = memory_case
    castle = root / "castle"
    prepare_castle(fixture["worker_python"], castle)
    providers = MemoryProviders(memory_settings(fixture["worker_python"], castle))
    run_id = uuid.uuid4().hex
    with closing(providers), model_fixture("available") as (url, requests):
        session = flow(memory_case, providers, url)
        waiting = session.start(
            run_id,
            task="Explain the SQLite decision",
            query="SQLite offline",
            required=True,
        )
        assert waiting["status"] == "waiting" and not requests
        frozen = store.load_run(run_id).state["inputs"]["memory"]
        assert frozen["bundle"]["texts"] == [
            "Atlas chose SQLite for offline persistence. 🙂\r\nExact original evidence.\r\n"
        ]
        assert [s["record_id"] for s in frozen["bundle"]["sources"]] == ["own"]
        providers.close()
        trace = (castle / "operations.log").read_text()
        assert trace.splitlines() == ["hello", "search", "snapshot"]
        assert not (castle / "operations.forbidden").exists()
        child = int((castle / "operations.pid").read_text())
        with pytest.raises(ProcessLookupError):
            os.kill(child, 0)
        prepare_castle(fixture["worker_python"], castle, mutate=True)
        command, host, path = resume_process(
            memory_case, url, run_id, waiting["revision"], "available"
        )
        assert store.load_run(run_id).state["inputs"]["memory"] == frozen
        assert (castle / "operations.log").read_text() == trace
        assert not (castle / "operations.forbidden").exists()
        assert len(requests) == 1
        messages = requests[0]["messages"]
        assert "Exact original evidence" in json.dumps(
            messages
        ) and "Changed source" not in json.dumps(messages)
        assert all(
            "Exact original evidence" not in m.get("content", "")
            for m in messages
            if m["role"] == "system"
        )
        assert not requests[0].get("tools")
        calls = recorder.calls(run_id=run_id)
        assert len(calls) == 1
        assert all(
            row["intent"]["context"]["billing_account_id"] == "payer-a" for row in calls
        )
        replay = subprocess.run(
            command,
            env={**os.environ, "LAB_MEMORY_RUNTIME_DSN": fixture["dsn"]},
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert replay.returncode in (0, 5) and len(requests) == 1
        host["principal"]["actor_id"] = "bob"
        path.write_text(json.dumps(host))
        denied = subprocess.run(
            command,
            env={**os.environ, "LAB_MEMORY_RUNTIME_DSN": fixture["dsn"]},
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert denied.returncode == 4 and len(requests) == 1


def test_unavailable_optional_continues_required_blocks_before_run(memory_case):
    fixture, _, store, _, _, root = memory_case
    settings = memory_settings(fixture["worker_python"], root / "absent")
    settings["bindings"][0]["worker_command"] = [str(root / "missing-worker")]
    providers = MemoryProviders(settings)
    with closing(providers), model_fixture("unavailable") as (url, requests):
        session = flow(memory_case, providers, url)
        required_id = uuid.uuid4().hex
        with pytest.raises(MemoryUnavailable):
            session.start(
                required_id,
                task="Explain missing memory",
                query="SQLite",
                required=True,
            )
        with pytest.raises(RunNotFound):
            store.load_run(required_id)
        assert not requests
        run_id = uuid.uuid4().hex
        waiting = session.start(run_id, task="Explain missing memory", query="SQLite")
        assert waiting["memory_status"] == "unavailable" and not requests
        providers.close()
        resume_process(memory_case, url, run_id, waiting["revision"], "unavailable")
        assert len(requests) == 1 and "unavailable" in json.dumps(
            requests[0]["messages"]
        )


def test_disabled_default_creates_no_castle_and_keeps_explicit_status(memory_case):
    _, _, _, _, _, _ = memory_case
    providers = MemoryProviders()
    with closing(providers), model_fixture("disabled") as (url, requests):
        session = flow(memory_case, providers, url)
        run_id = uuid.uuid4().hex
        waiting = session.start(
            run_id, task="Work without optional memory", query="history"
        )
        assert (
            waiting["status"] == "waiting"
            and waiting["memory_status"] == "disabled"
            and not requests
        )
        resume_process(memory_case, url, run_id, waiting["revision"], "disabled")
        assert len(requests) == 1
