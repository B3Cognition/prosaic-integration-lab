# Frozen bounded correction evaluation plan

> **For agentic workers:** Use superpowers:executing-plans, native selected.

**Goal:** Frozen failure-inclusive live comparison, then release/milestone advice.
**Architecture:** Private evaluation host around installed public Lab/SDK APIs;
independent case oracle, durable sample reservations, immutable frozen guards.
**Tech Stack:** Python3.12, existing installed Lab/SDKs/counters, synthetic HTTP.
**Spec:** `docs/superpowers/specs/2026-10-18-correction-live-design.md`.

## Global Constraints

-16samples:4fresh opaque cases×2models×2arms, independent workers,8potentialpairs.
-Per arm4requests/2tools/8192tokens/600seconds/output512; no tuning/retries.
-Prior1494/605/1805193;ceilings1524/625/1976623;8unknowns remain charged.
-Need34requests/12tools/0tokens, newceilings1558/637/1976623; explicitapproval.
-No live call before frozen offline qualification and approval; no push/release.
-SDK/Core/Lab executable source stays unchanged; preserve old environments.

## Review Focus

-Unknown/unreceipted observations cannot settle as known or be retried.
-Exact actual draft/evidence mismatch must not count as critic benefit.
-Native feedback must exclude gold/rules and raw critic claims.
-Frozen script/config/counter drift and missing consent must prevent dispatch.
-Source-scoped oracle must distinguish unread/missing/conflict without inventing values.

### Task 1: Prepare, qualify, freeze and dispatch the evaluation host

**Files:** `/private/tmp/prosaic-correction-live-{inputs,common,fixture,qualify,run,analyze,freeze}.py`,
`/private/tmp/prosaic-correction-live-host-tests/test_host.py`, local proof/results docs.
**Interfaces:** `build_inputs(seed)`, `oracle(case,rows,rules)`, `guard(authorized)`,
`run(proof,...,check=...)` around public execute/recover/score/compare APIs.

- [ ] RED→GREEN: fresh balanced cases/oracle, exact consent, drift/claims,
  conservative settlement and failure-inclusive matching/recovery.
- [ ] Run16actual-counter synthetic lanes plus fault tests; original counters
  and131installedpayloads/SDKs verified; one fresh final host review.
- [ ] Freeze all relevant bytes and calculate exact extra allowance; request it
  with concrete offline proof; wait for literal explicit approval.
- [ ] Dispatch frozen schedule once, reserve each full sample, stop on uncertainty.
- [ ] Independent source/accounting audit and network-denied recovery, preserve
  every result, ledger and previous guard; report benefit/gaps/release/next work.
