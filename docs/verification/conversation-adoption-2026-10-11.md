# Conversation adoption development evidence

Checkpoint: 2026-10-12, branch `codex/conversation-lab`, isolated worktree.
No live model, billing, shared database or publication action performed.

The clean installed release baseline passed 640 unit tests. Its five SDK packages
do not provide conversation support; this is compatibility evidence only.

Commit `050cec2`: authenticated host boundary, separate application quota/creation
schema, explicit provisioning, strict bodies and current grants. Watched failures
preceded implementation; the full baseline suite passed 673 tests with zero
skips and the existing Starlette warning (10.21 seconds).

Commit `3b3fd77`: shared allowance, pure fixed-schedule preflight, exact new-train
candidate curator and deterministic provider fixtures. Watched failures preceded
implementation; the full baseline suite passed 699 tests with zero skips and the
same warning (10.38 seconds).

The independent public phase/SQL relay/worker-control slice and boundary
hardening then passed the full 723-test unit suite, zero skips, the existing
warning (10.49 seconds). It includes the new public config inventory allowlist;
the conversation runner still explicitly refuses incomplete qualification before
engine work. These checks do not establish an installed conversation journey.

Environment: macOS ARM64, Python 3.12.14. Exact command:

```sh
.venv-baseline/bin/python -B -m pytest -q -p no:cacheprovider tests/unit
```

SQLite translation tests are explicitly SQL protocol evidence, not PostgreSQL
locks/grants qualification. HTTP units replace the application host interface;
provider fixture units use external wire requests. No private SDK engine is
patched. Current and historical release manifests/receipts remain unchanged.

Runtime candidate provenance is now verified against immutable source commit
`a59621c5f30d766d1217b37df777d3876075dc34` from the successful
[Publish SDK run 38181785317](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38181785317).
Its original Core dependency was independently downloaded from successful
[run 38077144248](https://github.com/B3Cognition/prosaic/actions/runs/38077144248),
commit `6ac6cfdfd47dc70ecf68e441aa004f07c3be3822`.
The release auditor checked original receipts, upstream wheel bytes, distribution
metadata, wheel/sdist payloads and required qualification records against pristine
Git archives. Runtime has 24 records: nine source, nine installed-wheel, four
PostgreSQL and two dependency-floor checks. All recorded JUnit checks have zero
failures, errors or skips; each PostgreSQL record contains 40 tests. Core has 15
required records. The source lanes explicitly exclude their separate wheel
metadata check; Linux also excludes the macOS-only framework check. Publishing
jobs were skipped: these are qualified candidates, not published releases.

Exact Runtime artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Runtime 0.9.0 wheel | `444460a01af1a439957a42d50cddf2f6be837cda1efb2bc9458251341c52e65d` |
| Runtime 0.9.0 sdist | `3ffd6605ff4d78696117e713db5dcd24d1f4ee21092832ca873e90bc1df53045` |
| Recorder 0.3.0 wheel | `5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca` |
| Recorder 0.3.0 sdist | `d7016ad8df370e6a1bca0c2e4cbfbaed7fed73c6911ce14c3b03192d499c1e2d` |

A separate `.venv-qualified-runtime` installed only these genuine wheels and
Core 0.4.1, with hash-locked third-party dependencies. `pip check` passed.
Before and after the original isolated installed conversation smoke, distribution
ownership, exact installed bytes, import locations and executable cache contents
matched those three wheels. The smoke passed pure preparation, two-turn history
and workspace-free execution with exactly two synthetic loopback requests.
No Harness distribution is installed there. The released five-SDK baseline stays
unchanged. This is upstream Runtime acceptance, not complete Lab adoption.

Local retained evidence: `.superpowers/sdk-candidates/runtime-qualified-summary.json`,
`selected-upstreams.partial.json` (explicitly pending Harness), and the execution
ledger's `qualified-runtime-verification.log`, `qualified-runtime-install.log`
and `qualified-runtime-installed-acceptance.log`. The immutable source scripts
and originals remain in separate candidate directories; local builds and historic
release manifests were not overwritten.

Pending: installed qualified Harness/controller/store,
functional journey and conservative workflow handoff, owned PostgreSQL/worker
loss/limit/security lanes, Linux AMD64/ARM64 × PostgreSQL 16/18, fresh consumer
wheel/sdist/image audits, optional bounded live opt-in, then public-index adoption.

Docker Desktop is running but its engine socket timed out. No test resources
were allocated/deleted or restart performed. This does not pass acceptance.
