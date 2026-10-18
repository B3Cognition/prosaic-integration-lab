# Strict plan validation and fresh memory comparison — 2026-10-17

The remaining validation minor is fixed and qualified. The fresh comparison
stopped safely after four completed samples and one accounting-unknown sample;
three scheduled samples were never dispatched. It does not establish that memory
helps either model. Lab memory and continuation budgeting remain experimental.
No push or release was performed.

## Candidate and qualification

Lab `0.5.1+continuation.2`, source
`b0072fa668d8d0d16a14e5ba95b183fedd344da7`, rejects equivalent floating-point
values in the derived `requiredTokens` and `availableTokens` fields in both
plan versions. Four regressions failed before the fix and pass afterward;
valid serialized integer contracts remain compatible. No model-specific change.

Full source suite: **1,333 passed** on Python 3.12.14, with one existing
Starlette/httpx deprecation warning. A separate environment installed an
exact-source wheel and the five public SDK wheels from the unchanged
`dependencies/continuation-candidate.json` manifest. Installed validation:
four strict regressions, 14 both-wire continuation scenarios and 10 legacy
workflow/replay scenarios passed. SDK and Lab payload audits and dependency
consistency checks passed. The first isolated regression invocation had a
test-helper import error; the corrected invocation imported Lab from installed
site-packages and added only the unit-test helper directory.

Runtime remains 0.9.7 and Harness 0.9.4. Active and historical dependency manifests
are unchanged. Wheel SHA256:
`221b07f140dc63e5622b3815816aeedc16138758c60e782cd2cdadf3f4827a4c`;
sdist SHA256:
`8e516c94594114b1e92b5e017e92923997682eb9cd3e2eaa054370b1c908ea2f`.

## Frozen comparison and limits

Two fresh synthetic cases (approval and missing evidence) × two unchanged
models × memory off/on: eight scheduled samples. History and trusted metadata
were frozen before current cases and private answers. Cases, prompts, quotations,
settings, counters, serving assets and operators were frozen before dispatch.
Both arms use typed evidence, bounded recovery and opt-in version 2 continuation
budgeting. All eight mandatory plans admitted and passed synthetic execution,
pure preflight and network-denied receipt replay. No live development probes.

Eight samples were selected to fit the remaining allowance. Full reservations
were 32 requests /16 tools /65,536 tokens. Per-case limits remained 4 requests,
2 tools, 8,192 tokens, 600 seconds and 512 output tokens. Cumulative ceilings
remain 1,475 requests /604 tools /1,976,623 tokens. The original stop-on-unknown
rule stopped the run; no uncertain sample was retried or reservation forgiven.

## Completed pairs

| Approval case | Memory off | Memory on | Recall actually exposed | Tokens off/on |
| --- | --- | --- | --- | --- |
| Smaller 7B | Pass after correction | Pass first attempt | Yes | 4,952 /2,755 |
| Larger 27B | Pass first attempt | Pass first attempt | No | 2,786 /2,750 |

The smaller model initially chose rejection despite correct fact fields, then
corrected to approval after public feedback. With memory it chose approval on
the first attempt, using two fewer requests and one fewer tool call. This is
one descriptive efficiency observation, not reliable evidence of a causal memory
benefit. The trajectories also differ in their number of lookups because of
the correction. The larger model's recalled episode was excluded by the full
planning quotation; its public requests were identical, so that pair cannot
measure memory-content effects. Neither model has a completed missing-evidence
pair. Scheduled coverage does not count as successful evaluation coverage.

The four completed samples have reconciled receipt/recorder/counter usage:
10 requests, 5 successful tools and 13,243 tokens. No continuation was refused,
no actual proposal exceeded its quoted slot, and no hard limit was breached.
Thus this slice does not exercise the live quotation-overage path; the installed
synthetic tests remain the evidence for that behavior.

## Stop, accounting and preservation

The larger model's memory-enabled missing-evidence sample dispatched one
request and no tools, then ended after 97.7 seconds with HTTP 200, empty output
and unknown token usage. It was not classified as a timeout. The retained
receipt and observation do not establish the underlying provider failure;
missing usage must not be treated as zero or attributed to memory reasoning.

Its full 4-request /2-tool /8,192-token reservation remains charged. Study charge
is therefore **14 requests /7 tools /21,435 tokens**, rather than the observed
request/tool count alone. Cumulative charge is **1,456 /595 /1,752,686**;
remaining allowance **19 /9 /223,937**. Eight unknown historical reservations
are retained in total, including this new one. Three unclaimed samples incur
no charge and remain unexecuted; the frozen study is incomplete.

A separate post-stop audit preserves the originally frozen full-run auditor.
It reconciles every completed sample, the unknown intent/observation and its
reservation, validates frozen plans and scope, replays copies with networking
denied, and verifies original trace bytes unchanged. All 34 prior ledgers and
428 prior comparison files plus 282 prior continuation files remain unchanged.
Private evidence was archived and a 35th canonical ledger appended.

Archive SHA256:
`709db8e9d52bc9a5d19ec4580aafaf18cfa41813a8322f2f69e604164b781ce5`.
Canonical ledger SHA256:
`2f8cd1fdc5638904d5434f1ea4a53fc51593a21d6ee4a99922b067c992310ae2`.
See the [structured checkpoint](data/continuation-memory-live-2026-10-17.json).

## Readiness

The validation fix is qualified, and failure fencing preserved the limits.
Memory efficacy remains unproven; this is not a completed eight-sample baseline
or production-memory qualification. The small model's corrected decision shows
feedback can work on this case, without resolving its earlier broader failures.

The next useful milestone is provider-neutral failure observability: preserve
bounded, sanitized response diagnostics; distinguish malformed/provider-error
responses from absent or invalid usage; and qualify those classifications with
synthetic fault injection while retaining unknown-usage fencing and preventing
uncertain redispatch. That operational gap should precede another live efficacy
run. Broader fresh task families, rejection, stale sources, longer trajectories
and additional providers remain evaluation gaps. No model-specific prompt tuning
or increase in limits is justified by these partial results.
