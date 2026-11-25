# Guided ecosystem onboarding implementation plan

> **For agentic workers:** Use superpowers:executing-plans for inline implementation and a fresh whole-branch review.

**Goal:** Give newcomers a credential-free first result, a guided fallback demonstration and an explicit path to real models and product integration.

**Architecture:** Reuse released Lab0.6.2/Runtime0.9.8 commands and installed public APIs. The README becomes the entry point; a quickstart connects existing demos, while a standalone example demonstrates workflow admission without inference. Browser unified-pool execution remains separate.

**Tech stack:** Markdown, Python3.12, released Prosaic SDKs, pytest; Docker only for optional service demonstrations.

**Spec:** The user's approved six-step guided-showcase description in this conversation.

## Constraints and review focus

- Preserve SDK pins, historical releases/evidence, existing policies and budgets.
- First run needs no credentials, Docker or inference; installation needs network.
- Distinguish workflow admission, native CLI execution, fixtures and live models.
- No implicit live dispatch, browser pool support or production authentication claims.
- Keep current relative links valid and retain old README section anchors as pointers.

## Tasks

- [x] Replace the README front door with benefits, ecosystem ownership, current release, a capability/prerequisite table and a start link; retain long-form historical/operator material separately and keep old section anchors usable.
- [x] Add a quickstart: checksummed released setup; zero-inference example; installed fixture/fallback checks with expected output; optional Docker workflow/browser; private native/local config and bounded CLI policies; benchmark default180/explicit240; symptom-based troubleshooting.
- [x] Add a minimal public-SDK workflow admission example and an end-to-end subprocess test. Observe failure before adding the example, then validate real installed SDK behavior. No execution engine changes.
- [x] Correct stale candidate/current-release labels in active guides/configs; add release0.6.2 verification summary, checkpoint and source/archive qualification. Run commands, links, full tests, clean build/installed example, then independent review. Keep this change local unless separately authorized to push/merge/release.

## Verification ledger

Implemented inline. The first example failed before implementation, then passed. Full suite: 1,923 passed in 500.29s (one existing dependency warning). Fresh setup and both installed consumers passed; 13 CLI and 18 fallback checks passed; both owned PostgreSQL service demos passed with verified cleanup. Independent review setup finding fixed and re-reviewed clean. See ../../verification/guided-onboarding-2026-10-25.md. No live provider calls, push, merge or release.
