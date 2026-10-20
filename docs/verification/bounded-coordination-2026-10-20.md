# Bounded coordination qualification

Status: local qualification in progress; no live run, push, merge or release.
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

Full source, installed artifacts, clean public wheel/rebuilt-sdist consumption,
payload verification and fresh whole-branch review remain required before
claiming this milestone qualified. Later exact-head Linux/platform CI remains
a merge/release gate. Earlier sandbox artifacts/evidence remain immutable.

Cumulative ceilings1558requests/637tools/1976623tokens; charged1509/610/1835168.
All39canonical ledgers and nine historical unknown reservations are preserved.
No new live allowance or inference. Memory/correction remain experimental.
