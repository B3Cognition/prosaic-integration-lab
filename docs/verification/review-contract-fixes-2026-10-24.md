# Critic contract and canonical SUE guidance — 2026-10-24

Both instruction defects are corrected without changing answer acceptance.
The live critic now completes all eight workflows. SUE remains unqualified on
the tested Qwen 7B profile: all eight workflows still stop on invalid model
responses. Memory and SUE remain independently disabled by default.

## Changes and boundaries

Implementation commit: `50c1b08`, against `c41d770`. New
`lab_runner.requirements_review_v2.build_comparison_workflow` uses the public
RuntimeAdapter to project a critic-specific task. It replaces only the critic's
output schema and instructions with the existing strict feedback contract.
Frozen source text/hashes, issue definitions and host-owned saved inputs remain
unchanged. Final-stage arguments pass through unchanged. The v1 package, source
lock, cases, answer keys, scorer and failed-run evidence remain byte-identical.

SUE now includes the exact static introduction and response-rule blocks from
the pinned canonical `build_turn_prompt`, with the original MIT notice. An
installed-resource differential test verifies those bytes against canonical
source SHA-256
`ba0523c407f0b96d269412c7f02dd371165944cfe044b8143be526022ae05da0`.
The enabled adapter fails closed if that policy hash differs. Its new version
`sue-review-v1.2` also seals the guidance digest into its identity.

This is prompt data, not a copied validator, state machine or model runner.
The pure SUE package, Castle worker, Core, Runtime and Harness implementations
are unchanged. Runtime owns model execution and usage; Harness owns accepted
state, receipts and resume; Lab owns the optional workflow and evaluation.
No SOAR or dense retrieval participates in the review path.

The ASTs of SUE's `fold_accepted`, `checked_advance`, `project_answer` and
independent validator are identical to the baseline. Settings, source/provenance
validation, session ownership and reporting modules are also unchanged. No
field became optional, no fence stripping was added to SUE, no failed answer
was accepted, and no budget, retry or deadline increased.

## Fresh verification

| Lane | Result |
| --- | --- |
| New prompt/negative-response regressions | 12 passed; observed RED first |
| Full enabled Lab source suite | 2,119 passed, zero skips; 612.40 s |
| SDK-only disabled/unavailable boundaries | 105 passed; no Castle/SUE installed |
| Installed v2 wire-contract tests | 4 passed |
| Installed PostgreSQL 16.15 | 76/76 named cases, zero skips |
| Installed PostgreSQL 18.6 | 76/76 named cases, zero skips |
| Corrected installed fixture comparison | 24/24 cells, 88 fixture requests |
| Live saved-state/wire audit | All 40 exchanges joined; network denied |
| Live offline replay | Zero additional requests |
| Independent read-only code review | No actionable findings |

Both database lanes verified cleanup, separate migration/runtime roles and a
genuinely lean worker. The consumer ran on macOS ARM64; PostgreSQL ran in Linux
ARM64 containers. This does not establish native Linux consumer qualification.
The full suite retains one existing Starlette deprecation warning.

The optional SUE CI path trigger and source-test command now include
`tests/requirements_review_v2`. Its existing no-skip check, installed lanes,
architecture matrix and timeout remain intact. This matches the complete
source-test scope executed above; remote CI still requires an authorized push.

Direct and rebuilt-sdist wheels are byte-identical with
`SOURCE_DATE_EPOCH=1792800000`. Qualified Lab wheel SHA-256:
`efc311e12b6abb1f118fae2bcb245ddcf2b7edb1cb31377424c6a8923f2318dd`.
It is a separately hashed unpublished 0.6.0 candidate; do not substitute a
same-version wheel. The old environment/wheels remain intact.

Retained setup diagnostics distinguish test/build mistakes from product
results: the first test driver omitted Harness's required run directory;
initial wheel payloads matched but ZIP timestamps differed; pip skipped a
same-version install before a forced reinstall in the separate environment;
installed admission rejected that stale payload, and directory-reuse admission
preserved its failure receipts. Accepted database outputs are specifically
`pg16-qualified/` and `pg18-qualified/`, not the initial rejected directories.
Assertions and admission checks were retained throughout.

## Fresh Qwen 7B benchmark

The fixed plan repeats the same eight cases and strategy order, with one trial
per cell. Model: `mlx-community--Qwen2.5-Coder-7B-Instruct-4bit`, authenticated
numeric-loopback oMLX, temperature 0.2, maximum output 4,096 tokens and explicit
thinking-disabled request settings. Endpoint settings and credentials were not
modified. Per cell: 30 requests, 65,536 reported tokens, 120 seconds. SUE retains
14 turns, 28 calls and 60 seconds per invocation; each step permits two attempts.

