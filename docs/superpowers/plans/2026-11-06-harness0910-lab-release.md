# Harness 0.9.10 adoption and Lab 0.9.7 release plan

> **For agentic workers:** Use superpowers:executing-plans for native execution of this approved dependency update.

**Goal:** Publish Lab 0.9.7 using Harness 0.9.10, Runtime 0.9.14 and Core 0.5.0.

**Architecture:** Retain public checksum-pinned SDK installation and closed compatibility families. Archive the prior manifests, provenance and memory freezes verbatim before advancing current records. Application behavior and session policy migration are unchanged.

**Tech Stack:** Python 3.12, released wheels, Docker, PostgreSQL 16/18, native Linux AMD64/ARM64 CI.

**Spec:** The maintainer's dependency and release request; `../specs/2026-10-09-prosaic-integration-lab-design.md`.

## Global constraints

- Core 0.5.0, Runtime 0.9.14, recorder 0.3.0 and store 0.4.1 retain existing public bytes.
- Keep unrelated checkouts and all historical evidence unchanged. No live inference.
- Require all four ordinary, four guarded and two reasoning jobs on final source.
- Merge only the expected qualified head with identical tree; publish original CI archives.

## Review focus

- Partially upgraded or unknown families must still fail closed.
- Previous SDK provenance must remain selectable by its original versions.
- Corpus, prompts, scoring and old freeze records must retain their bytes.
- Installed wheel and rebuilt source must carry the new archived resources.
- Owned-stack cleanup must pass; missing infrastructure cannot count as success.

## Task 1: Adopt the exact public SDK family

- [x] Update/add regression expectations for exact pins, closed gates, historical provenance and memory lineage; observe failure.
- [x] Archive active manifests/profile/freezes under `pre-harness0910` names. Update active manifests, profile, resource allowlists and development/evaluation freezes.
- [x] Admit the exact new family in `lab_runner/gates.py` and installed-consumer smoke selection, retaining all previous families.
- [x] Update current README/guides, Lab version and release notes; retain historical release documents.
- [x] Run focused regressions and full source tests with an SDK-only environment.

## Task 2: Qualify and publish

- [ ] Build wheel/source, consumer image and run owned PostgreSQL acceptance plus installed ordinary, guarded and reasoning checks.
- [ ] Review the complete diff, commit only scoped files, push PR and require all ten final-head CI jobs.
- [ ] Verify original CI archives and safe receipts; expected-head merge with equal trees.
- [ ] Tag and publish original CI archives plus sanitized qualification proof; verify anonymous downloads and fresh installed consumers. Attach separate postpublication proof.
