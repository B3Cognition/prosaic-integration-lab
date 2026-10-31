# Protected independent review — 2026-10-25

The explicit v4 evaluation workflow captures the source-only review before
advice exists on its execution path. An advice-informed candidate remains a
separate proposal. The canonical final is the captured independent review;
there is no automatic promotion or merging. This protects output ownership,
not the correctness of the initial finding.

Memory and SUE remain independently disabled by default. Existing v1/v2/v3
workflows, canonical SUE, Runtime/Harness SDKs, default dependency pins and the
strict scorer are unchanged. This is a local unpublished Lab candidate, not a
release qualification or a new default review route.

## Boundaries and verification

The source-only projection rejects advice, agent artifacts, foreign source
collections and unexpected input keys before Runtime dispatch. Host criteria
must exactly match the public case-neutral instructions, issue definitions and
schema. Frozen source hashes, local citation ranges, case identity and final
assessment/issue consistency remain mandatory. Capture through the public
Harness API verifies accepted stored evidence and records task, source, review,
run and receipt identities. The trusted consumer must authorize access to the
run; a digest or successful capture is not tenant authorization or truth proof.

`IndependentReview` owns immutable serialized bytes; exported dictionaries and
candidates cannot change its final. Candidate validation never changes citations
or infers findings from the host answer key. Invalid output consumes the existing
two-attempt ceiling and remains failed. Restore/resume of an accepted independent
run dispatches zero additional requests. Candidate failures retain that result.

Tests:25 v4/v3 candidate checks,14 installed v4 checks,10 study checks, and the
full default Lab suite: 2,033 pass (one existing Starlette deprecation warning).
Watched failing tests and failed setup logs are retained. Direct wheel and
sdist-rebuilt wheel have221 identical member payloads, with189 installed Python
payloads checked against source. No previous environment was modified.

Review found and fixed shared deadline enforcement during cells, unknown/pending
wire reporting, completed/in-budget pass accounting, and allowance source freeze.
Three new regression tests failed before the fixes and pass afterward. Shared
and per-cell Runtime budgets enclose every dispatch, in addition to the durable
benchmark allowance. Unknown completions retain the full cell reservation and
stop further dispatch.

## Controlled comparison

138 scheduled cells, three descriptive repeats. All eight original cases receive
a source-only independent and unchanged v3 critic/author baseline per repeat
(24+24). Cases04/07/08 receive90 paired advisory candidates: weak/strong trusted
instruction placement crossed with none, previous-raw, previous-compact,
latest-raw and latest-compact saved SUE advice. Every candidate for a case/repeat
shares the exact same accepted independent output. Rotated order reduces simple
order confounding; three repeats do not establish statistical significance.

Weak places fixed candidate guidance in system and public criteria in user.
Strong additionally moves only host-verified criteria/schema/instructions into
system. Source text, title/claim, independent model judgment and SUE advice stay
untrusted user data in both. Raw advice is the archived value unchanged; compact
uses the existing compact projection. No new SUE dialogue is generated. Candidate
costs exclude historical SUE generation and are not end-to-end SUE costs.

The baseline profiles differ in source-only wording/provenance enforcement as
well as critic composition; they are complete workflow comparisons, not a pure
ablation of the critic step. The paired candidate factors do hold their baseline,
task, source/advice bytes, scorer and profile fixed.

Same Qwen `mlx-community--Qwen2.5-Coder-7B-Instruct-4bit`, temperature 0.2,
4096 output ceiling, thinking disabled, streaming off, no tools. Original eight
cases, host keys, strict exact citation scorer and canonical validation remain
unchanged. Per cell: 360 seconds, 30 requests and 65,536 tokens; per call: 60 seconds,
two attempts per step. Shared limits: 720 requests, 1,572,864 tokens, 7,200 seconds
and 138 samples. Measured prompt/input hashes,
execution scripts, selected installed implementations, primary audit script and
the schedule were frozen before the first call. The paired analyzer and archive
sealer are reporting-only additions, included in the final manifest. No prompt
tuning or execution-source changes mid-run.

