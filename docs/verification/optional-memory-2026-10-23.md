# Optional memory integration — 2026-10-23

The optional Castle provider is wired through the Lab's host-owned
`Execution.memory` and `memory_session` boundary. It defaults to disabled and
uses a separate explicit qualification runner and operator CLI. No HTTP grants,
Core change, SUE or SOAR integration is added. FTS remains the default without
recency reordering; dense retrieval and recency are opt-in host settings.

Work is isolated on `codex/optional-castle-memory`, from committed Lab baseline
`dc473da`. The original Lab checkout's unrelated pending changes and the normal
`dependencies/releases.json` remain untouched. The exact candidate family is
[initial memory profile](../../dependencies/memory-candidates-2026-10-23-initial.json), SHA256
`76bb942041292dcee640a314c38f185c94424ec2cdd9b54e1a81f59f8b999812`.
Candidate Runtime/adapter/Castle packages are not published releases.

## Actual end-to-end evidence

Host: Python 3.12.15, macOS/Darwin ARM64. Host SDKs and Castle worker were
installed from the exact selected wheels in separate environments, without
editable sibling imports. The final lanes used the unchanged hash-locked
third-party host graph, SHA256
`022b22de1b5999ad7037fc3fe5d91981601a87bb1fd55e54a8b96a985df6064d`;
installed versions and every installed Lab Python payload were checked against
the lock and tested Lab wheel. `pip check` passed. Worker setup uses synthetic
four-dimensional zero embeddings with offline flags; no embedding model was
downloaded or executed.

| Lane | Actual result | Receipt |
| --- | --- | --- |
| PostgreSQL 16.15, Linux ARM64 database | 6 passed, 0 failures/skips, cleanup verified | [PG16](optional-memory-2026-10-23-pg16.json) |
| PostgreSQL 18.6, Linux ARM64 database | 6 passed, 0 failures/skips, cleanup verified | [PG18](optional-memory-2026-10-23-pg18.json) |
| Offline installed Linux ARM64 consumer | Build and disabled smoke passed | [Image](optional-memory-2026-10-23-image.json) |

Each database lane covers FileRunStore and PostgresRunStore and actual Runtime
Postgres metering with a separate restricted runtime role. It starts a real
installed Castle worker, freezes the exact original Unicode/CRLF text and
provenance, excludes foreign and incomplete records, and pauses with zero model
calls. It then closes/reaps the worker, changes the source and resumes from a
new interpreter with memory disabled. The frozen input stays identical, the
model receives the original evidence only as user data, and one metered call
retains the original payer. Repeated resume makes no additional model call;
another actor is denied. Optional unavailability allows explicit degraded
execution, required unavailability creates no run, and default disabled status
remains explicit.

The parent acceptance interpreter and resume subprocess use `-I`; pytest's
source-path injection is disabled and the parent asserts that the imported Lab
is its installed wheel. Receipts export only closed status/counts, selected
artifact hashes and owned resource metadata. No DSNs, source text, saved state
or raw failure logs are committed. Containers bind loopback, use private tmpfs
storage, and are removed only after exact owner/resource label validation.

The image build uses the immutable cached base in its receipt, no index/network,
the complete six host wheels and the Lab wheel. Castle stays outside the image.
Installed smoke runs non-root, with no network, a read-only root and all
capabilities dropped, and fails if disabled memory imports an adapter/neural
package or starts a process. This validates an offline overlay, not fresh Linux
dependency resolution or a full Linux Castle workflow. The tested Lab wheel
SHA256 is recorded in the image receipt; later documentation/sdist packaging
does not represent a new published release.

## Commands

The temporary host environment was `/private/tmp/prosaic-lab-memory-env`; the
source-test environment `/private/tmp/prosaic-lab-memory-sdk-env` had the same
selected SDK/locked dependencies with the Lab package absent, as existing tests
require. Commands ran in the isolated Lab checkout:

```sh
python -m build --no-isolation
python -m pip install --no-deps --force-reinstall dist/prosaic_integration_lab-0.5.0-py3-none-any.whl
python -I scripts/memory_smoke.py
python -I -m lab_runner.memory --enable --manifest dependencies/memory-candidates.json --artifacts /private/tmp/prosaic-lab-memory-wheelhouse --worker-python /private/tmp/castle-worker-installed/bin/python --postgres-version 16 --output /private/tmp/prosaic-memory-pg16-locked.json
python -I -m lab_runner.memory --enable --manifest dependencies/memory-candidates.json --artifacts /private/tmp/prosaic-lab-memory-wheelhouse --worker-python /private/tmp/castle-worker-installed/bin/python --postgres-version 18 --output /private/tmp/prosaic-memory-pg18-locked.json
python scripts/build_memory_consumer.py --base-image sha256:1717e6cc482d088b172c2e6bfce38fb580ca7fb1b7ef494a2caa2a8fdf09ace6 --manifest dependencies/memory-candidates.json --artifacts /private/tmp/prosaic-lab-memory-wheelhouse --lab-wheel dist/prosaic_integration_lab-0.5.0-py3-none-any.whl --output /private/tmp/prosaic-memory-image-verified.json
python -m pip check
```

## Review and limits

Follow-up: the [conversation contract investigation](conversation-contracts-2026-10-23.md)
records the resolution of the two failures below and the subsequent memory rerun.
The original checkpoint and receipts remain historical evidence for `966c231`.

The final full suite against the pinned host graph finished **963 passed,
2 failed, 0 skipped**, with one existing Starlette/httpx deprecation warning.
All 17 added memory unit/functional cases passed. The suite is not fully green:

- `test_simulated_tool_text_blocks_confirmation_without_effect_or_retry`
  expects `evidence/conformanceFailed`; the selected candidate SDK returns
  `reply/interrupted`.
- `test_public_approval_phase_failure_retains_real_journal_and_never_resumes[after-effect]`
  expects the prior conversation phase to be `needsResolution`; it is absent.

Both failures reproduce on an untouched archive of `dc473da`, using the same
exact candidate SDKs and pinned dependency environment (2 failures in 5.99s).
No upstream SDK or unrelated conversation changes were made. The full run
command was `/private/tmp/prosaic-lab-memory-sdk-env/bin/python -m pytest -q`;
the same two node IDs were rerun from the baseline archive. These are existing
candidate compatibility failures, not evidence for declaring the whole Lab
release-ready.

Independent review found two verification gaps: fresh-process resume could
inherit source imports, and the image builder accepted incomplete manifests.
Both were corrected; incomplete family and wheel/version mismatch cases fail
before build allocation. Cleanup also recovers a lost create outcome using the
fixture's unique labels and refuses a mismatched resource label.

The workflow is a bounded synthetic example: its 60-second wall-clock lifetime
includes review time. Longer operator review needs an explicit production
policy. This is host API/CLI qualification, without a new public HTTP feature,
live model/provider certification, AMD64 coverage or released SDK promotion.
See the [operator guide](../optional-memory.md) for configuration and ownership.
