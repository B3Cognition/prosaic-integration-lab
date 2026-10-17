# Fresh balanced memory comparison — 2026-10-17

The authorized12-sample live comparison is complete and independently audited.
It does not establish a reliable reasoning benefit from memory for either model.
It identifies a provider-neutral context-planning gap worth addressing next.
No push, merge or release was performed.

## Frozen experiment

Three new synthetic cases × two unchanged model profiles × memory off/on.
The families are relevant current history, invalidated source history and a
missing current fact. Small two/three-row indexes were fixed before quotation,
separating this experiment from the previous16-row mandatory-context stress.
The corpus also contains irrelevant and foreign-tenant decoys. History and
trusted metadata were frozen before authoring current cases and private answers.
Cases, prompts, settings and quotations were not tuned or rerun after results.
Model/arm order alternates by case; this is a single trajectory per cell.

The installed candidate family is exactly the one in the
[offline qualification](tool-outcomes-recovery-2026-10-17.md): Runtime
`0.9.7+tools.1`, Harness `0.9.1+tools.1`, Lab `0.5.1+tools.1`; reviewed Lab
source`355f08cdde6d988b8fabe0a44560cb78b535b791`. Wheels and installed payloads
were re-audited in a fresh isolated environment. Both arms enable the qualified
bounded-recovery policy and typed evidence; counter assets, model settings and
serving configuration retain their previous qualified fingerprints.

All12 frozen plans were admitted and passed synthetic native qualification with
the actual counters, pure preflight and network-denied receipt replay. Recall
was retained for two smaller-model cases and one larger-model case. The larger
model's relevant recall was excluded by the full-trajectory budget; changed-source
history was excluded by scope/reference validation for both models. These
decisions were preserved unchanged in the live run.

Full reservations were48requests /24tools /98,304tokens, within the existing
58request /30tool headroom. Each case retained4requests /2tools /8,192tokens /
600seconds and512output tokens. No live development probes were added.

## Results

| Model | Memory off | Memory on | Recall-exposed on cases | Actual tokens off/on |
| --- | --- | --- | --- | --- |
| Smaller,7B | 0/3 | 1/3 | 2/3 | 7,310 /9,477 |
| Larger,27B | 3/3 | 3/3 | 1/3 | 8,541 /9,010 |

| Family | Smaller off/on | Larger off/on | Interpretation |
| --- | --- | --- | --- |
| Relevant history | Fail /Fail | Pass /Pass | Smaller decision error persists after feedback; larger had no recall in either input. |
| Invalidated source | Fail /Fail | Pass /Pass | History filtered out in both models. Smaller continuations refused by the planning domain. |
| Missing fact | Fail /Pass | Pass /Pass | Smaller score gain is confounded by continuation allowance; larger passes both, with recall only in the on arm. |

There are three both-passed pairs, two both-failed pairs, one enabled-only pair
and no disabled-only pairs. All six paired trajectories requested the same
record sets within their pair. Public requests were identical where recall was
excluded; differences in those pairs are not evidence of memory-content effects.

The smaller model's relevant-history pair fetched current records and initially
returned the correct fact/citation fields, but chose `insufficient` instead of
the required rejection. Both permitted attempts failed to correct the decision.
With memory, its final attempt also dropped an available fact and citation.
These are answer/feedback failures after successful tools, not tool-call errors.

The larger model passed every case on its first workflow attempt. Only its
missing-fact pair actually tests recall exposure; two no-recall pairs cannot
demonstrate memory efficacy. Neither its raw success rate nor the small number
of exposed pairs establishes a broader memory benefit.

## Why the smaller model's apparent gain is confounded

Three continuations were safely refused before another HTTP request because
their counted input exceeded the frozen per-proposal quotation ceiling:

| Smaller-model case | Counted input | Planned ceiling | Excess | Already paid + proposed input/output reservation |
| --- | --- | --- | --- | --- |
| Changed source, on | 1,307 | 1,280 | 27 | 3,029 |
| Changed source, off | 1,307 | 1,280 | 27 | 3,029 |
| Missing fact, off | 1,211 | 1,152 | 59 | 2,877 |

