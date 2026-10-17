# Fresh live memory comparison after grounding corrections

All48fresh held-out samples completed and passed the evidence/accounting/replay
audit. The correction was partly successful: the smaller model no longer confused
record IDs with fact labels, and its complete-evidence answers cited the correct
current authority/revision. Missing-fact handling remains unresolved. Do not label
the smaller model fully fixed.

## Paired results

| Model | Memory off | Memory on | Paired outcomes | First-pass strict passes |
| --- | --- | --- | --- | --- |
| Qwen2.5-Coder7B | 8/12 (66.7%) | 9/12 (75%) | 1gain,0losses,8both pass,3both fail | 7 →9 |
| ThinkingCap-Qwen3.8-27B | 12/12 | 12/12 | 12both pass | 12 →12 |

Strict task success was41/48, with7failures, zero unknown outcomes and zero unrun
cases. Full baseline completeness means all outcomes and usage exist. CLIexit1
correctly reflects failed tasks; it does not mean the dispatch failed.

| Family | 7B off →on | 27B off →on |
| --- | --- | --- |
| Relevant history | 1/2 →2/2 | 2/2 →2/2 |
| Stale references | 2/2 →2/2 | 2/2 →2/2 |
| Empty history | 1/2 →1/2 | 2/2 →2/2 |
| Foreign-tenant decoys | 2/2 →2/2 | 2/2 →2/2 |
| Hostile notes | 2/2 →2/2 | 2/2 →2/2 |
| Missing current fact | 0/2 →0/2 | 2/2 →2/2 |

Memory's one7Bgain was relevant-22: both arms fetched/cited the correct current
records, but the control's decision was wrong. Therefore this gain does not
demonstrate better source selection. It is one run-specific decision difference,
with no repeated-trial/population claim. The larger model had no observed gain.

## What improved, and what did not

Across all24smaller-model final responses, there were zero source record IDs in
the facts array and zero JSON/fence failures. All20complete-evidence samples had
correct fact/citation fields and current-source citations. Both stale-reference
cases passed in both arms. These observations support the identifier-contract fix;
they are not proof against future errors or a causal before/after score estimate.

The remaining7smaller-model failures were:

- relevant-22off and no-match-22in both arms: correct current evidence, fact labels
  and citations, but a wrong decision after both attempts.
- missing-21/22in both arms: the model read the available auditor record plus
  observers, and substituted an observer citation for the absent auditor fact.
  Every final answer incorrectly included the absent fact. Three also gave the
  wrong decision; one returned insufficient but still listed/cited observer evidence.

Thus all four missing-evidence samples failed the full grounded contract. A
well-formed fact label is not evidence that its required authority is present.
The fixed explanatory feedback did not repair any of these7failures. Across8
smaller-model retry invocations, one other sample was repaired successfully.
Native public checks rejected these invalid outputs; none became accepted strict
benchmark answers. This is fail-closed protection, not a solved model behavior.

The larger model passed all24samples on its first attempt, including all4missing
samples. It fetched only22records per arm with zero irrelevant reads or duplicate
reads. No cap truncation, fence failure or timeout occurred in this run. The
previous27Bcap/fence defects were not changed; their absence here does not qualify
them as fixed.

## Cost

| Model/arm | Requests | Native tools | Reported tokens | Median seconds |
| --- | --- | --- | --- | --- |
| 7B off | 34 | 17 | 37605 | 9.52 |
| 7B on | 30 | 15 | 51447 | 12.88 |
| 27B off | 24 | 12 | 30573 | 65.06 |
| 27B on | 24 | 12 | 46217 | 93.91 |

Memory increased reported tokens36.8%for7B and51.2%for27B. Tokens include failures
and are not dollar charges. On the8smaller-model pairs both arms passed, tokens
were19967off versus28512on. Whole-arm inference time was118.5→161.6seconds for7B
and778.6→1059.1seconds for27B. These are observed serial local timings, not isolated
hardware-cost estimates.

There were24host retrievals taking0.0223seconds total. Gold recall was20/20retrieval
instances (10unique nonempty-history cases repeated across profiles), with60
episodes returned: pooled gold precision33.3%. All4empty-history queries returned
nothing; their empty denominators remain null. Additional model context dominates
the retrieval overhead. Routine retrieval is not justified for27Bon these cases;
7B's one extra success also carries a substantial token cost.

## Integrity, qualification and accounting

The exact offline-qualified memory.3 wheel remained pinned at SHA256
da3dd355af076e226454b8682817d98d963bf94412bf3b986cc194c9b16d6536.
SDK provenance, model profiles, temperature0.2, response cap512 and per-case caps
4requests/2tools/8192tokens/600s remained unchanged. No experimental code, prose,
case, corpus, grading or response normalization changed during the live run.
Prior offline qualification:1133source tests,64installed runtime tests,48native
fixtures, payload audit and immutable recovery/replay; see memory-grounding-2026-10-17.md.

The development/history freeze preceded fresh case authoring. New cases use new
entities/source IDs, fact labels availability/alarms, values/revisions, index order
and public conditions >=97/<=1. The historical corpus was expanded before freeze.
The original live cases are development evidence. Because case contents, corpus
and conditions differ, the old3/12→7/12 and new8/12→9/12 scores are not a controlled
causal estimate of the corrective implementation. Current within-case memory
on/off comparisons remain paired. Templates and closed grammar remain shared.

The offline audit rebuilt prepared contexts/retrievals, independently re-scored all
48samples, checked receipt digests/adapter budgets/tool events/current-source joins,
verified all48known settlements, and reconstructed the summary. Replay with socket
creation and execute_case/recover_case forbidden left all saved evidence, allowance
and summary bytes unchanged. Evidence is trusted host evidence, not independent
provider attestation. No extra live probes, hidden retries or failure reruns occurred.

Actual new usage:112requests/56tools/165842reported tokens. All56invocation receipts
finished with stop. All23prior ledger hashes remain unchanged, including five
fully charged historical unknown reservations. Cumulative retained usage:
1091requests/412tools/1190191tokens under approved1171/452/1417565. Remaining approved
headroom:80requests/40tools/227374tokens. No new unknown reservations or timeouts.

Private raw evidence: reports/retrieval-memory-grounding-live-20261017. Aggregate
audit, closed component/response diagnosis, authorization, frozen identity and audit
scripts: dist/memory-grounding-live-20261017. The aggregate collection omits raw
prompts, responses, recalled notes, endpoint configuration and secrets.

An intermediate progress message incorrectly inferred a passing first missing-fact
sample from an aggregate count. The message was explicitly corrected after reading
case receipts. The report and audit use the actual failing results throughout.

## Remaining work

The requested correction is incomplete: fact-ID syntax improved, but absence and
authority eligibility still fail for7B. The next justified experiment is a typed
public evidence summary that explicitly distinguishes authoritative current facts,
excluded observer records and absent required facts. It must not supply the private
expected decision or rewrite the model answer. Such a change moves eligibility
work into the consumer and must be labeled honestly in capability claims.

Numeric decision errors and weak correction-following also remain. More historical
context did not solve these. Preserve this run, then use a new development freeze
and fresh evaluation for any further tuning. Repeated/larger trials, selective
retrieval, semantic recall, richer historical outcomes, automatic memory lifecycle,
parallel orchestration and production qualification remain separate work; this
experiment adds none of them. No release, push or integration change was made.
