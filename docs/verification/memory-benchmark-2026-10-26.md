# Optional memory benchmark qualification — 2026-10-26

Implemented the explicitly invoked `lab_runner.memory_benchmark` consumer CLI
and [operator documentation](../memory-benchmark.md). Memory and SUE remain off
by default. The canonical requirements review, public HTTP surface, released
dependency manifest and ordinary application capture limits are unchanged.
No package publication or remote push was performed.

## Qualification

Host: macOS ARM64, Python 3.12.15. Execution uses installed public SDK APIs;
no sibling editable SDK or private engine import was added.

| Check | Actual result |
| --- | --- |
| Full unit/functional suite after final snapshot fix | 2,124 passed, 73 passing subtests, one existing Starlette deprecation warning; 490.13 seconds |
| Installed-wheel constrained-generation candidate lane | 27 passed, 36 passing subtests; 26.60 seconds |
| Installed 200-question synthetic fixture, before snapshot fix | 600/600 completed, 600 synthetic requests, zero unknown usage; identical saved replay |
| Real Castle retrieval diagnostic after snapshot fix | 300/300 captures over 100 questions; strict scope/provenance checks |
| Saved real-provider capture roundtrip | All 300 canonical saved captures revalidated with zero model/worker calls or allowance writes; paired Castle ranks/selections identical |
| Snapshot regression | Failed before fix, passed after; changed text/digest rejected |
| Independent snapshot review | Exactly the two intended digest encodings accepted across all 5,040 provenance-key orders; changed provenance rejected |

The full-suite command was `python -B -m pytest -q --durations=10`, with the
SDK-only environment's `bin` directory on PATH for subprocess tests. Installed
candidate tests used `python -I -B -m pytest`, importlib mode and no source-path
injection. Wheel/sdist were built with `python -I -B -m build --no-isolation`;
installed payload identity was checked separately.

Published Core 0.4.1, Runtime 0.9.8 and Harness 0.9.4 qualify the ordinary full
suite. Execution of this new CLI additionally needs Runtime
`0.9.8+jsonschema.2`, wheel SHA256
`0f5a6ab9ffbd150f3b0cbe5aae9e0491ea760ba38816f521f0312318361eb341`.
Published Runtime 0.9.8 lacks `json_schema_v1`; the CLI rejects it. Existing
published-version guards were not weakened. Public-index-only execution remains
blocked until that capability is released and qualified.

Initial socket-permission, candidate-version-guard and wrong-environment
negative-import failures remain preserved with successful unchanged-code
reruns. No PostgreSQL/native Linux matrix was rerun for this private consumer
CLI; these results are not new platform release certification.

## Integrity fixes

Independent review found that pending completion could release a reservation
despite known usage, unsealed resume could accept changed outcomes, and dotted
case IDs were incompatible with allowance IDs. Regressions now cover these.
Pending recovery retains the full reservation; immediate outcome/raw seals,
allowance digest/count reconciliation and exact checkpoint/receipt/output checks
protect resume. Case IDs receive a deterministic allowance-safe representation.

The real-worker attempt exposed a consumer replay defect: Castle hashes its
fixed public wire field order, whereas canonical evidence saving sorts JSON
keys. The verifier now reconstructs that order from independently compared
frozen provenance/text. Scope, revisions, timestamps, digest, exact bytes and
size checks remain intact. The original failed wheel/environment, frozen code,
receipts, terminal seal and replay failure were retained. An additive
compatibility audit verifies those original bytes using the explicitly
identified corrected verifier; it is not a passing model rerun.

## The 100-question study

Before inference, an independent reviewer audited 100 constructed questions
over the existing Prosaic notes/session exports: 90 supported questions and 10
abstention/scope controls, 200 facets and 239 reference attachments (166 distinct
source intervals). Two controls
have notes-only grants; other cases retain the whole eligible corpus. Thirty-five
pre-dispatch question/key amendments corrected unasked requirements and missing
supporting spans. Original inputs/precommits remain preserved. The key never
entered generation, retrieval selection or review packets.

The separate live attempt used the same local Qwen2.5-Coder-7B model, strict
constrained generation, zero tools and a finite shared allowance. It stopped
after two initiated requests:

- File-search output failed exact question-span and exhaustive frame-review
  validation: 1,204 known tokens, no accepted answer.
- Raw Castle's answer request timed out with unknown usage. Its full sample
  reservation of three requests / 98,304 tokens remains held.
- The remaining 298 samples are blocked in the original 300-sample denominator.
  Zero answers or critic revisions were accepted; no critic call occurred.

Actual aggregate tokens are unknown. The known request plus the unknown
reservation retain four requests / 99,508 tokens of capacity; four requests were
not executed. Answer completeness, abstention quality and critic benefit remain
**unmeasured**. No retry or reservation settlement was performed.

A separately frozen, no-inference diagnostic tested source visibility for all
100 questions with the same queries, scope and retrieval limits. Gold was opened
only after captures were sealed.

| Retrieval policy | Exact reference spans visible / 239 | Supported cases with all reference spans visible / 90 |
| --- | ---: | ---: |
| Fixed literal file search and bounded reads | 26 | 9 |
| Raw Castle FTS seeds | 158 | 45 |
| Same Castle seeds plus bounded expansion | 236 | 88 |

These are source visibility measurements, not complete-answer scores. Expansion
exposed 78 additional reference spans with identical raw ranks/selected seeds.
It still missed three full reference attachments across two supported cases and one abstention
control. Exact-span visibility is conservative for long quotations and does
not establish semantic entailment.

The file comparison is materially confounded: 198 of 200 strings contain
multiple words, searched as literal phrases by `rg -i -F` and tokenized by FTS.
The file arm had no source bodies in 88 cases. This cannot establish an advantage
over adaptive agent file search. A future study needs a separately precommitted
balanced query policy. Expansion also reuses searches and a warm provider, so
its elapsed time is not an independent cold-latency comparison.

All three incomplete expanded references have a relevant second-query top hit
left unopened after the first query filled five selections. They concern
historical setup prerequisites, benchmark qualification limits and fork release
setup. File search also exposes a qualification block that strict FTS leaves
incomplete; expansion recovers it. A future bounded allocator should precommit
fair selection across queries before another comparison, keeping raw rankings,
scope and provenance intact. No such after-outcome selection change was made.

## Preservation and remaining limits

Raw sources, keys, outputs, independent assessments, package artifacts, failed
tests and preflight evidence remain private, outside Git. The local study is
`prosaic-memory-benchmark-100-20261026`. Read-only checks bind nine historical
archive copies (22,039 indexed files) and both prior unknown reservations; the
new reservation is separate. A generated bytecode file from importing an older
verification helper was moved into new preflight evidence, then original
indexed bytes/filesets verified unchanged.

Keep SUE experimental and disabled, memory disabled, and packages unpublished.
Before claiming answer gains: correct query fairness in a new study, qualify
Qwen's strict span/frame contract and call lifetime, then obtain accepted paired
answers for independent adjudication. Synthetic throughput and source visibility
do not replace that evidence.
