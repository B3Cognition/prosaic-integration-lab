# Observatory 0.8.0 release plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Merge the Observatory and publish verified Lab 0.8.0 artifacts.

**Architecture:** Add release metadata to the main-based feature branch, qualify
that exact source through the existing protected PR matrix, merge only the
qualified head, then publish its original CI artifacts and provenance.

**Tech Stack:** GitHub pull requests, Actions, immutable release assets, Python
wheel/sdist consumers and the unchanged public SDK train.

**Spec:** Maintainer's “Ok proceed” after the completed merge/release readiness
work and green four-cell qualification. Merge and release are authorized.

## Constraints

- Version 0.8.0 is a minor release for the additive Observatory feature.
- Preserve Runtime/Harness/adapter pins and all historical tags/artifacts.
- No force pushes, tag replacement, paid inference or unrelated source changes.
- Never replace qualified release files with locally rebuilt files.
- Use the exact qualified source/tag and verify merge file-tree equality.

## Steps

- [ ] Update version/changelog/release guide; verify metadata and source assets.
- [ ] Commit/push and create the release PR; qualify its exact head on all four
  supported architecture/PostgreSQL cells.
- [ ] Verify safe receipts, archive payloads and checksums; merge with the expected
  head SHA only after all required checks pass.
- [ ] Tag the qualified source, publish original CI wheel/source with checksums
  and verification metadata, then verify anonymous downloads and clean consumers.
- [ ] Report the merged PR, release URL and actual post-publication evidence.

## Review focus

The previous 0.7.0 qualification cannot certify renamed 0.8.0 artifacts. Source
archives must retain Observatory runtime/authoring assets, and the source-only
host-fixture contract must stay explicit. Publication receipts must not contain
credentials or private run state. A successful build or release upload alone
does not prove clean public consumption.
