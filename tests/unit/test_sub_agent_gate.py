import json

import pytest

from lab_runner.gates import (MCP_CLIENT_RELEASE_TRAIN, expected_test_count, required_modes,
    supports_consumer_blueprints, supports_context_assembly, supports_sub_agents)
from lab_runner.mcp_client import RETAINED_WHEELS as MCP_RETAINED_WHEELS
from prosaic_integration_lab.sub_agents import RELEASE_TRAIN, TRAIN
from test_parallel_tool_hosted import paired_manifest


def release_manifest(train=RELEASE_TRAIN):
    data = paired_manifest(train)
    data.pop("candidate_lineage")
    if train == MCP_CLIENT_RELEASE_TRAIN:
        for item in data["artifacts"]:
            name = item["distribution"]
            if name in MCP_RETAINED_WHEELS:
                item["sha256"] = MCP_RETAINED_WHEELS[name]
    return data


def test_delegation_adds_only_its_owned_stack_lane():
    baseline = required_modes(candidate=False, manifest=release_manifest(MCP_CLIENT_RELEASE_TRAIN))
    assert len(baseline) == 13 and sum(expected_test_count(mode, True) for mode in baseline) == 426
    candidate = paired_manifest(TRAIN, kind="local-sub-agent-handoff", label="sub-agent-consumer",
                                witness="test_sub_agent_installed.py")
    for manifest, is_candidate in ((candidate, True), (release_manifest(), False)):
        modes = required_modes(candidate=is_candidate, manifest=manifest)
        assert modes == (*baseline, "sub-agents")
        assert sum(expected_test_count(mode, True) for mode in modes) == 450
        assert supports_context_assembly(manifest)
        assert supports_consumer_blueprints(manifest)
    candidate["candidate_lineage"]["candidates"][0]["qualification"]["result_counts"]["skipped"] = 1
    with pytest.raises(ValueError):
        supports_sub_agents(candidate)


@pytest.mark.parametrize("damage", ["mixed", "retained", "candidate", "duplicate"])
def test_published_delegation_rejects_mismatched_sdk_family(damage):
    manifest = release_manifest()
    artifacts = manifest["artifacts"]
    if damage == "mixed":
        next(item for item in artifacts if item["distribution"] == "b3-prosaic-runtime")["version"] = TRAIN["b3-prosaic-runtime"]
    elif damage == "retained":
        next(item for item in artifacts if item["distribution"] == "b3-prosaic-runtime-postgres")["sha256"] = "c" * 64
    elif damage == "candidate":
        manifest["candidate_lineage"] = {}
    else:
        artifacts.append(dict(artifacts[0]))

    with pytest.raises(ValueError):
        supports_sub_agents(manifest)


def test_published_delegation_audits_installed_bytes(monkeypatch, tmp_path):
    from lab_runner import sub_agents
    from prosaic_integration_lab import sdk_audit

    manifest = tmp_path / "published-manifest.json"
    manifest.write_text(json.dumps(release_manifest()))
    audited = []
    monkeypatch.setattr(sub_agents, "require_sub_agent_sdk", lambda: None)
    monkeypatch.setattr(sdk_audit, "audit", lambda path, wheels: audited.append(path))

    sub_agents.require_sub_agent_install(manifest, candidate=False)
    assert audited == [manifest]
    with pytest.raises(ValueError, match="dependency mode"):
        sub_agents.require_sub_agent_install(manifest, candidate=True)
    assert audited == [manifest]
