# Author deadline follow-up — 2026-10-16

Status: all20samples executed with complete usage and audited replay. Smaller10/10,
larger9/10,19/20combined. Both larger author workflows pass; a separate512token
generation truncation prevents a perfect run. No model-speed improvement claimed.

User requested fixing the larger model's author timeout, rerunning the benchmark,
and explaining findings/readiness for the roadmap gaps. Native execution remains
the selected method. This follow-up changes only benchmark timeout configuration;
production code and installed consumer/SDK artifacts remain unchanged.

## Diagnosis and selected change

Previous projection repair-02-p2-r1 stopped at run_deadline300.08s. Its critic
succeeded in154.71s with all3issues; author was cancelled with incomplete usage.
The other larger repair finished295.47s: critic113.53s plus author181.65s.
Earlier feedback runs finished243.30s and260.13s. Thus300s has little headroom
for two sequential native tool/final invocations; no evidence shows an author
decision, schema or tool-loop defect in this failure. Runtime's adapter receives
Harness's remaining run deadline, so the author inherits only the leftover time.

Use explicit600s case limits for both profiles. workflow_definition/policy already
bind that field to invocation timeout and total max_run_s. This raises both time
ceilings; it does not claim lower inference latency. No prompts, model settings,
SDKs, tools, scoring, case data or8request/4tool/16384token caps change. Comparison
policyDigest and workflowDigest must change; all other identity/profile fields
must match the preceding projection track. Preserve old300s evidence and charges.

## Execution checklist

- [x] Inspect failed and successful critic/author timings and installed deadline propagation.
- [x] Re-audit unchanged installed candidate:221payload files/18source resources match, fixture10/recovery3 qualification retained.
- [x] Run one larger repair-02 diagnostic, cap8requests/4tools/16384tokens/600s case.
- [x] Audit diagnostic and calculate full20sample request/tool/token headroom.
- [x] Obtain any needed explicit cumulative allowance extension, then rerun all20 under600s cases and14400s batch ceiling.
- [x] Re-score/audit all evidence and verify socket/provider-denied byte-identical replay.
- [x] Explain corrected-workflow versus first-pass behavior, timeout sensitivity, remaining gaps and next milestone.

Initial20 historical ledgers retain793requests/264tools/797192tokens, including5
fully charged unknown reservations. Approved829/282/1046071 leaves36/18/248879.
The new diagnostic fits that allowance. A complete20sample rerun requires its
own fresh allowance with graph-derived96requests/48tools/327680tokens peak;
compute the extension after actual diagnostics. No unknown attempt is retried.
The diagnostic is a fresh explicitly requested experiment, separate from the
old interrupted run and never represented as settlement of its unknown usage.

No new source tests/build are needed for a config-only experiment. Installed
payload qualification is checked fresh; prior1068passing source tests remain
historical qualification, not a newly executed suite. No service/database,
release, merge or platform requalification is claimed.

Diagnostic reports/quality-live-20261016-author-timeout-probe passes with complete
usage4requests/2tools/5766tokens. Critic57.77s, author126.23s, total184.23s. This
does not exceed the old300s limit: it confirms valid completion with unchanged
behavior, not that extra time caused this particular pass. Prior variability
and the deadline cancellation remain the rationale for explicit600s headroom.
Offline audit verifies score, receipt digests, public request retention, lookup
journal joins and known usage. No old unknown reservation was settled or retried.

All21 ledgers retain797requests/266tools/802958tokens and5 unknown reservations.
Approved829/282/1046071 leaves32/16/243113. Prepared output
reports/quality-live-20261016-author-timeout uses20samples,600s case,14400s batch,
and proposed96requests/48tools/327680tokens. Needed extension64/32/84567 yields
proposed cumulative893/314/1130638. Preparation is not permission to dispatch.
Current identity differs only policyDigest/workflowDigest from projection;
model profile fingerprints and installed artifact hashes match exactly.

The user explicitly approved64requests/32tools/84567tokens, raising cumulative
ceilings to893/314/1130638. Installed preflight passed retained-history, candidate,
profile/catalogue, identity and graph-derived reservation checks before dispatch.
Session67901 executes the20sample study with600s cases/14400s batch ceiling.
No previous known or unknown reservation is removed or discounted.

## Final result

