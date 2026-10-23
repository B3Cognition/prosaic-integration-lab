# Tool authorization and approval implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make exact tool actions require durable trusted-host approval that model content cannot grant.

**Architecture:** A private local consumer registry binds immutable proposals and host decisions. Its one-shot callback plugs into public Runtime CustomTool authorization, leaving execution and effect journals to the SDK/consumer.

**Tech Stack:** Python3.12, POSIX locks/fsync, public Runtime0.9.7/Harness0.9.4, pytest.

**Spec:** `docs/superpowers/specs/2026-10-18-tool-approval.md`

## Global Constraints

- Per case remains4requests/2tools/8192reported tokens/600seconds/output512.
- Global ceilings1558/637/1976623, charges1509/610/1835168, nine unknowns retained.
- No live requests, SDK changes, authentication service or model-specific tuning.
- Memory/correction and this blueprint stay experimental.

## Review Focus

- Forged model approval/actor fields must never change host consent (wire tests).
- Concurrent exact calls must obtain permission only once (race test).
- Lost consent acknowledgement must not permit retry after restart (subprocess test).
- Stale review or changed execution binding must fail before an effect (digest/scope tests).
- Revocation after claim cannot imply an in-flight effect was cancelled (spent-state test/docs).

### Task 1: Host approval registry and public SDK offline blueprint

**Files:**
- Create `lab_runner/tool_approval.py`, `lab_runner/tool_approval_fixture.py`.
- Create `tests/unit/test_tool_approval.py`, `tests/functional/test_tool_approval.py`.
- Create `scripts/tool_approval_smoke.py`, `docs/tool-approval.md` and qualification.
- Update `README.md`, `docs/handoff.md`, `docs/verification/progress.md`, `pyproject.toml`.

**Interfaces:**
- Consumes public `InvocationScope`, `ToolExecutionContext`, `CustomTool.authorize`; existing Lab canonical/private-file helpers.
- Produces `ApprovalGate(path, identity=sha256, tools={name:version}, approvers=[actor])`; `propose(id, tool_name=..., scope=InvocationScope, arguments=dict, evidence_digest=sha256, ttl_seconds=600)` returns immutable proposal with digest; `decide(id, actor=..., proposal_digest=sha256, approved=bool, decision_digest=sha256)`; `authorizer(id)` returns `(arguments, context)->bool`; `inspect(id)` reads private state without dispatch or approval.

- [x] Write tests for exact approval, forged decisions, digest/scope/action drift, deny/revoke/expire/cancel, one-shot races and process loss. Run and watch missing-blueprint failures.
- [x] Implement minimal private registry and strict persisted validation, with no executor, lease or effect-outcome claims. Run focused tests GREEN.
- [x] Write public-SDK both-wire boundary tests and installed-smoke entrypoint test; observe missing fixture/smoke failures before adding the fixture/script. Assert real effects and charged requests/tools, not mock calls.
- [x] Write adoption guide, run full source suite, build fresh wheel/sdist, reconcile installed payloads and run network-denied installed recovery proof plus clean-distribution checks.
- [x] Commit, run one fresh independent final review, fix material findings with watched regressions in one pass and repeat full checks as needed. Preserve immutable evidence and unchanged historical allowances. Keep the branch for review, without a new live run or release.
