# Public evidence and draft checks — 2026-10-16

Status: implemented, qualified and live rerun complete; all20samples measured and
audited. Smaller8/10, larger10/10. Two smaller-model failures remain unresolved.
User explicitly approved the757request/246tool ceiling. User authorized the
architecture and native implementation after three prompt variants left two
smaller-model failures. The validators reject those bad outputs; the model still
fails to correct them within its permitted attempts. This is not a complete
semantic fix or evidence of unaided model improvement.

## Consumer change

lab_runner/quality/checks.py parses the supported closed public task grammar;
fact names, authority, operators and numeric thresholds come from public text.
It resolves current authoritative revisions from the public index, distinguishes
an unfetched indexed record from a truly absent fact, and builds required/present/
missing fact lists, condition results and a clean answer from fetched values.
Record instructions are ignored. Unsupported grammar, ties, identity mismatch
and malformed numeric evidence fail closed.

execution.py replaces private-answer validation with public-derived validators
on reviewer/author answers and critic reviews. It checks all draft fields and
requires approved to agree with the complete issue set. Wrong outputs receive
bounded structured publicCheck feedback within the existing two-attempt limit;
accepted output always comes from a model receipt, never host replacement.
Current-attempt records are isolated, and persisted lookup journals support saved
receipt validation after reconstruction. Private expected answers remain solely
in the unchanged scorer; a poisoned-answer-key regression proves acceptance is
independent. Correct-draft control prevents blindly forcing critic disapproval.

No Core/Runtime/Harness engine changes. Suite, public schemas, scorer, tools and
model settings unchanged. Only proseDigest and workflowDigest differ from the
previous decision study. Formal comparison rejects mixed workflow identities;
describe this as a new validated-workflow track, not raw-model reasoning gains.
The grammar is benchmark-specific and does not interpret arbitrary prose policies.

## Verification

Initial10regressions failed, including private-answer-key dependence. First
focused31tests passed. Expanded execution/recovery and review tests caught two
test-author assumptions: FileRunStore IDs require32lowercasehex characters;
validator versions are separate from graph fingerprint and resume rejects their
changes with ValueError. Tests now exercise actual zero-dispatch recovery denial.

Fresh review found incomplete validator source binding and duplicate draft arrays
accepted as sets. Both were reproduced with failing tests and fixed. Digest now
binds checks.py plus execution.py, and duplicate facts/citation pairs are flaws.
Reviewer recheck found no further concrete supported-path issue. The interim full
run had1050pass/1failed (the corrected fingerprint test); final fresh command:
 /Users/michalbachorik/work/prosaics/prosaic-integration-lab/.venv-latest/bin/python -m pytest -q
Result1051passed, one existing Starlette warning,120.01s.11check-specific tests
pass. No service/database/hosted-provider requalification or release claimed.

Immutable consumer0.5.0+checks.1 built in
 /private/tmp/prosaic-checks-build/prosaic_integration_lab-0.5.0
Fresh installed environment/private/tmp/prosaic-checks-env; hash-locked dependencies,
pipcheck clean. Unchanged SDK manifest
027f857a2fc344b87201d3c4da4a850730f0fc435e6fcddb1384bf03229fef0e:
Core0.4.1,Runtime0.9.3+finalize.4,Harness0.8.2,both recorders0.3.0.

Archives preserved dist/quality-public-checks:
- wheel7547980c03a1ce882ae11d9c0922ad423d4ed028ac9aede400761032c88e5a8c
- sdist04722ddeaa8ed358b97128220c82656543ce3d9668d465514ac97d7ccde68fcf

Installed payload audit verified220files across all six wheels.17benchmark code/
resource files match the source, except intentionally candidate-pinned SDK
provenance. Installed smoke passes, fixture10/10 and recovery3/3 pass. Installed
missing-decision retry4requests/2tools, critic retry6/3, correct-draft control4/2
all pass using credential-free synthetic providers; none counts as live inference.
Qualification/private/tmp/prosaic-checks-qualification.json. Packaging/verification
scripts, manifest and outputs preserved beside archives. Documentation status
updates are subsequent to the immutable artifact; runtime payload is unchanged.