Session67901 finished exit1 for one task failure, with baselineComplete=true and
usageComplete=true. All20scheduled samples ran;19passed. A complete measured
baseline is not a claim that every task passed. Per-case time limits600s remain
explicitly bound to policy/workflow identity. No production source, package,
SDK, model feature, prompt, scorer or global configuration changed this turn.

| Profile | Task pass | Ordinary first pass | Accepted critic/final draft | Requests/tools/tokens | Median sample time |
| --- | --- | --- | --- | --- | --- |
| Smaller7B |10/10|7/8|2/2 and2/2|32/16/35605|3.13s|
| Larger27B |9/10|7/8|2/2 and2/2|23/11/32230|101.69s|

Combined55requests/27tools/67835tokens;4semantic correction events,0schema repairs.
The smaller profile's accepted-review metric includes host-targeted correction;
it does not measure unaided critic accuracy. Its tool metrics include4excess
calls above the declared lower bound and2irrelevant record reads. These remain
efficiency observations, not automatically forbidden calls.

Larger repair-01 completes263.24s (critic104.29s,author158.25s). Previously timed-out
repair-02 completes247.07s (critic115.01s,author131.77s). No new author deadline or
unknown usage. Diagnostic184.23s and full repair247.07s are both below the old300s
limit: successful reruns do not establish that extra time caused success. The
600s policy addresses observed deadline headroom; latency varies and was not
optimized. New sample maximum263.24s,p95at20observations247.07s; time sum1352.51s.

Remaining failure missing-02-p2-r1 is runtime_failure at122.19s, one provider
request/zero tools/1768tokens. HTTP200 but finish_reason=length and provider code
incomplete_generation:512completion tokens exhaust the unchanged per-response
cap before a complete tool call. Runtime rejects the partial artifact rather
than accepting an ungrounded answer. No automatic retry or cap change was added.
This failure was not present in the preceding run and is separate from timeout.

All22ledgers retain852requests/293tools/870793tokens, including the same5fully
charged old unknown reservations. No new unknown. Approved893/314/1130638 leaves
41/21/259845. Full-run audit independently rescored all20, verified known claims,
evidence/receipt digests, lookup joins, one-execute adapter budgets, projected
correction-input hashes, unchanged runtime bytes and exact600s case caps. Only
policyDigest/workflowDigest differ from projection identity. Replay with socket
creation and provider execution forbidden left summary, allowance and20canonical
evidence files byte-identical. Proof /tmp/prosaic-author-timeout-final-audit.json.
Scripts and safe qualification/audit/preflight records:dist/quality-author-timeout.

## Findings and readiness for the roadmap gaps

The reference roadmap is https://www.kdnuggets.com/the-roadmap-to-mastering-agentic-ai-systems-in-2026
(accessed2026-10-16). It separates single-agent execution, memory/graph control,
multi-agent coordination and operational hardening. The following is our inference
from local evidence, not a claim that the article certifies Prosaic.

| Area | Current evidence | Remaining gap |
| --- | --- | --- |
| Native tools and structured results | Real lookup, strict checks, bounded correction, explicit truncation rejection | Generation-cap handling, fewer redundant lookups, held-out cases and repeated trials |
| Stateful graph control | Native critic/check/corrector/author branches, receipts, replay | Episodic/semantic retrieval across tasks; durable workflow state alone is not retrieval memory |
| Agent collaboration | Sequential critic/author handoff and validated corrections | Parallel fan-out/join, shared budgets, cancellation and concurrent recovery qualification |
| Hardening | Finite ceilings, full unknown charging, failure evidence, no-inference replay | Candidate publication/adoption, hosted-provider qualification and separate arbitrary-code sandbox/production tests |

We are ready to tackle a bounded retrieval-memory experiment in a consumer or
Runtime tool, keeping Core discovery read-only. Begin with read-only retrieval,
source IDs/versioning, tenant isolation, freshness/conflict checks and a held-out
comparison with memory disabled under equal budgets. Measure recall and grounded
answers, not just whether retrieval returned documents. A first pilot should not
write automatic memories or introduce parallel scheduling at the same time.

Before calling this broadly reliable, qualify output-cap exhaustion separately
and broaden/repeat the benchmark. The tiny synthetic suite has host-computable
correction targets; it does not establish general planning, unaided reasoning,
long-horizon autonomy, semantic memory or production readiness. Extra inference
headroom is an operational policy fix, not evidence of a model capability gain.
Parallel orchestration should follow its own recovery/accounting tests after the
retrieval contract is stable. No new gap implementation or release was started.
