# Existing critic protection and Qwen qualification — 2026-10-25

The existing critic/author workflow now has explicit canonical-output protection.
SUE is a separate advisory workflow. Memory and SUE remain disabled by default.
The raw-handoff input-limit bug is fixed. Clean-control and semantic citation
failures remain unresolved; the generation experiments are not qualified for
adoption. No scorer, key, schema or assertion was weakened.

## What is protected

Use `build_protected_critic_workflow` from
`lab_runner.requirements_review_v5`, then run a public Harness with only
`{"publicTask": task}`. After successful completion, call
`IndependentReview.from_critic_harness(task, harness)` from
`lab_runner.requirements_review_v4`. This capture verifies real public SDK store
seals, accepted critic/final receipts, dependency bindings, exact task identity
and strict source/case/hash/range provenance. Raw recovery dictionaries cannot
enter this new capture API. The trusted host still owns authorization.

This path preserves existing v3 artifact bodies, schemas, complete workflow
definition, native argument projection and generation settings. Advice and
foreign inputs reject before dispatch; original consistency feedback is retained
and strict provenance checks follow it. It adds no constrained generation or new
evidence guidance to the existing critic. Existing v1–v4 entry points remain
compatible. The separately named `build_canonical_workflow` is the experimental
generation profile and must not be adopted on the current quality evidence.

Only after canonical capture, optional `candidate_messages(canonical, advice,
boundary="strong", handoff="compact")` constructs advisory inputs for public
Runtime under an explicit bounded policy. `canonical.outcome(candidate)` returns
the original final, a separate candidate, candidateAdvisory=true and
autoApplied=false. Unavailable, failed or conflicting advice cannot replace the
canonical result. An incorrect canonical review also stays incorrect; ownership
and source provenance do not certify semantic truth. No automatic promotion.

Core distributes prose; Runtime executes models and enforces invocation budgets;
Harness owns workflow state, bindings, retries and recovery; this Lab consumer
owns review policy, strict evaluation and advisory presentation. SUE and memory
have independent opt-in settings. SOAR is not in this provider/review path.

## Verification of the final protection-only path

- Full default Lab suite:2033 passed, one existing Starlette warning,530.34s.
- Source-isolated installed v3/v4/v5 review suites:43 passed.
- Released Runtime0.9.8/Harness0.9.4 protection fixtures:4 passed, including a
  rejected source-hash attempt, bounded valid retry, retained receipts and
  zero-call resume. No fixture assertion was weakened.
- Network-denied replay:103 recorded Qwen native requests match the original
  projection exactly;55 final validations retain original feedback with zero
  additional provenance rejections. This makes zero new model calls and is NOT
  a fresh live quality qualification of the protection-only wrapper.
- Wheel/sdist build and rebuild pass:223 identical member payloads and191 Python
  payloads matching source; imports resolve from the new installed environment.
  Final wheel SHA256:
  8a15ee898368febc05eb639f35167482faf7283f3c73be1b47a2532a77575e65.

A fresh read-only review found no material issues in the protection-only scope.
It independently replayed the103 requests/55 validations, compared the complete
workflow and rejected12 advice/foreign-input and4 provenance mutations. It did
not judge model quality, earlier experimental code, full-stack qualification,
historical integrity, caller authorization or the SDK seal implementation.
Those limits are not represented as passing release gates.

The full default suite uses the released SDKs and its configured default test
paths. Installed candidate review tests use Runtime0.9.8+jsonschema.2 and the
previously qualified SDK dependencies. No SDK source changes, new PostgreSQL or
native architecture matrix, publication, push, merge or release occurred.

## Same Qwen comparison, two preserved runs

Both runs use mlx-community--Qwen2.5-Coder-7B-Instruct-4bit, temperature0.2,
max4096 output tokens, thinking/streaming off, no tools, the original eight cases,
strict scorer/keys/exact citation spans, three repeats and138 scheduled cells.
Each has24 experimental critic baselines,24 unchanged v3 controls and90 paired
advisory candidates on04/07/08. Boundaries and raw/compact handoffs share the
same captured baseline. Saved SUE advice is reused; no fresh SUE dialogues are
generated and candidate cost excludes their historical generation.

Each cell has360s/30requests/65536tokens; each call60s, two attempts per stage.
Shared ceiling720requests/1572864tokens/7200s. Nested public Runtime budgets and
durable reservations stop unknown usage/overruns. Both completed with zero new
unknowns, pending reservations, tools or overruns. Inputs/scripts/scorer/source
and wheel identities were frozen before dispatch, with no mid-run tuning.

