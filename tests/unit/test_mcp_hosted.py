from copy import deepcopy
import json
from pathlib import Path

import pytest

from lab_runner.gates import (ALL_COUNTS, MCP_CLIENT_RELEASE_TRAIN, expected_test_count,
                              required_modes, supports_mcp_client)
from lab_runner.mcp_client import RETAINED_WHEELS
from prosaic_integration_lab.mcp_client import CASES, TRAIN


def candidate_manifest():
    published = json.loads(Path("dependencies/releases-pre-mcp-client-2026-11-11.json").read_text())
    artifacts = [item for item in published["artifacts"] if item["distribution"] in RETAINED_WHEELS]
    lineage = {"version": 1, "kind": "local-mcp-client-handoff", "candidates": [],
               "retained_artifacts": list(artifacts)}
    for sdk in ("runtime", "harness"):
        name = f"b3-prosaic-{sdk}"
        wheel = {"filename": f"{name.replace('-', '_')}-{TRAIN[name]}-py3-none-any.whl",
                 "sha256": "a" * 64}
        receipt = {"source_commit": "b" * 40, "artifacts": [wheel],
                   "distributions": [{"name": name, "version": TRAIN[name]}]}
        qualification = {"source_commit": receipt["source_commit"], "artifacts": [wheel],
                         "label": "mcp-client-consumer", "exit_code": 0,
                         "command": ["python", "-I", "-m", "pytest", "tests/test_mcp_installed.py"],
                         "result_counts": {"tests": 2, "skipped": 0, "failures": 0, "errors": 0}}
        candidate = {"sdk": sdk, "receipt": receipt, "qualification": qualification}
        if sdk == "harness":
            runtime = lineage["candidates"][0]
            candidate.update(runtime_receipt=deepcopy(runtime["receipt"]),
                             runtime_qualification=deepcopy(runtime["qualification"]))
        lineage["candidates"].append(candidate)
        artifacts.append({**wheel, "distribution": name, "version": TRAIN[name],
                          "source_commit": receipt["source_commit"]})
    return {"artifacts": artifacts, "candidate_lineage": lineage}


def test_required_case_counts_remain_release_specific():
    previous = json.loads(Path("dependencies/releases-pre-mcp-client-2026-11-11.json").read_text())
    released = candidate_manifest()
    del released["candidate_lineage"]
    for artifact in released["artifacts"]:
        artifact["version"] = MCP_CLIENT_RELEASE_TRAIN[artifact["distribution"]]
    for manifest, candidate, expected in [(previous, False, (12, 402)),
                                           (candidate_manifest(), True, (13, 426)),
                                           (released, False, (13, 426))]:
        modes = required_modes(candidate=candidate, manifest=manifest)
        assert (len(modes), sum(expected_test_count(mode, True) for mode in modes)) == expected
    assert len(CASES) * 2 == ALL_COUNTS["mcp-client"]


@pytest.mark.parametrize("damage", ["mixed", "unqualified", "skipped", "adapter", "unpaired"])
def test_invalid_mcp_candidate_refuses_admission(damage):
    manifest = candidate_manifest()
    runtime, harness = manifest["candidate_lineage"]["candidates"]
    if damage == "mixed":
        manifest["artifacts"][-1]["version"] = "0.9.15"
    elif damage == "unqualified":
        runtime["qualification"]["exit_code"] = 1
    elif damage == "skipped":
        harness["qualification"]["result_counts"]["skipped"] = 1
    elif damage == "adapter":
        next(item for item in manifest["artifacts"] if item["distribution"] == "b3-prosaic-harness-postgres")["sha256"] = "0" * 64
    else:
        harness["runtime_receipt"]["source_commit"] = "0" * 40
    with pytest.raises(ValueError):
        supports_mcp_client(manifest)


def test_lab_journal_preserves_only_bounded_controlled_failures():
    from prosaic_integration_lab.tool_journal import _snapshot_outcome

    failed = {"status": "error", "error": "mcp_catalogue_changed"}
    assert _snapshot_outcome(failed) == failed
    for outcome in ({**failed, "error": "private error message"}, {**failed, "result": {}}):
        with pytest.raises(ValueError, match="invalid_outcome"):
            _snapshot_outcome(outcome)


def test_optional_mcp_lock_matches_consumer_gate():
    from prosaic_integration_lab.mcp_client import MCP_LOCKED_VERSIONS

    lock = Path("dependencies/mcp-client.lock")
    assert dict(line.split()[0].split("==") for line in lock.read_text().splitlines()
                if line and not line.startswith("#")) == MCP_LOCKED_VERSIONS
