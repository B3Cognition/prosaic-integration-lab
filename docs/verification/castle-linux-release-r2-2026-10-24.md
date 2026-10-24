# Castle release candidate r2: reconciled upstream memory

Worker **3.4.2** and adapter **0.1.0** are prepared from Castle source
`ad18037b582148d9b23f82e8c95a416092b42b9f`, including all upstream develop
`9c5ba82` behavior. Memory remains disabled by default. No tag, index upload,
GitHub release or publishing workflow has been created or dispatched.

## Candidate identity and qualification

Use [the r2 seven-wheel manifest](../../dependencies/memory-release-candidates-2026-10-24-r2.json).
Its SHA-256 is `4c3739a2169799f4f255c44eae43d3ae0e7aa5ba89de4f55f20234153cb20977`.
The five public SDK identities/hashes and ordinary default configuration remain
unchanged. Earlier same-version candidates have separate manifests and receipts;
never substitute a different wheel for the selected digest.

[Lab PR #26](https://github.com/B3Cognition/prosaic-integration-lab/pull/26)
records the current native AMD64/ARM64 × PostgreSQL 16/18 run, its exact bundle
download and checksums, four sanitized receipts and final full regression results.
Require all four six-case native cells, zero failures/skips, installed payload
and measured architecture checks, verified cleanup, and all ordinary regression
checks before publication. CI status is evidence only after the run completes.

The [local build record](castle-linux-r2-local-build-2026-10-24.json) records
strict Twine 7 checks and both rebuilt-sdist wheel payload comparisons. Its
worker wheel SHA-256 is
`01f599742c5c3845d1b0d3ad4659fd570618de2fba8fa42a9feebca9637a42fa`;
adapter wheel SHA-256 is
`029fac711dfe8e4a121942ab69a13e7abbd147e3de7dde2f638ecedccfa70cb5`.
Native CI must consume these exact wheel bytes. Select the **CI retained**
source archives and their recorded checksums for publication; local setuptools
sdist compression timestamps can differ while rebuilt wheel payloads match.

Keep original CI ZIPs and extracted packages/receipts in the Lab checkout's
ignored reports directory as well as CI storage. CI retains the native bundle
and receipts for 90 days; the PR records archive digests and expiration dates.
Earlier [6329ecf native qualification](castle-linux-release-2026-10-24.md),
its raw receipts and all historical profiles remain intact.

## Preserved behavior and boundaries

The concurrent upstream feature adds standalone fast-memory recall/remember,
a SQLite sidecar and supervised ingest. Those modules and tests are preserved
unchanged. The Prosaic provider continues using its explicitly prepared scoped
FTS store; enabling it grants no ingest, remember or SUE operation. SUE and SOAR
stay outside provider reads. Raw FTS ranking remains default; recency and dense
retrieval remain separate opt-ins.

CLI resolution preserves `memory`, `brain`, `sue` and `provider`, with lazy
dispatch. The upstream two-process test split isolates resource-supervision
checks from heavy imports retained by the main test process. All tests still
run, coverage is appended and the final six-platform union retains the 85%
gate. Unbuffered logs, JUnit and stack dumps are retained before a CI job timeout.

Local merged verification: **2,510 main + 48 fresh-process supervision tests
passed**, 11 existing platform/SOAR skips, two benchmark deselections and
**85.30%** combined coverage. Adapter **76 passed**, lint/format pass. These are
separate from the required zero-skip native enabled-provider receipts.

The host snapshot workflow uses unchanged public Runtime 0.9.7. Model-facing
`memory_tools()` still requires its explicit Runtime error capability, which
that published version lacks. Dense/live-model, standalone fast-memory quality
and SUE/SOAR certification are outside this provider release qualification.

## Publication handoff

Review both [Castle PR #106](https://github.com/B3Cognition/cognitive-castle/pull/106)
and Lab PR #26 with green checks. Retain the exact CI wheels/sdists, checksums,
license/NOTICE and receipts. Confirm index ownership and Trusted Publisher setup
for both distributions; the existing Castle publishing workflow uploads only
the worker. Obtain explicit publication authorization before tags, GitHub
releases or uploads. The [beginner guide](../castle-quickstart.md) describes
package verification, explicit enablement, imported-source use cases and resume.
