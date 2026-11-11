"""Private metadata-only context candidate policy; no search or source reads.

Related introductions are explicit cross-source candidates, never neighbors.
The caller must render/charge whole fetched records within its evidence caps.
"""
from fractions import Fraction
from pathlib import PurePosixPath
import re

from .context_expansion import (NAMESPACE, SOURCE_KEYS, WINGS, _hex, _provenance,
                               _require, fetch_window, validate_catalog)


def _sources(catalog, sources):
    """Bind one unambiguous metadata path to each exact catalog source group."""
    _require(type(sources) is dict, "source map shape")
    grouped = {}
    for group, ids in catalog["groups"].items():
        record = catalog["records"][ids[0]]
        sid = record["sourceId"]
        _require(sid not in grouped, "ambiguous source groups")
        grouped[sid] = (group, record)
    _require(set(sources) == set(grouped), "source map identities")
    paths = set()
    for sid, value in sources.items():
        _require(type(sid) is str and _hex(sid) and type(value) is dict
                 and set(value) == {"path", "sha256", "wing"}, "source map entry")
        path = value["path"]
        _require(type(path) is str and 0 < len(path.encode("utf-8")) <= 512
                 and "\\" not in path and all(ord(c) >= 32 and ord(c) != 127 for c in path),
                 "source path")
        parsed = PurePosixPath(path)
        _require(str(parsed) == path and len(parsed.parts) == 2
                 and parsed.parts[0] == "exports" and parsed.suffix.casefold() == ".md"
                 and path not in paths, "ambiguous or unsafe source path")
        paths.add(path)
        record = grouped[sid][1]
        _require(_hex(value["sha256"]) and value["sha256"] == record["sourceFileSha256"]
                 and value["wing"] == record["wing"], "source map provenance")
    return {sid: catalog["groups"][group] for sid, (group, _) in grouped.items()}


def _tokens(path):
    return set(re.findall(r"[^\W_]+", PurePosixPath(path).name.casefold())) - {"note", "session", "md"}


def _hit(record):
    return dict(record_id=record["recordId"], text_sha256=record["textSha256"],
                revision=record["revision"], representation=record["representation"],
                wing=record["wing"], captured_at=record["capturedAt"], source_id=record["sourceId"])


def fetch_document_context(provider, seed_hit, catalog, namespace, allowed_wings,
                           sources, seen_ids=(), *, catalog_wings=WINGS):
    """Fetch <=8 exact slices in metadata-derived priority order.

    Order: seed; source index 0; one same-wing related source's indices 0/1;
    source neighbors -1,+1,-2,+2. Filename Jaccard similarity selects a related
    source only when it shares a nonstructural token; descending exact score,
    then lexical path/source ID settle ties. Already displayed bodies are
    skipped except the seed. Search previews are not displayed bodies.

    Each result preserves the fetched slice and adds contextRole and
    seedSourceId. These are rendering metadata, not altered provenance.
    No tasks, queries, answer keys, body scans, fallback reads, or retries.
    """
    validate_catalog(catalog, namespace=namespace, wings=catalog_wings)
    _require(namespace == catalog["namespace"], "namespace")
    _require(type(allowed_wings) in (list, tuple, set, frozenset) and bool(allowed_wings)
             and all(type(w) is str and w in catalog_wings for w in allowed_wings), "wing grant")
    _require(type(seed_hit) is dict and SOURCE_KEYS <= set(seed_hit), "seed shape")
    rid = seed_hit["record_id"]
    _require(type(rid) is str and rid in catalog["records"], "seed id")
    seed = catalog["records"][rid]
    _require(seed["wing"] in allowed_wings, "seed outside scope")
    _provenance(seed_hit, seed)
    groups = _sources(catalog, sources)
    _require(type(seen_ids) in (list, tuple, set, frozenset)
             and all(type(value) is str and value in catalog["records"] for value in seen_ids),
             "seen body identities")
    seen = set(seen_ids)
    sid = seed["sourceId"]
    ids = groups[sid]
    index = seed["chunkIndex"]  # validate_catalog requires a contiguous plain-int index.
    candidates = [(rid, "seed"), (ids[0], "sourceIntroduction")]
    tokens = _tokens(sources[sid]["path"])
    related = []
    for other, value in sources.items():
        if other == sid or value["wing"] != seed["wing"] or value["wing"] not in allowed_wings:
            continue
        other_tokens = _tokens(value["path"])
        common = tokens & other_tokens
        if common:
            score = Fraction(len(common), len(tokens | other_tokens))
            related.append((-score, value["path"], other))
    if related:
        other = min(related)[2]
        candidates.extend((value, "relatedIntroduction") for value in groups[other][:2])
    for offset in (-1, 1, -2, 2):
        neighbor = index + offset
        if 0 <= neighbor < len(ids):
            candidates.append((ids[neighbor], "neighbor"))
    planned, selected = [], set()
    for value, role in candidates:
        if value in selected or (value in seen and role != "seed"):
            continue
        selected.add(value)
        planned.append((value, role))
    _require(len(planned) <= 8, "candidate bound")
    result = []
    for value, role in planned:
        record = catalog["records"][value]
        fetched = fetch_window(provider, _hit(record), catalog, namespace, allowed_wings,
                               radius=0, catalog_wings=catalog_wings)
        _require(len(fetched) == 1, "single exact record")
        result.append(dict(fetched[0], contextRole=role, seedSourceId=sid))
    return result
