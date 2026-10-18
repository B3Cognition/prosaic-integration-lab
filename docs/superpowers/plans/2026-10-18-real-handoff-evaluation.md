# Frozen real-model handoff evaluation

> **For agentic workers:** Use superpowers:executing-plans for the selected native workflow.

**Goal:** Evaluate the existing typed handoff across both approved model profiles,
measuring critic contribution separately from independent host enforcement.

**Architecture:** Add an opt-in measured executor consuming public installed SDK
APIs and trusted registered counters. Preserve the graph, prose and default
synthetic-only executor. Freeze fresh cases and counter/SDK/operator identities
before live dispatch; the host allowance wrapper reserves whole cases first.

**Tech Stack:** Python3.12, installed SDK candidate family, pytest, qualified
local counter assets. No serving-engine import or model-specific prompt tuning.

**Spec:** `docs/superpowers/specs/2026-10-18-typed-handoffs.md` plus the user's
authorization for a frozen real-model evaluation across both models, with a
separate request for any additional allowance before exceeding current ceilings.

## Global Constraints

- Per case4requests/2tools/8192tokens/600seconds/output512; no automatic retry.
- Keep current graph, schemas, prompts, model profiles and serving settings.
- Preserve all historic evidence, reservations and unknown usage charges.
- No live probes, dispatch, push or release before the required allowance exists.
- Counter/provider/model mismatch fails before dispatch; unknown/overrun stops run.

## Review Focus

- Synthetic counters must never be silently substituted for a measured caller.
- A real-profile mismatch must fail before the first request.
- Shared request/token/tool caps cover planner, worker and critic together.
- Critic abstention, missed flaws and false alarms must be separate from host gates.
- Partial/unknown runs retain full reservations and are never silently redispatched.

### Task 1: Measured execution and frozen evaluation preparation

**Files:** `lab_runner/handoffs/execution.py`, new
`tests/functional/test_measured_handoffs.py`, private study operators under a new
temporary root, `docs/verification/real-handoffs-2026-10-18.md`.

**Interfaces:** `execute_counted_case(case, config, output, sample_id,
token_counter)` returns the same receipts/checkpoint/journal/counts plus elapsed
time and persisted recorder/turn/counter observations. Caller owns allowance and
explicit live opt-in. The existing synthetic executor remains the default.

- [ ] Write failing real-HTTP fixture tests for measured execution, counter mismatch,
  missing counter, shared exhaustion and network-denied reconstruction.
- [ ] Implement the public SDK executor and recording; focused tests pass.
- [ ] Run complete Lab suite, build and audit a private candidate wheel; obtain
  one fresh final review and fix important findings with RED/GREEN regressions.
- [ ] Freeze four fresh cases (approve/reject/missing/conflict), eight scheduled
  samples across two models, independent expected fields, exact artifacts,
  serving/counter guards and analysis protocol. Qualify all cases offline with
  actual registered counters against synthetic HTTP; no live endpoint probes.
- [ ] Request full allowance deficit after preparation: prior1468/601/1769171,
  ceilings1475/604/1976623, full reservation32/16/65536. Need25requests/13tools,
  new ceilings1500/617/1976623. Preserve eight unknown reservations.

### Task 2: Authorized live run, audit and interpretation

**Interfaces:** consume frozen qualification and explicit allowance approval.
All eight whole-case reservations must fit before starting. Stop on uncertainty,
overrun or asset drift. No tuning/correction after live results.

- [ ] Execute once per scheduled sample after allowance approval; save all receipts,
  counter proposals, observations and outcomes privately. Reconcile usage and
  copy/reconstruct saved state under a denied-network audit.
- [ ] Report per-model worker correctness, critic catches/misses/false alarms,
  critic coverage and request/token/time cost; compare pre/post critic decisions
  within the same trajectory, not an invented randomized no-critic experiment.
- [ ] Explain if evidence is insufficient to show critic benefit (including zero
  natural worker-error opportunities). Attribute host safety separately. Preserve
  all ledgers and artifacts; update handoff/progress and commit locally.

Ruling: use four cases per model, alternate model order, memory disabled, one
trial per pair. Cost: small exploratory coverage, no statistical efficacy claim.
Ruling: preserve existing prose/contracts before observing model outcomes, even
where their limitations may surface. Cost: task/contract adherence may limit
critic coverage; report that rather than tuning to these models.
