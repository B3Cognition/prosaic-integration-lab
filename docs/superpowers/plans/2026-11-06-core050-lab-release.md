# Lab 0.9.5 release plan

> **For agentic workers:** Use superpowers:executing-plans for native execution.

**Goal:** Commit and push the isolated SDK adoption, merge on green CI and publish Lab 0.9.5.

**Architecture:** Preserve installed public SDK ownership and exact checksummed
pins. Qualify a versioned source tree, merge only the reviewed head, and publish
its original successful hosted CI archives with separate public-consumer proof.

**Tech Stack:** Python 3.12, pytest, setuptools, GitHub Actions and immutable GitHub releases.

**Spec:** The maintainer's explicit “Ok merge, push, release”; existing Lab design,
AGENTS.md and the completed SDK-adoption plan/ledger.

## Global constraints

- Base main `3cf2d6416f822acde27bf721982571deaa38fe6b`; published latest 0.9.4.
- Core 0.5.0, Runtime 0.9.13, recorder 0.3.0, Harness 0.9.8, store 0.4.1.
- Keep historical manifests/provenance/freezes, prompt bytes and third-party lock unchanged.
- Preserve original dirty checkout; no unrelated files, SDK changes or live inference.
- Require four acceptance cells and two reasoning jobs on the exact final source.
- Publish original CI archives and new proof assets; do not replace prior releases.

## Review focus

- Exact-family admission retains nine lanes/context and rejects unknown mixtures.
- Historical benchmarks remain reproducible without changing corpus/scoring.
- Archive payloads and metadata match the qualified versioned Git tree.
- Test counts, no-skip requirements, provenance and owned cleanup remain strict.
- Anonymous downloads and fresh installs match original CI bytes after publication.

## Task 1: Versioned source

**Files:** `pyproject.toml`, `CHANGELOG.md`, `README.md`, current status/handoff,
`docs/release-0.9.5.md`, plus the already-tested isolated SDK adoption.

- [ ] Bump Lab to 0.9.5 and record release scope; preserve prior checkpoints.
- [ ] Run focused checks, build, full source and native/reasoning suites.
- [ ] Commit only the isolated scope; push a named branch and open a main PR.
- [ ] Obtain a whole-branch review and address blockers without weakening gates.

## Task 2: Hosted qualification and publication

**Files:** Private task-owned release evidence under `/private/tmp`; public
artifacts contain only archives, whitelisted receipts, checksums and provenance.

- [ ] Require all six final-source jobs green and validate actual receipts/counts/cleanup.
- [ ] Verify original CI artifact digests and source archive/wheel payloads.
- [ ] Merge with expected-head guard and verify source/CI/merge trees agree.
- [ ] Publish v0.9.5 with original CI bytes and safe qualification proof.
- [ ] Verify anonymous downloads and fresh ordinary/reasoning consumers, wheel and rebuilt source.
- [ ] Attach separate postpublication proof; confirm final public state and preserved prior assets.
