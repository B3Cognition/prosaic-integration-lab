"""Versioned synthetic dossiers and host-only answer-key admission."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from importlib.resources import files
import json

from jsonschema import Draft202012Validator

from . import SUITE_VERSION

MAX_JSON_BYTES = 65536
DECISIONS = ("APPROVE", "BLOCK", "INSUFFICIENT_EVIDENCE")
FINDING_CODES = (
    "requirements_satisfied", "candidate_unverified", "required_check_skipped",
    "candidate_mutated", "required_evidence_missing", "required_check_failed",
    "stale_evidence_used",
)
DRAFT_ERRORS = ("stale_evidence", "overlooked_failure")
RESPONSE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object", "additionalProperties": False,
    "required": ["decision", "findings", "draftErrors"],
    "properties": {
        "decision": {"enum": list(DECISIONS)},
        "findings": {"type": "array", "minItems": 1, "maxItems": 7, "items": {
            "type": "object", "additionalProperties": False, "required": ["code", "citations"],
            "properties": {
                "code": {"enum": list(FINDING_CODES)},
                "citations": {"type": "array", "minItems": 1, "maxItems": 32,
                    "uniqueItems": True, "items": {
                        "type": "object", "additionalProperties": False,
                        "required": ["recordId", "field"], "properties": {
                            "recordId": {"type": "string", "minLength": 1, "maxLength": 64},
                            "field": {"type": "string", "minLength": 1, "maxLength": 64},
                        },
                    }},
            },
        }},
        "draftErrors": {"type": "array", "maxItems": 2, "uniqueItems": True,
            "items": {"enum": list(DRAFT_ERRORS)}},
        "rationale": {"type": "string", "maxLength": 2048},
    },
}


def parse_json(text: str, *, maximum_bytes: int = MAX_JSON_BYTES) -> object:
    """Reject duplicate members, nonfinite numbers and oversized JSON."""
    if len(text.encode("utf-8")) > maximum_bytes:
        raise ValueError("JSON exceeds input byte bound")

    def pairs(items):
        result = {}
        for name, value in items:
            if name in result:
                raise ValueError("duplicate JSON member")
            result[name] = value
        return result

    def invalid_constant(value):
        raise ValueError("nonfinite JSON number")

    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_constant)
        # Exponent overflow (1e999) does not use parse_constant.
        json.dumps(value, allow_nan=False)
        return value
    except (TypeError, RecursionError, OverflowError) as exc:
        raise ValueError("invalid JSON") from exc


def canonical(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError, OverflowError) as exc:
        raise ValueError("not finite JSON") from exc


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_case(case: dict, key: dict) -> None:
    """Validate host assertions, never deriving a grade from malformed setup."""
    try:
        if not isinstance(case, dict) or set(case) != {"caseId", "title", "instructions", "records", "draft"}:
            raise ValueError("invalid case shape")
        if not all(isinstance(case[name], str) and case[name] for name in ("caseId", "title", "instructions")):
            raise ValueError("invalid case identity")
        if len(canonical(case)) > MAX_JSON_BYTES:
            raise ValueError("case too large")
        records = case["records"]
        if not isinstance(records, dict) or not 2 <= len(records) <= 32 or not {"policy", "candidate"} <= records.keys():
            raise ValueError("invalid records")
        for record_id, record in records.items():
            if not isinstance(record_id, str) or not 1 <= len(record_id) <= 64:
                raise ValueError("invalid record ID")
            if not isinstance(record, dict) or set(record) != {"recordId", "title", "kind", "fields"}:
                raise ValueError("invalid record shape")
            if record["recordId"] != record_id or not isinstance(record["fields"], dict) or not record["fields"]:
                raise ValueError("invalid record identity/fields")
            if not all(isinstance(record[name], str) and record[name] for name in ("title", "kind")):
                raise ValueError("invalid record metadata")
            if not all(isinstance(field, str) and 1 <= len(field) <= 64 for field in record["fields"]):
                raise ValueError("invalid field name")
        required_key_fields = {"caseSha256", "decision", "findings", "draftErrors"}
        if (not isinstance(key, dict) or not required_key_fields <= set(key)
                or not set(key) <= required_key_fields | {"optionalCitations", "requiredReadIds"}):
            raise ValueError("invalid key shape")
        if key["caseSha256"] != digest(case) or key["decision"] not in DECISIONS:
            raise ValueError("case/key binding or decision invalid")
        findings = key["findings"]
        if not isinstance(findings, dict) or not findings or not set(findings) <= set(FINDING_CODES):
            raise ValueError("invalid expected findings")
        for alternatives in findings.values():
            if not isinstance(alternatives, list) or not alternatives or len(alternatives) > 8:
                raise ValueError("invalid support alternatives")
            for support in alternatives:
                if not isinstance(support, list) or not 1 <= len(support) <= 32:
                    raise ValueError("empty or excessive support")
                seen = set()
                for pair in support:
                    if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(item, str) for item in pair):
                        raise ValueError("invalid support pair")
                    record_id, field = pair
                    if record_id not in records or field not in records[record_id]["fields"] or tuple(pair) in seen:
                        raise ValueError("invalid support reference")
                    seen.add(tuple(pair))
        optional = key.get("optionalCitations", {})
        if not isinstance(optional, dict) or not set(optional) <= set(findings):
            raise ValueError("invalid optional citation codes")
        for pairs in optional.values():
            if not isinstance(pairs, list) or len(pairs) > 32:
                raise ValueError("invalid optional citations")
            seen = set()
            for pair in pairs:
                if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(item, str) for item in pair):
                    raise ValueError("invalid optional citation pair")
                record_id, field = pair
                if record_id not in records or field not in records[record_id]["fields"] or tuple(pair) in seen:
                    raise ValueError("invalid optional citation reference")
                seen.add(tuple(pair))
        required_reads = key.get("requiredReadIds", [])
        if (not isinstance(required_reads, list) or len(required_reads) > 32
                or not all(isinstance(item, str) and item in records for item in required_reads)
                or len(set(required_reads)) != len(required_reads)):
            raise ValueError("invalid required exposure records")
        errors = key["draftErrors"]
        if not isinstance(errors, list) or not all(isinstance(item, str) for item in errors):
            raise ValueError("invalid draft errors")
        if len(set(errors)) != len(errors) or not set(errors) <= set(DRAFT_ERRORS):
            raise ValueError("invalid draft errors")
        if bool(errors) != (case["draft"] is not None):
            raise ValueError("draft/error mismatch")
        if case["draft"] is not None and not isinstance(case["draft"], dict):
            raise ValueError("invalid draft")
    except (KeyError, TypeError, RecursionError) as exc:
        raise ValueError("invalid host fixture") from exc


def validate_suite(cases: dict, keys: dict) -> None:
    if not isinstance(cases, dict) or not isinstance(keys, dict) or set(cases) != set(keys) or len(cases) != 8:
        raise ValueError("suite requires eight matching cases and keys")
    for case_id, case in cases.items():
        validate_case(case, keys[case_id])
        if case_id != case["caseId"]:
            raise ValueError("case ID mismatch")


def load_suite() -> tuple[dict, dict]:
    root = files(__package__).joinpath("data")
    public = parse_json(root.joinpath("cases.json").read_text(encoding="utf-8"))
    private = parse_json(root.joinpath("keys.json").read_text(encoding="utf-8"))
    if not isinstance(public, dict) or not isinstance(private, dict):
        raise ValueError("invalid suite resources")
    if public.get("suiteVersion") != SUITE_VERSION or private.get("suiteVersion") != SUITE_VERSION:
        raise ValueError("suite version mismatch")
    cases, keys = public.get("cases"), private.get("keys")
    validate_suite(cases, keys)
    return cases, keys


def public_task(case: dict) -> dict:
    """Construct the only initial task payload intended for a model."""
    return deepcopy({
        "suiteVersion": SUITE_VERSION, "caseId": case["caseId"], "title": case["title"],
        "instructions": case["instructions"], "policy": case["records"]["policy"],
        "candidate": case["records"]["candidate"], "draft": case["draft"],
        "recordCatalogue": [
            {name: record[name] for name in ("recordId", "title", "kind")}
            for _, record in sorted(case["records"].items())
        ],
        "responseSchema": RESPONSE_SCHEMA,
    })


RESPONSE_VALIDATOR = Draft202012Validator(RESPONSE_SCHEMA)
