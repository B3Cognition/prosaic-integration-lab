# Prosaic Castle fresh tests and benchmarks — 2026-10-24

Fresh run started 17:03:59 UTC against unchanged Lab
`8c92bb0dcaff016855acef8c7ae23a53be2e9202` and fork
`e810a016abab7b96b4c905b04314562065d5fed3`. No production code, assertions,
default flags, SDK versions or candidate wheels changed. Memory and SUE remain
independently disabled by default. No live model-service calls were made.

## Fresh test results

| Lane | Result |
| --- | --- |
| Full enabled Lab source suite | 2,107 passed, zero skips; 611.20 s |
| Castle main + fresh-process supervision | 2,558 + 48 passed; 85.62% combined coverage |
| Installed PostgreSQL 16.15 | All 76 named cases passed, zero skips |
| Installed PostgreSQL 18.6 | All 76 named cases passed, zero skips |
| Standalone SUE package/differential suite | All 75 passed |
| Disabled/unavailable boundaries with no Castle or SUE installed | All 105 passed |
| Installed frozen hackathon comparison | All 24 scripted cells passed |
| Normal and network-denied hackathon replay | Zero additional provider requests |

Both owned database fixtures used separate migration/runtime roles and verified
cleanup. The actual lean worker had no Torch, sentence-transformers, spaCy or
SML installed. All four supplied wheel hashes matched the candidate profile;
installed payload verification remained mandatory.

Castle's 12 optional SML skips and 108 slow/stress/benchmark deselections remain
explicit; real SML equivalence is unqualified. Existing Starlette/LanceDB
deprecation warnings remain. The initial standalone SUE invocation from its
package directory failed 63 comparisons because its legacy reference was absent
from the test import path. Supplying the required repository reference resolved
all 75 tests without source or assertion changes. Both logs are retained.

## Retrieval benchmark

The unchanged 36-document/40-query fixture has 10 development and 30 held-out
queries. Each arm uses three cold processes and two warm passes (80 warm search
measurements). Benchmarks ran after this task's test processes finished.
Local embeddings/reranker used the same explicitly cached weights, CPU only,
with network downloads disabled. Search timing excludes subsequent independent
fetch verification, as in the frozen benchmark; it is not end-to-end Harness
or worker-IPC timing.

| Arm | Warm median | Warm p95 | Cold median | Peak RSS |
| --- | ---: | ---: | ---: | ---: |
| Raw scoped LanceDB FTS | 3.40 ms | 3.91 ms | 894.60 ms | 138.70 MiB |
| Scoped FTS provider | 11.82 ms | 13.52 ms | 949.48 ms | 142.78 MiB |
| Opt-in dense profile | 278.43 ms | 300.89 ms | 7,568.63 ms | 3,110.39 MiB |

Provider overhead versus raw FTS is 8.42 ms at the median, including the
unchanged scope/provenance/dedup validation. All functional gates passed, with
zero network/optional-engine import attempts and no source changes during
measurement. Raw FTS ordering remains the default; no recency or rule boosts
were enabled.

Every development and held-out quality metric exactly matches the prior
qualification. Held-out recall@5 is 0.986667 for all three arms. MRR@5 is
1.0/1.0/0.98 and nDCG@5 is 0.986855/0.983644/0.973119 for raw FTS/provider/dense.
This small fixture shows no dense advantage; it does not establish performance
or recall for large corpora or different query distributions.

All three arms return nonempty hits for the unanswerable queries (the frozen
empty-for-unanswerable measure is 0.0). A returned memory record is evidence
to assess, not proof that the question has a supported answer.

## SUE engine and workflow costs

The separately installed pure engine completed 100 warmed dialogues per lens,
all nine lenses: 900 successful scripted dialogues / 6,300 accepted advances.
Median dialogue time was 0.928 ms, p95 0.950 ms; median advance was 0.125 ms.
Peak process RSS was 25.30 MiB. Heavy imports were forbidden and absent;
network and subprocess dispatch were forbidden. Engine identity remained
`bbde4669d1eb069dcb8c72e121cd08be4ca953b349f9243b9e650e0d1b596f0b`.
This one-source mechanics benchmark does not measure semantic review quality.

The initial instrumentation's platform-label helper attempted to launch
`uname` and was rejected by the process audit hook. Replacing only the label
lookup with native `os.uname()` produced the accepted run; the guard remained.
The initial script and failure log are retained.

The separate installed eight-case comparison has these actual fixture costs:

| Strategy | Requests per case | Fixture-reported tokens per case | Median fixture elapsed |
| --- | ---: | ---: | ---: |
| Direct | 1 | 15 | 0.138 s |
| Critic-author | 2 | 30 | 0.216 s |
| SUE + final synthesis | 8 | 120 | 2.188 s |

All three score 8/8 because responses are scripted from host-owned ground truth.
These token values are artificial fixture units, not real-model cost estimates.
Elapsed figures include local orchestration/persistence and were captured while
regressions ran; they are not isolated model throughput measurements. The pure
engine's sub-millisecond time must not be substituted for durable workflow cost.

Live review quality remains unmeasured. A real comparison needs an approved
model/endpoint, secret-managed credentials and a shared request/token allowance;
none was supplied for this run. No inference allowance or old unknown usage
reservation was changed. Native Linux consumer qualification and live transport
parity also remain separate.

## Preserved evidence and reproducibility

Fresh logs, JUnit files, candidate hashes, source identities, raw benchmark
samples, all 24 sample stores/receipts, replay output and benchmark scripts are
retained in `reports/prosaic-castle-retest-20261024T170359Z`, with a SHA-256
manifest. Original evidence remains at
`reports/prosaic-castle-fork-20261024`; its manifest is unchanged:
`307c9488075be138f746afdcb5f10fa004ec87bc5bc2da915e94ad092d431305`.

Commands used prepared installed environments, for example:

```sh
python -m pytest -q tests/unit tests/functional tests/sue_review tests/requirements_review
python -m pytest -q --ignore=tests/test_memory_runtime.py --ignore=tests/test_memory_api_integration.py --cov=cognitive_castle --cov=prosaic_castle --cov-fail-under=0
python scripts/safe_brain_tests.py --timeout 120 tests/test_memory_runtime.py tests/test_memory_api_integration.py -p pytest_cov --cov=cognitive_castle --cov=prosaic_castle --cov-append --cov-fail-under=0
PYTHONPATH=/absolute/fork python -m pytest -q /absolute/fork/packages/sue/tests
python -I -m lab_runner.prosaic_castle_fixture --enable --postgres-version 16 ...
python -I -m lab_runner.prosaic_castle_fixture --enable --postgres-version 18 ...
python -I -m lab_runner.requirements_review_v1 --fixture --output NEW_DIRECTORY
python -I -m lab_runner.requirements_review_v1 --replay --output SAME_DIRECTORY
HF_HOME=/absolute/cached-models HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python benchmarks/memory_provider_bench.py --output NEW_RESULT.json
```

The complete installed qualification command is in the
[user guide](../prosaic-castle.md#maintainer-qualification-command). Raw JSON
records hardware, model/cache identities, configuration and source hashes.
No original Castle changes, push, merge or release was performed.
