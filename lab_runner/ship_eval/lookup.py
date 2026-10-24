"""Host-owned synthetic reads; traces are not provider attestations."""
from __future__ import annotations

from copy import deepcopy

from .cases import digest

MAX_READS = 128


class LookupSession:
    def __init__(self, case: dict):
        self._case = deepcopy(case)
        self._trace: list[dict] = []

    def read(self, record_id: str) -> dict:
        if not isinstance(record_id, str) or record_id not in self._case["records"]:
            raise ValueError("unknown record ID")
        if len(self._trace) >= MAX_READS:
            raise ValueError("lookup allowance exhausted")
        record = self._case["records"][record_id]
        self._trace.append({
            "caseId": self._case["caseId"], "sequence": len(self._trace) + 1,
            "recordId": record_id, "recordSha256": digest(record),
        })
        return deepcopy(record)

    def trace(self) -> list[dict]:
        return deepcopy(self._trace)
