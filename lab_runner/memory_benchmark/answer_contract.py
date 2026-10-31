"""Private, key-free answer assembly. Checks attachment and structure, not semantics.

The caller supplies trusted source-body spans from actual rendered displays.
No file access, retrieval, inference, normalization or instruction execution occurs.
"""
from collections import Counter
from copy import deepcopy
import hashlib


SECTIONS = {
    "directAnswer": "Direct answer",
    "supportingDetails": "Supporting details",
    "chronologyAndBoundaries": "Chronology and boundaries",
    "limitations": "Limitations",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def shape(value, fields, label):
    require(type(value) is dict and set(value) == set(fields), label + " fields")


def nonempty(value, label):
    require(type(value) is str and bool(value.strip()), label + " must be nonempty text")


def unique_list(value, label):
    require(type(value) is list and all(type(item) is str and item.strip() for item in value), label + " list")
    require(len(value) == len(set(value)), label + " duplicates")
    return value


def indexed(values, fields, label):
    require(type(values) is list, label + " list")
    result = {}
    for value in values:
        shape(value, fields, label)
        nonempty(value["id"], label + " id")
        require(value["id"] not in result, label + " duplicate id")
        result[value["id"]] = value
    return result


def exact_range(value, text, label):
    start, end = value["start"], value["end"]
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), label + " bounds")
    nonempty(value["quote"], label + " quote")
    require(value["quote"] == text[start:end], label + " exact quote mismatch")


