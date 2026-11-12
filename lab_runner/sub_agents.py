"""Exact SDK and installed-payload validation for the delegation lane."""
from pathlib import Path

from prosaic_integration_lab.sub_agents import TRAIN, require_sub_agent_sdk
from .parallel_tools import validate_local_handoff


def validate_sub_agent_manifest(data):
    return validate_local_handoff(data, train=TRAIN, kind="local-sub-agent-handoff",
        label="sub-agent-consumer", witness="test_sub_agent_installed.py")


def require_sub_agent_install(manifest, *, candidate):
    from prosaic_integration_lab.dependencies import cache_directory, sdk_manifest
    from prosaic_integration_lab.sdk_audit import audit
    from .gates import supports_sub_agents

    data = sdk_manifest(manifest)
    if not supports_sub_agents(data) or candidate != ('candidate_lineage' in data):
        raise ValueError("delegation SDK family does not match dependency mode")
    require_sub_agent_sdk()
    root = Path(__file__).resolve().parents[1]
    audit(manifest, cache_directory(manifest, root / ".cache/wheels"))
