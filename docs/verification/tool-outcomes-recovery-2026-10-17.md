# Tool outcomes and bounded recovery — 2026-10-17

## Scope and behavior

This milestone implements provider-neutral tool outcome evidence in Runtime,
bounded recovery admission in Harness, and an opt-in reference in Integration
Lab. Core, model settings, memory prose and scoring remain unchanged. Candidates
are local qualification artifacts; nothing was merged, pushed or released.

Runtime's immutable `ToolOutcome` version 1 contract reports a closed code,
phase, effect, recovery category and replay flag. It derives these from trusted
execution branches, with no argument/result values or exception messages.
Native OpenAI-compatible and Anthropic execution, streaming and structured
observers carry the same safe categories. Existing model envelopes and version
1 journal payloads are preserved.

The default policy remains off. `RunPolicy.bounded_tool_recovery=True` stops
denied or controlled failures and unknown effects; it permits pre-handler
argument correction within existing limits. Runtime does not retry a callback.
`WorkflowPolicy.bounded_tool_recovery=True` requires both new Runtime capability
flags, validates full turn/call/tool/version identity, and may use only an
already-permitted next workflow attempt. Missing, contradictory, malformed or
uncertain evidence cannot authorize a retry. Successful required tools are not
repeated solely for an earlier corrected argument rejection. Runtime terminal
failures retain precedence. Default workflow and conversation identities remain
compatible.

Lab's `bounded_recovery=True` option binds enabled behavior into frozen
execution identity. Its scoped trace retains only validated new outcome fields,
leaving legacy missing evidence unclassified. The seven failed tool attempts in
the prior live comparison are not retroactively assigned a cause.

## Exact artifacts

| Package | Candidate | Source commit | Wheel SHA256 |
| --- | --- | --- | --- |
| Runtime | `0.9.7+tools.1` | `869192a970d52d29c605dfade43fc3dcad82f0dc` | `3aaf4bdd0694826725fe5169be331d131338e279c466bc248c08ab98c1df0eef` |
| Harness | `0.9.1+tools.1` | `f86e5e14551cd7aa13bd0a2ec2dd41e4e84e6abf` | `479f29031d2fb68293ca6ad17b3175f3c9b0793f7da20e803ea86475dd2ae547` |
| Lab | `0.5.1+tools.1` | `355f08cdde6d988b8fabe0a44560cb78b535b791` | `52aca1ce4971a76af1fa80165c09c36eb2524ff73e2d91e65a0334747bb6171f` |

The exact five-SDK family is in
[`tool-outcome-candidate.json`](../../dependencies/tool-outcome-candidate.json).
The [machine-readable qualification evidence](data/tool-outcomes-recovery-2026-10-17.json)
records the source/archive hashes, counts, limits and review outcome.
Core0.4.1, Runtime Postgres0.3.0 and Harness Postgres0.4.0 retain their original
published wheels. Released manifests and prior candidate artifacts are unchanged.
All three new wheel/sdist pairs built with `python -m build --no-isolation`,
including wheel construction from each sdist.

Fresh installed payload checks matched Runtime57, Harness35 and Lab119 files
to the wheel bytes. Their50/29/115 non-metadata files also matched the exact
source commits. Installer-regenerated `RECORD` files are excluded from direct
wheel byte comparison. A separate SDK audit matched all five installed wheels.

## Verification

Final post-review full source suites passed: Runtime1290/1skip (448.04seconds),
Harness855/2skips (166.62seconds) and Lab1294/0skips (181.75seconds):
3,439 passing source tests in total. Before review, the corresponding counts
were Runtime1290, Harness848 and Lab1294.
The Runtime source skip is its separately mandatory installed-wheel gate;
that gate passed explicitly on the final installed candidate. The two Harness
skips require an explicitly configured disposable Postgres lifecycle database.
The external database/auth/billing acceptance lane was not rerun and is not
claimed. Existing fork and HTTP test-client deprecation warnings remain.

