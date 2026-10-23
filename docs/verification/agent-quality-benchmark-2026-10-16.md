# Agent-quality benchmark verification — 2026-10-16

The benchmark and its sixty-sample live comparative baseline are complete in
the isolated `codex/agent-quality-benchmark` worktree, based on `dc473da`.
The final corrected-schema study measured every sample with known usage:
smaller profile 0/30 task passes, larger profile 4/30. Earlier interrupted runs,
the schema-visibility fix and their evidence remain preserved below. Complete
measurement is not model qualification or a claim of reliable task performance.

Existing uncommitted adoption/chat changes were copied as the baseline. The
original checkout remains untouched by implementation. No merge, push, release
or deployment occurred.

## Source, SDKs and test results

- Original baseline: 955 passed, one existing Starlette warning, 68.10 seconds.
- Intermediate implementation checkpoints: 1014 passed in 87.77 seconds,
  1025 passed in 94.04 seconds, and 1026 passed in 97.77 seconds.
- Pre-live complete source suite: **1028 passed**, zero failures/skips, the same
  existing warning, **98.99 seconds**.
- Final focused data/scorer/two-profile tests: 27 passed in 3.80 seconds.

The installed payload audit matched all five original wheels selected by manifest
SHA256 `87862e1d37fd2f2cc1b8c6cd9965289887b0c056b26e81781dad4929a70a36c6`:
Core 0.4.1, Runtime 0.9.3/recorder 0.3.0 and Harness 0.8.2/store 0.3.0.

The command environment was the original checkout's `.venv-latest/bin/python`;
test source and working directory were this isolated worktree. Fresh
`.venv-quality` and `.venv-sdist-quality` environments installed hash-locked
third-party dependencies and the five verified SDK wheels. `pip check` and
`git diff --check` passed.

## Test-driven implementation and review

Observed RED→GREEN cycles cover private scorer assertions, malformed input,
persisted reservations, actual SDK tool dispatch, failure/repair, controller
recovery, pure preflight, safe reporting, packaging and imported comparison
identity. Specific regressions also prove:

- Permuted fact/citation arrays remain semantically equivalent.
- A critic must identify the seeded decision error.
- Interrupted samples remain unknown on reconstruction, with no redispatch.
- A partial schedule cannot claim a complete baseline.
- Duplicate logical samples cannot inflate case coverage.
- Receipt run/request identities and successful completions match journal
  entries one-to-one in both directions.
- Reports require workflow, schema, scorer and qualified SDK identities.
- Unknown elapsed time is omitted from measured latency; profiles have separate
  latency summaries.
- Repair lower bounds include both required readers.
- Each conflicting-revision case changes the decision if stale evidence is used.

One fresh read-only reviewer found three Important issues and two Minor issues.
Both Minor issues were regraded Important because fabricated zero duration and
pooled-only latency would mislead comparisons. All five were fixed in one pass;
eight initially failing regression instances and 59 focused tests verified that
pass. No reviewer findings were deferred. Later dataset/packaging checks each
had their own observed failing and passing tests.

## Installed artifacts and fixture results

Isolated PEP 517 builds produced both archives. The packaging test first proved
missing wheel resources, then verified all seven packaged assets and the source
archive's configuration example. No consumer-environment build backend was
installed or changed.

`python -I scripts/agent_quality_smoke.py --source-root "$PWD"` passed against
fresh wheel and sdist installations. It checks installed module ownership,
resource loading, pure preflight, real fixture HTTP/tool dispatch and
correct/wrong scoring.

The current installed baseline at `reports/quality-baseline-ready/summary.json`
covers **10/10 cases**, with **24 provider requests**, **3600 reported tokens** and
all three separate recovery probes passing. Repeating the command produced
byte-identical public output without redispatch. Independent offline scoring
with socket creation denied reproduced every verdict and tool metric.
All necessary fixture calls have zero excess, including critic/author cases.

A full two-profile fixture regression executes ten cases through each configured
synthetic model identity, with independent provider counts. Their measured task
success rates are 1.0 and 0.0 and the comparison is complete. These are scripted
profiles, not two actual language models.

Recovery reconstructs public Harness controllers around saved receipt,
missing receipt and schema-failure states. Each probe records zero additional
provider/tool calls after reconstruction and preserved allowance reservations.
The fault-probe calls are separate from ordinary task-quality counts.

Pre-live delivery artifact SHA256 values:

| Artifact | SHA256 |
| --- | --- |
| Wheel | `27e076db34a98c1a6bbdad151df3d15c49d669dd387dd01080d72b8bb67f37a9` |
| Sdist | `1cdd0684df0417f0cf73560513cd330ccca7cbca2a5ac94d09f94a8393f25edd` |

