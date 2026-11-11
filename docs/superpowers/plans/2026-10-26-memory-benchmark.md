# Memory Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task.

**Goal:** Make the private memory comparison reproducible through a maintained opt-in Lab CLI with user datasets.

**Architecture:** New `lab_runner.memory_benchmark` consumer package. Dataset/public packet, private key and private model configuration remain separate. Reuse public Runtime/Harness and the tested consumer allocator/cache/contracts, preserving original experimental archives.

**Tech Stack:** Python 3.12+, existing public SDK family, jsonschema, literal rg, optional Castle adapter/worker.

**Spec:** `docs/superpowers/specs/2026-10-26-memory-benchmark-design.md`.

## Global Constraints

- No default enablement, SUE/SOAR path or publication. The later explicit
  maintainer request authorizes a separate frozen 100-question live comparison;
  no live calls are implied by installing or invoking the default CLI.
- Namespace and wing authority come from host policy, never the dataset/model.
- Up to 1,000 cases; frozen finite per-case and shared ceilings; no missing/failed case removal.
- Exact UTF-8 source bytes, strict citations, no weaker old assertions.
- Unknown/pending completion stops dispatch and retains reservations; no implicit redispatch.
- Private keys/source data/results never committed; portable installed-wheel commands.

## Review Focus

- Symlinks/path traversal or changed files must reject before reads/dispatch.
- Unknown completion with known token counts must retain allowance.
- Missing keys/verdicts must not produce a correctness score.
- Mixed namespaces/wings, altered previews or wrong revisions must fail closed.
- Large datasets must not enlarge per-task context or silently truncate denominators.

### Task 1: Frozen datasets and legacy consumer qualification

Files: new `lab_runner/memory_benchmark/{dataset,storage}.py`, portable consumer helpers, `tests/unit/test_memory_benchmark_dataset.py`, ported synthetic regressions.

Interfaces: `freeze(dataset_path, policy_path, output)`, `load_frozen(output) -> dict`; strict manifest includes files with source ID/wing/path, cases with IDs/question/queries/source grants; optional external keys. Policy supplies namespace/allowed wings.

- [x] Write dataset tests for supplied 200-case input, key isolation, exact CRLF/Unicode, tamper/path/scope rejection; run RED.
- [x] Implement bounded canonical decoding, safe scoped reads and exclusive frozen files; port consumer helpers with origin hashes and synthetic tests.
- [x] Run dataset and imported regression tests GREEN; retain output.

### Task 2: Scoped paired retrieval

Files: new `retrieval.py`, context helper parameter adaptation, focused tests.

Interfaces: `prepare(frozen, case, arm, directory, provider=None) -> public packet`; manual/strict/expanded, same queries and 32 KiB display allowance. Explicit Castle settings enter from host only. Provider snapshot/revision checks precede generation.

- [x] Write RED tests for scoped literal search, same-source expansion, allocator floor/cache, malformed provider evidence, changed snapshots and unavailable memory.
- [x] Implement fixed selection policy, bounded reads and source-bound frames using tested allocator/cache.
- [x] Run retrieval and all inherited tests GREEN.

### Task 3: Bounded execution and replay

Files: new `workflow.py`, maintained completeness profile, `runner.py`, CLI `__main__.py`, fixture helpers and tests.

Interfaces: run fixture/live with explicit config; immutable per-sample outcomes, public Harness receipts, shared BenchmarkAllowance v2; `status`/`replay` are read-only and dispatch zero calls. Review off by default; on schedules paired comparisons without changing retrieval.

- [x] Write RED tests for successful actual SDK fixture journey, strict rejected output, frozen resume, no dispatch on unknown/completed resume and no key leakage.
- [x] Implement public SDK execution, host-only configuration, durable reservations and raw evidence retention; expose CLI.
- [x] Run focused and existing workflow suites GREEN before real inference.

### Task 4: Scoring, documentation and qualification

Files: new `scoring.py`, example fixture/data/policy, `docs/memory-benchmark.md`, README links, verification ledger and tests.

- [x] Write RED tests for unlabelled unmeasured results, exact hash-bound complete facet verdicts, missing/failed denominators and additive reports.
- [x] Implement external verdict validation/reporting and document runnable small/bigger/own-data recipes and limitations.
- [x] Run full suite, build wheel/sdist, installed-wheel fixture and 200-case offline freeze/replay; review final diff and verify defaults/prior archive hashes.
- [x] Record exact results and limitations in `docs/verification/memory-benchmark-2026-10-26.md`. No push/release; separately authorized live attempt remains failed evidence with its unknown reservation retained.