| Run | Experimental passes | Unchanged critic passes | Requests | Tokens |
| --- | ---: | ---: | ---: | ---: |
| First |14/24|13/24|184|308062|
| Revision2 |13/24|11/24|189|363492|

First run:128 completed,4 control-blocked,6 preparation failures. Raw advice
was decoded with the16KB response default despite the256KB input contract.
The original audit failure and separate zero-call preparation reconciliation
are preserved. Revision2 fixes decoding and bounds the composed message at the
original256KB cap; response limits remain16KB. All six affected handoffs now
dispatch and complete. Revision2 has135 completed,3 control-blocked, no
preparation/dependency failures; both frozen offline audits pass.

Revision2 experimental case results:01=3/3,02=0/3,03=0/3,04=3/3,05=0/3,
06=3/3,07=1/3,08=3/3. The embedded-instruction case08 now cites exactly1–2,
and missing-policy case06 cites the required combined span. However, case02
still cites only2–2 instead of1–2; case03 selects the wrong finding category;
case05 invents undefined terms/contradictions; clean07 invents two false defects.
These are strict failures, not repaired outputs or reinterpreted keys.

All90 canonical invariants hold. Matched canonical reviews pass70/90, candidates
63/90:one improvement,eight regressions,81 ties. Saved advice contributes zero
improvements and seven regressions; no-advice candidates account for the other
gain/loss. Strong/no-advice and strong compact old/new advice each pass7/9;
advice uses more tokens. No incremental review-quality benefit is demonstrated.
This does not establish universal SUE inferiority or fresh end-to-end efficacy.

Across36 matched raw/compact pairs, compact gains five strict passes and loses
none, using85270 versus120253 candidate-stage tokens (29.1% fewer). Across45
boundary pairs, stronger boundaries gain two passes and lose one. Three repeats
on eight known cases are descriptive, not significance or held-out qualification.
The experimental baseline combines guidance, source presentation and grammar;
it cannot identify which change causes each semantic effect.

Do not adopt experimental generation changes. The semantic-fix request remains
incomplete. Before another generation change, use a matched grammar-on/off
ablation with unchanged prompts and saved critic context to isolate that effect.
Structured per-finding source roles would require separate design and held-out
qualification. No further prompt tuning or model calls follow the second run.

## Preserved evidence

The two immutable Qwen archives are under the shared Lab reports directory:

- castle-sue-canonical-critic-20261025:1192 files, manifest SHA256
  63e5158e8d55b49b6b3358b3b1efac46dc4e7bdbf01198f3b53bdd8e5176e170.
- castle-sue-canonical-critic-r2-20261025:1184 files, manifest SHA256
  f3fd74871aa602e642de77dbc273632dde7f3adedac741b0ff794fa7a36710f2.

They retain replies, failed attempts, scopes, stores, receipts, frozen snapshots,
resume evidence, reservations, exact advice, preflights, audits, source, wheels
and test logs. A metadata typo stopped one second-run preflight before any
allowance/run/model call; its failure is also retained. Final protection-only
mechanics evidence is sealed separately as castle-sue-protected-existing-20261025.

All14 prior archives/8842 files and the original unknown reservation reverify
unchanged. The original requirements-04--sue unknown reserves30requests and
65536tokens, actual/evidenceDigest remain null; old retained total49requests/
90345tokens is never offset by new known usage. Historical environments/wheels
are untouched. Memory and SUE defaults remain off.

Final local code commit:02a8007. The protection-only archive froze the source
bytes before this commit, with base HEAD a894d90; its frozen-source map and
installed wheel identify the final tested code. No archive was edited to replace
that historical HEAD. Final archive:190 files, manifest SHA256
`e4320e6945220ee1115f3a188347b2ac3801841fd91087ab69647f999a9b23e5`.

[Final mechanics archive](/Users/michalbachorik/work/prosaics/prosaic-integration-lab/reports/castle-sue-protected-existing-20261025/manifest.json),
[first Qwen run](/Users/michalbachorik/work/prosaics/prosaic-integration-lab/reports/castle-sue-canonical-critic-20261025/verification.md),
[second Qwen run](/Users/michalbachorik/work/prosaics/prosaic-integration-lab/reports/castle-sue-canonical-critic-r2-20261025/verification.md).

