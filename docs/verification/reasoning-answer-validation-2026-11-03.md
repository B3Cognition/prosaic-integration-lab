# Reasoning answer-validation candidate — 2026-11-03

Status: historical unreleased constructive-CRT candidate C2; the 72-call Qwen/Gemma study
completed on 2026-11-04. Qwen CRT improved; Gemma wrapping improved but its usable
answer rate regressed under the fixed output cap.

The source agents were subsequently shortened for a separate
[compact candidate C3 study](reasoning-prompt-compaction-2026-11-04.md).
The observations and body hash below describe C2, not the current source body.

## Scope

The maintainer requested addressing the repeated Qwen CRT error and Gemma JSON
fences through the blueprint prompts, then rerunning the comparison. All seven
effort-agent bodies add condition checking/correction, a constructive Chinese
Remainder Theorem procedure with modular-inverse/final-remainder checks, and
positive first/last-character JSON boundaries.
No expected answer, native reasoning prohibition, extra tool, API response-format
setting, Python implementation, SDK pin or published artifact is changed.

## Offline verification

On macOS ARM64 / Python 3.12, `.venv/bin/python -m pytest -q` passed **2,077**
tests in 625.86 seconds, with one existing Starlette deprecation warning. The
reasoning environment passed **31** tests using
`python -m pytest tests/reasoning_acceptance -q` in 7.53 seconds.
The normal isolated `python -m build` produced the private candidate wheel/sdist.
All fourteen baseline/candidate agents match their recorded sources; candidate
wheel Python payloads equal the published 0.9.3 wheel's payloads. Its metadata
still says 0.9.3; it is not a new public release. The constructive revision also
passed all **31** reasoning acceptance tests in 7.72 seconds and the final full
source suite: **2,077** passed in 591.08 seconds, with the same existing warning.

An initial source-suite attempt used the reasoning SDK environment and was
interrupted after 53 failures, 37 errors and 1,952 passes. The source environment
was restored to `dependencies/releases.json` (Runtime 0.9.8), with locked
third-party dependencies and no installed Lab wheel. Stale optimized/orphan
Runtime bytecode was retained separately and removed from that private environment;
installed SDK source was untouched. The five-wheel audit and full rerun passed.
The reasoning lane uses a separate fresh environment with Runtime 0.9.12.
An initial `--no-isolation` build lacked setuptools; the normal isolated build
succeeded. These are environment repairs, not weakened tests or source fixes.

## First candidate: stopped comparison

The first candidate compared published 0.9.3 prose with generic condition and
remainder checks plus JSON boundaries, using one common fresh
installed 0.9.3 runner and the verified reasoning SDK train. Six unchanged
synthetic questions, three runs, two versions and two models bound the batch to
**72** distinct inference requests. These are the same regression questions
already examined during prompt development, not held-out validation.

Qwen `ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ` uses native xhigh and thinking on.
Gemma `gemma-4-31B-it-oQ4e-mtp` uses medium, its one binary thinking-on setting.
The endpoint identifies Gemma 4 rather than a separate Gemma 4.1 identity.
Temperature zero, nonstreaming, no tools, one provider request, output cap 4,096
and a uniform 900-second deadline apply to both versions. Question order uses
recorded seeds; prompt order alternates inside adjacent matched pairs. Each model
has a serial worker; the separate endpoints run concurrently.

The complete fresh allowance is reserved before dispatch. No retries, fallback,
prompt tuning, model setting, template or cache changes are performed. Prior
study evidence and all consumed/unknown allowances remain untouched. Witnesses
check outgoing controls, native activation markers and generation prompt counts.
Only safe final integers, grades and usage are retained; credentials, private
URLs, arbitrary responses and generated reasoning are excluded from reports.

The batch stopped after **32** distinct attempts and **31** responses. Gemma
became unreachable after fifteen responses, and its sixteenth request reached
the 900-second deadline. Both workers stopped with cleanup verified. All prior
and frozen evidence hashes were unchanged. The original 72-unit reservation
remains fully retained with one unknown; it is never reset or reused.

Generic checking did **not** fix Qwen CRT: both observed candidate trials and
both baseline trials returned 654 instead of 423. Qwen knapsack improved in two
pairs, while digit counting capped in both prompts. In this partial prefix,
Gemma had four candidate caps versus one baseline cap and one unavailable
baseline response. No correct integer failed strict JSON in either Gemma prefix;
this incomplete sample does not establish a formatting fix. Forty planned slots
were never attempted and are not observations of the later candidate.

## Constructive CRT revision and gate

The second candidate supplies the constructive CRT formula and verifies each
modular inverse and final remainder. It contains no numeric answer or worked
solution. All fourteen baseline/candidate agents are frozen, and candidate wheel
Python payloads still match the public 0.9.3 wheel. The same audited installed
runner and reasoning SDK environment execute both versions.

A separate immutable shared allowance caps this revision at **72** inference
calls: a six-call Qwen CRT gate, 30 remaining Qwen slots, and 36 Gemma slots.
Each disjoint stage reserves its whole batch before dispatch. The gate's six
observations are part of the 72, not additional duplicate trials. Only a gate
with three correct, strict-JSON, normally completed candidate answers permits
the broader stages. The unavailable first-candidate request is never retried.

The gate **passed**: candidate 423 was correct and strict JSON in **3/3** runs;
the paired baseline returned incorrect 654 in **3/3**. Reasoning tokens were
593 per candidate response versus 396 per baseline response. Native controls,
rendered activation markers and generation prompt counts passed all six checks;
cleanup and frozen/prior hashes were verified. Six known units were consumed.

