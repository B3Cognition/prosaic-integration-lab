# Live controlled retrieval-memory comparison

All48live samples completed with known usage:12frozen cases x2memory arms x2local
models. Memory improved strict task success for both models in this run, with
different failure mechanisms and greater reported token use. No model, prompt,
retriever, corpus, response cap or grading rule was changed during the run.

## Results

| Model | Memory disabled | Memory enabled | Paired gains/losses | First-pass strict successes |
| --- | --- | --- | --- | --- |
| Qwen2.5-Coder7B | 3/12 (25%) | 7/12 (58.3%) | 4gains/0losses | 2 →6 |
| ThinkingCap-Qwen3.8-27B | 10/12 (83.3%) | 12/12 (100%) | 2gains/0losses | 10 →12 |

A pass requires current authoritative evidence, the correct decision/facts/citations,
and the frozen JSON-only output contract. Full task success was32/48; baseline
completeness means all48outcomes and usage measurements exist, not that all tasks
passed. The CLI's exit1 correctly reflected failed benchmark tasks; it was not a
dispatch failure or a reason to rerun cases.

| Family | 7B disabled →enabled | 27B disabled →enabled |
| --- | --- | --- |
| Relevant history | 0/2 →2/2 | 2/2 →2/2 |
| Stale references | 0/2 →0/2 | 2/2 →2/2 |
| Empty history | 1/2 →1/2 | 2/2 →2/2 |
| Foreign-tenant decoys | 1/2 →2/2 | 2/2 →2/2 |
| Hostile notes | 1/2 →2/2 | 2/2 →2/2 |
| Missing current fact | 0/2 →0/2 | 0/2 →2/2 |

For7B, four controls failed that passed with memory. Saved receipts support a source
selection/citation benefit: recalled pointers reduced irrelevant record reads from
33to14 and duplicate reads from27to16 across the arm. This is a source-locator
benefit, not evidence of general reasoning or continual learning. Memory did not
solve five cases: both stale cases, one empty-history case and both missing-fact
cases. In stale-memory cases it read and cited the correct current records, but
put record IDs in the facts array. In missing-fact cases it used observer records
where required auditor facts were absent and failed to return the required
insufficient result. Bounded feedback did not reliably repair these errors.

For27B, the two control failures were operational/output failures:

- missing-11: finish_reason=length,512completion tokens, before any successful
  lookup;1request/0tools/1411reported tokens, with known usage. This reproduces the
  existing response-cap gap. It was not a timeout or a measured wrong decision.
- missing-12: the native workflow accepted a correct answer inside Markdown JSON
  fences, but the strict scorer rejected the wire format. Removing fences for
  diagnosis gives exactly the native accepted answer and the correct fields. The
  original result stays failed; no post hoc normalization changed the score.

Memory-enabled versions of both cases passed. Thus the27B gain is completion and
format reliability under these fixed settings; this run does not demonstrate
better reasoning. If fenced answers were permitted, one of its two measured gains
would disappear. Any future output-policy change must be declared before a fresh
evaluation. Public firstPass counts workflow acceptance, so it is11for the27B
control arm; strict first-pass success is10because that count excludes the fence
failure. This distinction must remain visible rather than treating native
completion as final acceptance.

## Cost and retrieval

| Model/arm | Requests | Native tools | Reported tokens | Median seconds/sample |
| --- | --- | --- | --- | --- |
| 7B disabled | 44 | 22 | 37364 | 10.23 |
| 7B enabled | 36 | 18 | 51416 | 10.84 |
| 27B disabled | 23 | 11 | 25013 | 60.04 |
| 27B enabled | 24 | 12 | 39763 | 81.53 |

Memory used37.6%more reported tokens for7B despite fewer retries/requests, and59.0%
more for27B. These totals include failures; they are not dollar billing or a pure
per-success comparison. On cases both arms passed, tokens rose10.8%for7B (3pairs)
and51.5%for27B (10pairs). Whole-arm serial inference time was123→137seconds for7B
and730→973seconds for27B. Host retrieval itself took0.0163seconds total; added model
context and generation behavior dominate this experiment's overhead.

