# Persistent deployment and upgrades

The owned `qualify-recovery` measurement is documented in
[qualification.md](qualification.md). Durable acknowledged markers, a consistent
logical dump, restored readiness, public receipt/owner/revision/usage checks and
unchanged independent model counts are required. It neither resumes restored
runs nor certifies HA/PITR. Native measurements remain pending on this host.

`lab_runner` owns disposable fixtures and tears them down. A deployed service uses
a separately managed persistent PostgreSQL database and private runtime config;
its lifecycle is independent of the disposable runner. Never point the runner at
a shared or production database. Replicas only validate readiness and use their
restricted roles. They never migrate, restore or receive database-owner secrets.

The application migration CLI is an explicit operator job. Supply its owner DSN
through a secret-managed environment variable, rather than command-line text:

```sh
PYTHONPATH=src .venv/bin/python -m prosaic_integration_lab.migrations \
  --dsn-env SERVICE_MIGRATION_DSN --runtime-role app_runtime
```

Installed consumer wheels do not need the `PYTHONPATH=src` prefix. The CLI emits
only version/count/category diagnostics. Use it with the application's owner
role after provisioning the runtime role; use the libraries' public migration
tools separately for Harness/Runtime storage. `scripts/provision.py` is only the
fresh owned fixture bootstrap. It now delegates application DDL to the same
versioned migration implementation.

The application supports fresh schema creation and v1→v2 upgrade. An advisory
transaction lock serializes operators; shape validation rejects unknown or
incompatible versions before repair. Every DDL/backfill/ledger/grant operation is
one transaction. Identity, idempotency key/hash, request, workflow/assets and
phase are preserved. Runtime credentials cannot update the version ledger.

V1 omitted frozen namespace/environment. For nonempty v1, provide reviewed
per-run scope records from authoritative archived deployment evidence:

```json
[{"run_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","namespace":"archived-deployment","environment":"sandbox"}]
```

```sh
PYTHONPATH=src .venv/bin/python -m prosaic_integration_lab.migrations \
  --dsn-env SERVICE_MIGRATION_DSN --scope-records /private/reviewed-scopes.json \
  --runtime-role app_runtime
```

Coverage must be exact, with no duplicate/extra runs or identity overrides. The
file is bounded to 1 MiB and 10000 records. Missing or ambiguous attribution aborts;
the migrator never derives it from a current request, token or missing receipt.
V2 reruns preserve existing frozen scope and reject a conflicting supplied plan.

Before upgrades: stop/drain write admission, take a protected consistent logical
backup and verify restore into a separate database. Keep original ownership,
role grants, library schema versions and dependency/asset checksums. Do not
remove the source backup until restored HTTP readiness, owner views, revisions,
usage coverage and least-privilege credentials pass. Backup contents include
private prompts/state; use restricted storage and the deployment's encryption
and retention policy, never public test artifacts.

Rollback means restoring the reviewed pre-upgrade backup and compatible pinned
application/library image. There is no destructive v2→v1 downgrade command:
dropping frozen scope would discard authority. A running old image must not write
an incompatible newer schema. If validation fails, keep the database and evidence
intact and resolve the incompatibility before reopening write admission.

Run the owned proof:

```sh
.venv/bin/python -m lab_runner test --candidate --mode persistence --postgres-version 16
.venv/bin/python -m lab_runner test --candidate --mode persistence --postgres-version 18
```

It explicitly upgrades an owned v1 fixture, verifies every original field and
uncertain phase, rejects migration with runtime credentials, runs pg_dump/restore
into a second owned database, then starts a replica against the restored data.
Waiting review/revisions, unknown usage and uncertain starts survive without any
new model call. Approval of a restored waiting run adds no inference. The private
backup is mode 0600 and removed with the owned fixture. This is a logical restore
proof on both majors; deployment-specific HA/PITR/RPO/RTO qualification is separate.