## Completed Qwen comparison

All **36** Qwen requests returned measured responses, with full native-control,
rendered-prompt and generation prompt-token checks. Correct and directly usable
strict-JSON results improved from **9/18 to 12/18**, entirely from the original
CRT question. The five other questions remained **9/15** for both prompts.
Each prompt had three capped digit-counting outputs. Strict JSON was 15/18 in
both, including wrong integers; no mathematically correct Qwen answer failed
strict formatting.

| Question | Baseline correct | Candidate correct | Mean reasoning tokens, baseline → candidate |
| --- | ---: | ---: | ---: |
| Original CRT | 0/3 | 3/3 | 396 → 593 |
| Additional CRT | 3/3 | 3/3 | 297 → 324 |
| Grid paths | 3/3 | 3/3 | 425 → 435 |
| Knapsack | 0/3 | 0/3 | 737 → 774 |
| Distinct digits | 0/3 | 0/3 | 4,096 → 4,096 (capped) |
| Divisibility | 3/3 | 3/3 | 412 → 430 |

The new knapsack answer was 36 instead of the baseline's 38; both are wrong
(expected 35). The first candidate's incidental knapsack gain did not carry
over to the constructive revision. Reported reasoning tokens averaged 1,060.5
versus 1,108.67 across all attempts, with cap censoring; the CRT target alone
used about 50% more reasoning tokens. These are task-dependent costs, not a
general monotonic effort claim.

Both Qwen stages exited successfully, owned cleanup passed, and all sealed
source/prior evidence hashes remained unchanged. At the Qwen checkpoint the new
shared allowance had 36 known units retained, 36 remaining and zero unknowns.
The subsequent Gemma stage consumed the remaining 36. The earlier candidate's
separate 72-unit reservation and its unknown flag remain unchanged.

The final shared agent-body SHA256 is
`e9b2062005bcdb0dffd5e937997543bf625542db507e884a60d1ed526a60e40b`.
The safe Qwen analysis SHA256 is
`926c8825b69186b14134e17be585d0728b25712c6548070fc1bd266f1d6a4be4`.
Private receipts retain exact paired observations, hashes and the failed first
candidate; they contain no generated reasoning or arbitrary response text.

## Gemma continuation completed — 2026-11-04

The endpoint returned after the November 3 outage. A read-only check advertised
the same model ID. Both variants' native thinking markers were rechecked before
inference, and the baseline rendered prompt matched its earlier hash. The
remaining **36** requests completed with **36** received responses, no transport
failures, no retries and no changes to the frozen prompts, SDKs or limits.

| Metric | Published 0.9.3 | Candidate |
| --- | ---: | ---: |
| Correct integer returns | 12/18 | 9/18 |
| Correct integers failing strict JSON | 2 | 0 |
| Strict JSON among normally completed responses | 10/12 | 9/9 |
| Complete, correct, strict JSON across all attempts | 10/18 | 9/18 |
| Capped outputs | 6 | 9 |
| Wrong admitted integers | 0 | 0 |

Both fenced baseline answers occurred on the additional CRT question. Each
paired candidate returned the correct integer 13 as bare JSON. That is an
observed recovery of **2/2** formatting failures. However, two path-counting
candidate responses and one divisibility candidate response capped where their
paired baselines returned correct strict JSON. The extra caps outweighed the
formatting gains. The literal wrapping improvement therefore does not establish
an overall Gemma reliability fix at the 4,096-token limit.

| Question | Baseline correct | Candidate correct | Mean reasoning tokens, baseline → candidate |
| --- | ---: | ---: | ---: |
| Original CRT | 3/3 | 3/3 | 2,035 → 1,624.33 |
| Additional CRT | 3/3 | 3/3 | 1,628.67 → 2,833.33 |
| Grid paths | 3/3 | 1/3 | 3,363.33 → 3,724.67 |
| Knapsack | 0/3 | 0/3 | 4,093 → 4,092.67 (capped) |
| Distinct digits | 0/3 | 0/3 | 4,093 → 4,092.67 (capped) |
| Divisibility | 3/3 | 2/3 | 2,135.67 → 3,739.67 |

Mean reported reasoning usage rose from 2,891.44 to 3,351.22 tokens, about 15.9%.
The effect is task-dependent: the original CRT used about 20% fewer reasoning
tokens, while the additional CRT and divisibility used about 74–75% more. Counts
at the cap are censored, so they do not reveal the full desired reasoning length.
All admitted Gemma integers were correct; missing final answers remain ungraded
rather than being labelled demonstrated arithmetic errors.

The completed combined study has **72** attempts, **72** responses and **72**
native-control/rendered-marker/prompt-count checks. All three stage workers exited
successfully with owned cleanup verified. The shared allowance now retains
72 known units, with zero remaining and zero unknowns. All earlier evidence and
unknown reservations remain unchanged; no prior request was retried.

The complete safe analysis SHA256 is
`ef6e818aaf28483fb81c0ad35214905fca87ec5dc0df670cb805fdde2c293774`.
The earlier Qwen-only snapshot remains preserved. The Gemma stage ran after
endpoint restoration on November 4; Qwen ran on November 3. Each model has its
own contemporaneous baseline/candidate pairs, but cross-model timing or server
state is not controlled. No prompt was tuned during either model's stage.

These are adaptive prompt-development results on previously evaluated synthetic
questions. Temperature-zero repetitions are nested within question; the CRT gate
is one selected question, not three independent tasks or held-out validation.
Prompt checks remain instructions rather than enforced mathematical validation.
