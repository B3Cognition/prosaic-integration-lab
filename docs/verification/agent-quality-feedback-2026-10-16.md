# Corrective feedback follow-up — 2026-10-16

Status: partial fix; full20sample study completed and audited. Smaller9/10,
larger10/10,19/20overall. Missing-evidence correction held in the full run;
one critic failure persists. Do not claim the smaller model fully fixed.

## Diagnosis and changes

Prior public-checks receipts proved feedback reached both failed retries. The
missing-fact answer repeated wrongDecision; the critic repeated approvedtrue/
issuesempty despite all three draft-field mismatches in requiredReview feedback.
There was no tool/schema/feedback-delivery failure. Hypothesis: reduce nested
feedback and competing retry instructions, then test the original failures.

Consumer feedback.2 replaces full assessment JSON nested inside a feedback string
with a compact target plus exact mismatched fields and missingFacts/draftIssues.
Targets derive only from the public task and current-attempt fetched records.
Missing-current-record feedback is target-free. Every attempt still requires a
real lookup; host validators accept only model-produced valid output. No private
expected answer enters feedback. Public schemas, scorer, suite, tools, SDK train,
model settings and case8request/4tool/16384token/300slimits remain unchanged.

Live diagnostics reports/quality-live-20261016-feedback-probes:
- missing-01 passes:4requests/2tools/4427tokens. The previously failing retry now corrects its decision.
- repair-01 fails:4/2/4665; compact targetfalse/all3issues still yields true/empty.
- correct-draft control passes:4/2/4665; no forced disapproval.
Known totals12/6/13757. Control is separately labeled, not a benchmark case pass.

Ruling: retain compact reviewer feedback, but isolate critic correction from the
long original critic context. Consumer feedback.3 adds a native graph branch:
provisional critic(max1) -> public critic-check -> author on pass, otherwise a
short review-corrector(max1) -> public review validator -> author. The author
receives the accepted corrected review when present. Ordinary reviewer retains
two attempts; repair path still uses at most four invocations including two
author attempts. No host replacement of model output or profile escalation.

extract counts only checked accepted reviews for criticDetected. That metric now
includes the correction pipeline, not provisional critic first-pass accuracy.
A rejected correction blocks author; its provisional review is not counted as
accepted. New artifact content and callback source are bound into provenance.
Only proseDigest/workflowDigest differ from the preceding public-checks identity.

Live diagnostics reports/quality-live-20261016-feedback-stage-probes:
- repair-01 still fails:4requests/2tools/3926tokens. Both provisional critic and
  dedicated corrector return approvedtrue/issuesempty. The corrector receipt
  contains targetapprovedfalse and decision/facts/citations issues; no author runs.
- correct-draft control passes:4/2/4744; it correctly bypasses correction.
Known totals8/4/8670. The context-isolation hypothesis did not resolve this case.
Do not add another unmeasured prompt patch or claim a model capability fix.

## Source, artifact and diagnostic verification

Two compact-target dispatch regressions failed before implementation. Focused40
tests passed. Review found fields incorrectly always listed both approved/issues;
a partial-review regression failed, then passed after exact field comparison.
feedback.2 full source1055passed124.08s; earlier1054passed125.34s retained as history.

Dedicated-step routing regression first failed with same-agent critic retries.
After native graph implementation44focused tests passed. Added negative coverage
verifies stubborn wrong correction remains blocked with no author invocation.
Final fresh full source1057passed126.82s, one existing Starlette warning:
 /Users/michalbachorik/work/prosaics/prosaic-integration-lab/.venv-latest/bin/python -m pytest -q
Fresh routing review found no blocking issue. Existing fault probes cover ordinary
workflow recovery; no separate interrupted repair-branch resume qualification is
claimed. No service/database or hosted-provider requalification or release.

Immutable environments preserved:
- feedback.2/private/tmp/prosaic-feedback-env,220installed payload files/17source
  resource files audited; smoke/pipcheck and installed fixtures10/10/recovery3/3.
- feedback.3/private/tmp/prosaic-corrector-env,221payload files/18source files audited;
  smoke/pipcheck and installed fixtures10/10/recovery3/3.

SDK manifest unchanged027f857a2fc344b87201d3c4da4a850730f0fc435e6fcddb1384bf03229fef0e:
Core0.4.1,Runtime0.9.3+finalize.4,Harness0.8.2,both recorders0.3.0. Defaults unchanged.
feedback.1 was an intermediate offline build, never live-dispatched; archives kept.

