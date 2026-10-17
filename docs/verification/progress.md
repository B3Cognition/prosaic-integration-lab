# Implementation ledger — 2026-10-09 integration lab plan

## Tool outcomes and bounded recovery candidate — 2026-10-17

Runtime classifies portable tool outcomes; Harness validates complete call
identity before bounded recovery; Lab consumes the installed public contracts.
The [separate qualification ledger](tool-outcomes-recovery-2026-10-17.md) records
exact local candidates, source and installed/container checks, independent
review, limits and readiness. Released manifests and historical live evidence
are preserved. No provider-specific tuning or live inference is included.

## Published SDK adoption checkpoint — 2026-10-13

The active manifest now selects actual published Core 0.4.1, Runtime 0.9.0/
recorder 0.3.0 and Harness 0.8.0/store 0.3.0 wheels. The previous manifest is
preserved as `dependencies/releases-lab-0.4.0.json`. Fresh ordinary-index
adoption, unit/functional tests and released-mode stack evidence are recorded
in [the separate adoption ledger](published-conversation-adoption-2026-10-13.md).
The checkpoints below retain their original candidate and release evidence.

## Historical conversation candidate checkpoint

Conversation adoption is tracked separately in
[conversation-adoption-2026-10-11.md](conversation-adoption-2026-10-11.md).
Lab 0.5.0 candidate source `34f291e8c7f7dd3809767c2fbf518b55e50204d6`
passed all four Linux AMD64/ARM64 × PostgreSQL 16/18 cells in
[run 38212165309](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38212165309),
including the extracted-sdist stack: 1,395 acceptance executions, 475 conversation
checks, zero failures/skips and verified cleanup. The full local candidate/public
baseline suites passed 943/921 tests. This later docs-only entry records that
exact tested source. The earlier failed capacity result retains an unknown cause;
closed diagnostics repair reporting without claiming a capacity defect was fixed.
Release and ordinary public-index adoption remain pending, and the current
released manifest is unchanged. [Actual local conversation checks](local-conversation-2026-10-12.md)
passed the complete journey at `34f291e` with explicit strong workflow binding,
quoted-approval denial and zero-call duplicate replay. The earlier 7B/server
native failure remains documented. Original final-source platform receipts,
both demos and owned cleanup were independently verified; publication and hosted
qualification remain open.
The historical ledger follows.

Plan and native execution authorized by maintainer's “proceed” after local
endpoint credentials were identified. Branch: `codex/integration-lab`.

- Preflight: Tasks 1/2 share image/provenance; Tasks 2/3 share explicit schema
  provisioning; Tasks 3/4 share immutable owner attribution and assets; Tasks
  4/5 share observable fixture gates; Task 6 consumes runner/result contracts.
- Ruling: Work on a feature branch in the current checkout, preserving the
  uncommitted reviewed plan/config additions; no sibling source modifications.
- Ruling: Prosaic v0.3.1 tag resolves to Runtime's pinned commit. Install the
  original five release wheels with dependency resolution disabled after
  hash-locked third-party installation. Preserve original VCS METADATA and
  audit every installed wheel payload; this avoids mutable VCS resolution
  without rewriting upstream distribution contracts.
- Authenticated local model discovery succeeded. Select 7B Qwen Coder for
  optional local smoke. No key contents were printed or copied into Git.
- Dependency verifier: observed five failures before implementation, then five
  passing tests. All five downloaded wheels match release SHA256SUMS.
- Docker Desktop started; daemon reports Linux/aarch64. Python host 3.12.14.
- Consumer image and host installed-release payload audits passed. Original
  upstream METADATA is retained unchanged.
- Unit suite: 21 passing tests. HTTP acceptance failed against the scaffold,
  then 13 checks passed after public SDK implementation.
- PostgreSQL 16/18 deterministic acceptance: 20 checks passing, no skips,
  cleanup verified. Covers owner isolation, cross-replica progression, stale
  decisions, key races, uncertain starts, asset drift, exact decimal estimates,
  rejected-output usage and missing final usage.
- PostgreSQL 16 load lane: 22 passing checks, no skips, cleanup verified.
  Two blocked executions reject excess work; B remains usable.
