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

The application supports fresh schema v3 creation and explicit v1/v2→v3 upgrade. An advisory
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
V2/v3 reruns preserve existing frozen scope and reject a conflicting supplied plan.

V3 adds immutable owned proposals, native run references and an application-owned
business operation journal. The legacy `runs` fields and YAML request hash remain
unchanged. The migration validates the archived v1/v2 physical contract first,
adds v3 tables and restricted grants, and advances the version last in the same
transaction. Native references use a composite proposal/tenant/actor foreign key.
Runtime roles receive SELECT/INSERT on proposals and native references, with no
UPDATE/DELETE privileges. Journal updates are limited to state and outcome;
signatures and claim tokens are immutable. Readiness rejects broader mutation or
schema creation grants.

`ProposalStore` records exact canonical UTF-8 proposal TEXT and the public SDK
reference. Owner/key/body replay returns the original row before new retention
checks, including after a host bundle upgrade. The internal `policy_digest`
column stores the public reference's `bundleIdentity`: it identifies the whole
immutable admission/binding bundle, which includes policy, rather than a separate
policy-only projection. Current host authorization and revocation are independent.
Proposal transport is bounded to 65536 raw/canonical bytes, depth 64 and 65536
expanded nodes; duplicate keys, nonfinite numbers and invalid Unicode fail with
`invalid_request`. Harness alone admits graph/schema/tool semantics. References
are bounded to 4096 serialized bytes.

Populate `BundleRegistry` at trusted host startup with packaged immutable public
`WorkflowBundle` objects. Resolve the exact retained `(version, identity)` pair;
missing material raises `bundle_unavailable`, changed declarations raise
`bundle_conflict`. Neither a proposal nor a stored reference selects imports,
callbacks, directories or endpoints. Native reservation uses a separate
`native-run-v1` hash recipe and atomically inserts legacy ownership plus its
native proposal reference. Replays preserve original billing, namespace and
environment.

Native inputs consume the public `Workflow.prepare_inputs` snapshot: any finite
JSON value, including null, booleans, numbers, strings, arrays and objects. Stored
values and owner/key replay retain their original JSON type and nested content;
changed inputs conflict. The canonical outer proposal-ID/input record retains
the existing 65536-byte, depth-64 and expanded-node-65536 persistence bounds.
Workflow-specific input bounds apply during public preparation. Native HTTP run
and resume requests use the existing 8192-byte body limit. The service adds a
host transport constraint of 64 characters per pause-choice name to the SDK's
proposal schema returned by `/workflow-catalogue`. It enforces that constraint
after SDK admission and before proposal persistence, so every advertised choice
fits the resume field. Unicode and escaped names count as characters. Retained
proposals with unsupported names keep their immutable references but fail with
`invalid_request` before a run reservation or execution. The existing YAML
task/object request recipe remains compatible.

Construct `PgToolJournal(app_dsn, identity=...)` with a stable trusted logical
ledger identity, never a credential-bearing DSN as identity. A committed new row
starts uncertain; only the worker whose INSERT commits receives a `new` claim
token. Matching uncertain rows never grant dispatch permission. Commit compares
the opaque token and uncertain state; stale tokens cannot amend a completed
outcome. Matching completed claims return the bounded original outcome. Results
are limited to 262144 JSON bytes; invalid/oversized post-effect results preserve
uncertainty. Lost acknowledgement may conceal a committed result, so subsequent
claim reads evidence without redispatching. There are no expiring claims or
automatic reconciliation routes. Authoritative domain no-effect, idempotency or
fencing evidence remains an operator obligation; the journal does not make an
external effect atomic with outcome recording.

The dedicated required lane uses only owned persistence/journal tests:

```sh
.venv/bin/python -m lab_runner test --mode native-persistence --postgres-version 16
.venv/bin/python -m lab_runner test --mode native-persistence --postgres-version 18
```

This lane needs a consumer image containing the reviewed public SDK bundle and
ToolClaim APIs. Historical dependency pins remain unchanged until the separate
SDK release qualification step. The lane does not start a model or HTTP replicas.
Its owned databases exercise races, lost acknowledgements, token fencing,
immutable grants and preserved v2 phases. Missing infrastructure returns a
nonzero `not_qualified` receipt rather than a skip. Local Docker preflights on
2026-10-10 timed out after 15 seconds on both majors; no SQL or architecture
qualification is claimed from the collected tests or source-overlay unit suite.

Before upgrades: stop/drain write admission, take a protected consistent logical
backup and verify restore into a separate database. Keep original ownership,
role grants, library schema versions and dependency/asset checksums. Do not
remove the source backup until restored HTTP readiness, owner views, revisions,
usage coverage and least-privilege credentials pass. Backup contents include
private prompts/state; use restricted storage and the deployment's encryption
and retention policy, never public test artifacts.

Rollback means restoring the reviewed pre-upgrade backup and compatible pinned
application/library image. There is no destructive schema downgrade command:
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