Candidate hashes:
- feedback.2 wheela50d2d35d8a9d8ffb3cd9c3a044e54cd29dfb6ccb35489b3617ca4ae6522f521
- feedback.2 sdist52c44632a0d8856cda7116cef5af1d6f64fcdfc27c185574486d387663a31de7
- feedback.3 wheel74fc6fca4729ec3be771e8c751bc0c22cb0fad57e23999933759518cd950bd99
- feedback.3 sdistbc7ed5226964da4d63bcc0d8139bd66d41f30fd4bf45969e6ced3a2af3c7da97

Offline audit checked all5diagnostic receipt/evidence digests, exact usage, tool
counts, public request identity, scores and control outcomes. Safe output
/tmp/prosaic-feedback-probe-audit.json. Both candidate qualification records,
all three archive pairs, manifest and scripts preserved in dist/quality-feedback.
Historic reports, immutable allowances and unrelated work remain untouched.

## Prepared full comparison and allowance

All17ledgers retain669requests/202tools/640727reported tokens;4prior unknown
reservations fully charged. Current approved757/246/983040 leaves88/44/342313.
User explicitly approved8requests/4tools to765/250/983040. Installed preflight
passed candidate/profile/accounting/catalogue checks and reservation proof, then
session21989 completed the fresh20sample study. All prior ledgers remain preserved.

Prepared output reports/quality-live-20261016-feedback,10cases x1rep x2profiles,
unchanged case limits,10800sbatch; proposed residual96/48/342313. Reservation proof
checks the actual native graph is acyclic, bounds every agent attempt and per-
invocation request/tool cap, and simulates uniform8request/4tool reservations at
each scheduled sample. Ordinary maximum4requests/2tools; repair8/4. Full worst-
case peak96/48/327680, not a uniform20x8/4 overestimate. No caps were lowered.

After explicit approval, run installed:
 /private/tmp/prosaic-corrector-env/bin/python -I /private/tmp/prosaic-feedback-study.py .
 /private/tmp/prosaic-corrector-env/bin/python -I -m lab_runner.agent_quality --live --repetitions 1 --config <absolute-output>/config.json --output <absolute-output>
Then/private/tmp/prosaic-feedback-final-audit.py verifies all20verdicts/digests/tool
joins, all18ledger totals and provider/socket-denied byte-identical replay. Never
reset/reprice old unknowns or retry a new uncertain request automatically.

Remaining limitation is an observed smaller-model refusal to follow a correct
critic target even in the short dedicated context. Any future routing/decoding/
model change must be explicit and separately measured, not called a reasoning fix.

## Completed full study and final audit

reports/quality-live-20261016-feedback/summary.json reports baselineComplete true,
usageComplete true,20/20executed,19passed/1failed. CLIexit1 reflects the known task
failure, not an incomplete benchmark. No extra live retries or diagnostics after
the scheduled run.

- Smaller9/10(previous8/10), ordinary8/8, first-pass7/8. Accepted-review detection
  and strict corrected-draft success1/2.30requests/15tools/34049tokens, zero schema
  repairs,4semantic correction attempts across failed/successful workflows.
- Larger10/10, ordinary first-pass8/8, review/draft2/2;24requests/12tools/32749tokens,
  zero schema repairs or semantic correction attempts.

Combined54requests/27tools/66798reported tokens. Measured sample time sum1648.63s,
maximum260.13s under300s. All18ledgers retain723requests/229tools/707525tokens,
leaving42/21/275515 under approved765/250/983040. All4prior unknown reservations
remain fully charged; no new unknown usage or exceeded ceilings.

Live correction evidence:
- missing-01 initially returned wrongDecision, then the compact target retry
  returned a correct answer. The targeted diagnostic and full benchmark both pass.
- repair-02 initially listed only decision as a critic issue. The dedicated
  correction returned decision/facts/citations. Its author then initially made
  wrongDecision and corrected it after compact feedback. Final task passes.
- repair-01 still returns approvedtrue/issuesempty from both provisional critic
  and dedicated correction, despite targetfalse/all3issues in correction arguments.
  Both native invocations exit0 with valid JSON. The validator blocks attempt_limit
  before author; scorer reports invalidEvidence because no accepted final answer
  exists. This is not a transport, schema or feedback-delivery failure.

Final offline audit rescored all20verdicts, checked evidence/receipt digests,
per-sample accounting, tool/journal joins, identity bindings and all18ledger totals.
Provider execution and socket creation were forbidden during replay; summary,
allowance and all20canonical evidence files were byte-identical. Safe proof
/tmp/prosaic-feedback-final-audit.json and preserved copy in dist/quality-feedback.

The comparison measures validated workflows with different prose/workflow
identities. One repetition does not establish a population success rate or an
unaided model capability gain. Native execution, schemas, scorer, models and
settings stayed fixed. Candidate remains unpublished/unmerged, with unrelated
work and all historic evidence preserved. Underlying critic behavior remains
unfinished; the implemented changes improve corrections and keep failures closed.
