# SUE local Qwen pilot — 2026-10-24

The first real-model comparison does **not** qualify SUE for enabling. The
Qwen 7B matrix executed all 24 planned cells, but only the eight direct workflows
completed. The critic and SUE arms each exhausted validation attempts on all
eight cases. Scripted fixture success was evidence of mechanics, not live
review quality. Memory and SUE remain independently disabled by default.

## Completed Qwen 7B experiment

Model: `mlx-community--Qwen2.5-Coder-7B-Instruct-4bit`, authenticated local oMLX
at numeric loopback, macOS ARM64. All arms used temperature 0.2, 4,096 maximum
output tokens and an explicit upstream `enable_thinking: false`. No shared
server settings, credentials, models or production defaults were modified.

Eight frozen `requirements_review_v1` cases were evaluated once per strategy,
rotating strategy order between cases. Cases, source hashes, final prompts,
schemas, expected answers and scorer were unchanged. The host operator's final
workflow constructor was checked against the frozen fixture constructor by AST.
Every cell retained the common limits of 30 requests, 65,536 reported tokens
and 120 seconds; SUE additionally retained 28 calls, 14 turns, two attempts per
step and the hard 60-second invocation policy. Unlimited tokens were authorized
by the user, but these smaller experiment bounds were intentionally retained.
No expected-answer module was imported into execution. Grading occurred after
dispatch ended. This is one pilot on short, deliberately simple synthetic
documents, not a repeated blinded study or evidence for realistic corpus-wide
review quality.

| Arm | Workflows completed | Strict end-to-end passes | Requests | Reported tokens | Median elapsed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 8/8 | 4/8 | 8 | 8,439 | 6.05 s |
| Critic-author | 0/8 | 0/8 | 16 | 16,711 | 9.83 s |
| SUE + synthesis | 0/8 | 0/8 | 16 | 15,667 | 13.58 s |

Failed-arm elapsed values measure an aborted workflow, not the cost of a
successful review. No critic or SUE final synthesis was reached. These results
cannot rank the substantive quality of completed critic or SUE reviews.

All 40 physical HTTP exchanges reconcile with Runtime request and token counts:
**40,817 reported tokens, zero tools, zero unknown or pending reservations** in
this experiment. No request was retried after an unknown completion. Validation
retries remained bounded at two per step. Completed direct runs and saved
failed runs were validated using public Harness and SUE inspection APIs during
network-denied replay, with zero additional requests.

Direct's exact known-issue checks passed on cases 01, 02, 03 and 07. Cases 04–06
failed assessment and issue matching. Case 08 found the contradiction but failed
the exact citation-support check. Across all eight direct cases, schema and case
identity passed 8/8, assessment and issue matching passed 5/8, and citations
passed 7/8. Exact citation matching is intentionally strict and was not changed.

## Observed blockers

1. **The critic prompt carries a conflicting output contract.** Its task
   arguments advertise the final review schema and instruct the model to return
   that schema, while Harness requires `{"feedback": string}` for the critic
   step. All 16 Qwen 7B critic responses returned the final-review shape, and
   both Qwen 27B critic attempts did the same. Harness correctly rejected them.
   This is a benchmark/workflow contract problem; it does not establish that
   critic-author reasoning is ineffective.
2. **SUE response reliability is inadequate on Qwen 7B.** All 16 attempts omitted
   the required `addresses` field; nine also used Markdown fences despite the
   strict raw-JSON instruction. Every attempt failed validation. No turn was
   accepted, and no final review exists to grade. Offline unwrapping was used
   only to diagnose the contents of fenced responses; no SUE receipt, accepted
   state, validator, score or replay was repaired.
3. **The adapter omits canonical semantic response guidance.** The original
   SUE prompt explains the verdict/test-result relationship, unsupported claim
   updates, exact premise grounding and that `addresses` refers to earlier
   dialogue turns. The current Lab prompt supplies a question, shape schema and
   generic grounding instructions, but omits those explanations. This is a
   concrete compatibility gap when moving model execution out of Castle. Its
   causal contribution to Qwen 7B's failures has not been isolated. A late Qwen
   27B response passed the JSON shape schema but public `castle_sue.advance`
   rejected it: it supplied a claim with `CONTRADICTED` and addressed turns
   `[1,2]` in the first turn. Canonical validation prohibits both.