## Owned stack acceptance

All lanes below use Linux ARM64, Python 3.12.14 and audited released SDKs.
They passed with zero skips, verified payload audits and exact-owned cleanup.

| Lane | Cases | Seconds | Owner |
| --- | ---: | ---: | --- |
| Native PostgreSQL 16 | 54 | 258.57 | `221b877312c74ddaad517afc8e3abd8b` |
| Native PostgreSQL 18 | 54 | 260.39 | `3d115c0d81ce42388f71a2c3525cd6d7` |
| Conversation PostgreSQL 16 | 97 | 428.51 | `be52f6a1329e4237b9c753f4eb7f46d3` |
| Conversation PostgreSQL 18 | 97 | 428.59 | `34dd654f267a4e85834586fc6a10966b` |

Total: **302 required acceptance executions**. The tested service image is
`sha256:0a82634f13db3a8c10162d384ec7c8a371d54c8d5afa3086f1ab8aa4e1f21e49`.
Two earlier lanes on initial image
`sha256:7c2c6a4bffc742b9259a0a061b5e565858aef5cfc316a0150a4e939f371ec467`
also passed (native PG16: 54/246.79 seconds; conversation PG18: 97/411.98 seconds).

The dataset-only corrections produced delivery image
`sha256:77f99bf834d1c63b0a72f1d7d68cef7a4803c1dd598f960e780a934dbeb66e32`.
Comparison of all **114 public source/configuration files** in the service and
delivery images found exactly one difference:
`lab_runner/quality/data/evidence-review-v1.json`. Service code, runner code,
SDK manifest and other resources are byte-identical. All 17 delivery benchmark
package files matched the pre-live source. The updated dataset passed its own complete
container fixture run with networking disabled, ten task passes and 24 provider
requests. This is component-specific evidence, not a claim that the 302 service
checks were rerun on the dataset-only image.

## Requirement evidence

| Approved acceptance criterion | Evidence |
| --- | --- |
| Ten checkable cases and relevant records | Packaged suite admission, independent numeric/precedence tests and all-ten-case SDK fixture run |
| Pure scoring and malformed/evidence rejection | Scorer unit tests and socket-denied replay; eight review regressions |
| Critic rejection/repair, failures and recovery | Functional execution/recovery tests and complete fixture baseline |
| Pure default, no external credentials for fixtures | Preflight constructor/socket/process sentinels and installed smoke |
| Finite allowances survive uncertainty and replay | Concurrency, crash/reopen, settlement conflict and unknown-usage tests; duplicate command redispatch sentinel |
| Wheel/sdist ownership and resources | Archive tests plus isolated fresh installed smokes |
| Complete Lab and owned native acceptance | 1028 source tests and four owned lanes above, with explicit source/image scope |
| Reproduction and baseline receipts | `docs/agent-quality.md`, fixture evidence and the complete corrected-schema sixty-sample live baseline below |

## Approved live attempts

The maintainer approved ten cases × three repetitions × two existing local
profiles, with shared ceilings of 480 provider requests, 240 tool calls, 983040
reported tokens and 1800 seconds.

The initial model catalogue check failed with ConnectError: the local server was
not running. The launch should have been gated on that failed readiness check;
instead it dispatched one failed connection attempt and halted on unknown usage.
Its terminal receipt, empty handler journal and full reservation remain in
`reports/quality-live-20261016/`. No reservation was reset or relabeled known.

The existing oMLX app and managed server were started without configuration or
model changes. An authenticated catalogue read confirmed both approved models.
The failed run was left intact. A fresh baseline used the residual ceiling:
472 requests, 236 tool calls, 966656 tokens and the remaining original time.
Its deadline had a 0.133-second launch offset; observed execution stopped well
inside the original thirty minutes. Evidence is in
`reports/quality-live-20261016-ready/`.

| Observation | Smaller profile | Larger profile |
| --- | ---: | ---: |
| Scheduled samples | 30 | 30 |
| Executed samples | 30 | 1 |
| Task passes | 0 | Not established before timeout |
| Native tool executions | 0 | 0 |
| Known provider requests | 60 | Usage incomplete |
| Known reported tokens | 34028 | Unknown |
| Median measured elapsed time | 2.9023 seconds | One 30.0398-second timeout |

All sixty smaller-profile responses had known usage. Forty-two mentioned the
registered tool name in response text, but none produced a successful native
tool event or handler call. Harness correctly rejected these as required-tool /
answer admission failures. This is a tool-transport outcome, not evidence that
the smaller model cannot perform the underlying arithmetic.