The final installed Runtime tests passed55 checks, including the mandatory wheel
gate, both provider wire formats, streaming, argument and authority failures,
controlled failure versus model dictionaries, post-effect handler failure,
invalid/oversized results, journal commit/replay/uncertainty, cancellation,
request/tool caps and observer ownership. Installed Harness passed24 recovery
checks, including durable malformed/contradictory evidence rejection and legacy
terminal precedence. Runtime's static installed ownership/no-Node/CLI smoke
also passed.

```text
<isolated-python> -I -B scripts/scoped_memory_smoke.py --source-root <checkout> --output <new-private-directory> --bounded-recovery
10 scenarios / 19 synthetic provider requests / 9 tool attempts
no additional replay requests; saved trace bytes unchanged
```

This ran from outside the checkout against the final installed Lab wheel. It
covers scoped hostile and irrelevant recall, optional recall exclusion,
mandatory context refusal, memory off, semantic repair, unknown usage, context
capacity limits and pre-dispatch argument repair. Argument repair uses four
requests and two tool attempts, with only one successful handler execution.
Receipt-only replay denies network, retrieval and quotation.

The final public-input consumer image is Linux aarch64:
`sha256:51021c31a46723db45d4daea7b6296c6ce4869d263cfd322389dd5054d90bf1c`.
The same10 scenarios passed with `--network none --read-only`; local loopback
fixtures remain available while external egress is denied. This image uses
the existing public-source consumer layout with installed exact SDK wheels;
the separate environment above qualifies installation of the Lab wheel itself.

## Independent review and fix pass

One fresh reviewer examined the Runtime, Harness and Lab ranges. It found no
Critical or Minor issues and two Important findings. Both entered one fix pass:

- Full tool identity validation: matching only call IDs could accept a completion
  for another tool, and malformed names/IDs could raise rather than block. Seven
  regressions were watched failing, then passing; the24-test recovery set passes.
  The same admission boundary preserves successful builtin tools and provider
  IDs reused in separate native turns, without fabricating builtin versions.
- Mandatory installed-wheel gate: an old version expectation rejected the
  candidate. Its installed regression was watched failing, then passing.

No second review substitutes for these regressions and final suites. No review
findings were deferred, and none were declined within scope.

One implementation ruling reused existing isolated Runtime/Lab worktrees and
created Harness from its exact previously qualified0.9.0 source because its
primary checkout was older. Cost: one additional local Harness worktree.
Branches and evidence are preserved; no merge or publication is implied.

## Limits and readiness

No live inference occurred. Charged cumulative usage remains1,417 requests /
574 tools /1,696,913 tokens, including seven unknown reservations. Ceilings
remain1,475 /604 /1,976,623; remaining allowance is58 /30 /279,710.
Case caps remain4requests /2tools /8,192tokens /600seconds, output512.
The prior canonical allowance ledger and evidence archive were verified
byte-identical. All earlier reservations stay charged.

Offline qualification is complete and ready for a controlled fresh trial
within the remaining allowance. This milestone improves
diagnosis and bounded recovery, not demonstrated model or memory efficacy.
Uncertain effect reconciliation remains application-owned. The prior smaller
model's semantic decision and feedback failures, large mandatory-context
refusals, memory selection quality and wider multi-agent/distributed governance
remain open. No provider-specific tuning was introduced.

After offline closeout, a controlled fresh trial must fit the remaining
allowance. A full24-sample memory comparison requires96request/48tool reservation
slots and does not fit current58/30 headroom. A balanced12-sample comparison
(three families × two models × memory on/off) can reserve48requests/24tools/
98,304tokens under the unchanged case caps. No such
live trial is dispatched or authorized by this qualification report.

Private artifacts, source-suite logs, synthetic receipts and payload audits are
retained under `/private/tmp/prosaic-tools-*`; the closeout evidence archive
records their immutable hashes. The execution ledger is retained to preserve
historic evidence as instructed.
