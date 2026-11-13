# Enabled Castle: native Linux release qualification

The optional **FTS host snapshot provider** passed on native Linux AMD64 and
ARM64 with PostgreSQL 16 and 18. Memory remains disabled by default. Worker
3.4.2 and adapter 0.1.0 are prepared artifacts, not published packages.

## Exact artifacts and results

[Native qualification run 40070773603](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/40070773603)
built the distributions once, then installed the same wheels in all four cells.
The builder used clean exports of Castle commit
`6329ecf4923f18e57795fae5dac87e1fb1c5f3a8` and Lab PR merge commit
`886c0aaad5087379cf8d163ba5da6d1247419b33` (branch head `40a8156`).

| Native Linux | PostgreSQL | Cases | Failures | Skips | Cleanup |
| --- | --- | --- | --- | --- | --- |
| AMD64 | 16.15 | 6 | 0 | 0 | verified |
| AMD64 | 18.6 | 6 | 0 | 0 | verified |
| ARM64 | 16.15 | 6 | 0 | 0 | verified |
| ARM64 | 18.6 | 6 | 0 | 0 | verified |

Each strict gate measures the host and worker interpreters, Docker daemon and
actual pinned PostgreSQL image architecture. Installed Lab, worker, adapter and
public SDK Python payloads match their selected wheels. Public SDK manifest
SHA-256 remains `fc4eef2c3d32b641a9c6e12cc7b012464132e0cfbf5e87bbc4e848c72b71b95b`.

The six cases exercise both File and PostgreSQL stores: exact Unicode/CRLF
snapshots; exclusion of foreign and incomplete records; source mutation and
worker shutdown; fresh-process resume with memory disabled; unchanged frozen
input, owner denial and payer attribution; no duplicate model call; disabled
default; and optional versus required unavailability. The fixture rejects actual
neural/SUE/SOAR imports and Python socket connection attempts, and acceptance
asserts no forbidden-attempt marker. This import/socket instrumentation is not
an OS network sandbox.

## Preserved evidence

- [Summary and five artifact ZIP digests](castle-linux-2026-10-24-summary.json).
- [Exact package builds, source lineage and sdist rebuild comparisons](castle-linux-2026-10-24-build.json).
- [AMD64/PG16 receipt](castle-linux-2026-10-24-amd64-pg16.json),
  [AMD64/PG18 receipt](castle-linux-2026-10-24-amd64-pg18.json),
  [ARM64/PG16 receipt](castle-linux-2026-10-24-arm64-pg16.json),
  [ARM64/PG18 receipt](castle-linux-2026-10-24-arm64-pg18.json).
- [Worker and adapter wheel/sdist checksums](castle-linux-2026-10-24-SHA256SUMS).
- [Selected seven-wheel manifest](../../dependencies/memory-release-candidates-2026-10-24.json),
  identical to the CI bundle manifest (SHA-256
  `c91d99ca1852ad6d7cd39a1cf4c18cdcbd882103e8fb0b525e85fd35c68b9ecf`).
- [Download the exact release bundle](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/40070773603/artifacts/12551630620).
  Its ZIP SHA-256 is
  `759ace1d3fb9dd47332f6fb4aef907362f9e6a158c6d5e44490b4329f0d42933`.

All five original ZIPs were downloaded and checked against GitHub's digests.
Local copies, extracted packages and receipts are retained in the original Lab
checkout under `reports/castle-native-release-40070773603/`. CI artifacts expire
on 2027-01-22; retain these exact bytes before that date. Receipts export resolved
worker dependency versions/archive hashes, counts and resource identities, with
no DSNs, source text or private run state. Historical profiles and evidence are
unchanged. Later documentation/evidence commits do not alter qualified Python
payloads or replace the selected bundle.

## Package and regression preparation

Strict Twine 7 checks passed for both wheels and both sdists. Rebuilding each
sdist produces the same wheel payloads. The adapter sdist includes its tests,
fixtures, examples, smoke script, license and NOTICE. A clean Runtime-only
installed host smoke passed, including the unsupported model-tool gate.

Local merged Castle regression: 2,453 passed, 11 existing platform/SOAR skips,
two benchmark deselections, 85.68% coverage with the existing 85% threshold.
Local full adapter regression: 76 passed against the separately identified
earlier tool-capable Runtime/Harness candidates. Local Lab source regression:
1,912 passed before the final guard/export additions; all 33 focused release
checks pass. These local results are separate from the zero-skip native lane.

Final upstream regression/coverage and default-memory checks are attached to
[Castle PR #106](https://github.com/B3Cognition/cognitive-castle/pull/106) and
[Lab PR #26](https://github.com/B3Cognition/prosaic-integration-lab/pull/26).
Release still requires those checks to be green; this report certifies the
native enabled-provider lane, not every release mode.

## Fixes and scope

The first native build (`40070241829`) exposed missing Linux-only dependencies
in a macOS-generated tooling lock. Universal resolution fixed it while keeping
dependency hashes and public SDK pins enforced. Run `40070338916` then exposed a
qualification-guard false positive: LanceDB probes Torch availability lazily
without importing it. A red-to-green regression distinguishes the probe from
module execution; actual imports are still rejected before their body runs.
All original acceptance assertions remain, including the new forbidden marker
checks. Failed receipts and build artifacts are preserved separately.

Castle regression attempt 1 of `40069833509` stopped reporting test progress
beyond its configured job limits; the six job logs returned missing blobs. It
was canceled and the complete unchanged matrix retried. The available attempt-1
archive contains lint and coverage diagnostics only; no passing result is
inferred for those canceled tests.

Raw FTS ranking remains the default; recency and dense retrieval are opt-in.
SUE, SOAR, legacy model operations, dense/live-model quality and Windows provider
support are outside this qualification. Existing Castle modes remain available.
Public Runtime 0.9.7 supports host snapshots but lacks `custom_tool_errors_v1`
and `ToolExecutionError`; adapter `memory_tools()` correctly refuses it.

Before publication, review both PRs and their full regression checks, select
these exact archives/checksums, verify package-index ownership and Trusted
Publisher setup for both distributions, and explicitly authorize publication.
Castle's existing publishing workflow uploads only the root worker and is not
an artifact-preparation command. No tags, GitHub releases or index uploads were
created by this qualification.
