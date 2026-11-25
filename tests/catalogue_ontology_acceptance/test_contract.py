"""Check experimental disclosure and admission through the installed SDKs."""

import json
import os
import runpy
import subprocess
import sys

from prosaic.ontology import load_ontology
from prosaic_harness import WorkflowAdmissionError, WorkflowBindings, WorkflowCatalog, WorkflowFactory, WorkflowPolicy
from prosaic_runtime import CustomTool, EndpointConfig, ProsaicArtifact, RuntimeConfig
import pytest
import yaml


def _unexpected_call(_arguments):
    raise AssertionError("Discovery or admission ran a tool")


def _factory(ontology, schema, *, visible_agents=("reviewer",), runtime_tools=("read_receipt",),
             direct_tools=("read_receipt",)):
    agents = {
        name: ProsaicArtifact(
            f"subagents/{name}.md", "subagent",
            {"name": name, "description": "Fixture reviewer.", "tools": [tool]},
            "Fixture reviewer.",
        )
        for name, tool in (("reviewer", "read_receipt"), ("private-reviewer", "read_policy"))
    }
    parameters = {"type": "object", "additionalProperties": False}
    tools = {
        name: CustomTool(name, "Fixture tool", parameters, _unexpected_call, "1")
        for name in ("read_receipt", "read_policy")
    }
    return WorkflowFactory(
        catalog=WorkflowCatalog(agents=agents, schemas={"receipt": schema}, ontology=ontology),
        bindings=WorkflowBindings(
            config=RuntimeConfig(
                {"fixture": EndpointConfig("http://127.0.0.1:1/v1", "unused")}, {}, "fixture",
                allowed_tools=frozenset(runtime_tools),
            ),
            custom_tools=tools,
        ),
        policy=WorkflowPolicy(
            allowed_agents=visible_agents, allowed_schemas={"receipt"}, allowed_tools=set(tools),
            allowed_direct_tools=direct_tools, max_provider_requests_per_invocation=0,
            max_tool_calls_per_invocation=1,
        ),
    )


@pytest.fixture
def attachment(copied_blueprint):
    return load_ontology(copied_blueprint / "fixtures/attachment.json")


@pytest.fixture
def receipt_schema(copied_blueprint):
    return json.loads((copied_blueprint / "receipt.schema.json").read_bytes())


