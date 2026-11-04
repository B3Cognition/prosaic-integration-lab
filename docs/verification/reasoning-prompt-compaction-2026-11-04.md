# Compact reasoning prompts — 2026-11-04

Status: local, unreleased compact candidate C3; all 72 requests completed.
Qwen retained the CRT fix and improved knapsack. Gemma's completed answers kept
strict JSON, but capped outputs increased; the cap-reduction target failed.

## Change and experiment

The maintainer requested reducing Gemma's capped outputs while retaining the
JSON formatting improvement and Qwen's constructive CRT fix. All seven agent
bodies now use 95 words instead of the longer candidate C2's 169. They retain
the CRT formula, modular-inverse condition, positive zero handling, the exact
first-`{`/last-`}` final-response rule, one integer `answer` field and no tools.
The general condition-check/correction loop and duplicate inverse/remainder
checks are removed. No numeric answer, worked example, removed reasoning
prohibition, API response-format control, Python implementation or SDK pin is
added or changed.

For the unchanged original CRT task, read-only server tokenization measured
candidate input reduction from 298 to 218 tokens for Qwen (26.8%) and from 269
to 192 for Gemma (28.6%). The shared
body SHA256 is
`476e7976a77f971eb9a296ab1d27f5538f123e31ffd5822cd97dc477861a56f4`.

The same installed public Lab 0.9.3 runner and Runtime 0.9.12 execute baseline
and compact prompts. The baseline comes from the public 0.9.3 wheel; candidate
copies match source and the private built wheel. Python payloads are unchanged.
Candidate metadata still says 0.9.3; these bytes are not a published release.

The bounded study reuses six previously evaluated questions and two independent
exact answer oracles per question, three temperature-zero repetitions, two
prompts and two models: at most 72 distinct requests. Gold answers are not sent
to the models. Prompt order alternates inside adjacent pairs; the same question
block is substituted identically for the five non-anchor tasks. This is adaptive
prompt development on reused regression questions, not held-out validation.
The repetitions are nested within questions, not independent task samples.

Qwen `ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ` uses native xhigh and thinking on.
Gemma `gemma-4-31B-it-oQ4e-mtp` uses medium, its binary thinking-on control.
The advertised Gemma ID identifies Gemma 4 rather than separately establishing
a Gemma 4.1 identity. Both prompts use 4,096 total output tokens, nonstreaming,
no tools, one provider request per invocation and a 900-second deadline.
Each model has a serial Runtime worker; independent endpoints may overlap.

A fresh shared allowance reserves disjoint batches: six Qwen CRT gate requests,
30 remaining Qwen requests and 36 Gemma requests. The gate's six are part of 72.
No retries, fallback, allowance resets or study changes to server, template or
cache settings are permitted. Prior evidence and unknown reservations remain
untouched. Outgoing native controls, rendered activation markers and generation
prompt counts are checked. Only safe final integers, grades, usage and hashes
are retained; no credentials, private URLs or generated reasoning are published.

The Qwen gate passed: all three compact answers returned 423 as complete strict
JSON, versus incorrect baseline 654 in all three. Reported reasoning tokens
were 456 per compact response, versus 396 for baseline and 593 for historical
C2. The historical C2 comparison is context, not a simultaneous third arm.

## Completed Qwen comparison

All 36 Qwen requests returned responses. Correct and directly usable strict
JSON increased from **9/18 to 15/18**, versus historical longer C2's 12/18.
The compact prompt retained the original CRT improvement in all three trials
and also corrected all three knapsack trials. Both prompts capped on all three
distinct-digit counting attempts; no integer was admitted for those outputs.
Strict JSON including wrong integers was 15/18 for both prompts.

| Question | Baseline correct | Compact correct | Mean reasoning tokens, baseline → compact |
| --- | ---: | ---: | ---: |
| Original CRT | 0/3 | 3/3 | 396 → 456 |
| Additional CRT | 3/3 | 3/3 | 297 → 358 |
| Grid paths | 3/3 | 3/3 | 425 → 436 |
| Knapsack | 0/3 | 3/3 | 737 → 907 |
| Distinct digits | 0/3 | 0/3 | 4,096 → 4,096 (capped) |
| Divisibility | 3/3 | 3/3 | 412 → 428 |

