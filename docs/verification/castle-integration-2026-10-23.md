# Castle integration PR qualification — 2026-10-23

The integration has been brought onto `main` at
`78cfef46a19bbe49c29f945243e0b690d95fc70d` (merge checkpoint `638075d`).
Memory remains disabled by default. The normal released SDK manifest is
byte-for-byte unchanged from main, SHA256
`fc4eef2c3d32b641a9c6e12cc7b012464132e0cfbf5e87bbc4e848c72b71b95b`:
Core 0.4.1, Runtime 0.9.7, Runtime recorder 0.3.0, Harness 0.9.4 and Harness
Postgres 0.4.0. Host dependencies match the unchanged hash lock, SHA256
`022b22de1b5999ad7037fc3fe5d91981601a87bb1fd55e54a8b96a985df6064d`.

The first five entries of the current
[Castle profile](../../dependencies/memory-candidates.json) are those exact public
SDK artifacts. It additionally selects the original unpublished adapter 0.1.0
and Castle worker 3.4.1 wheels. Profile SHA256:
`c93c82347f2b9cfb143b8fff5c53b5b868056048a86445693d841c233c98363d`.
The initial older profile and its receipts remain preserved separately;
[prior checkpoints](optional-memory-2026-10-23.md) are historical evidence.

## Actual results

Host: macOS/Darwin ARM64, Python 3.12.15. Database and consumer containers:
Linux ARM64. The separate installed Castle worker uses Python 3.11.15. These
results do not qualify Linux AMD64 or claim paid/live model efficacy.

| Check | Result | Evidence |
| --- | --- | --- |
| Complete source unit/functional suite on current public SDKs | **1847 passed**, 0 failures/skips, 509.58s | One existing Starlette/httpx deprecation warning |
| Complete required conversation lane, PostgreSQL 16 | **97 passed**, 0 failures/skips, cleanup verified, 460.57s | [Receipt](castle-integration-2026-10-23-conversation-pg16.json) |
| Complete required conversation lane, PostgreSQL 18 | **97 passed**, 0 failures/skips, cleanup verified, 461.26s | [Receipt](castle-integration-2026-10-23-conversation-pg18.json) |
| Installed Castle memory lane, PostgreSQL 16 | **6 passed**, 0 failures/skips, cleanup verified | [Receipt](castle-integration-2026-10-23-memory-pg16.json) |
| Installed Castle memory lane, PostgreSQL 18 | **6 passed**, 0 failures/skips, cleanup verified | [Receipt](castle-integration-2026-10-23-memory-pg18.json) |
| Installed offline memory consumer image | Build and disabled-default smoke passed | [Receipt](castle-integration-2026-10-23-image.json) |
| Beginner walkthrough | Real worker, frozen original text after source mutation and disabled-provider resume, one local fixture response | [Receipt](castle-integration-2026-10-23-demo.json) |

Both conversation receipts pass the existing `lab_runner.gates.validate` gate,
including its current 97-case count, zero skips, public payload audit and verified
cleanup. They cover all five required conversation files: journey, persistence,
security, recovery and limits. Actual worker kills, lease fencing, repeated
recovery, owner/deployment quotas and native effect journals are included.
The run used the ordinary released-mode builder and runner; no candidate-lineage
or release gate was bypassed. The ordinary image includes no Castle adapter or
worker, and its conversation service runs with memory disabled.

The installed Castle lanes verify complete selected wheel identities/checksums
and Python payloads before allocation. Parent and resume interpreters use `-I`,
pytest source injection is disabled, and the imported Lab is checked against its
installed wheel. Actual scoped snapshots retain exact Unicode/CRLF evidence and
provenance; foreign/incomplete records stay excluded. Resume after source change
and worker shutdown preserves the original bundle and payer with no repeat call.
Optional/required unavailable memory and disabled defaults are exercised on both
File and SQL stores. Database owner/migration and restricted runtime roles remain
separate. Every owned container, volume and network was checked during cleanup.

## Integration adjustments

- Main now contains provider-neutral `lab_runner.memory`. Castle qualification
  is named `lab_runner.castle_memory`; existing memory packages/data are retained.
