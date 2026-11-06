# Prosaic 0.5 SDK adoption implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this scoped update inline.

**Goal:** Adopt published Core 0.5.0, Runtime 0.9.13 and Harness 0.9.8 in both active Lab manifests and verify the complete integration suite.

**Architecture:** Retain checksum-pinned public wheels and installed-payload auditing. Extend the Lab's explicit supported-train records while preserving historical manifests, packaged provenance and existing admission rules. Archive and refresh dependent memory provenance freezes without changing benchmark inputs.

**Tech Stack:** Python 3.12, pytest, locked third-party dependencies, Docker Linux ARM64, PostgreSQL 16/18.

**Spec:** User request in this chat; existing Lab design and AGENTS.md ownership boundaries.

## Global constraints

- Core 0.5.0; Runtime 0.9.13; Harness 0.9.8; Runtime recorder 0.3.0; matching Harness store 0.4.1.
- Verify actual PyPI wheel downloads against original GitHub release checksums and source receipts.
- Keep the third-party lock, historical evidence, unrelated working tree and live-model settings unchanged.
- Use only public installed SDKs; no library patches, paid inference, broad Docker cleanup, publication or unrelated commits.

## Review focus

- Unknown/mixed trains must still fail closed; all nine required modes and context cases must remain enabled.
- Archived public and private benchmark trains must remain reproducible and selectable.
- SDK provenance embedded in the Lab wheel must match the active manifest bytes.
- Real-stack tests must verify their exact owned cleanup and must not pass missing infrastructure by skipping.
- Record the actual architecture and PostgreSQL versions tested without claiming unrun live/provider qualification.

## Task 1: Adopt the verified SDK train

- [x] Preserve both former active manifests and former packaged public provenance in named snapshots.
- [x] Update dependencies/releases.json and dependencies/releases-reasoning.json from verified public artifacts.
- [x] Add the coherent train to lab_runner/gates.py and packaged quality provenance selection; preserve older trains.
- [x] Update focused provenance/admission tests and run them with the new installed SDK family.
- [x] Update README, current installation guides and a new verification ledger; retain historical release reports.

## Task 2: Verify the integration

- [x] Install the hashed third-party lock and exact five SDK wheels; audit installed payloads and pip dependencies.
- [x] Run PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q and separate reasoning acceptance.
- [x] Build the Lab wheel/sdist and run installed reasoning/distribution smoke checks.
- [x] Build an isolated released consumer image and the immutable historical baseline.
- [x] Run scripts/required_acceptance.py for PostgreSQL 16 and 18 using the isolated immutable image IDs; inspect every lane and cleanup receipt.
- [x] Review the scoped diff, record actual commands/results and report remaining platform limits.
