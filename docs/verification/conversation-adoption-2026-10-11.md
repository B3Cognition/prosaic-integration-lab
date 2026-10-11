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

Pending: rebuilt exact Runtime candidates, installed Harness/controller/store,
functional journey and conservative workflow handoff, owned PostgreSQL/worker
loss/limit/security lanes, Linux AMD64/ARM64 × PostgreSQL 16/18, fresh consumer
wheel/sdist/image audits, optional bounded live opt-in, then public-index adoption.

Docker Desktop is running but its engine socket timed out. No test resources
were allocated/deleted or restart performed. This does not pass acceptance.
