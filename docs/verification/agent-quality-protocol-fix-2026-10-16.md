# Native lookup and draft-correction instruction fix — 2026-10-16

The user requested fixing repeated tool rounds and failed draft corrections,
then rerunning the benchmark. Work remains in the existing isolated
`codex/agent-quality-benchmark` worktree. Earlier baselines and allowances are
preserved. No SDK engine, scorer, private expected answer, workflow graph,
model configuration or tool cap changed.

## Confirmed causes and intervention

Read-only inspection of the complete previous live baseline found all 26
`tool_round_limit` invocations requested `lookup_records` again after the
invocation's journal already contained all required records. Repair authors
received both the flawed draft and accepted critic artifact; there was no
missing-input binding. Seven intermediate answers rejected for `wrongFacts`
had correct decisions/citations but embedded numeric values in facts. Successful
answers used one lookup batch and factId-only facts.

Reviewer, critic and author prose now explicitly permits one batched lookup
per attempt and requires final JSON immediately after its result. Authors must
recompute and replace draft fields against evidence. Reviewer/author prose and
the public answer-schema description define facts as factId strings, excluding
numeric values and prose. These instructions expose the existing contract and
limits; no hidden answer-key values or field-level host feedback were added.
The scorer still rejects missing reads, wrong facts and incomplete workflows.

Only `proseDigest` and `schemaDigest` differ from the previous baseline's
identity. Removing the new schema description reproduces the earlier schema
exactly. Strict report comparison intentionally rejects these changed identities;
any before/after discussion is an explicitly identified instruction intervention,
not a claim that the two configurations are identical.

## Verification before inference

- Complete Lab suite: **1031 passed**, one existing Starlette warning, 98.69s.
- Isolated wheel and sdist built in `dist/quality-protocol/`; both installed
  smokes passed. All installed benchmark resources matched the source.
- Installed fixture baseline: **10/10** task passes, **3/3** recovery probes.
- Installed five-wheel SDK payload audit and `pip check` passed.
- Authenticated catalogue GET confirmed both approved models before launch.
- Fresh allowance absent before launch; every numerical limit reconciled with
  all four previous ledgers, retaining the three unknown reservations in full.

## Authorized live rerun

`reports/quality-live-20261016-protocol/config.json` schedules the same ten
cases × three repetitions × two profiles, with 300-second cases and a finite
10800-second batch window. It uses only residual ceilings of **186 requests /
183 native tool calls / 733089 reported tokens**. No earlier report or allowance
is reset. Raw receipts, model output and handler journals remain private.

The installed-wheel rerun is complete: **60/60 measured with known usage**,
`baselineComplete: true`, `usageComplete: true`. Sample elapsed time totals
2531.02 seconds (42.18 minutes); no case timed out. CLI exit 1 reflects the
remaining failed tasks, not incomplete measurement.

## Measured effect of the instruction intervention

| Larger-profile metric | Previous run | Instruction-fix rerun |
| --- | ---: | ---: |
| Task passes | 4/30 | 16/30 |
| First-pass ordinary cases | 4/24 | 11/24 |
| Seeded critic detections | 6/6 | 5/6 |
| Corrected-draft task passes | 0/6 | 5/6 |
| Failed invocations at tool round limit | 26 | 13 |
| Intermediate wrongFacts repairs | 7 | 0 |
| Irrelevant-record observations | 51 | 2 |
| Duplicate-record observations | 39 | 10 |
| Calls above case lower bound | 7 | 0 |
| Native tool calls | 43 | 34 |
| Provider requests | 86 | 69 |
| Reported tokens | 90125 | 80573 |
| Median elapsed seconds | 74.2389 | 66.8149 |
| p95 elapsed seconds | 137.1196 | 170.3415 |
| Maximum elapsed seconds | 160.0375 | 173.1017 |

Every author that received an accepted critic result completed a correct draft
in the rerun. The sixth critic stopped with `incomplete_generation`, so its
author never ran. Thirteen other workflows still requested another lookup
round and were blocked at the unchanged native cap. Instruction clarification
therefore improved the behavior but did **not eliminate** repeated tool requests.
Latency tail increased despite the lower median; this is not a universal
performance improvement claim.

The smaller profile remains **0/30**, with no native lookup dispatch. It made
60 requests and reported 47640 tokens; median case elapsed was 2.6809 seconds.
This instruction intervention did not resolve that profile's native tool-use
failure and does not establish inability to perform the underlying arithmetic.
The ten duplicate-record observations on the larger profile correspond to the
five required critic/author pairs; they are not all unnecessary work.

## Reconciliation and replay

The installed audit recomputed all sixty verdicts and evidence digests,
matched actual receipt counts to every known allowance settlement, rebuilt the
public report exactly and confirmed CLI output agrees. Repeating the saved
schedule with socket creation and provider dispatch forbidden yielded
byte-identical public summary, allowance and sixty canonical sample files.
No additional inference occurred during replay.

The rerun used **129 requests / 34 native tool calls / 128213 reported tokens**.
Across all five runs, conservative retained capacity is **423 requests / 91
tools / 378164 tokens**, including the full three earlier unknown reservations.
All original numerical ceilings remain respected. Residual balances are **57
requests / 149 tools / 604876 tokens**; balances are not actual billing figures
or permission to reset an allowance. Raw evidence remains private under
`reports/quality-live-20261016-protocol/`.

## Runtime continuation — explicitly authorized

Runtime keeps tools available after acquisition; its round cap rejects a second
request rather than making a final-answer-only turn. Native WorkflowFactory
also rejects acquisition bindings. A host-configured finalization phase is the
concrete proposed fix for the remaining repeated-round failure. See
`docs/superpowers/plans/2026-10-16-runtime-tool-finalization-proposal.md` for the
opt-in behavior, regressions, budget rules and pinned-wheel qualification plan.

The user explicitly authorized “Extend Runtime and qualify it.” Runtime work
is isolated from its unrelated main-checkout changes, based on qualified v0.9.3.
The opt-in implementation, pinned candidate qualification and residual-budget
study are recorded in `agent-quality-runtime-finalization-2026-10-16.md`.
This document remains the immutable instruction-only study record; its original
released SDK environment and private evidence are preserved.
