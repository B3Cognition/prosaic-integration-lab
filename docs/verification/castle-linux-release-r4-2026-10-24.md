# Castle r4: split hardening, optional integration and release packaging

Memory remains **disabled by default**. Worker **3.4.2** and adapter **0.1.0**
are unpublished candidates; publication is not authorized by this preparation.

Castle PR #106 is superseded, with its original branch and evidence retained:

1. [#107 shared hardening](https://github.com/B3Cognition/cognitive-castle/pull/107)
   targets develop and preserves standalone Castle modes/SUE/SOAR.
2. [#108 optional provider](https://github.com/B3Cognition/cognitive-castle/pull/108)
   targets #107; default raw FTS, dense/recency explicit, read-only scope/provenance.
3. [#109 release packaging](https://github.com/B3Cognition/cognitive-castle/pull/109)
   targets #108; aligned versions, explicit spaCy model provisioning and complete
   adapter source archives. LanceDB remains a required backend/dependency.

## Exact candidate and preserved evidence

The selected source is `40df257ba7e97422920b83c2d787a784ae6f85fa`. The
[r4 seven-wheel profile](../../dependencies/memory-release-candidates-2026-10-24-r4.json)
is copied byte-for-byte from the locked native build manifest, SHA-256
`239124011fbc4096ac78a7e01460562eb3d0158ff23257f14dc09e9e51cb0aec`.
The five public SDKs, including Runtime 0.9.8, remain unchanged; their manifest
SHA-256 is `36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.
The disabled example remains SHA-256
`f6c789fdb09cb7b7104902622ddbc27a39a07d0906571fde64d2cc62e4c2ed97`.

Retain exactly the [original r4 bundle ZIP](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/40081503610/artifacts/12554938224),
SHA-256 `f2df3ab68b70c034273fb6d0a3fd230701d9decdafbf34167694b8929c18bfd9`.
Its selected worker/adapter publication candidates are:

| Archive | SHA-256 |
| --- | --- |
| `cognitive_castle-3.4.2-py3-none-any.whl` | `a90227b49db26d2c9122e77cd2d6afc900f440d60f4149824c315737b10f1723` |
| `cognitive_castle-3.4.2.tar.gz` | `ff2c42a16a48cc68f57ba13d48b25b6663e0d44444f692f196bd7c866b84106d` |
| `b3_prosaic_memory_castle-0.1.0-py3-none-any.whl` | `a98f05706331614f01126badd51f8c14d03e0dd0f9024dfa0d3b9abb0262c826` |
| `b3_prosaic_memory_castle-0.1.0.tar.gz` | `c86111ea7ab567f0269407f149353fb649d7d2293e2fe920c8b187c0e23087b5` |

R2/r3 original archives, profiles and receipts remain unchanged as historical
candidates; r4 supersedes their publication selection. Do not substitute a
same-version rebuilt archive. Even identical code can yield different ZIP/gzip
bytes; keep the chosen original bytes and digests together.

The Lab build source is CI merge `062c4f4d7ec7a4d6375fa91813f75069d2a4e7aa`,
with parents main `8194f6a0f6e64c6186c8aa129bc759e9e3ef3008` and branch
`776f3112d6fbc30e3a149e13b322135820c94fa6`. All 148 installed Lab package Python
payload files match the current source. Both sdists rebuild their wheel payloads;
all four archives pass strict Twine checks. Build tools are recorded in build.json.

## Verification gates

Final-source native qualification [run 40081503610](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/40081503610)
passed all four Linux AMD64/ARM64 × PostgreSQL 16/18 cells: six cases each,
**24 passed, zero failures/skips, cleanup verified**. The
[independently verified summary](castle-linux-r4-native-2026-10-24.json) binds
exact source/archive lineage, native worker/database architecture, installed
package payloads, frozen snapshots/resume and explicit unavailability. All five
original artifact ZIP digests and 76 worker-dependency hashes per cell were
checked. Raw ZIPs, build bundle, receipts and run metadata are retained in
`reports/castle-pr-split-20261024/native-40081503610`.

The shared-hardening matrix [40080992056](https://github.com/B3Cognition/cognitive-castle/actions/runs/40080992056)
passed all six platform jobs, lint, Version Guard and the unchanged 85% coverage
gate. Native Windows cleared the nineteen fixture failures: UTF-8 data, canonical
paths, actual unchanged permissions, both home variables and legal URI-escaped
filenames. No production code changed for those fixture corrections. Original
Windows RED logs and subsequent GREEN logs remain retained.

Require the matching provider and packaging PR matrices before release. The
original CI stall's exact call remains unproven; current independent process
deadlines/stack/heartbeat logs cover imports, test calls and teardown, preserve
failure exit status and retain diagnostics before the job deadline. Assertions,
test selection, six-platform coverage and the 85% gate are preserved.

Local final root verification: 2516 main + 48 fresh-process supervision tests
passed, 85.31% combined coverage; adapter 76 passed in its tool-capable SDK
test environment. The frozen benchmark's functional/integrity guards passed,
with raw/provider FTS warm p95 4.39/14.09ms and explicit dense 311.40ms. These
synthetic retrieval results do not establish production answer quality.

## SUE and release boundaries

SUE remains in Castle source and does not depend on SOAR. See the source-pinned
[SUE use and Prosaic fit guide](https://github.com/B3Cognition/cognitive-castle/blob/40df257ba7e97422920b83c2d787a784ae6f85fa/docs/prosaic-sue.md).
It is a separate optional advisory review workflow: Castle supplies exact frozen
evidence/pure policy, Runtime owns individual model attempts, Harness owns
accepted state, budgets and resume. It never runs implicitly during memory reads.

Public Runtime 0.9.8 still lacks `custom_tool_errors_v1`; model-tool registration
remains capability-gated. This release qualifies host health/search/fetch and
snapshot/resume, not that separate model-tool path. No package publication,
automatic capture, memory activation or SUE/SOAR quality certification is included.
