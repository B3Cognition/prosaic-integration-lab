# Per-claim question links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate model forecasting of future claim IDs in question parts.

**Architecture:** New opt-in `compact-host-claim-parts-v1` wire inherits unique
quote selections and host-owned frame bookkeeping. Each claim declares nonempty
unique questionPartIds; questionParts omit claimIds. Host validates membership
and derives reverse lists in claims-array order, then runs the unchanged
canonical validator. Existing six profiles remain byte-compatible.

**Tech Stack:** Python3.12, installed public Runtime/Harness, JSON Schema.

**Spec:** User-approved recommendation in conversation; exact wire below.

## Global constraints and wire

- Preserve canonical schema,16384-byte limit, scope/provenance and scorer.
- Claim wire adds required `questionPartIds` (unique strings,minItems1).
- Question-part wire has id,quote,missingEvidenceIndices ONLY.
- Duplicate part IDs, missing/empty/unknown references and old reverse-link
  fields fail closed. Never infer or repair a link or prune claims.
- Parts may have only missingEvidenceIndices; partial/abstained answers remain.
- Multiple parts per claim are valid; canonical membership is preserved.
- Model chooses relationships; host owns deterministic reverse serialization.
- Memory/SUE defaults off; SUE/SOAR/SDKs/provider untouched; no publication.

## Review focus

- Duplicate part IDs must fail before a map can collapse them.
- Missing-evidence-only parts and unsupported absence retain canonical checks.
- Multi-part claims and non-default claim ordering preserve membership/rendering.
- Wire/expanded output over16384 bytes still fails; no new claim-count cap.
- Old frozen workflows/profile mismatch must fail without another provider call.

## Task1 — new profile and installed workflow

- [ ] RED: add tests/unit/test_memory_benchmark_claim_parts.py for exact new
  shape/roundtrip,8-claim late membership, multi-part membership, missing-evidence
  only/empty abstention, duplicate/unknown/missing/empty/old links, malformed
  offsets/provenance/size and raw immutability on failure.
- [ ] Implement profile/schema/resolve/encode/guidance in generation.py; extend
  explicit host-frame repair prompt selection in completeness_profile.py and
  synthetic new-profile initial fixture support in fixture.py. No canonical
  validators change. Use existing HOST_PROFILES workflow integration.
- [ ] Add installed candidate native answer/review/resume and runner tests under
  tests/memory_benchmark_candidate/test_claim_parts.py, asserting exact raw
  failures, no retry and retained unknown allowances.
- [ ] Verify108 byte comparisons for all six previous profiles, protected
  canonical functions/schema unchanged, full released source suite, wheel/sdist
  payload equality and fresh installed candidate workflows. Review whole change.

## Task2 — bounded same-Qwen diagnostic and preservation

- [ ] Fresh operator protocol: same q001/manual full bodies/Qwen, temp0,
  max4096, Runtime600s/observer615s; at most3 consistency trials,32768tokens each,
  shared3requests/98304tokens/1900s. Stop first invalid or unknown; no retries.
- [ ] Before calls, verify43 old archive copies,12 unknown ledgers,7 known
  ledgers and unchanged serving settings/source. Capture exact wire/SSE/usage.
- [ ] Structural acceptance always includes unchanged canonical validator.
  Semantic completeness requires separate named exact-proof assessment; no
  scoring of invalid/partial output. No larger sample without qualification.
- [ ] Preserve all failures/reservations, report limitations and exact counts,
  seal a manifest-listed private durable copy. No product adoption/release.