## Results and decision

All 138 scheduled cells are accounted for: 96 workflows complete, 12 strict-blocked,
30 dependency-failed. The latter are all case 07 candidates: their independent
review failed, so they consume zero provider calls and remain failures. Total
145 physical requests/219,943 reported tokens, zero unknown usage, pending
settlements, overruns, tool calls or audit/replay requests. No fresh SUE generation.

| Baseline, all 8 cases x3 | Completed | Strict passes | Requests | Reported tokens |
| --- | ---: | ---: | ---: | ---: |
| Explicit source-only v4 | 16/24 | 7/24 | 33 | 35,836 |
| Existing v3 critic/author | 20/24 | 14/24 | 52 | 53,187 |

The v4 source-only profile must not replace the existing critic on these results.
Protection is mechanically verified, but it preserves wrong reviews as well as
correct ones. This is a complete profile comparison, not evidence that removing
the critic step alone caused the difference. All existing modes remain unchanged.
The critic also has unresolved failures: false positives on clean case 07, blocked
case 06, and wrong citations on case 08. A relative lead does not certify quality.

Case 04 strict candidate passes, three repeats per cell:

| Saved advice / handoff | Weak boundary | Strong boundary |
| --- | ---: | ---: |
| None | 0/3 | 3/3 |
| Previous SUE, raw | 0/3 | 0/3 |
| Previous SUE, compact | 3/3 | 3/3 |
| Latest SUE, raw | 0/3 | 3/3 |
| Latest SUE, compact | 3/3 | 3/3 |

Strong/no-advice costs 3,719 tokens across its three case 04 candidates, compared
with 5,196 latest-compact, 5,718 previous-compact and 6,969 latest-raw tokens for the
same 3/3 result. Previous-raw costs 14,700 tokens and passes 0/3. Generation of the
saved advice is excluded from those costs. Compact advice recovers this finding
in some weak-boundary conditions, so the data do not support "all SUE advice is
worse." They do not establish added value beyond the cheaper strong/no-advice
candidate, nor identify which removed raw fields caused the observed effect.

Every case 08 candidate identifies the correct contradiction (30/30) but cites
lines 1–3 instead of the unchanged required 1–2 support span: 0/30 strict passes.
Neither stronger instruction roles nor raw/compact advice fixes that citation
failure. Case 07 cannot support a handoff-quality conclusion: all three independent
reviews repeatedly return an empty citations list and fail the unchanged minimum
citation schema. No replacement baseline or answer-key citation is inserted.

Across the 60 executed candidates: 18 strict passes, 60 immutable canonical-final
invariants, and no candidate promotion. Their matched independent reviews all
have incorrect strict results, so canonical scores remain 0/60. Candidate gains
are proposals; reporting them as improved accepted output would be misleading.
The other 30 planned handoffs remain dependency failures, not excluded successes.

For the 30 available weak/strong pairs, strong gains 6 strict passes and loses 0;
six pairs pass both ways and 18 fail both. For the 24 available raw/compact pairs
with advice, compact gains 9 and loses 0; three pass both and 12 fail both.
Raw advice totals 72,147 tokens; compact 43,768, a 39.3% candidate-stage reduction.
Those counts concern cases 04/08 only: clean-control dependencies failed. The
planned denominators are 45 per boundary and 36 per advice representation, with
15/12 dependency failures respectively; they are not new general acceptance rates.

The original end-to-end Qwen comparison still favored critic 5/8 over SUE 3/8 at
about one third of SUE's token cost. An earlier run favored SUE 4/8 over critic 2/8.
This study generates no new SUE dialogue and cannot replace either result with
a fresh SUE-versus-critic score. Evidence supports using the existing critic as
the routine review baseline today, not a general claim that Socratic review is
inferior on every task or model.

Recommended next approach, before adopting a new route:

1. Preserve the existing critic/author review as the canonical baseline, with SUE
   remaining an explicit sidecar. Qualify capture of that exact workflow before
   integration; do not substitute the lower-scoring source-only profile. The v4
   source-only path stays an explicit research option.
2. Prefer verified host criteria in system and source/model advice in user for
   candidate experiments. Start with the strong/no-advice control. If a user
   requests SUE, prefer the tested compact representation and preserve raw advice
   in evidence; do not promote its candidate automatically.
3. Investigate clean-review citation feedback and source-span generation as
   separate issues, with case-neutral public validation. Preserve original keys,
   strict scorer and failed evidence; no range repair or weaker acceptance.
4. Test any revised profile against the exact existing prompt plus held-out clean,
   injection and failure-behavior cases before another default or efficacy decision.
   A prompt/source-profile change needs its own frozen comparison, not a mid-run fix.

These recommendations are not additional implemented changes or release gates
declared passed. No new PostgreSQL/native acceptance matrix was run in this task;
earlier evidence remains intact and no SDK/service-default changes were made.

## How to use the protected path

This API is an explicit Lab evaluation opt-in, with the separately qualified
candidate dependencies recorded in artifacts.json; it does not change service
flags or silently select unpublished SDKs. A trusted consumer builds
`lab_runner.requirements_review_v4.build_independent_workflow(config)`, executes
it through public Harness with only `{"publicTask": task}`, then captures the
accepted result using `IndependentReview.from_harness(task, harness)`.

The consumer can obtain matched advisory prompts with
`candidate_messages(independent, advice, boundary="strong", handoff="compact")`
and execute those through public Runtime with its own explicit bounded policy.
`independent.outcome(candidate)` validates the proposal while returning the
original canonical final plus separate candidate/identity fields. The result has
`candidateAdvisory=true` and `autoApplied=false`. No candidate-selection or human
approval authority is implied. Callers still own authorization and disposition.

## Evidence

The network-denied main audit joins all 145 wire requests to public Runtime turn
evidence or Harness receipts, recomputes strict grades, checks accepted state,
identity/source/projection joins, exact role payloads and known allowance totals.
The separate paired audit recomputes grades and verifies60 dependency/canonical
bindings plus30 zero-call dependency failures. Both dispatch zero requests.

All 11 prior archives/5426 files reverify unchanged, including the original
unknown30request/65536token reservation and its old retained49requests/90345tokens.
Fresh known usage never offsets that reservation. Source freeze includes121
implementation/script files, the original cases/keys/scorer, exact advice inputs,
profile/order and the durable allowance implementation. The archive retains
raw wire replies, invalid attempts, stores, receipts, bindings, snapshots, usage,
tests, failed logs, wheel/sdist artifacts and both audit outputs. Seal facts and
the per-file hashes are recorded in manifest.json; its own hash is recorded in
the committed verification note. No push, merge, release or publication.

## Sealed evidence and commands

Archive: `reports/castle-sue-protected-20261025`,1040 files, manifest SHA256
`d15198cf33cb8467f842e707fd4991a23cf3f62690bf3f883acd52bd0f350d87`.
Local implementation commit: `db8d780`; no push. All 11 prior archives/5426 files
and the original unknown reservation verify unchanged after sealing.

Actual verification commands include `python -m pytest -q` from the Lab checkout
(full default: 2,033), installed `python -m pytest -q test_study.py` (10), and the
source-isolated candidate protection tests (14). Full outputs and watched
failures are retained in the archive's named test logs. From the study root,
`./live-env/bin/python study.py preflight`, `./live-env/bin/python study.py`,
`./live-env/bin/python audit.py` and `./live-env/bin/python inspect_results.py`
produce the frozen execution and two offline audit outputs. `seal.py` verifies
all sources and previous evidence before and after archiving. The environment
itself is excluded; exact candidate wheels/sdist and installed-source snapshots
are retained. The endpoint key is never archived.