Baseline knapsack returned 38; compact returned the correct 35. Baseline had
six wrong admitted integers across CRT and knapsack, versus none for compact.
Reported reasoning tokens averaged 1,060.5 → 1,113.5 across all attempts,
including censored cap counts. The shorter input did not imply uniformly lower
reasoning cost. These are observed regression-task gains, not held-out accuracy.

## Completed Gemma comparison

All 36 Gemma requests returned responses, with native controls and rendered
prompt counts checked, no transport failure and owned cleanup verified.

| Metric | Fresh published 0.9.3 | Compact C3 |
| --- | ---: | ---: |
| Correct integer returns | 11/18 | 5/18 |
| Complete, correct strict JSON | 8/18 | 5/18 |
| Correct integers failing strict JSON | 3 | 0 |
| Strict JSON among normally completed responses | 8/11 | 5/5 |
| Capped outputs | 7 | 13 |
| Wrong admitted integers | 0 | 0 |

All three baseline answers on the additional CRT question were correct but
fenced. Only one paired compact answer completed as correct bare JSON; the
other two capped. Compact grid paths completed correctly once versus twice for
baseline. All three compact divisibility answers capped, while all three paired
baselines completed correctly. Knapsack and distinct-digit counting capped for
both prompts in all trials. Original CRT completed correctly for both prompts.
Thirteen compact outputs had no admitted final integer; they are ungraded,
not demonstrated wrong arithmetic answers.

Reported mean reasoning tokens rose from 2,976.5 to 3,593.56 (20.7%). Those
means are censored by the output cap. Historical longer C2 had nine caps and
nine usable correct JSON answers; C3 had thirteen and five. C2 is historical
context, not a simultaneous third arm. Shortening this input did not reduce
Gemma's cap failures and does not qualify as a Gemma reliability improvement.

## Final verification and limits

All **72/72** planned requests returned responses, with no transport failure,
retry or fallback. Native wire controls, rendered activation markers and full
generation prompt-count/control checks passed **72/72**. All three workers
exited successfully; owned listeners and temporary execution state were cleaned
up. The fresh allowance retains 72 known request units, zero remaining and zero
unknown reservations. Frozen/source hashes, the historical C2 evidence, the
interrupted first candidate and the original repeated comparison all remain
unchanged. No prior unknown reservation was reset or reused.

The report distinguishes strict JSON among completed outputs, correct integers,
complete correct strict JSON across all attempts, and capped outputs.
A missing final integer remains ungraded rather than a demonstrated arithmetic
error. Reasoning counts at the output limit are censored, and missing usage is
never replaced with zero. Do not infer a Gemma cap improvement from prompt size.

The safe complete analysis SHA256 is
`71b2007747afd2b95df58214aa36c9618e2c64db957ec7562cf44f7347754721`;
the frozen input ledger SHA256 is
`ddb4360c90d63dde9584264b7241a00660191afb86cc317ccc98d49f3f62933c`.
Private receipts preserve exact paired observations and hashes, without raw
generated reasoning or arbitrary response text. The private experiment wheel
freezes the tested agents and Python payloads; documentation was updated after
the study and is not asserted to match that wheel's earlier README bytes.

The [previous qualification](reasoning-answer-validation-2026-11-03.md) preserves
C2's full comparison, including Gemma's nine caps versus six for baseline and
the interrupted first candidate's unknown response. No publication is authorized
by this prompt experiment.

## Offline verification

On macOS ARM64 / Python 3.12, the ordinary pinned SDK environment passed
`.venv/bin/python -m pytest -q`: **2,077 passed** in 623.10 seconds, with the
existing Starlette deprecation warning. The separate pinned Runtime 0.9.12
environment passed the **31** reasoning acceptance tests in 7.12 seconds.
Both installed SDK families match all five of their verified wheel payloads.
The normal isolated build produced a private wheel and sdist. All fourteen
baseline/compact agent copies were verified before inference; the candidate's
Python payloads match the public 0.9.3 wheel. No SDK or package version changes
are part of this experiment.