- PostgreSQL 16/18 recovery: 25 passing checks, no skips, cleanup verified.
  Receipt-persisted worker loss recovers without dispatch; missing receipt
  requires explicit consent. Prepare failure prevents dispatch, observation
  failure does not redispatch, exact replay does not duplicate estimates.
  Evidence owners: `a2e758e966fe4c9985ff7f057045f462` (16),
  `68e0ae3e885e489592ccb89b86871fd2` (18).
- Ruling: Gate public Harness `on_event` at `accepted`, after receipt
  persistence and before the next checkpoint. Fixture receives event type
  only, never private event payloads.
- Ruling: Docker reassigns ephemeral ports on restart. Re-read ports from the
  same verified container ID. Reproduced this failure before fixing the test.
- Local smoke: exit 0, no timeout, expected output, 85 reported tokens. Initial
  artifact discovery used the wrong source; corrected via public `source`
  constructor option. No library code changed.
- Host Python 3.12.14/libpq 18.0.6; Docker Linux/arm64. Wheel/sdist builds passed.

## Review and corrective verification

One independent read-only reviewer examined the first slice. Two important
findings were reproduced with failing regressions and corrected:

- Persist create intentions before engine mutation; reconcile only exact
  owner/resource labels to real IDs after lost acknowledgements. Unresolved
  intentions remain failures. A successful inventory proves removal; engine
  errors never count as absence. Renamed resources retain immutable labels.
- Freeze namespace/environment in application reservations (app schema 2).
  Run reads/resume/usage reject scope drift with 409 before consulting a
  different run-store/recorder scope. Measured usage cannot become a false zero.
- Readiness now checks the application run-table contract as well as schema
  version; missing tables fail without automatic repair.
- Unit suite grew to 25 passing checks. Namespace drift regression failed on
  the prior image, then passed in PostgreSQL 16/18 recovery acceptance.
- Final unit suite: 27 passed, including stripped/incomplete JUnit exports.
  Sanitization runs in `finally` before teardown, including failure/timeout.
- Final recovery: 27 passed on both PostgreSQL majors. Deterministic: 21 passed;
  load: 23 passed. No skips; cleanup verified. Sanitized receipts are retained
  in `2026-10-09-linux-arm64.json`. No owned test containers remain.
- Full-design omissions listed below remain outside this first-slice review.
  Identity override headers are ignored, never used as trusted attribution.

## Visible accounting evidence

The CLI now supports `python -m lab_runner demo --open-report`. It captures
five real HTTP workflows across A/B: normal completion for Alice/Bob/Carol,
two invalid-output attempts for Alice, and missing final usage for Bob.
The six independent fixture dispatches match six owner-scoped ledger calls.
Five calls have complete usage; one remains unresolved. The known fixture
estimate is USD 0.001850; unknown usage is never rendered as a zero charge.

The saved HTML/JSON contains filtered provider-call IDs, token counts,
estimates and coverage, not credentials, DSNs, prompts or raw operator snapshots.
Demo verification passed on PostgreSQL 16 and 18 with cleanup verified.
The report persists under `.lab/<id>/report/` after fixture teardown.
Unit suite now has 29 passing checks, including decimal report sums, unknown
coverage and HTML escaping. These checks were watched failing before coding.

## Remaining plan coverage

Tasks 1–4 have an executable first slice; Task 5 has fault/load coverage but is
not complete against the full spec. Remaining adapter-schema/corruption negative
cases, tool loops, quarantined/conflicting evidence, token-budget recovery,
changed-default/scope recovery, public-log sentinels, non-sticky proxy and
CI/architecture matrix remain. Task 6 is unimplemented; Task 7 is disabled and
requires separate live-provider authorization. The design and historic issue
body remain unchanged; partial milestones do not complete the full checklist.
# Configurable terminal workloads (2026-10-09)

Added `lab_runner run --users --runs-per-user --concurrency` and a second-terminal
`lab_runner watch --directory --stream accounting|requests`. Trusted fixture
identities span two tenants. Sessions alternate replicas and verify cross-replica
approval, per-run usage and other-user read/usage denial. Request events include
status and latency; accounting events export filtered counts and exact synthetic
amounts. Finite closed-loop sessions, no blind retries, optional explicitly
allowed capacity rejections, independent dispatch/ledger reconciliation and
verified exact-owned cleanup form an initial load/stress foundation.

