# Release Train Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Commit all authorized repository changes and publish verified releases in dependency order.

**Architecture:** Integrate existing reviewed Runtime/Harness fixes into their main branches. Publish immutable GitHub release artifacts, then pin their exact bytes and commits in the integration blueprint before released-mode acceptance and publication.

**Tech Stack:** Python wheels/sdists, pytest, owned PostgreSQL/Docker fixtures, GitHub Actions and Releases.

**Spec:** Maintainer request: commit everything in all repositories, increase versions as needed, create new releases.

## Global Constraints

- Publication, shared-branch integration and all existing changes are explicitly authorized by the maintainer.
- Preserve historic red receipts and unrelated private/ignored data. Never publish secrets, private runs, databases or generated credentials.
- No paid inference. Keep public installed SDK boundaries and exact-owned cleanup.
- No force push or tag replacement; fetch and preserve remote work.
- Prosaic 0.3.1 is unchanged at its current release tag; verify it, avoid an unnecessary version bump.

## Review Focus

- Unreleased Anthropic behavior requires Runtime minor 0.7.0, not patch-only relabeling.
- Both PostgreSQL adapter artifacts must ship their reviewed 0.1.1 fixes and compatible core version constraints.
- Harness must pin the actual new immutable Runtime release commit.
- Lab must consume downloaded published wheels, reject payload tampering, and pass released-mode native gates.
- Billing work must be committed and verified without publishing private fixture evidence.

## Tasks

- [ ] Fetch all remotes; integrate the clean Runtime/Harness fix branches and remote main changes.
- [ ] Release Runtime 0.7.0 with recorder 0.1.1: version/CI/docs, full core + adapter tests, builds and installed wheel checks, commit/push, native CI, tagged GitHub assets/checksums.
- [ ] Release Harness 0.6.1 with store 0.1.1: new Runtime commit pin, version/CI/docs, full core and owned adapter matrix, builds/installed checks, commit/push, native CI, tagged GitHub assets/checksums.
- [ ] Commit the complete lab including approved Lago work; release lab 0.2.0 with new immutable release manifest and updated provenance checks. Full local suite, released PostgreSQL 16/18 acceptance and Lago lanes, native matrix, source/wheel artifacts and checksums.
- [ ] Verify every remote release/asset, clean tracked checkouts and included upstream fixes; update issues and release ledger with actual evidence and outstanding deployment qualification.

Execute inline. User has already chosen publication; no additional menu or publication approval is required.
