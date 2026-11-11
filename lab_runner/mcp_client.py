"""Exact MCP candidate handoff and installed distribution validation."""
from pathlib import Path
import re

from prosaic_integration_lab.mcp_client import TRAIN

RETAINED_WHEELS = {
    "b3-prosaic": "e858a853595746c6930fbe062e84bd8ece1a366aa3b126f2fe11bfb7cb2ceb81",
    "b3-prosaic-runtime-postgres": "5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca",
    "b3-prosaic-harness-postgres": "99fe045d9e5711efd678644bfd44ac2406f94ffd2156f8bccfa28878e7385944",
}


def validate_mcp_manifest(manifest):
    artifacts = manifest.get("artifacts", ())
    if len(artifacts) != len(TRAIN) or {a["distribution"]: a["version"] for a in artifacts} != TRAIN:
        raise ValueError("exact MCP candidate family required")
    lineage = manifest.get("candidate_lineage", {})
    if lineage.get("version") != 1 or lineage.get("kind") != "local-mcp-client-handoff":
        raise ValueError("MCP candidate lineage required")
    candidates = lineage.get("candidates", ())
    if [item.get("sdk") for item in candidates] != ["runtime", "harness"]:
        raise ValueError("paired MCP candidates required")
    runtime, harness = candidates
    if (harness.get("runtime_receipt") != runtime.get("receipt")
            or harness.get("runtime_qualification") != runtime.get("qualification")):
        raise ValueError("Harness qualified different Runtime bytes")
    by_name = {a["distribution"]: a for a in artifacts}
    for candidate in candidates:
        sdk = candidate["sdk"]
        name = f"b3-prosaic-{sdk}"
        artifact = by_name[name]
        receipt, qualification = candidate["receipt"], candidate["qualification"]
        commit = receipt.get("source_commit", "")
        counts = qualification.get("result_counts", {})
        if (not re.fullmatch("[0-9a-f]{40}", commit) or commit != artifact["source_commit"]
                or qualification.get("source_commit") != commit
                or qualification.get("label") != "mcp-client-consumer"
                or qualification.get("exit_code") != 0
                or qualification.get("artifacts") != receipt.get("artifacts")
                or "test_mcp_installed.py" not in " ".join(qualification.get("command", ()))
                or {d["name"]: d["version"] for d in receipt["distributions"]} != {name: TRAIN[name]}
                or {"filename": artifact["filename"], "sha256": artifact["sha256"]} not in receipt["artifacts"]
                or set(counts) != {"tests", "failures", "errors", "skipped"}
                or any(type(value) is not int or value < 0 for value in counts.values())
                or counts["tests"] == 0 or any(counts[key] for key in ("failures", "errors", "skipped"))):
            raise ValueError("invalid MCP candidate qualification")
    retained = lineage.get("retained_artifacts", ())
    if len(retained) != len(RETAINED_WHEELS):
        raise ValueError("original Core and adapter wheels required")
    for name, sha256 in RETAINED_WHEELS.items():
        if by_name[name]["sha256"] != sha256 or by_name[name] not in retained:
            raise ValueError("retained wheel differs from released bytes")
    return manifest


def require_mcp_install(manifest):
    from prosaic_integration_lab.dependencies import cache_directory, sdk_manifest
    from prosaic_integration_lab.mcp_client import require_mcp_client_sdk
    from prosaic_integration_lab.sdk_audit import audit

    root = Path(__file__).resolve().parents[1]
    validate_mcp_manifest(sdk_manifest(manifest))
    require_mcp_client_sdk()
    audit(manifest, cache_directory(manifest, root / ".cache/wheels"))