4. **Qwen 27B exceeds the admitted invocation lifetime.** The current public
   SUE adapter settings cap an invocation at 60 seconds. A genuine first SUE
   response arrived at 72.62 seconds and remained unaccepted. Extending this
   lifetime requires an explicit adapter policy change and tests; no such
   change was made to force the benchmark through.

Before another quality comparison, make the critic's stage-specific contract
explicit and expose/use canonical SUE answer guidance through the pure engine's
public interface. Keep all source, ownership, shape, semantic and provenance
validators intact. Add prompt-contract regressions and fixtures for the
observed malformed responses. Any configurable timeout increase belongs in
the consumer/Harness policy, bounded by the common workflow deadline and
shared allowance. Model execution remains in Runtime. None of these fixes
requires SOAR or a Castle-owned model runner.

Keep the frozen v1 results. A changed prompt or policy requires a separately
identified study with fresh source locks and the same direct baseline, rather
than overwriting this failed result. Only after execution reliability is
established should repeated held-out cases measure quality, cost and latency.

## Qwen 27B diagnostics and retained uncertainty

The initially selected `ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ` ran first with its
existing default thinking behavior. Its first direct request hit 60 seconds
without observed completion or usage, and the study stopped. Its entire
30-request/65,536-token sample reservation remains unknown. The initial
observer used daemon handlers, so its dispatch-summary boolean failed to mark a
still-pending wire row as unknown; the durable Runtime and allowance records
correctly retain the uncertainty. That initial boolean is not completion proof.

One separate 16-output-token endpoint diagnostic with thinking disabled
returned in 1.15 seconds and reported 17 tokens. It was not a retry of the
review sample and did not establish the timeout's sole cause. A separately
identified thinking-disabled 27B experiment then completed direct in 25.39
seconds (1,039 tokens), blocked the critic after two schema failures (2,045
tokens), and stopped at the first SUE timeout. The observer retained its late
72.62-second HTTP response (1,237 provider-reported tokens), but Runtime had
already returned unknown usage. Its full sample reservation remains unknown.

That second observer waited for its handler and preserved the late response.
The strict initial report join rejected the discrepancy between late wire usage
and Runtime's unknown receipt. The failure log is retained; the independent
offline audit confirms saved state, receipts and wire identities without
claiming complete Runtime accounting for that sample.

Across the three experiments plus the endpoint diagnostic, **46 physical
requests** were issued. Observable provider responses report **45,155 tokens**,
including the late unaccepted response; one request's token usage was never
observed. Conservative retained sample charges total **104 request units and
174,990 token units**, including both full unknown reservations. These are
fresh-study figures only. Historical ledgers and unknown reservations were
neither reset nor reused. No monetary estimate or invoice is inferred.

## Verification and evidence

All experiments use installed Core 0.4.1, Runtime 0.9.8, Harness 0.9.4, Lab
0.6.0 and standalone SUE 0.1.0. Installed wheel-record hashes were verified;
canonical SUE engine identity remains
`bbde4669d1eb069dcb8c72e121cd08be4ca953b349f9243b9e650e0d1b596f0b`.
Source digests were checked before every sample. The pure SUE engine and
production code were not changed. A separate operator enabled only its SUE
study arm. No memory worker, dense model, SOAR or original Castle model runner
was used by this review experiment.

The host operator passed all three offline fixture arms before live dispatch.
All 40 Qwen 7B request/receipt/accepted-output joins passed independent offline
audit, including public Harness validation of its existing complete JSON-fence
output support. The initial observer-only audit assumed plain JSON for every
accepted final output and failed on a legitimate complete JSON fence. Its
corrected diagnostic unwraps only the exact envelope supported by Harness and
still verifies the accepted value against the stored receipt and captured raw
response. Both audit versions are retained; product assertions are unchanged.

Private synthetic evidence is retained under
`reports/castle-sue-qwen-pilot-20261024/`: frozen plans and operators, actual
requests and responses (without authorization headers), public stores,
receipts, reports, classification, accounting, offline checks, replay and
SHA-256 manifest. Prior [test and retrieval evidence](prosaic-castle-retest-2026-10-24.md)
is preserved unchanged. The failure classification changes no grading.

Exact installed commands included:

```sh
python -I /absolute/study/operator.py
python -I /absolute/qwen7b-study/operator.py replay
python -I /absolute/qwen7b-study/audit.py
python -I /absolute/qwen7b-study/classify.py
```

No production code, assertions, default flags, push, merge or release changed.
