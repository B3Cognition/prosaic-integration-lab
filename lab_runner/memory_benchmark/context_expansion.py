"""Private equal-budget pilot driver. No source paths, queries, or model code.

The caller must construct CastleMemoryProvider with this namespace and task wing
grant; the existing wire API does not return a namespace in individual slices.
Return value is the unchanged fetched MemorySlice dictionaries. Account text
bytes with sum(len(item['text'].encode('utf-8')) for item in result), and snapshot
accepted IDs against this catalog's textSha256/revision before answer generation.
"""
import hashlib
import re
from datetime import datetime

NAMESPACE = "pilot-michal-prosaic-20261025"
WINGS = {"notes", "sessions", "excluded-notes"}
RECORD_KEYS = {"recordId", "textSha256", "revision", "representation", "wing",
    "sourceId", "chunkIndex", "orderGroup", "sourceFileSha256", "capturedAt"}
SOURCE_KEYS = {"record_id", "text_sha256", "revision", "representation", "wing",
    "captured_at", "source_id"}
SLICE_KEYS = {"record_id", "text_sha256", "slice_sha256", "text", "start_char",
    "next_start_char", "complete", "provenance", "schema_version"}

def _require(ok, label):
    if not ok:
        raise ValueError(label)

def _sha(value):
    return hashlib.sha256(value).hexdigest()

def _hex(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None

def _captured(value):
    _require(type(value) is str and len(value) <= 128, "captured_at")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("captured_at") from None
    _require(parsed.tzinfo is not None, "captured_at timezone")

def validate_catalog(catalog, *, namespace=NAMESPACE, wings=WINGS):
    _require(type(catalog) is dict and set(catalog) == {"schemaVersion", "namespace",
        "corpusSha256", "sourceCount", "recordCount", "records", "groups"}, "catalog shape")
    _require(type(catalog["schemaVersion"]) is int and catalog["schemaVersion"] == 1,
        "catalog version")
    _require(type(namespace) is str and bool(namespace) and type(wings) in (list, tuple, set, frozenset)
        and bool(wings) and all(type(w) is str and bool(w) for w in wings), "explicit host scope")
    _require(catalog["namespace"] == namespace and _hex(catalog["corpusSha256"]), "catalog identity")
    records, groups = catalog["records"], catalog["groups"]
    _require(type(records) is dict and type(groups) is dict and bool(records) and bool(groups), "catalog maps")
    _require(type(catalog["recordCount"]) is int and catalog["recordCount"] == len(records), "record count")
    _require(type(catalog["sourceCount"]) is int and catalog["sourceCount"] == len(groups), "source count")
    seen, identities = set(), set()
    for group, ids in groups.items():
        _require(_hex(group) and type(ids) is list and bool(ids), "order group")
        identity = None
        for i, rid in enumerate(ids):
            _require(type(rid) is str and bool(rid) and len(rid.encode()) <= 512
                and rid in records and rid not in seen, "record identity")
            seen.add(rid)
            record = records[rid]
            _require(type(record) is dict and set(record) == RECORD_KEYS, "record shape")
            _require(record["recordId"] == rid and record["orderGroup"] == group
                and type(record["chunkIndex"]) is int and record["chunkIndex"] == i, "chunk order")
            _require(all(_hex(record[key]) for key in ["textSha256", "sourceId", "sourceFileSha256"]), "record hash")
            _require(type(record["revision"]) is str and
                re.fullmatch(r"[A-Za-z0-9_.-]{1,256}",record["revision"]) is not None, "revision")
            _require(record["representation"] == "project" and record["wing"] in wings, "source scope")
            _captured(record["capturedAt"])
            current = tuple(record[key] for key in ["sourceId","wing","revision","representation","sourceFileSha256"])
            if identity is None:
                identity = current
            _require(current == identity, "cross-source group")
        _require(identity not in identities, "split or duplicate source group")
        identities.add(identity)
    _require(seen == set(records), "unlisted records")
    return catalog

def _provenance(actual, record):
    _require(type(actual) is dict and SOURCE_KEYS <= set(actual), "source shape")
    expected = dict(record_id=record["recordId"],text_sha256=record["textSha256"],
        revision=record["revision"],representation=record["representation"],wing=record["wing"],
        captured_at=record["capturedAt"],source_id=record["sourceId"])
    _require(all(actual[key] == value for key,value in expected.items()), "source provenance")

def fetch_window(provider, seed_hit, catalog, namespace, allowed_wings, radius=2, *, catalog_wings=WINGS):
    """Fetch at most five exact <=800-character chunks through provider.fetch.

    No alternate-source expansion, fallback reads, hidden searches, or retries.
    Any missing/malformed/stale chunk aborts the complete window.
    """
    validate_catalog(catalog, namespace=namespace, wings=catalog_wings)
    _require(namespace == catalog["namespace"], "namespace")
    _require(type(allowed_wings) in (list, tuple, set, frozenset) and bool(allowed_wings)
        and all(type(w) is str and w in catalog_wings for w in allowed_wings), "wing grant")
    _require(type(radius) is int and 0 <= radius <= 2, "radius")
    _require(type(seed_hit) is dict and SOURCE_KEYS <= set(seed_hit), "seed shape")
    rid = seed_hit["record_id"]
    _require(type(rid) is str and rid in catalog["records"], "seed id")
    seed = catalog["records"][rid]
    _require(seed["wing"] in allowed_wings, "seed outside scope")
    _provenance(seed_hit, seed)
    ids = catalog["groups"][seed["orderGroup"]]
    index = seed["chunkIndex"]
    selected = ids[max(0,index-radius):index+radius+1]
    out = []
    for selected_id in selected:
        expected = catalog["records"][selected_id]
        value = provider.fetch(selected_id, start_char=0, max_chars=800)
        _require(type(value) is dict and set(value) == SLICE_KEYS, "slice shape")
        _require(type(value["schema_version"]) is int and value["schema_version"] == 1
            and value["record_id"] == selected_id and value["text_sha256"] == expected["textSha256"], "slice identity")
        _require(type(value["start_char"]) is int and value["start_char"] == 0
            and value["next_start_char"] is None and value["complete"] is True, "incomplete slice")
        text = value["text"]
        _require(type(text) is str and 0 < len(text) <= 800, "slice text bounds")
        try:
            raw = text.encode("utf-8")
        except UnicodeError:
            raise ValueError("slice encoding") from None
        _require(_hex(value["slice_sha256"]) and _sha(raw) == value["slice_sha256"]
            == value["text_sha256"] == expected["textSha256"], "slice exact bytes")
        _require(type(value["provenance"]) is dict and set(value["provenance"]) == SOURCE_KEYS, "provenance shape")
        _provenance(value["provenance"], expected)
        out.append(value)
    return out
