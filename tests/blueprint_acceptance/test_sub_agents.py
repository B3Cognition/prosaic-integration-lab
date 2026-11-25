"""Copy the blueprint and run it using only installed SDK entry points."""
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

import pytest


@pytest.fixture
def copied_blueprint(tmp_path):
    if os.environ.get("PROSAIC_SUB_AGENTS_REQUIRED") != "1":
        pytest.skip("installed delegation lane")
    from lab_runner.blueprints import copy_blueprint
    from prosaic_integration_lab.sub_agents import require_sub_agent_sdk

    require_sub_agent_sdk()
    root = copy_blueprint("sub-agents", tmp_path / "graph")
    spec = importlib.util.spec_from_file_location("copied_delegate_host", root / "host.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (root / "NOTICE").is_file() and (root / "LICENSE").is_file()
    return root, module


@pytest.fixture
def journal():
    from prosaic_runtime import ToolClaim

    class Journal:
        contract_version = "tool-journal-v1"
        identity = "copied-host"
        version = "1"

        def claim(self, _namespace, _key, signature):
            return ToolClaim("new", signature, "token")

        def commit(self, _namespace, _key, token, _outcome):
            assert token == "token"

    return Journal()


@pytest.mark.parametrize("provider", ["openai-compatible", "anthropic"])
@pytest.mark.parametrize("case", ["siblings", "scope-and-citations"])
def test_copied_sub_agent_host(copied_blueprint, journal, provider, case):
    from prosaic_harness import MemorySessionStore
    from prosaic_runtime.accounting import MemoryRecorder
    from prosaic_integration_lab.sub_agents import run_case

    _, module = copied_blueprint
    store = MemorySessionStore(namespace="copied-host")
    store.initialize(sub_agents=True)
    run_case(case, provider, journal=journal, store=store, recorder=MemoryRecorder(provider_id=provider),
             build_host=module.build_host)


@pytest.mark.parametrize("provider", ["openai-compatible", "anthropic"])
def test_copied_yaml_workflow(copied_blueprint, tmp_path, journal, provider):
    import yaml
    from lab_runner.parallel_tools import endpoint
    from prosaic_harness import ContextScope, FileRunStore, Harness
    from prosaic_runtime import EvidenceDraftV1, ExecutionContext, ToolResultV1
    from prosaic_runtime.accounting import MemoryRecorder
    from prosaic_integration_lab.sub_agents import calls

    root, module = copied_blueprint
    scope = ContextScope("copied-host", "sandbox", "graph", "tenant", "actor", "payer")
    context = ExecutionContext(application_id="graph", tenant_id="tenant", actor_id="actor",
                               billing_account_id="payer")
    reads = []

    def lookup():
        reads.append("graph")
        return ToolResultV1(data={"relationship": "api → worker → kafka"}, evidence=(
            EvidenceDraftV1("service-graph", "1", "private-location", "/relationship", "Dependency"),))

    def finish(payload):
        evidence = re.findall(r"ev_[0-9a-f]{64}", json.dumps(payload))
        assert evidence
        return json.dumps({"supported": True, "summary": f"Kafka is reachable [cite:{evidence[0]}]"})

    with endpoint(provider) as (url, wire, replies):
        runtime = root / "runtime.yml"
        config = yaml.safe_load(runtime.read_text())
        config["profiles"]["local"].update(base_url=url, model="synthetic", provider=provider)
        runtime.write_text(yaml.safe_dump(config))
        flow = module.build_workflow(scope, journal=journal, namespace="copied-workflow",
            documents={"analyze": "Analyst graph brief", "review": "Reviewer checklist"}, lookup=lookup,
            authorize_pack=lambda _: True, authorize_launch=lambda *_: True,
            authorize_result=lambda *_: True, authorize_evidence=lambda _: True,
            executable=str(Path(sys.executable).with_name("prosaic")))
        store = FileRunStore(tmp_path / "run-store", namespace="copied-host")
        store.initialize(sub_agents=True)
        replies[:] = [
            calls("analyze", {"task": "Trace the Kafka dependency"}),
            calls("graph_lookup"),
            '{"finding":"Kafka is reachable"}',
            calls("review", {"task": "Review the proposed claim", "draft": {"claim": "Kafka is reachable"}}),
            '{"finding":"The claim is supported"}',
            finish,
        ]
        with store:
            state = Harness(flow, store=store, run_id="a" * 32, context=context,
                            accounting=MemoryRecorder(provider_id=provider)).run({"question": "Can api reach Kafka?"})

    assert state["status"] == "completed"
    assert state["outputs"]["review_dependencies"]["supported"] is True
    assert "[cite:ev_" in state["outputs"]["review_dependencies"]["summary"]
    assert len(wire) == 6 and reads == ["graph"]
    assert "Analyst graph brief" in json.dumps(wire[1])
    assert "Reviewer checklist" not in json.dumps(wire[1])
    assert "Reviewer checklist" in json.dumps(wire[4])
    assert "Analyst graph brief" not in json.dumps(wire[4])
    assert "private-location" not in json.dumps(wire[5])
