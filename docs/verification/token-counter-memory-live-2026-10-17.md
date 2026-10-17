# Qualified counters and fresh memory comparison

The 48-sample comparison completed and passed independent receipt, allowance,
integrity and network-disabled replay checks. Existing limits stayed unchanged.
Typed evidence improved observed strict success; recall supplied no observed
success gain. The next justified milestone is **scoped, budget-aware retrieval
and context assembly**, with traceable admission and failure outcomes.

## Results

Each cell contains six fresh cases, one per relevant, stale, empty-history,
tenant-decoy, hostile-history and missing-current-fact family.

| Profile | Evidence | Memory off | Memory on |
| --- | --- | --- | --- |
| Qwen2.5-Coder 7B | Raw records | 2/6 | 2/6 |
| Qwen2.5-Coder 7B | Typed evidence | 4/6 | 3/6 |
| ThinkingCap-Qwen3.8 27B | Raw records | 6/6 | 5/6 |
| ThinkingCap-Qwen3.8 27B | Typed evidence | 6/6 | 6/6 |

Raw success was 15/24; typed success was 19/24. Across formats/models, memory
off passed 18/24 and memory on passed 16/24. There were no enabled-only paired
successes and two disabled-only successes. These are observations on this run,
not population estimates or isolated format/memory causal effects.

For the smaller profile, typed evidence corrected the relevant-history case
in both arms and the missing-fact case without recall. With recall, its initial
missing-fact answer still approved despite an absent required fact. Its retry
could not finish within admission limits. Both stale and hostile cases continued
to fail. Every smaller-profile strict pass was a first-pass success; completed
corrections did not add strict passes. Three correction continuations were
denied, so their hypothetical corrected final answers were never observed.

The larger profile's raw missing-fact/memory-on sample reached the unchanged
512-token output limit before producing a usable tool call. This was known usage,
not an author timeout or unknown request. All twelve larger typed samples passed.
Two raw lookup attempts in the smaller relevant-history control returned tool
errors. Receipts establish unsuccessful execution; they do not expose enough
error detail to assign a more specific cause.

## Retrieval is the next architectural gap

The host retrieved 4/5 intended historical episodes among 15 returned episodes:
recall 0.8, precision 4/15. The stale case missed its intended episode. The hostile
archive episode was returned in **all five populated-tenant cases**, not only
the hostile family. Current entity/task words and instruction-rich note text
therefore do not provide sufficient relevance isolation in this lexical design.
Foreign-tenant episodes were excluded in every condition.

The no-match case uses an empty tenant. It establishes empty-history behavior,
not rejection of irrelevant history within a populated tenant. Its initial
arguments and outcomes matched across memory arms for both models/formats.
All four enabled conditions per case retrieved identical episodes. Families
do not isolate hostile-note effects because exposure spans all populated cases.

Recall consumed 113,500 reported tokens versus 77,821 without recall across the
same number of samples. These totals include failures and denied continuations;
they are not billing estimates or success-adjusted efficiency measurements.

## Bounds and independent verification

The frozen study used both original profiles/settings, max output 512 and case
caps of 4 provider requests / 2 native tools / 8,192 reported tokens / 600 seconds.
No model-specific implementation changes or evaluation tuning followed the freeze.

| Accounting | Requests | Native tools | Reported/charged tokens |
| --- | --- | --- | --- |
| Fresh comparison actual | 118 | 60 | 191,321 |
| Cumulative charged, including all prior reservations | 1,363 | 547 | 1,621,526 |
| Existing cumulative ceiling | 1,475 | 604 | 1,976,623 |
| Remaining allowance | 112 | 57 | 355,097 |

All 48 comparison claims are known and within caps, with no overruns. Three
smaller typed continuations were denied before HTTP. Stale and hostile enabled
cases each had 6,252 tokens settled, with a proposed 2,144-input + 512-output
reservation: 8,908 exceeds 8,192. The missing enabled case had 6,034 settled plus
2,057 + 512: 8,603 exceeds 8,192. These are failed tasks with successful budget
enforcement. Denied counter traces are separate from dispatched request counts.

Seven older/qualification unknown reservations remain fully charged. This
includes the qualification operator's missing-working-directory error. The
historic known overrun and its supplemental charge remain unchanged.

Every receipt's qualified counter descriptor, SDK attempt totals, provider/tool
events, source journal, answer score and allowance digest were reconciled.
Counter traces matched 118 dispatched requests plus three denied proposals;
grouped input bounds covered each receipt's reported prompt total. No per-request
live study usage claim is made from aggregate receipts. Counter development
qualification and its narrower live coverage are documented separately in
[token counter qualification](token-counter-qualification-2026-10-17.md).

Both complete reports replayed byte-identically with sockets, provider execution
and receipt recovery disabled. Post-run checks matched all 109 installed Lab
payload files to the reviewed wheel/source and retained tokenizer, serving and
profile guards. All 27 pre-existing historical ledger hashes were unchanged.
The full source suite passed 1,229 tests, installed SDK payload verification
matched 138 files, and the installed memory smoke passed eight native fixtures.

Audited results: [machine-readable report](data/token-counter-memory-live-2026-10-17.json)
and [retrieval exposure checks](data/token-counter-memory-exposure-2026-10-17.json).
The reviewed executable source is `f6a18ad`, Lab `0.5.1+counter.2`; its wheel SHA256
is `06fb441b0c8b7c70b3a84291af5b72d36ae42f8648d36645cbd7aa2ef73917b7`.
Runtime remains the previously qualified `0.9.7+budget.3` candidate.

## Readiness and next milestone

Ready to proceed with a bounded **retrieval/context assembly** milestone. The
provider-neutral Runtime counter contract and failure accounting are adequate
for the frozen local registrations. Memory should remain opt-in, and invalid
model answers must continue to fail validation. This run does not establish
autonomous memory-write or general deployment readiness.

The next milestone should qualify trusted scope/relevance metadata, source
freshness and current-evidence priority; keep instruction text from dominating
retrieval relevance; and allocate optional recall within full tool/retry budget
headroom. Record exclusions, admission decisions, per-request usage and tool
failure categories in a portable trajectory trace. Keep execution/admission in
Runtime, orchestration in Harness/consumers and memory policy in the application
or Lab reference. Core remains a Markdown distribution engine.

Acceptance should include populated-tenant irrelevant-history cases, isolated
hostile-note cases, stale-source invalidation, oversized recall, denied retries
and crash/replay tests. Freeze policy before a new held-out comparison. Qualify
additional serving providers independently. No further model prompt tuning or
larger limits are justified by this evidence.

This follows the [roadmap's](https://www.kdnuggets.com/the-roadmap-to-mastering-agentic-ai-systems-in-2026)
dynamic-context, episodic-memory and trajectory-observability gaps. Persistent
memory writes/expiry and richer semantic retrieval remain later open work.

The implementation/history freeze preceded current-case authoring, but the author
knows the synthetic answers. Raw then typed formats ran sequentially; one case per
family, shared hostile exposure, stochastic/provider state and aggregate receipt
usage limit generalization. Other providers/templates require their own counter
qualification. Private evidence and five canonical allowance copies are retained
beside prior studies; their 32 historical ledgers independently sum to the
cumulative charge above. No push or release is included.
