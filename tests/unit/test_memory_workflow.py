import uuid

import pytest
from prosaic_harness import FileRunStore, RunNotFound
from prosaic_runtime import EndpointConfig, RuntimeConfig

from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.memory_provider import MemoryProviders, MemoryUnavailable
from prosaic_integration_lab.memory_workflow import MemoryWorkflowSession


def session(tmp_path, *, required=False):
    store = FileRunStore(tmp_path / "runs", namespace="memory-test")
    flow = MemoryWorkflowSession(
        providers=MemoryProviders(),
        store=store,
        config=RuntimeConfig(
            {"fixture": EndpointConfig("http://127.0.0.1:9/v1", "synthetic")},
            {},
            "fixture",
        ),
        principal=Principal("tenant", "alice", "payer"),
        namespace="memory-test",
    )
    return flow, store


def test_disabled_workflow_freezes_status_and_replay_does_not_recapture(tmp_path):
    flow, store = session(tmp_path)
    run_id = uuid.uuid4().hex
    result = flow.start(run_id, task="what happened?", query="history")
    assert result["status"] == "waiting" and result["memory_status"] == "disabled"
    assert store.load_run(run_id).state["inputs"]["memory"] == {
        "status": "disabled",
        "bundle": None,
    }
    flow.providers.close()
    assert flow.start(run_id, task="what happened?", query="history") == result
    with pytest.raises(ValueError, match="conflict"):
        flow.start(run_id, task="different", query="history")
    flow.principal = Principal("other", "alice", "payer")
    with pytest.raises(PermissionError):
        flow.status(run_id)
    store.close()


def test_required_disabled_blocks_before_harness_creation(tmp_path):
    flow, store = session(tmp_path)
    run_id = uuid.uuid4().hex
    with pytest.raises(MemoryUnavailable, match="disabled"):
        flow.start(run_id, task="what happened?", query="history", required=True)
    with pytest.raises(RunNotFound):
        store.load_run(run_id)
    store.close()
