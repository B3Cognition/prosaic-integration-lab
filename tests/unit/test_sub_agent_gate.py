from pathlib import Path

import pytest

from lab_runner.gates import expected_test_count, required_modes, supports_sub_agents
from prosaic_integration_lab.dependencies import sdk_manifest
from prosaic_integration_lab.sub_agents import TRAIN
from test_parallel_tool_hosted import paired_manifest


def test_delegation_adds_only_its_owned_stack_lane():
    published = sdk_manifest(Path("dependencies/releases.json"))
    baseline = required_modes(candidate=False, manifest=published)
    assert len(baseline) == 13 and sum(expected_test_count(mode, True) for mode in baseline) == 426
    candidate = paired_manifest(TRAIN, kind="local-sub-agent-handoff", label="sub-agent-consumer",
                                witness="test_sub_agent_installed.py")
    modes = required_modes(candidate=True, manifest=candidate)
    assert modes == (*baseline, "sub-agents")
    assert sum(expected_test_count(mode, True) for mode in modes) == 450
    candidate["candidate_lineage"]["candidates"][0]["qualification"]["result_counts"]["skipped"] = 1
    with pytest.raises(ValueError):
        supports_sub_agents(candidate)