Each last-column value is below the unchanged8,192-token case ceiling. It is a
single-next-request reservation calculation, not a guarantee that every later
possible trajectory fits. The full original plans required7,424tokens for
changed-source cases and6,912 for missing/off, also below8,192. Safety held;
the fixed sub-allocations and canonical-response quotations were restrictive.

For missing/on, recall increased the quoted continuation ceiling to1,408.
Its actual input of1,368 was admitted and it returned a correct final answer.
Both arms fetched the same two records, including the observer record. Thus the
off arm never got its final decision call, while the on arm did. Adding recall
changed quotation rounding/slack as well as semantic context. The observed1/3
versus0/3 gain cannot be isolated as improved reasoning or source selection.

This is a planning-coverage and admission-comparability gap, not an observed
token-counter overrun or broken outer-budget enforcement. The quotation
protocol explicitly did not guarantee arbitrary model-selected continuations.
It should now be improved without increasing limits or tuning these models.

## Operational findings and usage

All14 tool attempts completed successfully and carry validated `ok` outcomes.
The three stops above are classified as token admission failures, not unknown
tool errors. This live run did not exercise the repairable tool-error path;
that behavior remains established by the separate offline qualification.

All12 samples settled with known usage. Native receipts, unique provider call
IDs, recorder observations, actual token bounds, proposal decisions and source
journals reconcile. Each observed input was within its admitted bound and each
output was at most512tokens. Re-scoring reproduced the original results.
Receipt-only recovery ran on copies with sockets denied; original execution
files and saved trace bytes were preserved. There were no new unknown or
overrun reservations and no repeated inference for failed samples.

Actual live usage:25requests /14tools /34,338tokens. Memory-off arms used
12requests /7tools /15,851tokens; on arms13requests /7tools /18,487tokens.
The2,636-token difference includes recall and the extra admitted continuation,
so it is not a pure measurement of memory overhead. Timing is descriptive only:
single trajectories, model switches and cache state prevent causal latency claims.

Cumulative charged usage is now1,442requests /588tools /1,731,251tokens.
Ceilings remain1,475 /604 /1,976,623; remaining33requests /16tools /245,372tokens.
All seven historic unknown reservations remain fully charged. The prior33
canonical ledgers retain their original bytes; this run appends the34th.

Initial dispatch was rejected by automatic approval review over unspecified
destination/payload provenance. Read-only checks established numeric loopback
destinations and newly authored synthetic payloads, excluding private expected
answers and gold labels. The same dispatch was approved after those checks;
the rejected attempt consumed no requests or reservations. There was no workaround
or destination change.

## Release and next-milestone recommendation

The generic Runtime/Harness tool-outcome and bounded-recovery fixes are worth
pushing for review and releasing through the normal release pipeline. Their
default-off compatibility and offline correctness do not depend on showing a
memory benefit. This comparison found no budget overrun, unknown effect or
tool-execution defect. It does not replace the unrun external DB/auth/billing
acceptance gates, and no release has been authorized or performed here.

Keep Lab memory/context planning experimental and opt-in. Do not market it as
an accuracy improvement. We are ready to move to a provider-neutral continuation
planning milestone: cover schema-permitted tool-response variants and safely
reallocate unused trajectory headroom while retaining shared request/tool/token
caps, context capacity, output limits and unknown-usage fencing. Optional recall
should not improve admission merely by creating rounding slack. Use frozen
counterfactual comparisons and provider-format fixtures to qualify that property.
No serving-specific branches or model prompt tuning are called for.

Smaller-model decision/feedback failures remain a separate reason to retain
deterministic acceptance checks and explicit escalation after bounded attempts.
Distributed effect reconciliation and multi-agent handoff/governance remain
later roadmap work; this small experiment does not qualify them.

Limitations: one case per family, only rejection/missing-fact outcomes, no
approve-class case, no repeated trials, and no hostile-note or large-index
evaluation in this slice. The12 cells are balanced across models/arms/families,
not decision classes. These results are descriptive, not a general ranking or
statistical claim about either model or memory architecture.

See the [sanitized measurements](data/balanced-memory-live-2026-10-17.json),
[protocol](../superpowers/plans/2026-10-17-balanced-memory-comparison.md) and
[private-evidence preservation receipt](data/balanced-memory-preservation-2026-10-17.json).