def test_discovery_and_execution_are_offline(copied_blueprint, tmp_path):
    storage = tmp_path / "owned-storage"
    storage.mkdir()
    script = """
import json
from pathlib import Path
import runpy
import sys

attempts = []

def offline(event, _args):
    if event.startswith("socket.") or event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.system"):
        attempts.append(event)
        raise AssertionError(f"Unexpected external operation: {event}")

sys.addaudithook(offline)
project = Path(sys.argv[1])
host = runpy.run_path(str(project / "host.py"))
baseline = host["build_factory"](project)
attached = host["build_factory"](project, attach_ontology=True)
assert baseline.describe() == attached.describe()
assert baseline.proposal_schema() == attached.proposal_schema()
plain = host["build_workflow"](project, baseline)
enriched = host["build_workflow"](project, attached)
assert plain.fingerprint == enriched.fingerprint
first = host["run_demo"](plain)
assert first == host["run_demo"](enriched) == {
    "status": "completed",
    "receipt": {"candidateId": "fixture-17", "receiptId": "receipt-17", "check": "passed"},
}
public = json.dumps([baseline.describe(), attached.describe(include_ontology=True), first])
for marker in ("private-reviewer", "read_policy", "private-policy", "unattached"):
    assert marker not in public
assert not attempts
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(copied_blueprint)],
        cwd=tmp_path, env={**os.environ, "TMPDIR": str(storage)}, text=True,
        capture_output=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert not list(storage.iterdir())


def test_projection_is_opt_in_scoped_and_detached(copied_blueprint, attachment, receipt_schema):
    factory = _factory(attachment, receipt_schema)
    expected = json.loads((copied_blueprint / "fixtures/visible.json").read_bytes())
    assert "ontology" not in factory.describe()
    assert _factory(None, receipt_schema).describe(include_ontology=True) == factory.describe()

    enriched = factory.describe(include_ontology=True)
    assert enriched["ontology"] == expected
    assert set(enriched["agents"]) == {"reviewer"}
    assert set(enriched["tools"]) == {"read_receipt"}
    assert set(enriched["ontology"]["concepts"]) == {"candidate", "receipt"}
    assert enriched["ontology"]["relations"] == [
        {"source": "receipt", "predicate": "verifies", "target": "candidate"},
    ]

    attachment["concepts"]["receipt"] = "Caller mutation."
    enriched["ontology"]["concepts"].clear()
    assert factory.describe(include_ontology=True)["ontology"] == expected
    denied = _factory(attachment, receipt_schema, visible_agents=(), runtime_tools=(), direct_tools=())
    assert "ontology" not in denied.describe(include_ontology=True)


def test_discovery_bounds_combined_response(attachment, receipt_schema):
    factory = _factory(attachment, receipt_schema)
    plain = factory.describe()
    enriched = factory.describe(include_ontology=True)
    sizes = [len(json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode())
             for doc in (plain, enriched)]
    maximum_bytes = sum(sizes) // 2
    assert factory.describe(maximum_bytes=maximum_bytes) == plain
    with pytest.raises(WorkflowAdmissionError):
        factory.describe(include_ontology=True, maximum_bytes=maximum_bytes)


@pytest.mark.parametrize("kind", ["malformed-json", "duplicate-key", "unknown-concept"])
def test_core_rejects_invalid_attachments(kind, tmp_path, copied_blueprint, attachment):
    source = tmp_path / "invalid.json"
    if kind == "malformed-json":
        value = "{"
    elif kind == "duplicate-key":
        fixture = (copied_blueprint / "fixtures/attachment.json").read_text(encoding="utf-8")
        value = fixture.replace('"schemaVersion": 1,', '"schemaVersion": 1, "schemaVersion": 1,', 1)
        assert value != fixture
    else:
        attachment["relations"][0]["target"] = "unregistered-concept"
        value = json.dumps(attachment)
    source.write_text(value, encoding="utf-8")
    with pytest.raises(ValueError):
        load_ontology(source)


@pytest.mark.parametrize("category", ["agents", "tools"])
def test_unregistered_aliases_are_rejected(category, attachment, receipt_schema):
    attachment[category]["unregistered"] = ["receipt"]
    with pytest.raises(WorkflowAdmissionError, match="unknown_reference"):
        _factory(attachment, receipt_schema)


def test_workflow_admission_ignores_ontology_authority(copied_blueprint, attachment, receipt_schema):
    host = runpy.run_path(str(copied_blueprint / "host.py"))
    factory = host["build_factory"](copied_blueprint, attach_ontology=True)
    graph = yaml.safe_load((copied_blueprint / "workflow.yml").read_text(encoding="utf-8"))
    with pytest.raises(WorkflowAdmissionError, match="invalid_definition"):
        factory.build({**graph, "ontology": attachment})
    with pytest.raises(WorkflowAdmissionError, match="invalid_definition"):
        factory.build_json(json.dumps({"definition": graph, "ontology": attachment}))

    assert _factory(attachment, receipt_schema).build(graph).definition["start"] == "read"
    no_direct_grant = _factory(attachment, receipt_schema, direct_tools=())
    assert "read_receipt" in no_direct_grant.describe(include_ontology=True)["ontology"]["tools"]
    with pytest.raises(WorkflowAdmissionError):
        no_direct_grant.build(graph)

    graph["steps"]["read"]["tool"] = "read_policy"
    with pytest.raises(WorkflowAdmissionError):
        factory.build(graph)
