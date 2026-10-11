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

Lab [0.3.0 is published](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.3.0)
at source `59ea44b97224415e22fec64c2b9bf39bd9503276`. The
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

## Released-package native qualification

[Run 38119573605](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38119573605)
succeeded in released mode at exact source
`59ea44b97224415e22fec64c2b9bf39bd9503276`. All four Linux AMD64/ARM64 ×
PostgreSQL 16/18 cells passed 216 required cases each / 864 total, zero
failures/errors/skips. All 32 lane cleanups and four separate native demo
cleanups were verified. Each cell also passed 540 source tests with one existing
deprecation warning. Each demo independently reconciled two complete synthetic
model calls and remained billing-ineligible.

The original API run/job/artifact records, four safe archives and logs were
retained and checked against the closed payload, count, image, manifest,
baseline, migration and cleanup predicates. Active manifest SHA256 remains
`37a7b0dcf7bffa1c64481aafc7173e947c1e083616adcf50112e53022d589aca`.
The original Lab 0.2.0 upgrade source remains
`59752bef3e6b3ffde0ecbf38f34815d184043e20` with baseline manifest SHA256
`f972db9d828b6ab0ffcf6ca210082e5cbc3b7678f5a1b8f42bbc482b9aafb472`;
all ten legacy-upgrade cases per cell retain the actual schema v2→v3 checks.

| Cell | Original artifact ID | Archive SHA256 | Receipt SHA256 |
| --- | --- | --- | --- |
| ARM64 / PostgreSQL 16 | 11695590636 | `f992ef04a7d494cbaf94719c920c8410ad2d67325b47335affddbe51a53dbe77` | `db1c25990420e0ddbd2c09c3584e82c20dde627182e929fc20d18c54862f3f05` |
| ARM64 / PostgreSQL 18 | 11693874958 | `58238ceb0441e82097ab5cc7f96618e841f78f6a1219e633f8065c9623523f9f` | `8395c4e62bc36b8671ebff117b0dbeef53b35178cdd464deba7c3855c41c3489` |
| AMD64 / PostgreSQL 16 | 11694119624 | `30e0bd1413c8e02604900c22b9d386e6e6f961bf04e11f4a32329a0b7026c3cc` | `35830fec3041cac51a5592f0c2e183d5940c20bbf29a1d67cb828db38256d602` |
| AMD64 / PostgreSQL 18 | 11695130636 | `e6f873a2e791310a2089038c428fde4422405eade01bdf0b65892d93349668ef` | `721c0a980445f93c4ede8ea563c4126f0c8cf8a9aceeb1a3995485aec42b53e0` |

| Cell | Immutable consumer image |
| --- | --- |
| ARM64 / PostgreSQL 16 | `sha256:ba9feb7bc4a2a993fde11d329a2bcf6368d3605e7f11ae01de988b418566fcfc` |
| ARM64 / PostgreSQL 18 | `sha256:4f2f7dc4e32d00a271e16f5dc033d487e2162115efc53c957000d204b66dac15` |
| AMD64 / PostgreSQL 16 | `sha256:e0eda10f23038e9a736879e6ca35da6bac3c3fd0d2946d328cfc2e6c7c7ec77c` |
| AMD64 / PostgreSQL 18 | `sha256:4364ff37b375938056b35e2c26a4193063c8c87b1568d2e426a2c6100f238e40` |

The PostgreSQL 16 cells used
`postgres:16@sha256:ca0bd484cb98bf4b24eb1010e73fb3fcbd6714d240fbc1a10eea5b7dbecb641d`;
PostgreSQL 18 cells used
`postgres:18@sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336`.

## Verified public Lab assets

The remote annotated `v0.3.0` tag dereferences the exact qualified `59ea44b`
source. The public release was published on 2026-10-11. Actual downloaded
assets, original local files and GitHub API digests match:

| Published asset | SHA256 |
| --- | --- |
| [Wheel](https://github.com/B3Cognition/prosaic-integration-lab/releases/download/v0.3.0/prosaic_integration_lab-0.3.0-py3-none-any.whl) | `634a5eaa9d961c80981c1d98c72bcddb2a74def36a58c8e79aead0af7ac0b643` |
| [Source distribution](https://github.com/B3Cognition/prosaic-integration-lab/releases/download/v0.3.0/prosaic_integration_lab-0.3.0.tar.gz) | `805975e6139b8b2e436ee5d4ca4bf65e2eca6a543a5c2404a1c5e8c349dc47a3` |
| [Checksums](https://github.com/B3Cognition/prosaic-integration-lab/releases/download/v0.3.0/SHA256SUMS-0.3.0.txt) | `0f0c81bc69b40b6f65aaebb9174af7e6f0c42620b96ef074624773f958ed8e64` |
| [Verification receipt](https://github.com/B3Cognition/prosaic-integration-lab/releases/download/v0.3.0/VERIFICATION-0.3.0.json) | `d06d396dfed5391296b0047548d00d77862e99a576331d05f65cfe95c33279d3` |

Run `38119573605` and the `v0.3.0` assets qualify source
`59ea44b97224415e22fec64c2b9bf39bd9503276`. This later documentation-only
commit records that evidence; it is not a newly qualified source or rebuilt
release. The source tag and published assets remain unchanged.

The [hardening ledger](hardening-2026-10-10.md) retains candidate run
`38080612477` at source `94f313e49707a09e7d0f3abbf818a9861bd6b14a`, with its
864 cases, 32+4 cleanup checks and synthetic-call results. That evidence remains
specific to its original source; it does not qualify the final public-manifest
adoption. The [CLI preparation ledger](publication-preparation-2026-10-10.md)
similarly retains its original 539-test source checkpoint.

Synthetic fixture success does not qualify real providers, customer billing,
production deployment identity/TLS, HA/PITR or long soak capacity. Private
configuration, raw logs, credentials and backups remain outside public artifacts.
