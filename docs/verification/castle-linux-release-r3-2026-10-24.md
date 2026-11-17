# Castle r3 stack: current public Runtime 0.9.8

Memory remains disabled by default. Worker **3.4.2** and adapter **0.1.0** retain
the exact qualified Castle source `ad18037b582148d9b23f82e8c95a416092b42b9f`.
No package is published by this preparation.

## Current stack and preserved archives

Main advanced through PR #27 to public Runtime 0.9.8 during qualification.
The [r3 seven-wheel profile](../../dependencies/memory-release-candidates-2026-10-24-r3.json)
matches that current public family; its SHA-256 is
`74ff57004d3e43632073184fa2851dfca6fb31257cead8971a43987a8a0020d4`.
It is copied byte-for-byte from the completed native build's manifest.
The public SDK manifest SHA-256 is
`36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.
The default release manifest and disabled memory configuration receive no
Castle enablement or dependency changes from this integration.

Use the wheel folder from [native run 40077572030](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/40077572030)
for the current setup guide. Its Castle worker and adapter wheels are
byte-identical to the selected original r2 release wheels. The new Lab wheel
also includes main's Runtime 0.9.8 adoption; it is separately identified and
does not replace the older Lab/SDK qualification evidence.

The worker/adapter **publication archives remain the original r2 bundle from
run 40074232401**, identified in the [r2 preparation record](castle-linux-release-r2-2026-10-24.md).
Their exact SHA-256 values are:

| Archive | SHA-256 |
| --- | --- |
| `cognitive_castle-3.4.2-py3-none-any.whl` | `01f599742c5c3845d1b0d3ad4659fd570618de2fba8fa42a9feebca9637a42fa` |
| `cognitive_castle-3.4.2.tar.gz` | `1690e263a3dd7c57ae4aabfd94ea717a24e6697c45bc141da0187209c5bf43fb` |
| `b3_prosaic_memory_castle-0.1.0-py3-none-any.whl` | `029fac711dfe8e4a121942ab69a13e7abbd147e3de7dde2f638ecedccfa70cb5` |
| `b3_prosaic_memory_castle-0.1.0.tar.gz` | `6e9974dd12ee4301d93cbb99d31947dbc662df31f315ae19b6b0b341f9efdaac` |

Source-archive compression timestamps can differ across builds. Keep each
original archive and its digest together; do not substitute another same-version
sdist even when its rebuilt wheel payloads match.

## Completed enabled-provider evidence

[The retained r3 native summary](castle-linux-r3-native-2026-10-24.json) records
all four native Linux cells: AMD64 and ARM64, each with PostgreSQL 16 and 18.
Each passed six cases with zero failures, zero skips and verified cleanup.
The receipts verify native host/worker/PostgreSQL architecture, installed Lab
payloads, exact seven-wheel identities, frozen Unicode/CRLF snapshots, restart
after source mutation and worker shutdown, scope/owner checks and optional versus
required unavailability. Each also retains 76 hashed worker dependencies.

The build's Lab CI merge source is
`7c4ce7d08db94672ee41f6f951f15a3a8e255f77`, incorporating main
`8194f6a0f6e64c6186c8aa129bc759e9e3ef3008`. All 136 `lab_runner/` package
payload files were checked against that merged source. All five original
artifact ZIP hashes, extracted bundle and raw receipts are retained in
`reports/castle-native-release-40077572030` in the Lab checkout. Earlier r2
Runtime 0.9.7 receipts, full acceptance results and selected archives remain
separate and unchanged.

The Runtime 0.9.8 full Lab matrix is recorded in
[PR #26](https://github.com/B3Cognition/prosaic-integration-lab/pull/26).
Do not infer completion from a running workflow. The earlier full r2 matrix
passed 1,914 unit/functional tests and 334 real-stack cases per cell against
Runtime 0.9.7; it does not substitute for the newer baseline's full checks.

The complete local source suite against the exact public Runtime 0.9.8 wheel
passed **1,920 tests** with one existing warning in 506.95 seconds. No tests or
assertions were excluded. Its raw log is retained as
`reports/castle-release-local-20261024/castle-lab-runtime098-full.log`.

## Release boundaries and outstanding gate

Raw FTS ranking remains default. Recency and dense retrieval remain explicit
opt-ins; SUE, SOAR and the standalone fast-memory sidecar stay separate from
provider reads. Runtime 0.9.8 still lacks `custom_tool_errors_v1`; the adapter's
model-facing tool gate remains enforced. This qualifies the host snapshot path.

Castle full-CI run `40073959832` timed out its six test jobs in attempt 1.
The bounded Linux 3.12 debug retry in attempt 2 also timed out. No test
diagnostics artifact or test log was recoverable; the retry archive contained
only coverage-job logs and its runner diagnostics. Both archives and timeout
annotations are retained locally. Full Castle CI remains a release-clearance
blocker. Local full and CPU diagnostic runs passed 2,558 tests with 85.30%
coverage, and the earlier tool-capable adapter suite passed 76 tests; these
do not replace the missing platform CI results.

Keep both PRs draft until the required full checks and review clear. Confirm
publisher/index ownership for each distribution before an explicitly authorized
publication; the existing Castle publishing workflow handles only the worker.
The [beginner guide](../castle-quickstart.md) explains actual capture/import,
explicit enablement, frozen review/resume and unavailable-memory behavior.