def validate_answer(answer, question, frames):
    """Return an independent validated dict with deterministic legacy firstAnswer.

    Passing proves exact quote attachment and schema/reference consistency only.
    It does not prove entailment, bounded wording, meaningful review, exhaustive
    question decomposition, relevant-fact selection or semantic completeness.
    """
    nonempty(question, "question")
    require(type(frames) is dict, "frames map")
    required = {"questionParts", "claims", "evidence", "sections", "frameReview",
                "citations", "missingEvidence", "status"}
    require(type(answer) is dict and required <= set(answer) <= required | {"firstAnswer"}, "answer fields")
    require(type(answer["citations"]) is list, "legacy citations list")
    require(type(answer["missingEvidence"]) is list, "missingEvidence list")
    for text in answer["missingEvidence"]:
        nonempty(text, "missingEvidence entry")
    require(type(answer["status"]) is str and answer["status"] in {"answered", "partial", "abstained"}, "status enum")
    require(not answer["missingEvidence"] or answer["status"] != "answered", "missing evidence requires partial/abstained")

    for frame_id, frame in frames.items():
        nonempty(frame_id, "frame id")
        require(type(frame) is dict and type(frame.get("display")) is str
                and type(frame.get("bodySpans")) is list, "trusted frame shape")
        previous_end = 0
        for span in frame["bodySpans"]:
            require(type(span) is dict and type(span.get("start")) is int and type(span.get("end")) is int
                    and previous_end <= span["start"] < span["end"] <= len(frame["display"]), "trusted body span bounds/order")
            previous_end = span["end"]

    evidence = indexed(answer["evidence"],
        {"id", "frameId", "displaySha256", "start", "end", "quote"}, "evidence")
    for item in evidence.values():
        require(type(item["frameId"]) is str and item["frameId"] in frames, "evidence frame not supplied")
        frame = frames[item["frameId"]]
        require(item["displaySha256"] == hashlib.sha256(frame["display"].encode("utf-8")).hexdigest(), "display digest mismatch")
        exact_range(item, frame["display"], "evidence")
        require(any(span["start"] <= item["start"] < item["end"] <= span["end"]
                    for span in frame["bodySpans"]), "quote outside one displayed source body")

    claims = indexed(answer["claims"], {"id", "text", "kind", "evidenceIds"}, "claim")
    claim_texts = set()
    used_evidence = set()
    unsupported_absences = set()
    for cid, claim in claims.items():
        nonempty(claim["text"], "claim text")
        require(claim["text"] not in claim_texts, "duplicate claim text")
        claim_texts.add(claim["text"])
        require(type(claim["kind"]) is str and claim["kind"] in {"observation", "inference", "absence"}, "claim kind")
        refs = unique_list(claim["evidenceIds"], "claim evidenceIds")
        require(set(refs) <= evidence.keys(), "unknown evidence id")
        if claim["kind"] != "absence":
            require(bool(refs), "observation/inference requires evidence")
        elif not refs:
            unsupported_absences.add(cid)
        used_evidence.update(refs)
    require(used_evidence == evidence.keys(), "unused evidence entry")

    parts = indexed(answer["questionParts"],
        {"id", "start", "end", "quote", "claimIds", "missingEvidenceIndices"}, "question part")
    require(bool(parts), "at least one question part required")
    part_claims, missing_indices, absence_limits = set(), set(), set()
    for part in parts.values():
        exact_range(part, question, "question part")
        refs = unique_list(part["claimIds"], "question part claimIds")
        require(set(refs) <= claims.keys(), "unknown question-part claim")
        indices = part["missingEvidenceIndices"]
        require(type(indices) is list and all(type(i) is int and 0 <= i < len(answer["missingEvidence"]) for i in indices)
                and len(indices) == len(set(indices)), "missingEvidence indices")
        require(bool(refs or indices), "question part has no disposition")
        part_claims.update(refs)
        missing_indices.update(indices)
        if indices:
            absence_limits.update(refs)
    require(part_claims == claims.keys(), "claim not assigned to a requested part")
    require(missing_indices == set(range(len(answer["missingEvidence"]))), "unassigned missingEvidence")

    shape(answer["sections"], SECTIONS, "sections")
    rendered_sections, assigned = [], []
    for key, heading in SECTIONS.items():
        section = answer["sections"][key]
        shape(section, {"claimIds", "reason"}, "section")
        refs = unique_list(section["claimIds"], "section claimIds")
        require(set(refs) <= claims.keys(), "unknown section claim")
        require(type(section["reason"]) is str, "section reason text")
        if not refs:
            nonempty(section["reason"], "empty section reason")
        assigned.extend(refs)
        lines = [claims[cid]["text"] for cid in refs] or [section["reason"]]
        if key == "limitations":
            lines += answer["missingEvidence"]
        rendered_sections.append(heading + ":\n" + "\n".join(lines))
    require(Counter(assigned) == Counter({cid: 1 for cid in claims}), "each claim must render exactly once")
    if unsupported_absences:
        require(answer["status"] in {"partial", "abstained"} and bool(answer["missingEvidence"]), "unsupported absence requires explicit missing evidence")
        require(unsupported_absences <= set(answer["sections"]["limitations"]["claimIds"])
                and unsupported_absences <= absence_limits, "unsupported absence requires linked limitation")

    require(type(answer["frameReview"]) is list, "frameReview list")
    reviews = {}
    for review in answer["frameReview"]:
        shape(review, {"frameId", "disposition", "claimIds", "reason"}, "frame review")
        fid = review["frameId"]
        require(type(fid) is str and fid in frames and fid not in reviews, "frame review identity")
        require(type(review["disposition"]) is str and review["disposition"] in {"used", "duplicate", "irrelevant", "insufficient"}, "frame review disposition")
        refs = unique_list(review["claimIds"], "frame review claimIds")
        require(set(refs) <= claims.keys(), "unknown frame-review claim")
        nonempty(review["reason"], "frame review reason")
        linked = {cid for cid, claim in claims.items()
                  if any(evidence[eid]["frameId"] == fid for eid in claim["evidenceIds"])}
        if review["disposition"] == "used":
            require(bool(refs) and set(refs) == linked, "used frame must identify its supported claims")
        else:
            require(not linked, "claimed evidence frame must be marked used")
        reviews[fid] = review
    require(reviews.keys() == frames.keys(), "every supplied frame requires review")

    rendered = "\n\n".join(rendered_sections)
    require("firstAnswer" not in answer or answer["firstAnswer"] == rendered, "supplied firstAnswer conflicts with deterministic rendering")
    result = deepcopy(answer)
    result["firstAnswer"] = rendered
    return result