The first larger-profile workflow reached its thirty-second run deadline. Its
receipt reports cancellation, unknown usage and zero tool handler calls. Server
events show a roughly twelve-second cold load consuming part of that allowance,
followed by request cancellation. The runner stopped immediately; 29 samples
remain unexecuted. The larger profile's task quality is not established by this
timeout.

The sixty-sample report is explicitly incomplete (`baselineComplete: false`):
31 attempted, zero passes, 29 unexecuted, usage incomplete. Do not present it as
a completed profile comparison. Both runs together conservatively retain 76
requests, eight tool calls and 66796 tokens against the approved ceilings,
including full maxima for both unknown reservations. Residual capacity is 404
requests, 232 tool calls and 916244 tokens.

## Approved ninety-second continuation

`reports/quality-live-20261016-90s/config.json` defines a fresh coherent sixty-
sample comparison with ninety-second case timeouts for both profiles, retaining
all prior evidence and deducting its full reservations. It uses only the residual
404-request / 232-tool / 916244-token capacity, with a new thirty-minute window.
The user approved this continuation. Its fresh allowance was created and live
execution started after an authenticated catalogue check confirmed both models.

This changes the per-case policy and requests a new time window; it is not an
automatic retry or an alteration of either saved run. The approved design's
unknown-usage halt remains in force throughout this approved continuation.
Original and future results cannot be merged as if their policies were equal.

The approved continuation stopped normally on the unknown-usage guard after
32 of 60 samples, with 28 not dispatched (`baselineComplete: false`,
`usageComplete: false`). Process exit was 1. Rebuilding the safe report from its
saved rows reproduced it exactly.

| Observation | Smaller profile | Larger profile |
| --- | ---: | ---: |
| Executed / scheduled | 30 / 30 | 2 / 30 |
| Accepted task completions | 0 | 0 |
| Native lookup calls | 0 | 4 |
| Observed provider requests | 60 | 8 |
| Reported tokens | 33538 | Incomplete |
| Median elapsed | 2.3694 seconds | 88.5103 seconds (two observations) |

The larger profile's first case finished both attempts in 86.9935 seconds with
known usage: four requests, two tools and 3457 reported tokens. Both responses
were JSON but failed the required types for facts/citations. The second case
made four requests and two tool calls before reaching `run_deadline` at
90.0270 seconds; its final cancelled response left token usage unknown.
Neither workflow completed. The scorer's invalid-evidence classification reflects
the absence of an accepted final answer, not a fabricated-tool finding.

The new allowance retains 72 requests / six tools / 53379 tokens, including the
entire unknown reservation. Across all three attempts, retained capacity totals
148 requests / 14 tools / 120175 tokens. The unused original numerical ceilings
are 332 / 226 / 862865; these are accounting balances, not authorization for
another run. No allowance was reset, and no further live request was dispatched.

## Live-discovered schema visibility defect

The benchmark bound schemas to Harness validation but did not include them in
model-visible instructions. Inspection of installed Harness shows it supplies
request/artifact/feedback inputs, not the step schema. Two real-provider payload
regressions independently confirmed the omission for ordinary and critic/author
workflows. Schema failures in the historical runs therefore cannot fairly
qualify either model's structured-output quality. Native tool/cancellation
observations remain useful diagnostics.

The Lab now derives each agent's instructions from its packaged prose and the
canonical public schema. Reviewer/author receive the answer schema; critic
receives the review schema. The prose digest binds the effective instructions,
so corrected runs have a different identity and cannot adopt or silently merge
the old evidence. Private answer assertions are never added to those prompts.
Three regression instances were observed failing before the fix; the full
execution file then passed all 20 tests. No SDK engine change was made.

Final verification after the schema-visibility correction:

- Complete source suite: **1031 passed**, zero failures/skips, one existing
  Starlette warning, **96.13 seconds**.
- Isolated wheel/sdist build succeeded under `dist/quality-schema/`. Installed
  smokes passed for both archives. The wheel's 17 benchmark package files match
  the source and installed environment byte-for-byte. `pip check` and installed
  five-wheel SDK payload audit passed.
- Corrected installed fixture: `reports/quality-baseline-schema/summary.json`,
  **10/10 passed**, 24 requests, 3600 reported tokens, all three recovery probes
  passed. Socket-denied offline rescoring reproduced all ten verdicts and tool
  metrics; rebuilding its public report reproduced it exactly.
- Corrected consumer image:
  `sha256:3c547257e66cfd1bfcda7e172ec521d3eeeb3779c5f903f41a99e45e01ecc4c2`.
  Its complete fixture run passed 10/10 with networking disabled. Comparison of
  all 114 public files against the service-qualified image found only the three
  benchmark modules (`execution.py`, `suite.py`, `runner.py`) and the previously
  corrected case dataset differ. Service code and SDKs remain byte-identical;
  the earlier 302 service acceptance executions are not claimed as rerun.

