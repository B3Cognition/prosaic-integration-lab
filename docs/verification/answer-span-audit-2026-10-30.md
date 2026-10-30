# Optional answer-span audit verification — 2026-10-30

The audit is an explicit, experimental, audit-only consumer workflow. Memory
and SUE remain disabled by default. Original answers, Castle retrieval, the
strict scorer, protected critic and existing completeness profile are unchanged.
No live inference, repair, push or publication was performed.

## Test matrix

| Lane | Environment | Result |
|---|---|---|
| Original Lab unit/functional suite | macOS ARM64, Python 3.12.15, released Runtime 0.9.8, Harness 0.9.4, SDK-only | 2033 passed; one upstream Starlette deprecation warning |
| Memory, benchmark, audit and protected critic | macOS ARM64, Python 3.12.15, frozen Runtime 0.9.8+jsonschema.3, Harness 0.9.4 | 368 passed; 109 subtests passed |
| Installed wheel | Fresh isolated macOS ARM64 environment, same frozen candidate SDKs | All four synthetic fixture cases passed |
| Offline consumer-image wheel overlay | Linux ARM64, immutable cached base and verified wheel inputs, network disabled | All four synthetic fixture cases passed; installed payloads matched all eight wheels |

The core deliberately rejects unqualified candidate SDKs, so the two profiles
are separate. Collection proves their executed union covers all 2291 default
tests and includes 2391 unique tests with the explicit extension lanes. These
counts are not the sum of the two rows: ten tests overlap.

The original suite's file list is the `test_*.py` files from
`git ls-tree -r --name-only f6673f3b761842f17fa78129c748dddde27485cb tests/unit tests/functional`,
run with `.venv-public/bin/python -m pytest -q`. The complete list and executed
command are retained in `execution/coverage-matrix.json` and the core log.
The candidate command was:

```sh
.venv/bin/python -m pytest -q \
  tests/memory_benchmark_candidate tests/unit/test_mb* \
  tests/unit/test_memory_benchmark* tests/unit/test_memory_span_audit* \
  tests/unit/test_memory_workflow.py tests/unit/test_memory_provider.py \
  tests/requirements_review_v5 \
  --basetemp .superpowers/sdd/2026-10-30-castle-answer-span-audit/candidate-final-complete-fixtures
```

## Review fixes and controls

A fresh independent review identified four Important issues. Six parametrized
regression controls failed before the fixes; all now pass:

- A limitation-only claim cannot establish factual coverage.
- A positive claim verdict must cover the complete non-whitespace text. Several
  exact spans are allowed, while adverse findings may identify an offending clause.
- A resolved status recommendation must agree with the audit's own judgments.
- Frozen provenance binds installed Runtime/Harness payload digests as well as
  versions; same-version replacement rejects resume without dispatch.

Additional controls cover explicit conflict disclosure, correct abstention,
wrong selected citations, adverse mixed claims, exact Unicode/CRLF addresses,
scope and body boundaries, immutable inputs, capped output, strict rejection of
untrusted source/ledger instructions as host authority, and zero tools/retries.
No existing assertion was weakened. The Auth0 test fixture now constructs its
excessive expiration at execution, preventing collection-time drift during the
long suite; the rejection assertion and authentication product code are unchanged.

The four installed-wheel/image cases were:

| Case | Outcome | Synthetic requests | Held synthetic allowance | Resume requests |
|---|---|---:|---:|---:|
| Omitted condition | findings | 2 | 0 | 0 |
| Complete answer | clear | 2 | 0 | 0 |
| Unavailable context with correct abstention | clear | 2 | 0 | 0 |
| Unknown usage | unresolved | 1 | 65536 | 0 |

The original answer remained unchanged in every case. All real model-call
counts were zero. Prior unknown live invocations were neither retried nor settled.

## Packaging and preservation

Build command: `.venv/bin/python -m build --no-isolation --outdir <fresh private artifact directory>`.
Every wheel production payload is compared with source and the source archive.
Relative to the sealed tested baseline, there are three added audit modules and
one modified production module, the explicit benchmark CLI dispatcher. All 237
other preexisting production payloads are byte-identical, including scoring,
protected critic, application defaults and earlier completeness behavior.
Private run evidence is excluded from the distributions.

Private evidence is retained in the new `castle-answer-span-audit-20261030`
pilot archive, with exact-file manifest/seal, source recovery patch, original
and rebuilt distributions, review and RED/GREEN logs, raw native fixture receipts,
coverage proof and installed-wheel/image evidence. It also records the rehash of
29 historical durable archives and all 13 held historical reservations. Earlier
sealed archives were not modified. Package checksums are in each artifact
directory's `package-proof.json`; the final manifest pins all archived bytes.

## Limits and next gate

This is fixture qualification of the audit workflow, not live-provider or
PostgreSQL qualification. This task did not run AMD64 or PostgreSQL 16/18 lanes.
Exact spans establish attachment and consistent dispositions; they cannot prove
semantic entailment, exhaustive obligations, paraphrase quality or real-model
injection resistance. Overlapping question spans still need semantic evaluation.

Live serving health and the disputed q022 labels remain unresolved gates. Before
a live comparison, independently adjudicate the labels, qualify recovered serving,
and predeclare cases, repeats, shared budgets and stopping rules. Keep the same
strict scorer and fixed denominators, and report misses, false alarms, invalid
or unresolved runs, cost and held reservations. Any repair stage needs its own
design and comparison. The current audit makes no answer-improvement claim.

See [usage and boundaries](../answer-span-audit.md).
