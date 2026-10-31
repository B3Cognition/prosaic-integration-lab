# Castle answer-span audit implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Preserve watched RED/GREEN output and obtain one fresh final review.

**Goal:** Add an independently disabled, audit-only consumer workflow that detects omissions in actual answers without changing Castle retrieval or adopting repairs.

**Architecture:** Castle supplies scoped, frozen evidence. A Lab source-obligation stage receives no draft; a second stage audits exact canonical answer spans, citation support and status. Runtime owns execution/usage and Harness owns frozen acceptance/resume. The protected critic, current completeness workflow and strict scorer remain unchanged.

**Tech stack:** Python 3.12, JSON Schema, installed public Prosaic Runtime/Harness APIs, loopback synthetic provider fixtures.

**Spec:** `/Users/michalbachorik/Library/Application Support/Prosaic/pilots/endpoint-audit-design-20261027/answer-span-audit-design.md`, preserved in sealed manifest `3d53cab2a31b9759a74dde49f93050fc6facec889f18ba61b176f72cd43eef2d`.

## Global constraints

- Memory and SUE remain independently disabled by default. SUE and SOAR are outside the audit/provider path.
- Preserve namespace, wing, revision, exact Unicode/byte and provenance checks; never expand supplied source scope.
- Packet maximum 262144 UTF-8 bytes; raw and canonical output maximum 16384 bytes per stage; output maximum 4096 tokens per call.
- At most 16 question parts, 32 source obligations and 32 additional findings. Exceeding a cap rejects/unresolves; it never truncates or shrinks the denominator.
- Two sequential calls maximum; 120 seconds per call, 270 seconds per audit, 65536 reported tokens reserved per audit, zero tools/retries.
- Unknown completion/usage blocks subsequent work and holds the full reservation. Completed resume dispatches zero calls.
- No automatic repair, answer/status rewrite, score changes, live inference, publishing, pushes or release in this implementation scope.
- Private raw run evidence stays outside committed documentation. Preserve prior archives and allowances without mutating sealed roots.

## Review focus

1. Source-only qualifications cannot satisfy factual coverage without actual claim text; legitimate paraphrases remain eligible for semantic review.
2. Correct scoped abstentions can be clear through typed limitation proof; limitations can never satisfy factual answer coverage.
3. Every claim and ledger obligation needs a disposition, including mixed unsupported clauses and wrong selected citations.
4. Prompt injection and correct-looking foreign identifiers confer no authority; mutable nested inputs cannot change frozen scope.
5. Unknown usage, changed bindings and cap exhaustion fail closed while retaining originals and exact evidence.

## Task 1: Recover the exact tested baseline and verify it

**Files:** Restore preserved `lab_runner/memory_benchmark/`, its tests and documentation into this isolated worktree before adding audit code. Record restoration separately from new changes.

**Consumes:** Source archive `memory-missing-parts-20261027/artifacts/prosaic_integration_lab-0.6.0.tar.gz`, SHA256 `e20e1de5e61f60c937afec50b55ac9c04d567dfca07a2cdfbc15edf1e492da8f`; matching wheel SHA256 `5c6a23cca753078ec42d9ef20f379601061e59c1a57fae298f47fe29a4a93685`.

**Produces:** Immutable baseline source/package proof and a passing baseline test log.

- [x] Verify source/wheel hashes against the durable manifest and extract only safe regular paths; reject archive links/traversal.
- [x] Restore the exact 73 differing/new source files relative to `f6673f3b761842f17fa78129c748dddde27485cb`; leave unrelated primary checkouts untouched. Compare all packaged Lab payloads with the previous installed proof.
- [x] Reconstruct the previous locked public SDK environment; verify candidate Runtime `0.9.8+jsonschema.3` and Harness `0.9.4` payloads instead of using the unrelated main checkout's older SDKs.
- [x] Run the existing memory benchmark/candidate suites, memory workflow and canonical review tests before changes. Save complete output; resolve a failed baseline before attributing failures to this feature.

## Task 2: Immutable views and strict audit contracts

**Create:** `lab_runner/memory_benchmark/span_audit_contracts.py`, `tests/unit/test_memory_span_audit_contracts.py`.

**Consumes:** Existing validated `completeness_profile.ReviewPacket`, canonical answer and trusted frame metadata.