- The host snapshot workflow grants no model tools. Its relevant Runtime gate
  is `invocation_budgets_v1`; the adapter's separate `memory_tools()` function
  retains its `custom_tool_errors_v1` gate and is not called by this integration.
  Provider scope, digest/revision and provenance checks were not relaxed.
- The normal public build inventory includes the new host provider/workflow
  modules, so disabled deployments do not depend on unlisted source files.
- The [beginner guide](../castle-quickstart.md) provides use cases, exact package
  prerequisites, a runnable synthetic walkthrough, real-palace preparation,
  trusted owner configuration, start/status/resume and troubleshooting. It states
  that capture hooks, public HTTP grants and model memory tools are not automatic.

Independent read-only review found no actionable issue in the disabled path,
namespace preservation, public Runtime boundary, walkthrough cleanup or CLI
commands. The walkthrough and the documented `castle provider prepare` flags
were exercised against the exact installed worker. The latter used an isolated
synthetic home so its Palace lock could not touch an unrelated Castle home.

## Commands and artifacts

The source-test environment had installed public SDKs and locked third-party
dependencies with no installed Lab, as existing source-bootstrap cases require.
The installed-memory environment separately installed the Lab wheel and adapter.
Both environments passed their package/payload checks. Commands ran in the
isolated checkout:

```sh
/private/tmp/prosaic-castle-pr-sdk-env/bin/python -m pytest -q
python scripts/build_consumer.py --manifest dependencies/releases.json --wheel-dir /private/tmp/prosaic-castle-pr-public-wheels --tag prosaic-castle-conversation-pr:638075d
python -m lab_runner test --mode conversation --postgres-version 16 --consumer-image sha256:2c60831266858858514a32335b6e2b0afd40e1debb5730f46077a0d4f0aac44a
python -m lab_runner test --mode conversation --postgres-version 18 --consumer-image sha256:2c60831266858858514a32335b6e2b0afd40e1debb5730f46077a0d4f0aac44a
python -m build --no-isolation
python -I scripts/memory_smoke.py
python -I -m lab_runner.castle_memory --enable --manifest dependencies/memory-candidates.json --artifacts /private/tmp/prosaic-castle-pr-memory-wheels --worker-python /private/tmp/castle-worker-installed/bin/python --postgres-version 16 --output /private/tmp/prosaic-castle-pr-memory-pg16.json
python -I -m lab_runner.castle_memory --enable --manifest dependencies/memory-candidates.json --artifacts /private/tmp/prosaic-castle-pr-memory-wheels --worker-python /private/tmp/castle-worker-installed/bin/python --postgres-version 18 --output /private/tmp/prosaic-castle-pr-memory-pg18.json
python examples/castle_memory_demo.py --enable --worker-python /private/tmp/castle-worker-installed/bin/python --directory /private/tmp/prosaic-castle-pr-walkthrough
python scripts/build_memory_consumer.py --base-image sha256:2c60831266858858514a32335b6e2b0afd40e1debb5730f46077a0d4f0aac44a --manifest dependencies/memory-candidates.json --artifacts /private/tmp/prosaic-castle-pr-memory-wheels --lab-wheel dist/prosaic_integration_lab-0.6.0-py3-none-any.whl --output /private/tmp/prosaic-castle-pr-memory-image.json
```

The tested installed memory image records its exact Lab wheel hash. Source
distribution packaging additionally includes the beginner guide, walkthrough,
operator config and sanitized receipts. Later documentation additions do not
alter the tested Python payload or constitute a published release.

Only sanitized receipts are committed. Raw logs, private run state, DSNs,
credentials and per-stack host configuration remain outside Git. The walkthrough
receipt contains only deliberately synthetic notes.

## Remaining limits

The Castle adapter/worker are still unpublished candidates and require the
qualified wheel bundle; the PR is prepared for review, not package publication.
Memory remains off by default, raw FTS ranking is preserved, recency and dense
retrieval remain explicit opt-ins, and SUE/SOAR stay outside the provider path.
The small example workflow has a 60-second lifetime including review time.
Fresh worker dependency installation, other platforms, live model quality and
automatic coding-tool capture are not newly qualified by these local results.
