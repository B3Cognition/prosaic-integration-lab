# Capacity and retention pilot

Run synthetic traffic from the terminal (no paid inference):

```sh
.venv/bin/python -m lab_runner stress --candidate --users 6 --duration 20 --rate 1 --concurrency 2 --tenant-capacity 1
.venv/bin/python -m lab_runner stress --candidate --users 6 --duration 10 --rate 30 --concurrency 8 --tenant-capacity 1 --allow-overload
```

The command prints request events and the exact evidence directory. In another
terminal use `lab_runner watch --directory DIRECTORY --stream accounting`.
Use `--stream requests` for request events. `run --users N --runs-per-user N`
remains the finite workflow-count runner. Candidate commands require the built,
checksummed candidate image; see [release-gates.md](release-gates.md).

Stress offers arrivals at a fixed rate with bounded client concurrency and no
mutation retries. Client shedding, service rejection, approval deferral, errors,
completed-workflow p95, and independently reconciled provider calls are separate
results. Default SLO: p95 <=2 seconds, rejection <=5%, and completed throughput
>=90% of offered rate. `--allow-overload` permits SLO failure, never correctness
or accounting failure. Completed-request latency excludes rejected requests.

Measured local ARM pilot: six users, 1 arrival/second for 20 seconds, concurrency
2, tenant admission 1: 20/20 completed, zero rejection/error, p95 0.1615 seconds.
At 30 arrivals/second for 10 seconds: 300 offered, 163 accepted/provider calls,
107 completed, 193 rejections (including 56 deferred approvals), zero errors;
completed p95 0.1291 seconds, rejection 64.33%. Accounting reconciled, but the
SLO failed. Actor completion was uneven under overload. This is not a 30 RPS
capacity claim or a long-soak qualification. Receipts are recorded in the fix ledger.

Optional private service config `capacity` accepts `writes` (1..2), `reads`
(1..4), `per_tenant` (1..writes), `max_runs` (1..10000), and `max_tenant_runs`
(1..max_runs). Defaults: 2, 4, 2, 10000, 10000. Admission limits are per replica;
record limits cover the shared application database across namespaces. New keys
stop at the ceiling. Existing keys remain usable. Atomic reservations across
replicas preserve idempotency and unknown effects; records never expire automatically.

Inspect retention using a private operator config (0600, owned by the caller):

```sh
.venv/bin/python -m lab_runner retention --config PRIVATE_CONFIG
.venv/bin/python -m lab_runner retention --config PRIVATE_CONFIG --archive --destination NEW_PRIVATE_DIRECTORY
```

Archive creates private copies with checksums, preserving application reservations,
public SDK state and usage. Uncertain or unresolved records are retained explicitly.
It never deletes source records or makes a missing receipt safe to retry. Copies
contain private tasks/state: do not publish them. This paginated copy is not a
point-in-time database backup. Use the tested [backup/restore procedure](persistence.md)
for disaster recovery. Deletion and idempotency expiry require a separately reviewed
policy and migration; neither is implemented.

Credential delivery permits at most 64 retained generations, including interrupted
ones. At the ceiling it stops without changing the active pointer. Retirement is
manual: drain/restart all consumers, verify the current config and CA, revoke old
credentials, and review noncurrent generations before removing any. A noncurrent
pointer alone does not prove a running process has stopped using its generation.

Before expanding this pilot, qualify native deployment hardware, longer soak,
database growth and HA/PITR, actual provider latency, tool effects, monitoring,
and operator recovery. Deferred approvals require owner action, not automatic retries.