## Prepared live rerun and explicit budget gate

At dispatch, all14prior ledgers retained597requests/166tools/554938reported tokens,
including4fullycharged unknown reservations. The then-approved604/240/983040 left
7/74/428102. A full20sample schedule could require160requests/80tools and327680tokens.
User explicitly approved153requests/6tools to cumulative757/246/983040. Installed
preflight passed all identity/hash/profile/catalogue/accounting checks and full
20sample worst-case reservation headroom. Live session94206 completed; no old
allowance was reset and no prior sample repeated.

Prepared output reports/quality-live-20261016-public-checks,10cases x1rep x2profiles;
caps160/80/428102,300s cases,10800s batch. New preflight explicitly verifies all20
worst-case reservations fit, preserved totals, wheel hash, unchanged profiles,
unchanged suite/schema/scorer/SDK identity and catalogue readiness before dispatch.
Approved run commands:
 /private/tmp/prosaic-checks-env/bin/python -I /private/tmp/prosaic-checks-preflight.py .
 /private/tmp/prosaic-checks-env/bin/python -I -m lab_runner.agent_quality --live --repetitions 1 --config <absolute-output>/config.json --output <absolute-output>
Final audit/private/tmp/prosaic-checks-final-audit.py verified all20receipt verdicts/
counts/journal joins, all15ledger totals and provider/socket-denied byte-identical replay.
Never reset old ledgers or retry a new unknown automatically. No global model
settings, token cap, releases, integration or unrelated changes authorized here.

## Completed live results and limits

Fresh10cases x1repetition x2profiles: baselineComplete true, usageComplete true,
20/20executed,18/20task passes. The CLI exit1 reflects the two known task failures,
not an incomplete measurement. No extra live diagnostics or retries after the run.

- Smaller8/10, ordinary first-pass7/8, critic detections and strict corrected-draft
  successes1/2.28requests/14tools/31678tokens; zero schema repairs,3semantic retries.
- Larger10/10, ordinary first-pass8/8, critic/draft2/2.24requests/12tools/31684tokens;
  zero schema repairs or semantic retries.

Combined52requests/26tools/63362tokens; measured sample time sum1662.37s, maximum
267.02s under300s. All15ledgers retain649requests/192tools/618300tokens, leaving
108/54/364740 under757/246/983040. All4historic unknown reservations remain charged;
no new unknowns or exceeded ceilings.

The new checks demonstrated a live correction in smaller repair-02: first review
listed only decision, then publicCheck requiredReview feedback caused the retry
to list decision/facts/citations before the author completed correctly. The
unchanged scorer alone only requires decision detection; the new validator now
enforces complete field comparison before accepting a review.

Two smaller failures persisted:
- missing-01: both model answers had wrongDecision. Feedback in the second receipt
  correctly showed one missing required fact and the public-derived answer, yet
  the model repeated the wrong decision. Blocked attempt_limit, scored invalidEvidence.
- repair-01: both critic outputs were approvedtrue/issuesempty. The second receipt
  contained requiredReview false with all three field issues, but the model ignored
  it. Blocked attempt_limit; author was not invoked. Scored invalidEvidence rather
  than the historical criticMissedError because no accepted final answer exists.

All smaller native invocations returned exit0; these failures are not missing
feedback delivery, malformed JSON or broken native calls. Guards now reject the
bad outputs instead of accepting an incorrect critic review. Smaller task success
remains8/10 versus decision.3; larger is10/10 versus the preceding9/10 study,
whose final case truncated. One repetition does not establish a durable model
quality gain or causally attribute that larger-model difference to this change.

Final audit rescored all20results and verified evidence digests, per-sample counts,
tool/journal joins, identity fields and cumulative reservations. Replay forbade
socket creation and execute_case; summary, allowance and20canonical evidence files
were byte-identical. Safe audit output/tmp/prosaic-checks-final-audit.json and copy
dist/quality-public-checks/prosaic-checks-final-audit.json. Complete public report
reports/quality-live-20261016-public-checks/summary.json. Exact candidate and source
work remain unpublished/unmerged; unrelated work and all historic evidence preserved.