Verified on Docker Desktop Linux/arm64, host Python 3.12.14, PostgreSQL 16:

- `.venv/bin/python -m pytest -q`: 38 passed. Includes CLI startup without
  editable consumer installation, input limits, accounting-only replay and a
  subprocess follower that waits for new evidence and ends after cleanup.
  External HTTP/recorder boundary regressions exercise workload handling of
  deferred approvals, mismatched ledger evidence and failed owner isolation.
- `run --users 6 --runs-per-user 2 --concurrency 2`: 12 completed, no rejection
  or error, 12 independently counted calls reconciled; cleanup verified.
  Receipt `.lab/7195ba18e5364658949c6d6f8fa714d5/result.json`.
- `run --users 12 --runs-per-user 3 --concurrency 12 --allow-overload`: 12
  completed, 24 capacity-rejected, no correctness errors, 12 reconciled calls;
  cleanup verified. Receipt `.lab/9376828b24c84b6abfe080ef34cce776/result.json`.
- `test --mode load`: 23 passed, zero skips, cleanup verified.
  Receipt `.lab/71393af4cc4c4c479a9feb0cd518a744/result.json`.
- Final single-user path: one completion and one reconciled call, cleanup
  verified, filtered accounting replay successful.
  Receipt `.lab/08740463e1d34bc7abdad1cb345eb696/result.json`.
- Review found that resume admission can reject an already measured workflow.
  Added separate start-rejected and approval-deferred outcomes, retaining usage
  for waiting workflows without retry. Final real `run --users 20
  --runs-per-user 10 --concurrency 20 --allow-overload`: 16 completed, 168
  start-rejected, 16 approval-deferred, no errors; 32 fixture dispatches match
  32 complete accounting calls. Cleanup verified.
  Receipt `.lab/eee0bc31bd714786922dec04cb6f63e9/result.json`.

An intermediate host CLI import failed after reusing the consumer's source-only
projection. A subprocess regression demonstrated that failure; removing that
host installation assumption restored startup. No model/provider credits used.
Arrival-rate control, soak duration, latency thresholds and performance
certification remain pending. Existing acceptance gaps below remain unchanged.

## Production blueprint audit

Maintainer requested aggressive testing and a report of production gaps.
Implemented `--mode audit`: 58 required test cases on PostgreSQL 16 and 18,
49 passing and 9 failing on each, zero skips, cleanup verified. Confirmed gaps
are accounting/application readiness contract/grants, metadata allocation before
execution admission, unauthenticated partial bodies, root execution and writable
assets. Assertions intentionally remain red until their owners fix the behavior.
No library source was patched and the existing green lanes were not weakened.

Added passing checks for malformed/oversized input, owner-scoped key reuse,
completed/lost-response non-redispatch, conflict/quarantine accounting, public
and stdout/stderr sentinels, restricted role identity permissions and finite
token budgets after durable SDK reconstruction. Explicit retry cannot bypass
unknown/consumed token limits; tools remain disabled.

Fresh verification: lab units 38; Prosaic 432 Python/differential plus 55 original
CLI checks; installed wheel smoke passed without Node; released Runtime 361;
newer Runtime checkout 456 (separate scope); release-matching Harness 172.
Released Runtime PostgreSQL adapter tests: 24 passed, zero skips, owned fixture
cleanup verified, after supplying its Harness fixture path and CREATEDB only
to the isolated migration role for its missing-database case. The first two
setup failures are retained separately. Installed five-wheel payload re-audit
and lab wheel/sdist build passed.
Existing recovery 27 on both PostgreSQL majors, load 23 on 16. Baseline 50 users
completed 500 workflows with 500 reconciled calls and zero errors/rejections.
Overload 100 users/1,000 attempts: 6 completed, 971 start-rejected, 23
approval-deferred, 29 measured calls reconciled, zero correctness errors.

One parallel demo setup failed with an unresolved network-create intention and
failed cleanup receipt; successful owner-filtered inventories later found no
owned engine resources. The original failure remains preserved. A fresh demo
18 succeeded. Initial library test setup/provenance failures were corrected,
not counted as product bugs. The full evidence, fix ownership/acceptance and
conditional deferrals are in
`production-readiness-2026-10-09.md`.
