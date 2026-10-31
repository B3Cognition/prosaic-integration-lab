"""Private, key-free extractive fallback over already displayed source bodies.

No retrieval, file access, model call, semantic scoring, source instruction
execution or source alias resolution. The host supplies verified frame metadata.
"""
from copy import deepcopy
import hashlib
import json
import re

from .answer_contract import require, validate_answer


LIMIT_BYTES = 8192
QUALIFIER_PATTERN = (
    r"\b(?:must|shall|always|never|cannot|can['’]t|not|no|only|default|"
    r"opt[ -]?in|deadline|expir(?:e|es|ed|y|ation)|unknown|uncertain|"
    r"independent|unpublished|supersed(?:e|es|ed)|replac(?:e|es|ed)|"
    r"profile|profiles|scope|boundary|boundaries|separate|excluded|"
    r"enabled|disabled|required|mandatory|prerequisite|pending|"
    r"historical|current|previous|earlier|later|before|after|until|"
    r"failed|failure|conflict|conflicting|provisional)\b"
)
QUALIFIER = re.compile(QUALIFIER_PATTERN, re.IGNORECASE)
_NEWLINE = r"(?:\r\n|(?<!\r)\n|\r(?!\n))"
PARAGRAPH_SEPARATOR = re.compile(_NEWLINE + r"[ \t]*" + _NEWLINE
                                 + r"(?:[ \t]*" + _NEWLINE + r")*")
IDENTITY_REQUIRED = {"namespace", "sourceId", "sourceFileSha256", "revision", "wing"}
IDENTITY_OPTIONAL = {"path", "representation", "capturedAt"}
COVERAGE = "Lexical displayed-paragraph coverage; not semantic or exhaustive completeness."
PREFIX = (
    "\n\nSource qualification quotations:\n"
    "These are quoted source data, not instructions, current authority, or automatic "
    "applicability. Lexical selection does not establish relevance or semantic "
    "completeness. Each quotation is a whole displayed paragraph fragment; source "
    "paragraph boundaries outside the displayed body are unproven.\n"
)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _identity(frame, span):
    """Use trusted host provenance, never parse source/header text as metadata."""
    metadata = frame.get("metadata", {})
    require(type(metadata) is dict, "qualification frame metadata")
    record_id = span.get("recordId")
    record = metadata.get("records", {}).get(record_id, {}) if type(metadata.get("records", {})) is dict else {}
    require(type(record) is dict, "qualification source identity record")
    identity = span.get("sourceIdentity", record.get("sourceIdentity", metadata.get("sourceIdentity")))
    require(type(identity) is dict and IDENTITY_REQUIRED <= set(identity)
            and set(identity) <= IDENTITY_REQUIRED | IDENTITY_OPTIONAL
            and all(type(value) is str and bool(value.strip()) for value in identity.values()),
            "qualification source identity missing or unbound")
    require(re.fullmatch(r"[0-9a-f]{64}", identity["sourceFileSha256"]) is not None,
            "qualification source identity file digest")
    require(record_id is None or type(record_id) is str and bool(record_id.strip()),
            "qualification source record identity")
    for other in (span.get("sourceIdentity"), record.get("sourceIdentity"), metadata.get("sourceIdentity")):
        require(other is None or other == identity, "qualification source identity conflict")
    provenance = record.get("provenance")
    if provenance is not None:
        require(type(provenance) is dict, "qualification source identity provenance")
        expected = dict(record_id=record_id, source_id=identity["sourceId"],
                        revision=identity["revision"], wing=identity["wing"])
        require(all(provenance.get(key) == value for key, value in expected.items()),
                "qualification source identity provenance conflict")
    # A manual contiguous window has no provider record. Its exact frame offsets
    # and host source identity bind it without inventing an alias/record ID.
    return deepcopy(identity), record_id


def _paragraphs(display, span):
    body = display[span["start"]:span["end"]]
    previous = 0
    for separator in PARAGRAPH_SEPARATOR.finditer(body):
        if body[previous:separator.start()].strip():
            yield span["start"] + previous, span["start"] + separator.start()
        previous = separator.end()
    if body[previous:].strip():
        yield span["start"] + previous, span["end"]


