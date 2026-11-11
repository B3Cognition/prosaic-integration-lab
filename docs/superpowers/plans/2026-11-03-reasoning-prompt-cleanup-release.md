# Reasoning prompt cleanup and Lab 0.9.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan inline. Steps use checkbox syntax for tracking.

**Goal:** Remove the ambiguous hidden-reasoning prohibition from all seven
reasoning agents, verify the resulting package and publish Lab 0.9.3.

**Architecture:** Change only the shared prose instruction and release metadata
and documentation. Runtime retains native effort control ownership; the Lab
retains separate control verification, JSON grading and answer correctness.

**Tech Stack:** Python 3.12, installed public Prosaic SDKs, pytest, setuptools,
GitHub Actions and immutable GitHub release artifacts.

**Spec:** The maintainer explicitly requested removing the phrase from every
blueprint, running tests and releasing the next Lab version. The immediately
preceding 12-call prompt study found wording sensitivity without an arithmetic
accuracy improvement. This instruction authorizes the implementation, PR merge
after green CI and publication; no further confirmation is required.

## Global Constraints

- Version 0.9.3 follows published 0.9.2; start at main 77650299c7270e3a7d63592d271a6f7953fcc193.
- Remove only `, hidden reasoning` from each of the seven effort-agent bodies.
- Preserve strict JSON instructions, effort metadata and native mappings.
- Preserve both SDK manifests byte-for-byte: ordinary Runtime 0.9.8; reasoning Runtime 0.9.12.
- Preserve historical evidence, existing tags/assets and unrelated working trees.
- Require the full ordinary four-cell AMD64/ARM64 × PostgreSQL16/18 matrix and both reasoning architectures.
- Publish original successful CI wheel/sdist, never locally substituted rebuilds.
- Verify source/CI/actual merge trees, archive inventories, safe receipts, public downloads and fresh installed consumers.
- No additional live inference or SDK release is needed for this patch.

## Review Focus

Existing effort-consistency, installed-blueprint, archive-inventory and consumer
checks cover the change's inputs. No new uncovered input classes or production
interfaces are introduced by this seven-file copy edit. Do not add a test that
merely mirrors the removed words; inspect the exact body diff and run the real
existing suites and packaged consumers.

### Task 1: Prompt and release source

**Files:** `lab_runner/reasoning_eval/data/subagents/*.md`, `pyproject.toml`,
`CHANGELOG.md`, `README.md`, `docs/reasoning-effort.md`,
`lab_runner/reasoning_eval/data/README.md`, `docs/release-0.9.3.md`,
`docs/current-status.md`, `docs/handoff.md`.

**Interfaces:** Consumes the unchanged canonical Markdown inspection contract;
produces seven identical bodies differing only in effort metadata and versioned
wheel/source resources. No Python interfaces change.

- [ ] Verify existing baseline suites with required fixture loopback access.
- [ ] Remove the phrase in all seven agents; update 0.9.3 metadata/docs and explain the limited accuracy finding.
- [ ] Run full ordinary pytest, all reasoning acceptance tests and installed fixture controls; build/audit wheel and source payloads.
- [ ] Commit/push the final versioned source and open its PR, retaining all required CI workflows.

### Task 2: Review, qualification, merge and publication

**Files:** Host-only release evidence under `/private/tmp/prosaic-lab-0.9.3-release`;
no release credentials, raw logs or endpoint configuration enter the source tree.

**Interfaces:** Consumes Task 1's exact source commit and immutable CI artifacts;
produces public original archives, checksums, safe qualification and subsequent
postpublication receipts under new asset names.

- [ ] Obtain one fresh whole-branch review and address any blockers.
- [ ] Require both final-source CI workflows and all six jobs to succeed; verify original archives, SDK pins, test counts and cleanup.
- [ ] Merge with an expected-head guard and verify identical qualified/source/merge file trees.
- [ ] Tag the qualified source as v0.9.3 and publish original CI bytes plus safe provenance.
- [ ] Verify anonymous downloads, fresh ordinary/reasoning wheel and rebuilt-source consumers, and preservation of all older tags/assets.
- [ ] Attach postpublication proof as new assets and report the published release.
