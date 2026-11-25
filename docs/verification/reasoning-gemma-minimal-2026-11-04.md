# Gemma-specific minimal prompt — 2026-11-04

Status: local, unreleased candidate C5; the fresh 36-request Gemma comparison is complete.
All twelve normally completed candidate answers were correct strict JSON;
usable answers improved versus fresh 0.9.3, while caps matched that baseline.
All seven shared Qwen effort agents remain byte-for-byte unchanged from compact
C3. No new Qwen inference is performed.

## Scope and frozen protocol

The maintainer requested keeping the compact Qwen prompt while trying a simpler
Gemma-specific prompt that preserves strict JSON, then rerunning Gemma. The new
`subagents/gemma-medium.md` contains the unchanged task, one integer `answer`
field, the exact positive first-`{`/last-`}` final-response rule and the existing
tool prohibition. It also preserves C3's exact explicit no-fences/commentary/
extra-fields prohibition, removing only the CRT procedure. The body has 69 words
versus shared C3's 95. For the unchanged original CRT task, native rendered input
falls from 192 to 111 tokens; public 0.9.3 uses 95 tokens.
Read-only model tokenization confirms the thinking activation marker for all
four prompts (baseline, C3, stopped C4 and C5). The new body SHA256 is
`cf47f8f3f4152b52832f9872f66b83fca41053d01b173df46356d5120b8d9aaa`.

## Positive-only attempt stopped

C4 first tried only positive JSON instructions, removing the explicit no-fences
line as well as the CRT procedure. Its 62-word body rendered to 100 tokens, but
all three normally completed candidate answers were correct integers inside
fences. The attempt stopped between requests after **16** known responses, with
cleanup verified and no transport failure or unknown dispatch. Its eight
candidate attempts yielded zero usable correct JSON, three correct-but-fenced
answers and five caps. The paired eight baselines yielded four usable correct
JSON answers, one correct-but-fenced answer and three caps. This is an incomplete
failed prefix, not a full comparison.

The old allowance remains 16 known request units retained, 20 unused and zero
unknown. Its unused slots are not reused. The independently frozen C5 revision
restores exactly the no-fences line and otherwise matches C4. C5 uses a fresh
36-request allowance, so this follow-up uses at most **52** inference requests
including the stopped prefix. Qwen's shared prompts remain unchanged throughout.

## Final revision protocol

The default API-backed Gemma workflow now explicitly chooses this variant.
Shared effort agents, SDK pins, Python payloads and package version 0.9.3 are
unchanged. Runtime profiles and the Lab multi-effort live command do not perform
automatic model-based prompt selection. A Qwen workflow must explicitly select
the Qwen profile and its shared xhigh agent. This is a private blueprint/workflow
candidate, not a published 0.9.3 replacement.

One newly constructed serial worker compares fresh public 0.9.3 with C5 using
the same installed public Lab 0.9.3 / Runtime 0.9.12 environment. The six reused
regression questions, three temperature-zero trials, exact previous Gemma order
and alternating version order give **36** distinct requests. Only the question
block is substituted identically for five non-anchor tasks; two independent
exact oracles per question remain unchanged. Gold answers are not sent to models.

The approved server advertises `gemma-4-31B-it-oQ4e-mtp`, identifying Gemma 4
rather than separately verifying Gemma 4.1. Medium requests native
`enable_thinking: true`; it is one binary on control, not a distinct budget.
Both arms use 4,096 total output tokens, a 900-second deadline, nonstreaming,
no tools and one provider request per invocation. A fresh shared 36-call
allowance reserves the full batch atomically. No retries, fallback, allowance
resets or study changes to server, template or cache settings are performed.
Prior C3, C2, interrupted C1 and original repeated-study evidence are preserved.

All prompts and execution inputs were frozen before inference. Wire controls,
native thinking markers and generation prompt counts are witnessed. Retained
observations contain only safe final integers, grades, usage and hashes; no
credentials, private URLs, raw generated reasoning or arbitrary answers are
published. A private copy of the exact new file occupies the same medium-agent
slot as baseline to preserve metadata and execution equivalence.

## Completed comparison

All **36/36** requests returned responses, with no transport failure or retries.