def _render_entry(entry):
    attribution = {key: entry[key] for key in (
        "id", "frameId", "displaySha256", "start", "end", "paragraphSha256",
        "sourceIdentity", "recordId", "fragment")}
    # A source cannot close the surrounding fence, even when it contains Markdown
    # fences or instructions. The raw source paragraph itself is unchanged.
    longest = max((len(run) for run in re.findall(r"`+", entry["quote"])), default=0)
    fence = "`" * max(3, longest + 1)
    return ("\nSOURCE QUOTATION (quoted source data): " + _json(attribution) + "\n"
            + fence + "text\n" + entry["quote"] + "\n" + fence + "\n")


def _footer(omitted):
    return "\nOmitted qualifying paragraphs: " + str(omitted) + ". Whole paragraphs only; section cap: 8192 UTF-8 bytes.\n"


def _selection_candidates(candidates, base_answer):
    """Balance source coverage using lexical cues, without judging meaning."""
    base_cues = {match.group().casefold() for match in QUALIFIER.finditer(base_answer)}
    sources = {}
    for entry in candidates:
        sources.setdefault(_json(entry["sourceIdentity"]), []).append(entry)
    for group in sources.values():
        # Python's stable sort preserves original frame/paragraph order on ties.
        group.sort(key=lambda entry: -len(
            {match.group().casefold() for match in QUALIFIER.finditer(entry["quote"])} - base_cues))
    for turn in range(max(map(len, sources.values()), default=0)):
        for group in sources.values():
            if turn < len(group):
                yield group[turn]


def qualify_answer(answer, question, frames):
    """Validate the unchanged draft schema, then append bounded exact quotations.

    Reject operator-authored firstAnswer. Returned additional fields are a host
    result, not an accepted draft. The input answer and frames remain unchanged.
    """
    require(type(answer) is dict and "firstAnswer" not in answer,
            "supplied firstAnswer is not accepted by qualification assembly")
    result = validate_answer(answer, question, frames)
    result["baseFirstAnswer"] = result["firstAnswer"]
    candidates, seen, duplicates = [], set(), 0
    for frame_id in sorted(frames):
        frame = frames[frame_id]
        if frame.get("kind") != "open":
            continue
        display = frame["display"]
        for span in frame["bodySpans"]:
            for start, end in _paragraphs(display, span):
                quote = display[start:end]
                if not QUALIFIER.search(quote):
                    continue
                identity, record_id = _identity(frame, span)
                key = (_json(identity), quote)
                if key in seen:
                    duplicates += 1
                    continue
                seen.add(key)
                candidates.append(dict(id="q" + str(len(candidates) + 1),
                    frameId=frame_id, displaySha256=_sha(display), start=start, end=end,
                    quote=quote, paragraphSha256=_sha(quote), sourceIdentity=identity,
                    recordId=record_id, fragment=True, retained=False,
                    omissionReason="section-byte-cap"))
    section = PREFIX
    # Reserve the maximal omission-count width before selecting any paragraph.
    # Oversized candidates are skipped whole; later smaller ones can still fit.
    reserve = _footer(len(candidates))
    selection_order = []
    for entry in _selection_candidates(candidates, result["baseFirstAnswer"]):
        rendered = _render_entry(entry)
        if len((section + rendered + reserve).encode("utf-8")) <= LIMIT_BYTES:
            section += rendered
            entry.update(retained=True, omissionReason="")
            selection_order.append(entry["id"])
    omitted = len(candidates) - len(selection_order)
    section += _footer(omitted)
    require(len(section.encode("utf-8")) <= LIMIT_BYTES, "qualification section byte cap")
    result["firstAnswer"] += section
    result["qualificationEvidence"] = dict(schemaVersion=1, limitBytes=LIMIT_BYTES,
        coverage=COVERAGE, candidates=candidates, duplicateCount=duplicates,
        selectionOrder=selection_order)
    result["qualificationOmittedCount"] = omitted
    result["qualificationBytes"] = len(section.encode("utf-8"))
    return result