**Produces:** `freeze_audit(packet) -> AuditPacket`; `AuditPacket.to_dict() -> dict`; `source_view(packet) -> dict`; `answer_view(packet) -> dict`; `validate_ledger(value, packet) -> dict`; `validate_audit(value, packet, ledger) -> dict`.

- [x] Write and watch failing tests for source-only "disabled", Unicode/CRLF offsets, source/header spill, missing rows, substituted IDs, foreign scope, mutable input and limit exhaustion.
- [x] Build distinct source, claim-answer and limitation span types; freeze canonical renderer order, question, status, links and original bytes. Exclude quotes, frame reasons and wire placeholders from factual answer text.
- [x] Add closed versioned schemas for source obligations and answer audit. Enforce complete identity sets and state-specific proof requirements. Derive `clear/findings/unresolved` structurally; never infer entailment in the host.
- [x] Add and run controls for clean paraphrases, unknown-in-context abstention, conflicting sources, mixed claims, swapped citations and explicit scoped limitation proof. Model semantic claims remain unproven by schema validity.

## Task 3: Public two-stage Harness workflow

**Create:** `lab_runner/memory_benchmark/span_audit_workflow.py`, `tests/memory_benchmark_candidate/test_span_audit.py`.

**Consumes:** Task 2 contracts and existing execution profiles.

**Produces:** `build_audit_workflow(config, packet) -> workflow`; `run_audit(config, packet, directory, *, accounting=None) -> dict` containing the unchanged original, distinct audit sidecar/status and private operator evidence.

- [x] Write failing loopback-provider tests for draft-hidden source extraction, exact dependency bindings, strict projected schemas, zero tools/retries and unchanged original answer.
- [x] Compose `source-obligations -> answer-audit -> done` through installed public Runtime/Harness APIs. Stage 2 independently sees the same authorized bodies and bound ledger; no grading key or historical verdict enters either prompt.
- [x] Verify completed resume makes zero calls. Changed owner, packet, answer, scope, versions or policy rejects resume. Unknown usage prevents dependent dispatch and retains full allowance.
- [x] Preserve failed raw receipts and inner timeout metadata alongside outer unknown usage. Assert prompt-injection fixtures cannot alter tools, scope or workflow ownership.

## Task 4: Explicit opt-in runner, documentation and review

**Modify:** Existing benchmark CLI/runner only to add a separate explicit audit operation; do not alter default answer or completeness paths.

**Create:** `docs/answer-span-audit.md`, `tests/unit/test_memory_span_audit_cli.py`, a verification report with raw-log references.

**Consumes:** Task 3 public consumer API.

**Produces:** An explicitly selected audit-only fixture/consumer operation; ordinary memory/SUE/default paths remain unchanged.

- [x] Write failing CLI/default tests, including attempted automatic repair, missing opt-in and unavailable memory with frozen context.
- [x] Add explicit audit-only selection and report original answer versus audit sidecar separately. Preserve strict fixed denominators and no-oracle fallback reporting.
- [x] Run the full appropriate Lab unit/functional suite plus memory/canonical review suites; build the wheel and run installed-wheel fixture checks. Record actual results and infrastructure limitations.
- [x] Request a fresh final regression review, fix substantive findings with RED/GREEN checks, and preserve final diff/verification evidence privately.
- [x] Document that real Qwen quality, q022 adjudication and any repair stage require a separately predeclared bounded comparison. Do not issue model requests or reuse unknown invocations.

## Current state

The baseline was restored from sealed artifacts and the audit-only workflow is
implemented in the isolated `codex/castle-answer-span-audit` worktree. The primary
Lab checkout remains untouched. A fresh review found four Important issues;
limitation-only coverage, unaudited positive-claim suffixes, contradictory status
judgments and same-version SDK replacement are now rejected. The focused native
suite passed 44 tests before the final conflict/instruction-boundary controls.
The final wider candidate suite passed 368 tests plus 109 subtests, and the
released-SDK rerun passed all 2033 tests. Installed-wheel checks passed on macOS
ARM64 and offline Linux ARM64. Final source packaging includes the verification
report and private evidence is retained with a sealed recovery archive. No live
inference, repair, push or publication is authorized by this plan.