| Metric | Fresh public 0.9.3 | Gemma-specific C5 |
| --- | ---: | ---: |
| Correct integer returns | 12/18 | 12/18 |
| Complete, correct strict JSON | 9/18 | 12/18 |
| Strict JSON among normally completed responses | 9/12 | 12/12 |
| Correct integers failing strict JSON | 3 | 0 |
| Capped outputs | 6 | 6 |
| Wrong admitted integers | 0 | 0 |
| Mean reported reasoning tokens | 2,848.56 | 2,836.5 |

All three baseline answers on the additional CRT question were correct but
fenced; all three paired candidate answers were complete, correct bare JSON.
Original CRT, grid paths and divisibility were correct strict JSON in all three
trials for both prompts. Knapsack and distinct-digit counting capped in all
three trials for both prompts. No new wrong integer was admitted.

| Question | Usable correct JSON, baseline → candidate | Mean reasoning tokens, baseline → candidate |
| --- | ---: | ---: |
| Original CRT | 3/3 → 3/3 | 2,004 → 2,041.67 |
| Additional CRT | 0/3 → 3/3 | 1,946.33 → 1,353.33 |
| Grid paths | 3/3 → 3/3 | 2,817 → 3,177 |
| Knapsack | 0/3 → 0/3 | 4,092.67 → 4,092.67 (capped) |
| Distinct digits | 0/3 → 0/3 | 4,092.33 → 4,093 (capped) |
| Divisibility | 3/3 → 3/3 | 2,139 → 2,261.33 |

The new Gemma variant had six caps versus historical shared C3's thirteen and
longer C2's nine, while preserving strict JSON on every completed response.
It matched the fresh baseline's six caps, so this is not evidence of better
completion than public 0.9.3. The practical paired gain is three recovered
formatting failures, without the extra caps observed in the earlier candidates.
Aggregate reported reasoning counts were nearly unchanged and censored; task
costs moved in both directions.

The analysis keeps correct integers, strict JSON conditional on normal completion,
usable correct strict JSON across all attempts, and capped outputs separate. Missing
final integers are ungraded rather than demonstrated arithmetic errors. Counts
at the output cap are censored; missing usage stays unknown. Earlier C2 and C3
are historical context, not simultaneous third arms. These are adaptively reused
questions, not held-out validation; repeats are nested within tasks.

## Final verification

Native wire controls, thinking activation markers and generation prompt-count
checks passed **36/36**. Owned worker, listener and temporary-state cleanup was
verified. The C5 allowance retains 36 known units, zero remaining and zero
unknown; C4 still retains 16 known units, 20 unused and zero unknown. Total live
inference in this follow-up was **52** requests, including the stopped prefix.
All frozen/source hashes and previous C4 → C3 → C2 → interrupted C1 → original
study evidence passed verification. Qwen's seven shared agents match their
previous tested hashes, with no new Qwen inference. Prior unknown reservations
remain unchanged.

The complete safe analysis SHA256 is
`0c324cdd17a1057b0d1d3f43418773134e26b51c896e4a8395bdaff4423f210a`;
the frozen input ledger SHA256 is
`2ba89452de0853d8e1745378ef2c097241ec336b4ce5720f3f215682f7fa0386`.
Private receipts preserve exact paired observations without raw generated
reasoning or arbitrary answer text. The experiment wheel freezes tested agent
and workflow bytes; documentation was updated afterward and is not asserted to
match that wheel's earlier README bytes.

## Offline checks

The private isolated wheel/sdist build passed. Its new Gemma agent, workflow and
all seven protected shared agents match source; Python payloads match public
0.9.3. C4's reasoning acceptance lane passed **31** tests in 6.38 seconds;
the C5 revision passed **31** in 8.62 seconds.
Initial restricted runs failed because the sandbox blocked fixture sockets and
process inspection; their logs are preserved. With required fixture permissions,
the C4 full source suite passed **2,077** tests in 584.35 seconds, with the existing
Starlette deprecation warning. Both five-wheel installed SDK audits passed.
C5's separate full source suite passed **2,077** tests in 579.27 seconds, with
the same existing warning. Its two five-wheel installed SDK audits also passed.
No product workaround, dependency
replacement or weakened assertion was introduced.

The [C3 qualification](reasoning-prompt-compaction-2026-11-04.md) preserves the
previous shared-prompt Gemma result: five usable answers and thirteen caps out
of eighteen. This experiment does not authorize a release.
