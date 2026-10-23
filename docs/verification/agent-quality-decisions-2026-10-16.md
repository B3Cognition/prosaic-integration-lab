# Decision and critic correction — 2026-10-16

Status: partial improvement; all20samples measured and audited across a preserved
19sample run and linked one-sample continuation. Smaller8/10, larger9/10;
requested semantic fixes remain incomplete.
The user requested fixing the smaller model's wrong decisions and missed draft
flaws, then rerunning. Do not claim completion until the new live results exist.

## Diagnosis and measured attempts

The previous complete native-call study passed6/10 on the smaller model.
conflict-02 and missing-01 repeatedly returned wrong decisions; both critics
missed a required decision flaw. Both final authors nevertheless returned correct
answers. No transport or schema failures explain these results.

Private comparison found that resolved revision conflicts were treated as absent
evidence, one available required fact was treated as complete evidence, and
critic approval tracked rollout approval instead of draft correctness.
All changes below are generic methods derived from the public task and schema;
no expected values, case-specific thresholds, scorer or schemas were changed.

Consumer0.5.0+decision.1 clarified evidence selection, completeness-first decisions,
all-condition evaluation, independent draft recomputation and field-by-field
issue mapping. Four original failures plus a correct-draft control were tested
separately, not merged into the benchmark:
- conflict-02 passed:2requests/1tool/1886tokens.
- missing-01 failed:4requests/2tools/3429tokens.
- repair-01 failed:4requests/2tools/3928tokens.
- repair-02 passed:4requests/2tools/4000tokens.
- correct-draft control passed:4requests/2tools/4060tokens; approved true, empty issues.
Total18requests/9tools/17303tokens; all usage known. This is2/4 corrected
failures plus a successful control, not a full benchmark success.

Consumer0.5.0+decision.2 added abstract completeness examples, symmetric draft
comparison examples and issues-before-approved output ordering. A focused
missing-01 retest still failed:4requests/2tools/3690tokens, known usage.
Its critic changes have not yet been live-tested.

A standalone evidence-first serialization probe incorrectly passed cwd=None
to the classic Runtime API. It raised TypeError before HTTP; an exact offline
reproduction with urllib networking blocked confirmed0HTTP attempts.
The diagnostic wrapper nevertheless settled the reservation unknown. That
immutable reservation remains fully charged at2requests/1tool/8192tokens.
It is not retried or repriced. All later inference stopped. No SDK defect is
claimed; this was an agent-authored probe admission mistake.

## Final prepared candidate

Consumer0.5.0+decision.3 additionally requests facts and citations before the
decision, so evidence is serialized before the decision string. Review JSON asks
for issues before approved. Fields, schemas and grader semantics remain identical.
The model may ignore output-order instructions. Live results below demonstrate
partial improvement only.

The five SDK wheels are unchanged from the last qualified study:
Runtime0.9.3+finalize.4, Core0.4.1, Harness0.8.2 and both recorders0.3.0.
Manifest027f857a2fc344b87201d3c4da4a850730f0fc435e6fcddb1384bf03229fef0e.
No Core, Runtime or Harness engine changes. Models,512-token output settings,
native envelope/finalization/json_mode controls and workflow budgets unchanged.
Only effective proseDigest changes from the previous study identity.

Candidate archives:
- wheel4c234dec7138600999dbe5cb3136c7a812696c125d167d9184a3a44c4ad8afd1
- sdistd28013eaa2eb4b4f029b51c8c68105b2febd318e854c035f49bdafcec1cbba66

Fresh final source suite1034passed, one existing Starlette warning,112.39s.
Installed fixture10/10 and recovery3/3 pass;16final-only payloads checked.
Five-wheel payload audit passes. Separate installed environment:
 /private/tmp/prosaic-semantic3-env.
No literal wording tests; existing payload/schema/provenance/scorer tests and
actual live reproductions are the meaningful checks for these prose changes.
The earlier source runs for intermediate wording also passed1034tests; the fresh
final run is authoritative. No service/database requalification or release claim.

## Budget gate and prepared rerun

All12prior ledgers retain548requests/142tools/498989tokens, including three
historic unknowns and the conservatively charged admission-error reservation.
The user explicitly approved40additional requests, raising cumulative ceilings
to600/240/983040. Preflight verified candidate identity, preserved reservations,
unchanged profile fingerprints and both local models before dispatch.