There were24host retrievals. Gold history was found in20/20eligible retrieval
instances (10unique gold-bearing cases repeated for the two profiles), with56total
retrieved episodes: pooled precision20/56=35.7%. All four empty-history retrievals
returned zero episodes. Empty metric denominators remain null. These measurements
show full recall on a tiny lexical corpus, with substantial non-gold context; they
do not establish semantic retrieval quality or general corpus coverage.

## Verification and allowance

The previously qualified consumer0.5.0+memory.2 wheel remained pinned at SHA256
f428b0b3d0cf0f36c47229fcb4154ce098027de1ac113555bec984042c778eb9,
with the same exact qualified SDK manifest and model profiles. The approved
extension151requests/75tools/133371tokens was recorded before dispatch, raising
cumulative ceilings to1044/389/1264009. Limits stayed4requests/2tools/8192tokens/600s
per sample,192/96/393216for the48sample reservation, with a28800s batch deadline.
Both profiles kept temperature0.2 and max_tokens512.

Offline audit independently reconstructed all48prepared contexts/retrieval results,
re-scored all outcomes, reconciled receipt digests/adapter budgets/tool lifecycle
events/current-source journal joins and known settlements, and rebuilt the summary.
Replay with socket creation, execute_case and recover_case forbidden left every
saved evidence/allowance/summary byte unchanged. These are trusted host receipts,
not independent provider attestation. No live diagnostics, additional cases or
manual retries were dispatched.

Actual new usage was127requests/63native tool calls/153556reported tokens. All48new
claims settled known. Four native tool completions were errors in7B stale controls;
successful lookup journals are counted separately from those failed native calls.
All22historical ledger hashes were unchanged. Cumulative retained usage is
979requests/356tools/1024349tokens, including the same five fully charged historical
unknown reservations. Remaining approved headroom:65requests/33tools/239660tokens.
There were no timeouts and no new unknown reservations. The final receipt finish
reasons were63stop and1length; the known cap failure is retained in the score.

Private raw evidence: reports/retrieval-memory-live-20261016 (the directory keeps
its preparation date). Aggregate audit, closed diagnosis, frozen identities,
authorization and audit scripts: dist/retrieval-memory-live-20261017. Raw prompts,
notes, answers, endpoint configuration and secrets are not copied into that aggregate
collection. The offline implementation qualification remains documented in
retrieval-memory-2026-10-16.md. No experimental source changes occurred in this live
turn, so the new verification is the live evidence audit and immutable replay.

## What is ready, and what remains

The bounded read-only retrieval/context contract now has real model evidence and
is ready for targeted follow-up work. It is not a production or general-memory
qualification. Next priorities are:

1. Fix7B's public field distinction, authoritative-source selection and missing-fact
   abstention, with precise corrective feedback and a fresh evaluation freeze.
2. Qualify output-cap handling and align native parsed-answer acceptance with the
   declared strict wire-format contract. Keep execution failure, formatting failure
   and semantic failure separate in metrics.
3. Test selective retrieval and context reduction before enabling memory routinely.
   Add harder semantic matching, neutral-note/reminder ablations, repeated trials
   and larger held-out sets. One trial per arm on12synthetic cases is an early signal;
   it cannot isolate useful pointers from reminder/priming effects or establish a
   population gain.
4. Treat richer historical outcomes and memory lifecycle as separate milestones.
   These notes mainly expose source pointers; stale cases test old references and
   latest revisions, not an explicitly recalled wrong numeric value or decision.
   This pilot adds no learned memory writes, update/expiry policy, real-history
   ingestion, embedding search, parallel fan-out/join or hosted/production service
   qualification. The checked-in corpus is not autonomous cross-session learning.

Preserve this run as evidence. Any tuning based on these findings turns these cases
into development material and requires fresh held-out cases for the next claim.
