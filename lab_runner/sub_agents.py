"""Exact candidate handoff for the delegation lane."""
from pathlib import Path

from prosaic_integration_lab.sub_agents import TRAIN, require_sub_agent_sdk
from .parallel_tools import validate_local_handoff


def validate_sub_agent_manifest(data):
    return validate_local_handoff(data, train=TRAIN, kind="local-sub-agent-handoff",
        label="sub-agent-consumer", witness="test_sub_agent_installed.py")


def require_sub_agent_install(manifest):
    from prosaic_integration_lab.dependencies import cache_directory, sdk_manifest
    from prosaic_integration_lab.sdk_audit import audit
    validate_sub_agent_manifest(sdk_manifest(manifest))
    require_sub_agent_sdk()
    root = Path(__file__).resolve().parents[1]
    audit(manifest, cache_directory(manifest, root / ".cache/wheels"))
