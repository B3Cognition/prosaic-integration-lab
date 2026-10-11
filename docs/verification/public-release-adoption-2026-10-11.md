# Public SDK adoption — 2026-10-11

The five `b3-prosaic` patch distributions are public. Ordered publication used
the original qualified artifacts, with no SDK rebuild or byte substitution.
Actual PyPI and GitHub wheel/sdist downloads match their original receipts;
the normal index consumer checks also passed dependency resolution, import
ownership, existing CLIs, installed payload audits and `pip check`.

| SDK | Exact published source | Successful promotion |
| --- | --- | --- |
| Core 0.4.1 | `6ac6cfdfd47dc70ecf68e441aa004f07c3be3822` | [38116854936](https://github.com/B3Cognition/prosaic/actions/runs/38116854936) |
| Runtime 0.8.1 / recorder 0.2.1 | `3566731c39a3fff2837acd93a96baa2187764206` | [38117263240](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38117263240) |
| Harness 0.7.1 / store 0.2.1 | `cba77d09d1844ff624911295aecd58021b457c08` | [38118430476](https://github.com/B3Cognition/prosaic-harness/actions/runs/38118430476) |

The active `dependencies/releases.json` contains the five actual public wheel
URLs and original source/hash tuples. Its exact SHA256 is
`37a7b0dcf7bffa1c64481aafc7173e947c1e083616adcf50112e53022d589aca`.
The independent active-family regression failed against the previous legacy
manifest and passes against this verified public manifest. The earlier Lab
0.2.0 manifest, original 0.6 baseline, candidate profiles/caches, historical
verification receipts and retained legacy assets remain unchanged.

Lab source version is prepared as 0.3.0. The
[README](../../README.md#try-the-native-workflow) installs the exact public
manifest into a fresh environment, audits its payloads, builds a released-SDK
consumer and drives the native HTTP demo. The
[consumption guide](../consume-native-workflows.md#construct-a-workflow-in-memory)
also provides a runnable public workflow construction example; it validates and
seals an alias-based graph without model, tool or database execution.

## Local public-package checkpoint

A new Python 3.12.14/macOS ARM64 environment installed the unchanged hash-locked
third-party graph and downloaded all five wheels from the actual manifest URLs.
Installed SDK payload audit and `pip check` passed. The active-family regression
and focused gate/CLI checks passed. The complete adopted source suite passed
540 tests, zero failures or skips, with one existing Starlette/httpx deprecation
warning.

The first full run exposed nine stale test fixtures that still supplied the
historical active manifest hash. The production gate correctly rejected them.
The fixture now derives the current manifest digest, while the retagged-candidate
case supplies otherwise valid active labels and must still fail before resource
allocation. Count, lineage, payload and billing-image rejection predicates are
unchanged. Actual legacy-upgrade source `59752bef3e6b3ffde0ecbf38f34815d184043e20`
and baseline hash
`f972db9d828b6ab0ffcf6ca210082e5cbc3b7678f5a1b8f42bbc482b9aafb472`
remain immutable. The original 531-pass / nine-failure log is retained as setup
evidence; the corrected full run is the 540-pass result above.

```sh
python -m pytest tests/unit/test_release_gates.py tests/unit/test_released_provenance.py tests/unit/test_native_gate.py -q
python -m pytest -q
python scripts/audit_install.py --manifest dependencies/releases.json
python -m pip check
```

The final Lab released-package native gate is pending. It must qualify the
final committed source on all four Linux AMD64/ARM64 × PostgreSQL 16/18 cells,
216 cases each / 864 total, zero failures/errors/skips, 32 lane cleanups and four
separate native demo cleanups. Its original run, immutable image/manifest/source
identities, sanitized receipts and publication verification belong in the
Lab 0.3.0 release notes and verification asset after those operations actually
succeed.

The [hardening ledger](hardening-2026-10-10.md) retains candidate run
`38080612477` at source `94f313e49707a09e7d0f3abbf818a9861bd6b14a`, with its
864 cases, 32+4 cleanup checks and synthetic-call results. That evidence remains
specific to its original source; it does not qualify the final public-manifest
adoption. The [CLI preparation ledger](publication-preparation-2026-10-10.md)
similarly retains its original 539-test source checkpoint.

Synthetic fixture success does not qualify real providers, customer billing,
production deployment identity/TLS, HA/PITR or long soak capacity. Private
configuration, raw logs, credentials and backups remain outside public artifacts.