The fresh same20sample schedule is prepared in
reports/quality-live-20261016-decisions:10cases x1repetition x2profiles,
300-second cases,10800-second batch. Caps52/98/484051 were the exact residuals
at dispatch. The installed run(session82410) stopped normally with CLIexit1:
19/20executed, usageComplete true, baselineComplete false. That original report
remains a partial study; the linked continuation below completes the schedule.
All19settlements are known; no new unknown usage.

## Measured results and reservation headroom

Smaller model8/10(previous6/10); ordinary first-pass6/8, strict critic/draft1/2
(previous0/2). conflict-02 nowpasses after one semantic retry; repair-02 passes.
missing-01 still returns wrongDecision twice and exhausts its permitted attempts;
the scorer reports invalidEvidence because no accepted final answer exists.
repair-01 critic still emits approvedtrue/issuesempty despite draft errors;
its author produces the correct final answer, but strict repair grading fails.
All14smaller native invocations exit0; no schema repairs. These are reasoning
failures, not failed native calling. Both requested key orders were followed in
the persistent failing reviewer/critic attempts, so ordering alone is insufficient.

At the original stop, larger model9/9measured, including its first critic/draft
case; repair-02-p2-r1 had not been dispatched.
Original totals48requests/24tools/54215tokens;17/19passes. All13ledgers retained
596requests/166tools/553204tokens, with all4prior unknown reservations charged.
The final case requires8requests reserved before dispatch, but4remain under600.
Preflight checked remaining totals but missed this reservation headroom. No
ceiling was exceeded. The original report/allowance remain immutable.

Offline19sample rescore, receipt digests, tool/journal joins, per-sample settlement,
cumulative accounting and socket/provider-denied byte-identical replay all pass.
Audit script/private/tmp/prosaic-semantic3-final-audit.py, partial audit output
/tmp/prosaic-semantic3-partial-audit.json. A separately prepared one-sample
continuation/private/tmp/prosaic-semantic3-continuation.py retains the original
schedule, identity, cases, limits and profile; it uses a new allowance and writes
a linked combined report without overwriting the19sample report.

## Approved one-sample continuation and final audit

User explicitly approved4additional requests, raising the cumulative request
ceiling to604; tools240/tokens983040 unchanged. Continuation session41993 ran
only repair-02-p2-r1 with unchanged identity/profile/case limits. Separate ledger
reports/quality-live-20261016-decisions-continuation/allowance.json reserves8;
actual1request/0tools/1734tokens, known usage. No prior sample was rerun.

The critic invocation exited1 with provider_error_code incomplete_generation,
finish_reason length, completion_tokens512, HTTP200. It exhausted the unchanged
output cap before a complete artifact/tool call could be trusted. No lookup or
author execution occurred. This is an observed new failure relative to the prior
complete larger-model10/10; one repetition does not establish its frequency or
attribute it conclusively to prompt changes. No retry or output-cap change.

Linked combined summary at
reports/quality-live-20261016-decisions-continuation/summary.json:
baselineComplete true, usageComplete true,20/20executed,17/20passed.
Smaller8/10(previous6/10), larger9/10(previous10/10), both strict critic/draft1/2.
Combined49requests/24tools/55949reported tokens. All14ledgers retain
597requests/166tools/554938tokens; residual7/74/428102 under604/240/983040.
All4prior unknown reservations remain fully charged; no new unknowns or overruns.

Final offline audit rescored all20samples, checked receipt digests/tool-journal
joins/settlements and cumulative accounting, replayed the original report with
socket/provider execution forbidden, and rebuilt the linked combined summary
byte-identically. Original summary/allowance and all canonical evidence stayed
byte-identical. Final audit/private/tmp/prosaic-semantic3-final-audit.py and
/tmp/prosaic-semantic3-final-audit.json; copies preserved in dist/quality-decisions.
No code or model settings changed during continuation. No release or integration.

## Architecture discussion before further fixes

Three instruction variants leave the same missing-fact and critic failures.
Do not attempt a fourth prompt-only patch. Proposed consumer workflow change:
emit a typed intermediate evidence table with required/present/missing fact IDs,
selected revisions and each condition result; check internal consistency before
the public answer. Recompute a clean answer separately, then compare every draft
field explicitly to obtain critic issues. Inputs must derive solely from the
public task and fetched evidence, never expected answers or case-specific rules.
Preserve the present workflow as the baseline and qualify the changed workflow
separately; do not misrepresent an altered representation as prose-only evidence.
Discuss that architecture with the user before further implementation or inference.
