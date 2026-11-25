# Qwen/Gemma prompts and Lab 0.9.4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan inline. Steps use checkbox syntax for tracking.

**Goal:** Keep the tested compact Qwen and separate Gemma prompts, obtain green CI, merge and release Lab 0.9.4.

**Architecture:** Only blueprint, workflow and release documentation/metadata
change. Runtime still owns native effort controls. The Lab keeps arithmetic,
strict JSON, completion and native-control evidence separate.

**Tech Stack:** Python 3.12, installed published SDKs, pytest, setuptools,
GitHub Actions and immutable GitHub release assets.

**Spec:** The maintainer explicitly authorized keeping these prompts, fixing
CI, merging and releasing a new Lab version. The retained
[Qwen/shared comparison](../../verification/reasoning-prompt-compaction-2026-11-04.md)
and [Gemma comparison](../../verification/reasoning-gemma-minimal-2026-11-04.md)
identify the exact bodies and their limits. This instruction supersedes those
experiments' earlier no-publication scope; no further confirmation is needed.

## Global Constraints

- Version 0.9.4 follows published v0.9.3; base main is `0220109` with the same tree as qualified v0.9.3 source `719fdb1`.
- Preserve all seven 95-word compact shared Qwen bodies and the selected 69-word Gemma body byte-for-byte.
- Preserve both SDK manifests and lock files: ordinary Runtime 0.9.8, reasoning Runtime 0.9.12.
- Explicit Gemma workflow selection does not add automatic model-specific prompt routing.
- Require four Linux AMD64/ARM64 × PostgreSQL 16/18 acceptance cells and both installed-reasoning architectures on the final versioned source.
- Publish original CI wheel/sdist; no local replacement or existing tag/asset mutation.
- Preserve all failed/unknown live evidence and allowances. No additional live inference or SDK release is needed.

## Review Focus

- The Gemma file must ship in both archives and resolve in the installed workflow: existing installed workflow validation plus exact archive/source audit.
- Qwen/shared bodies must remain identical except effort metadata and match tested hashes: existing consistency tests plus release inventory.
- Gemma output caps must not be relabelled wrong integers or JSON success: retained qualification tables and independent review.
- Release bytes must belong to the exact qualified 0.9.4 tree: source/CI/merge tree comparison, archive inventory and SDK audits.
- Public downloads must match the original CI assets and work in clean consumers: postpublication ordinary/reasoning wheel and rebuilt-sdist checks.

### Task 1: Final versioned source and review

**Files:** Eight `lab_runner/reasoning_eval/data/subagents/*.md` files,
`workflow.yml`, blueprint README, `pyproject.toml`, `CHANGELOG.md`, `README.md`,
`docs/current-status.md`, `docs/reasoning-effort.md`, `docs/handoff.md`,
`docs/release-0.9.4.md`, and the three retained prompt qualification ledgers.

**Interfaces:** Consumes tested canonical Markdown and unchanged SDK APIs;
produces a versioned 0.9.4 source tree and installable example resources.

- [ ] Update metadata and current release documentation, preserving historical experiment identity and limitations.
- [ ] Start `.venv/bin/python -m pytest -q`; run the 31 reasoning acceptance tests and build/audit exact source/archive inventories with required fixture permissions.
- [ ] Commit and push the versioned branch after the focused tests/build pass; open and attach its PR while the full local suite and CI finish. Do not merge until every required result passes.
- [ ] Obtain a fresh whole-branch review; address blockers and verify fixes without weakening existing gates.

### Task 2: CI, merge and immutable publication

**Files:** Private release evidence under `/private/tmp/prosaic-lab-0.9.4-release-*`;
no credentials, raw reasoning or host run state enter Git or public receipts.

**Interfaces:** Consumes the exact reviewed head and successful CI artifacts;
produces merged/tagged source, original public archives, verification/checksums
and separately named postpublication proof.

- [ ] Require all six final-source jobs green; inspect counts, no-skip gates, cleanup and original artifact digests. Diagnose and fix any real failures.
- [ ] Merge with an expected-head guard and verify qualified source, CI merge tree and actual merge tree equality.
- [ ] Publish v0.9.4 with original CI archives, safe receipts, checksums and source/merge provenance.
- [ ] Verify anonymous downloads and fresh ordinary/reasoning wheel and rebuilt-source consumers; attach postpublication proof without replacing assets.
- [ ] Confirm previous releases/tags/assets are preserved, record completion and report the public release URL.