| Strategy | Completed | Strict passes | Requests | Reported tokens | Median elapsed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 8/8 | 5/8 | 8 | 8,439 | 4.04 s |
| Critic-author | 8/8 | 2/8 | 16 | 14,842 | 8.86 s |
| SUE + final synthesis | 0/8 | 0/8 | 16 | 20,196 | 15.01 s |

All **40 physical requests / 43,477 reported tokens** reconcile with Runtime
and Harness evidence. No tools, new unknown reservations, pending samples or
overruns remain. All 24 cells ran; grading happened after inference ended.
Public status/report inspection and offline scoring replay were network-denied.
The independent audit also reconstructed the critic's exact projected wire
arguments and verified SUE's exact canonical instructions and projection.

The critic's eight replies now match the feedback schema; all eight final
reviews were reached. Its 2/8 strict final passes do not demonstrate a quality
benefit over direct review. SUE's 16 attempts all omitted required fields:
15 omitted `addresses`, and one omitted `revision_reason`. Eleven additionally
used Markdown fences, forbidden by SUE's unchanged raw-JSON contract. No SUE
turn or final synthesis was accepted. Diagnostic fence unwrapping classified
the failures only; it did not repair outputs, receipts, scores or accepted state.
SUE's elapsed time therefore measures an aborted workflow, not successful-review
latency. No substantive SUE review-quality comparison is available.

Across the old/new runs, all eight direct prompts are byte-for-byte identical,
and model/profile settings, task hashes, schemas, keys, scorer and order match.
Direct changed from 4/8 to 5/8 strict passes despite unchanged prompts; one
sample per case does not isolate stochastic or cache effects. The local server
was warm, and its prefix-cache state was not reset. Timings are descriptive,
not evidence that unchanged direct execution became faster because of this fix.
Cases are deliberately short and simple, and exact citation matching stays
strict. These numbers do not establish general review quality.

The next useful experiment would test provider-supported constrained generation
through Runtime while retaining the same validators, followed by repeated
held-out comparisons if SUE execution becomes reliable. No such change, prompt
tuning after observing these results, extra model study or timeout increase was
performed. Qwen 27B's earlier 60-second-limit failures remain unresolved; that
profile was not retried here. SOAR cannot substitute for reliable model output.

## Recovery and preserved evidence

Adapter identity changes are intentional. A copied old failed SUE store remains
inspectable with its retained old candidate, with network denied. The corrected
candidate rejects that old binding as `binding_unavailable`, with no request or
state rewrite. Use the matching retained wheel for old-run inspection/resume;
never silently reinterpret old sealed reviews under the new guidance. The
original failed store's file hashes remained unchanged in the compatibility
probe.

All prior evidence stays immutable, including
`reports/castle-sue-qwen-pilot-20261024/` (manifest SHA-256
`4b44c9ba86b83ea03fb33fb25837f564aaff637300c745d5147673e49bcf6354`).
Its two unknown timeout reservations remain charged; this rerun did not reset,
settle or reuse them. Previous Castle test and retrieval archives also remain
unchanged.

Fresh raw logs, RED/GREEN results, wheels/sdist, installed qualification,
fixture/live stores, actual HTTP exchanges without authorization headers,
receipts, frozen operators/plans, comparison, classifications, compatibility
probe and SHA-256 manifest are retained separately in
`reports/castle-sue-contract-fixes-20261024/`.

The small final CI-selector correction and updated documentation are retained
in `reports/castle-sue-contract-fixes-ci-20261024/`, which references the main
archive's manifest rather than modifying it.

Final hygiene removed one redundant trailing blank line from the guidance module
and each new test module. The addendum verifies identical Python ASTs against the
qualified implementation and records the focused regression rerun. The benchmark
and wheel hashes above identify the retained tested candidate before that
whitespace-only cleanup; no benchmark evidence was rewritten.

Commands used the source-test environment and a separate installed candidate:

```sh
python -m pytest -q tests/unit tests/functional tests/sue_review tests/requirements_review tests/requirements_review_v2
SOURCE_DATE_EPOCH=1792800000 python -m build --no-isolation
python -I -m lab_runner.prosaic_castle_fixture --enable --postgres-version 16 ...
python -I -m lab_runner.prosaic_castle_fixture --enable --postgres-version 18 ...
python -I /absolute/new-study/operator.py
python -I /absolute/new-study/operator.py replay
python -I /absolute/new-study/audit.py
python -I /absolute/new-study/compare.py
```

No push, merge, publication, original Castle backport or default enablement.
