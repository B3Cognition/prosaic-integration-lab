# Compact memory handoff qualification — 2026-10-26

The maintainer approved reducing repeated model input while preserving strict
citation validation, then a separate same-Qwen preflight. The explicitly frozen
`compact-citations-v1` transport is implemented. `canonical-v1` remains the
default; memory and SUE stay disabled, and SOAR remains separate. No packages or
branches were published or pushed. Changes remain local and uncommitted.

## What changed

The host keeps the full immutable source/identity/quotation packet. The model
receives each original frame display once plus address-only paragraph and
canonical citation IDs. A compact draft uses the same IDs. Before Harness accepts
an answer or repair, the host resolves only exact issued IDs, then applies the
unchanged canonical answer schema, grounding validator, source scope/provenance,
question/frame coverage and 16 KiB canonical output limit. Invalid or foreign IDs
fail; there is no fuzzy matching or citation repair. Search previews cannot grant
whole-record citations. Raw wire replies/checkpoints remain preserved separately
from resolved canonical candidates, and replay checks both and their relationship.

The canonical critic schema and critic-to-independent-author composition remain
unchanged. Runtime executes models; Harness owns state/resume; Lab owns this
explicit consumer projection and validation. No Castle, Runtime, Harness or Core
source was modified. Compact generation restricts evidence selection to complete
indexed paragraphs and supplied whole-window/record citations; arbitrary
canonical subspan drafts still use the existing transport.

## Verification

| macOS ARM64 / Python 3.12.15 | Result |
| --- | --- |
| Final full released-SDK unit/functional suite | 2,159 passed + 73 subtests, one existing Starlette warning, 490.62 seconds |
| Installed constrained-generation candidate, compact and balanced regressions | 67 passed + 36 subtests, 33.38 seconds |
| Focused compact/dataset/CLI/recovery | 36 passed |
| Python identity: source/wheel/sdist/installed | 210 payloads match |
| No-call transport audit on previous sealed captures | 300 captures / 6,169 displayed body spans preserved exactly |
| Historic preservation before/after | 13 archive copies / 32,539 indexed files, four earlier unknown reservations unchanged |

Fresh review found an offline dependency regression: freezing a dataset imported
optional execution SDKs. An isolated installed-process test reproduced it with
SDK imports denied; lazy execution imports fixed it. Both canonical and compact
freeze/load now pass that guard. All other inspected transport/replay paths had
no concrete finding. The earlier 2,158-test first-stage suite passed but is
preserved separately from final verification. Failed tests, the loopback sandbox
failure, initial builder/test-layout failures and earlier builds are retained.
No native Linux/PostgreSQL matrix was rerun for this consumer-only change.

## Payload reduction without evidence removal

All 100 original questions, source bytes, source grants and strict grading key
remain unchanged. No new retrieval-quality run is claimed: the audit revalidates
the previous 300 sealed real-provider captures and compares their legacy/compact
model projections without model or worker calls and without reading the key.
Retrieval/ranking/selection/context modules are byte-identical to the balanced
study. All displayed text and paragraph addresses are preserved.

| Arm, 100 captures each | Total legacy argument bytes | Compact argument bytes | Reduction |
| --- | ---: | ---: | ---: |
| File search | 8,008,996 | 3,716,404 | 53.6% |
| Raw Castle | 4,107,639 | 1,723,654 | 58.0% |
| Expanded Castle | 9,885,207 | 4,014,025 | 59.4% |

These are canonical argument JSON bytes, not tokens, total wire/prompt bytes or
latency. The final audit uses Runtime's actual `validation_feedback=null`
envelope; the earlier approximation used an empty array and differed by two
bytes/request. Both audit versions remain preserved.

## Qwen preflight remains blocked

The same three known cases were frozen across three arms (nine scheduled
samples). The endpoint/model, strict semantic scorer, canonical answer and critic
schemas, 60-second call limit, 4,096 output-token limit, no-tools policy and
27-request / 884,736-token preflight allowance remain unchanged. Installed
Runtime is the separately checksummed `0.9.8+jsonschema.2` candidate; public
released-version guards are intact.

The first q001 file-search request carried 35,393 argument bytes, versus 75,789
in the preserved previous run. It still timed out: 60.24 seconds in the answer
stage, 61.45 seconds for the sample. Runtime records a single attempt, timeout,
empty stdout and unknown usage. One request was initiated; eight samples are
blocked; zero answers/reviews were accepted and the critic made no call.
The new full three-request / 98,304-token reservation remains held separately
from all four older unknown reservations. Actual token use is unknown, not zero.

Normal installed CLI replay exactly reproduces the terminal summary without
inference or worker calls. The grade template has no accepted answers to judge;
the strict scorer correctly reports semantic quality and critic benefit as
unmeasured. The precommitted readiness gate fails, so the 100-question model
batch was not started. No retry, reservation settlement, validator/scorer
relaxation or deadline increase occurred.

The reduction is verified; the timeout cause is still unknown. Next investigate
serving queue time, schema/grammar setup, prompt prefill and decoding before
another generation change or benchmark. A timing trace should distinguish
those causes; neither a reachable model endpoint nor a smaller packet proves
the model can finish inside the fixed deadline. No such diagnostic inference
or serving change is included here.

Private corpus, raw failures, receipts, source snapshots, protocols and artifact
hashes are preserved outside Git in `memory-benchmark-compact-20261026`.
