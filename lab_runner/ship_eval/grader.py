"""Pure scoring against admitted host evidence and private assertions."""
from __future__ import annotations

from . import SCORER_VERSION, SUITE_VERSION
from .cases import MAX_JSON_BYTES, RESPONSE_VALIDATOR, canonical, digest, validate_case
from .lookup import MAX_READS


def validate_trace(case: dict, trace: list[dict]) -> set[str]:
    if not isinstance(trace, list) or len(trace) > MAX_READS:
        raise ValueError("invalid host trace")
    reads = set()
    for sequence, entry in enumerate(trace, 1):
        if not isinstance(entry, dict) or set(entry) != {"caseId", "sequence", "recordId", "recordSha256"}:
            raise ValueError("invalid host trace entry")
        record_id = entry["recordId"]
        if not isinstance(record_id, str) or record_id not in case["records"]:
            raise ValueError("unknown traced record")
        if (type(entry["sequence"]) is not int or entry["sequence"] != sequence
                or entry["caseId"] != case["caseId"]
                or entry["recordSha256"] != digest(case["records"][record_id])):
            raise ValueError("trace identity, sequence or content mismatch")
        reads.add(record_id)
    return reads


def grade(case: dict, key: dict, response: object, trace: list[dict]) -> dict:
    validate_case(case, key)
    reads = validate_trace(case, trace)
    checks = dict.fromkeys(("schema", "decision", "findings", "citations", "retrieval", "repair"), False)
    report = {"suiteVersion": SUITE_VERSION, "scorerVersion": SCORER_VERSION,
        "caseId": case["caseId"], "caseSha256": digest(case), "passed": False, "checks": checks}
    try:
        schema_valid = len(canonical(response)) <= MAX_JSON_BYTES and RESPONSE_VALIDATOR.is_valid(response)
    except (ValueError, TypeError, RecursionError):
        schema_valid = False
    if not schema_valid:
        return report
    checks["schema"] = True
    checks["decision"] = response["decision"] == key["decision"]
    codes = [finding["code"] for finding in response["findings"]]
    checks["findings"] = len(codes) == len(set(codes)) and set(codes) == set(key["findings"])
    checks["repair"] = set(response["draftErrors"]) == set(key["draftErrors"])
    citations_valid = True
    cited_records = set()
    for finding in response["findings"]:
        cited = {(item["recordId"], item["field"]) for item in finding["citations"]}
        cited_records.update(record_id for record_id, _ in cited)
        alternatives = [set(map(tuple, support)) for support in key["findings"].get(finding["code"], [])]
        allowed = set().union(*alternatives) if alternatives else set()
        allowed.update(map(tuple, key.get("optionalCitations", {}).get(finding["code"], [])))
        if not any(support <= cited for support in alternatives) or not cited <= allowed:
            citations_valid = False
    checks["citations"] = citations_valid and checks["findings"]
    checks["retrieval"] = (bool(cited_records) and cited_records <= reads
        and set(key.get("requiredReadIds", [])) <= reads)
    report["passed"] = all(checks.values())
    return report