| Corrected artifact | SHA256 |
| --- | --- |
| Wheel | `e4c5eff5bd0e00dcbad15733d95d7fffb015ba141e4946307ac8392173f4645e` |
| Sdist | `2ae4a8d950630d6c7c09a9f91526d20b71049ffd9fe44530cdbea33923fec8be` |

These archive hashes precede the final documentation-only updates. At this
checkpoint the remaining deliverable was a complete live comparison using the
corrected schema-bearing instructions and sufficient case/batch time. That
approved continuation is now complete below. Policy changes retained all prior
reservations and identities.
The branch and uncommitted worktree remain preserved; no integration or release
has been performed.

## Approved five-minute continuation

The user requested increasing timeout and proceeding. The corrected-schema
sixty-sample study uses 300-second case limits and a finite 10800-second batch
window. Its fresh configuration is
`reports/quality-live-20261016-300s/config.json`, with the exact residual ceilings
of 332 requests / 226 tools / 862865 reported tokens. No profile, model or output
token limit changed. Authenticated catalogue readiness and source/installed
corrected-module equality were checked successfully before dispatch. All three
earlier runs and their full unknown reservations remain intact.

### Complete live comparative baseline

`reports/quality-live-20261016-300s/summary.json` and `cli-summary.json` agree.
Both `baselineComplete` and `usageComplete` are true: sixty scheduled samples,
sixty observed, four passes and 56 failures, with no unexecuted or unknown-usage
sample in this study. CLI exit 1 records failed tasks; it does not invalidate
complete measurement. Sequential sample elapsed time totals 2601.60 seconds
(43.36 minutes), within the approved extended window. No case timed out.

| Metric | Smaller profile (`local`) | Larger profile (`local-strong`) |
| --- | ---: | ---: |
| Task passes / observed | 0 / 30 | 4 / 30 (13.33%) |
| First-pass ordinary cases | 0 / 24 | 4 / 24 |
| Seeded critic detections | 0 / 6 | 6 / 6 |
| Corrected-draft task passes | 0 / 6 | 0 / 6 |
| Native tool calls | 0 | 43 |
| Provider requests | 60 | 86 |
| Reported tokens | 39651 | 90125 |
| Schema repair attempts | 30 | 0 |
| Task repair attempts | 0 | 7 |
| Median elapsed seconds | 2.4719 | 74.2389 |
| p95 elapsed seconds | 3.0365 | 137.1196 |
| Maximum elapsed seconds | 3.0795 | 160.0375 |

The smaller profile never produced the required native lookup. All thirty
workflows exhausted admission attempts. All 26 failed larger-profile workflows
ended at the native `tool_round_limit`: a model requested another tool round
after the permitted round. Seven intermediate answers triggered `wrongFacts`
repair feedback; these failures concern the required fact-identifier set and
do not establish incorrect numeric decisions. The accepted cases were
`combine-01` repetition two and `missing-02`, `injection-01`, `injection-02`
repetition three. Every pass was first-attempt ordinary execution. Detecting a
seeded error did not yield a completed critic/author correction in this study.

The larger profile requested 129 records, including 51 irrelevant-record
observations and 39 duplicate-record observations, with seven calls above the
case lower bounds. Duplicate observations include required critic/author reads;
they must not all be called unnecessary work. The smaller profile has no tool
efficiency observations because it dispatched no tools. The principal measured
gap is reliable completion after native lookups, followed by answer-contract
correctness. These results apply to the exact local profiles, schemas, prose,
case limits and SDK identities recorded in the report.

The final offline audit admitted every canonical sample, matched all verdicts
and metrics to the report, recomputed receipt/evidence digests and reconciled
every sample's actual counts to the allowance. Rebuilding the public report was
exact. Replaying the same schedule with provider dispatch and socket creation
forbidden produced byte-identical public summary, allowance and all sixty
canonical evidence files. No extra inference was made during this audit.

This study recorded **146 requests, 43 native tool calls and 129776 reported
tokens**. Across all four studies, conservative retained capacity is **294
requests / 57 tools / 249951 tokens**, below the original numerical ceilings.
The three earlier unknown reservations remain fully retained. Balances are
186 requests / 183 tools / 733089 tokens; they are accounting balances, not
actual billing figures or authorization to launch more studies. Historical
policies are not merged into the final success denominator.

Task 5 and the benchmark goal are complete. Recovery remains separately
qualified by the fixture probes and native/conversation acceptance above; live
task failures do not become recovery successes. All work remains uncommitted in
the isolated branch, preserving the copied unrelated baseline. No merge, push,
release, deployment or shared service configuration change occurred.
