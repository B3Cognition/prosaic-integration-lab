# Durable failure isolation — offline qualification, 2026-10-18

PR18 was marked ready and merged as `1c52747b187043c98f7113eeada7bcdb3cf3cdab`.
All four required AMD64/ARM64 × PostgreSQL 16/18 jobs passed at reviewed head
`a287b1a`; [CI run](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/39145470211).
This milestone starts from that merged revision on `codex/durable-failure-recovery`.

## Scope

Experimental Lab `0.5.1+isolation.2` adds a private single-host containment journal
around whole SDK operations. It persists admission before dispatch, fences
journal writers on explicit isolation, retains complete reservations and permits
only explicit receipt-only recovery. Known overruns retain actual excess and
block new admission. The [adoption guide](../failure-isolation.md) states the
host authorization/evidence-verification duties and local durability limits.

This is a host blueprint, not a replacement Runtime recorder, Harness engine,
distributed queue or provider-specific recovery policy. No upstream SDK changes,
model/prompt tuning, live calls or stable release are included. Memory and
correction remain experimental; model/critic benefit remains unestablished.

## Initial qualification (`isolation.1`)

- Unit tests: 14 RED missing-blueprint failures, then 14 GREEN. They cover
  process loss after admission/start/completion, concurrency, duplicate claims,
  revoked writers, scope/input drift, conflicting recovery, invalid counts,
  fixed deadlines, malformed/private files and honest overrun containment.
- Functional tests: four both-wire public-SDK lanes and one source-import
  rejection check; focused suite **19 passed**. The first unprivileged attempt
  could not bind loopback sockets; the authorized offline run passed without
  skips. A healthy case uses an independent fixture rather than changing a
  closed-over failing fixture's configuration.
- Installed smoke: four OpenAI-compatible/Anthropic lanes, **16 synthetic
  requests**, four network-denied recovery checks, three real subprocess exits
  at journal commit boundaries. Unknown usage stays unknown; fully persisted SDK
  evidence lost before journal completion can be reconciled. Unrelated reserved
  work completes in both cases. No live requests.
- All **135** packaged source payloads match the installed wheel byte-for-byte.
- Full source suite: **1672 passed**, one existing Starlette/httpx deprecation
  warning, 390.62 seconds. No skipped acceptance requirement was substituted
  for missing infrastructure.
- Clean public-index wheel and rebuilt-sdist adoption passed: isolated imports,
  installed payloads, public construction, CLI checks, existing quality/memory
  smoke checks, pip consistency and owned temporary cleanup. Stack execution
  was **not** part of this local distribution check; PR18's earlier matrix is
  evidence for its own revision, not this new candidate.

The first installed smoke executed its checks but could not write the final
report because the automatically created parent directory was not private.
Preserved its evidence and failure log; repeated into a fresh explicit 0700
study root and passed. No evidence was overwritten or permissive check added.

Public dependencies remain Core0.4.1, Runtime0.9.7, Harness0.9.4,
Runtime-PostgreSQL0.3.0 and Harness-PostgreSQL0.4.0. Manifest SHA256:
`fc4eef2c3d32b641a9c6e12cc7b012464132e0cfbf5e87bbc4e848c72b71b95b`.

Candidate wheel SHA256:
`09e4bdf48bf1d30e7ef47699a9a31a62c0f70f207fae30c814014ae673c9a6bb`.
Candidate sdist SHA256:
`b123512631b73f659860344b424fd430e438c8633d3348dba02aa03cd329e4db`.

## One fresh review and material fix

The independent `gpt-6-astra/high` reviewer found one Important issue at
`e52acee`: a previously admitted item could start after another item's known
overrun. The start gate now checks the journal-wide latch inside the same
exclusive lock. Queued work stays reserved and requires explicit recovery.
Six regressions (requests/tools/tokens × completion/recovery) failed RED before
the fix; the focused suite then passed **25 tests**. The reviewer independently
passed the original 19 tests and reproduced the issue. Zero Critical/Minor
findings; declined-to-judge list empty. No re-review was dispatched.

The fixed candidate is `isolation.2`; all original candidate evidence and
installed environments remain intact. Its 135 source/wheel/installed payloads
match. Final wheel SHA256:
`549682edd6c0dd100c0e477140cb835790569c6fa64a1e249c9f7fab1d9b3088`.
Final sdist SHA256:
`1228038bb9019bbe93385d2fd2abe2b01509450f4b09a2093a0f7657e5818c79`.
Final full source suite: **1678 passed**, one existing warning, 376.64 seconds.
Repeated installed qualification passed four both-wire lanes /16 synthetic
requests, four network-denied recoveries, three process-loss boundaries and
six blocked queued starts. Repeated clean wheel/rebuilt-sdist public adoption
passed, including owned cleanup; no stack execution or live calls. The one
material fix pass is complete; no deferred minors or design rulings.
Host qualification was Python3.12.14 /Darwin arm64; Linux/platform acceptance
for this new candidate remains a future review-PR CI gate.

## Preserved limits and adoption boundary

Per case remains 4 requests / 2 tools / 8192 reported tokens / 600 seconds /
512 output tokens. Cumulative ceilings remain **1558 / 637 / 1976623**;
charged **1509 / 610 / 1835168**, with **nine unknown reservations** charged.
The new containment journal is inside a separately authorized reservation; it
never grants or refunds allowance. Existing frozen studies retain their original
stop policies and cannot opt into isolation retrospectively.

The historical read-only verifier passed: six frozen live samples, 9853 guards,
38 prior ledgers and eight prior unknown reservations unchanged, plus the
latest study's retained unknown. No replay/provider call occurred. Current
canonical total remains 39 ledgers and nine unknown reservations.

Initial proof: `/private/tmp/prosaic-isolation-final-study-20261018`, installed
environment `/private/tmp/prosaic-isolation-final-env`, artifacts
`/private/tmp/prosaic-isolation-artifacts-20261018`. Final proof uses
`/private/tmp/prosaic-isolation-qualified-study-20261018`, environment
`/private/tmp/prosaic-isolation-qualified-env`, artifacts
`/private/tmp/prosaic-isolation-qualified-artifacts-20261018`. Preserve the
initial failed report root `/private/tmp/prosaic-isolation-study-20261018` as well.

Preserved **341** files in the canonical reports directory
`durable-failure-evidence-20261018` (original/fixed artifacts, RED/GREEN and full
logs, installed journals, review/ledger, public distribution receipts, historical
verifier and merge receipt). Verified the copy and every archived payload.
Archive `prosaic-durable-failure-evidence-20261018.tar.gz`, SHA256:
`2983a213242007b4cd3ffc38b57381545f8c9007c35ba8ab164a883b3b3e2847`.
Proof manifest SHA256:
`13f70a0cf77d630c77a81238cb2f12d3019f57d1e58e3f951159236718bde2e2`.
Qualified executable source commit: `ee89d3f`. Keep the local branch and worktree;
review-PR CI and any release/live decisions remain separate gates.

Before a new live evaluation: freeze new operators/cases and
accounting baseline, qualify the consuming host's receipt verification, reserve
all spend under current caps, and obtain live authorization. No new live run
is authorized by this offline qualification.
