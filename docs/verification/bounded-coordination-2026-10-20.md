# Bounded coordination qualification

Final code at b70b5f0 passes **1,930 source tests** with one existing Starlette
warning in523.46seconds. Clean public wheel and rebuilt-sdist consumers pass,
including all48installed coordination lanes and network-denied replays in each.
All144source/wheel/installed payloads and five public SDK payloads match;
dependency consistency passes. One Important review finding is fixed with
16watched RED→GREEN corruption regressions. Zero deferred minors.

Status: locally qualified, kept on codex/bounded-coordination for later PR/CI.
No live run, push, merge or release. Later Linux/platform acceptance remains
required for this new branch. Previous PR22 head5c888bf separately passed all
four exact-head CI cells in run39409054174; it remains open and unmerged.
The maintainer approved the complete two-worker blueprint under existing limits.
Branch codex/bounded-coordination starts at PR22head5c888bf; its pending CI and
release closure remain separate. Runtime0.9.7/Harness0.9.4/Core0.4.1 and both
adapter pins remain unchanged. The shared parent cap is4requests/2tools/
8192tokens/600seconds; child caps2/1/4096, output512. No SDK edits.

Watched protocol RED→GREEN:19tests initially, plus partial-failure precedence
and omission of raw worker IDs. Actual-SDK faults exposed recorder intents
preceding budget admission. Use public budget counters and receipts rather
than treating intent count as request count. Failed/incomplete fault outcomes
retain all evidence and unknown accounting; cancellation never refunds capacity.
The corrected focused gate passes86tests in36.98s, including48actual both-wire
sequential/parallel lanes, two process-loss boundaries and15saved-state faults.
A separate FIFO reader regression timed out before the nonblocking regular-file
check and passes afterward. No gate was weakened or skipped.

Standalone source recipe/replay pass48lanes/48network-denied inspections on
macOS arm64/Python3.12.14. Its observed130provider admissions/68tool calls and
18900known reported tokens are synthetic fixture quantities.42/48lanes have
complete usage; the rest retain unknowns. These are infrastructure observations,
not model efficacy, guaranteed latency gains or invoices. Schedule-dependent
fault totals need not repeat exactly. Early replay of an unfinished recipe
correctly refused missing evidence; the later completed separate replay passed.

The fresh review found replay validated the join but ignored contradictory
qualification flags/counters. Final replay validates a closed schema, strict
types, supported caps, fixed assertions and accounting completeness, reconciles
counts with worker evidence and rejects contradictory overlap/wire claims.
All48previous valid lanes still replay. Installed replay also passes under
Python -O and refuses the reviewer's copied corrupted proof. No second review
was commissioned; the single fix pass and full green suite close the finding.

Final wheel56e8a641dbaaf5b376ca4c5aa71236b144a132733b140603d2ccb8cc2ae6b807;
sdist9d2799914e07828503f474f4b1ceccbc9e3c9ef380b045bc42d8f68fc7cc1eff.
Artifacts/environment: /private/tmp/prosaic-coordination-final-artifacts-20261020
and /private/tmp/prosaic-coordination-final-env. Verification ledger additions
follow the builds; audited package payloads remain identical. Initial artifacts,
source study, failed probes and earlier sandbox evidence remain immutable.
Private evidence destination is the agent-quality reports directory under
bounded-coordination-evidence-20261020, with a separately verified tar/manifest;
the private preservation receipt records hashes and counts.

## Decisions and retained boundaries

- Keep a known failure visible when its peer is unfinished; usage stays unknown.
  Cost: status precedence does not itself list all diagnostic causes.
- Export ordered statuses rather than worker IDs; the private plan retains
  correlation. Cost: applications use plan order for per-worker association.
- Distinguish recorder intent, budget admission and actual delivery. Preserve
  unresolved usage and reservations; failed/incomplete fault outcomes are valid.
  Cost: conservative unresolved capacity, never an automatic refund/retry.
- Accept intact hardlinked evidence when receipts/digests validate; no bypass
  was demonstrated. Cost: protect storage from alias mutation independently.
- SDK receipt permissions belong to Harness/host storage; strict Lab sidecar
  checks and private enclosing roots remain required. Cost: weak deployment
  directory protection can expose SDK data; no blanket per-file claim.
- Exclude malicious trusted-host rewriting; hashes detect corruption rather
  than authenticate a host. Cost: applications must authenticate/protect state.
- Retain the reviewed current behavior for launch/receipt interruptions,
  foreign/duplicate assignments, unknown/missing peers, failure precedence,
  shared counters/deadlines and child1msfloor, cooperative cancellation/late
  outcomes, intent/admission distinction, actual overlap, receipt-only network
  denial, malformed/unsafe sidecars, safe summaries, installed packaging,
  synthetic/live separation and separate full qualification. Cost: finite
  offline coverage cannot certify every schedule, provider or deployment.

The full review's19considered-and-declined items, three implementation rulings,
watched failures and completion records are preserved in the private execution
ledger/review package. No other actionable findings or deferred minors remain.

Cumulative ceilings1558requests/637tools/1976623tokens; charged1509/610/1835168.
All39canonical ledgers and nine historical unknown reservations are preserved.
No new live allowance or inference. Memory/correction remain experimental.
