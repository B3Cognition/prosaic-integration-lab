# Build repeatable multiuser and accounting acceptance lab

The maintainer approved the
[integration-lab design](https://github.com/B3Cognition/prosaic-integration-lab/blob/main/docs/superpowers/specs/2026-10-09-prosaic-integration-lab-design.md)
on 2026-10-09. This issue is the continuation checklist for Codex on another
machine. The repository currently contains documentation only; it has no
working service, stack or acceptance commands.

Read [AGENTS.md](https://github.com/B3Cognition/prosaic-integration-lab/blob/main/AGENTS.md)
and [docs/handoff.md](https://github.com/B3Cognition/prosaic-integration-lab/blob/main/docs/handoff.md)
before starting. Write/review the implementation plan and select the execution
method before coding. Retain the approved design; do not restart brainstorming
unless the scope materially changes.

## Remaining work

- [x] Approve the written design and preserve ownership/safety boundaries.
- [x] Create the public repository and publish documentation-only handoff.
- [ ] Write/review the implementation plan and select execution method.
- [ ] Lock released core/adapter wheels and SHA256 provenance; build the clean
      consumer image without sibling checkouts or private imports.
- [ ] Implement exact-owned disposable stack provisioning, explicit schema init,
      restricted grants, readiness gates and identity-validated cleanup.
- [ ] Implement generated fixture identities, owner-only authorization,
      PostgreSQL-backed HTTP idempotency and filtered public run/usage views.
- [ ] Wire Harness/PostgresRunStore and Runtime/PostgresRecorder public SDKs;
      keep trusted ExecutionContext out of prompts and preserve it on resume.
- [ ] Prove zero-model-call A-start/B-resume workflow execution.
- [ ] Implement synthetic model responses, independent dispatch counters and
      fixed usage/rate fixtures; prove content and accounting isolation.
- [ ] Exercise same-run races, stale decisions, duplicate starts and identity
      spoofing; deny non-owner access without dispatch or data disclosure.
- [ ] Add deterministic worker-loss/receipt/unknown-call recovery gates.
- [ ] Test accounting prepare/observe failures, unknown/partial/quarantined usage,
      immutable replay and changed-default/conflicting-context resume.
- [ ] Prove bounded overload, per-replica resource cleanup and repeated full-suite
      runs with fresh isolation; preserve state within restart scenarios.
- [ ] Add a non-sticky load balancer and alternating-replica acceptance proof.
- [ ] Add PostgreSQL 16/18 required CI; verify Linux/arm64 and Linux/amd64 and
      report any untested architecture/version combinations.
- [ ] Implement explicit live TokenProxy mode with secret-managed credentials
      and a shared maximum-call allowance; no live tests in default CI.
- [ ] Record fresh commands/results, sanitized JUnit/JSON diagnostics,
      dependency provenance, residual limits and exact cleanup evidence.

## Completion requirements

- The design's 16 acceptance scenarios have executable assertions.
- One documented deterministic command starts fixtures, runs assertions,
  exports sanitized results and cleans only owned resources.
- Recovery/load lanes are synthetic and use observable fault gates, not sleeps.
- Missing required infrastructure/skipped gates fail; no false-green suite.
- Model dispatch counts and accounting evidence are checked independently.
- Authorization metadata, workflow state and usage evidence survive tested
  replica restarts without automatic redispatch of uncertain calls.
- Public responses/logs do not expose secrets or private operator state.
- No production auth, exactly-once external effects, zero-loss failover,
  customer charging or whole-run cost-coverage claim beyond measured resources.

Link commits and actual verification evidence when checking an item. Fix library
defects with regressions in the owning upstream repository, not local patches.
