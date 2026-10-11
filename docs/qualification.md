# Bounded operational qualification

These tools consume the released, checksummed SDK baseline independently of the
native persistence work. Build the consumer image from the current source before
execution. A profile is a strict version-1 JSON object; start with
[qualification.synthetic.json](../configs/qualification.synthetic.json).

```sh
.venv/bin/python -m lab_runner qualify --profile configs/qualification.synthetic.json --postgres-version 16
.venv/bin/python -m lab_runner qualify --profile configs/qualification.synthetic.json --postgres-version 18
.venv/bin/python -m lab_runner qualify-recovery --profile configs/qualification.synthetic.json --postgres-version 16
.venv/bin/python -m lab_runner qualify-recovery --profile configs/qualification.synthetic.json --postgres-version 18
.venv/bin/python -m lab_runner qualify-recovery --mode native --profile configs/qualification.synthetic.json --postgres-version 16
.venv/bin/python -m lab_runner qualify-recovery --mode native --profile configs/qualification.synthetic.json --postgres-version 18
```

No lane skips an unavailable engine or missing deployment input. Reports retain
`fixture_passed` separately from `qualified` / `not_qualified`. The suite and
canonical profile SHA256 bind observations and receipts; CLI evidence additionally
records the immutable image, SDK manifest, architecture and cleanup result.
Missing or zero observations, unknown usage, independent-call/ledger mismatch,
failed cleanup or a target miss cannot qualify. A successful local unit suite is
not native-stack evidence.

Profiles require duration (1..3600 seconds), fixed arrivals (greater than zero,
at most 100/second and 10000 total), concurrency (1..64), users (1..1000), shared
provider calls and application records (1..10000), report bytes (1024..262144),
observation windows, p95/rejection/per-identity completion targets, provider/tool
latency (0..5 seconds), and RPO/RTO targets. JSON booleans and nonfinite numbers
are rejected as bounds. Longer soak requires a separately supplied explicit
profile; the short example is the deterministic default.

Arrivals have no client queue or mutation retry. The runner reserves one call and
one application record before each scheduled start and stops admitting work at
the earliest duration/call/record ceiling. In-flight work drains with finite HTTP
deadlines. The synthetic dispatch endpoint enforces its shared call allowance
atomically; rejected allowance attempts and actual dispatches are separate. Model
timing resets in `finally`; the dispatch ceiling stays active until owned teardown
so a late worker cannot escape it. Tool timing is measured through
an owned synthetic operation fixture, not a consequential tool.

Offered, accepted, completed, start-rejected, approval-deferred, client-shed and
error counts remain separate. Fairness keys include both trusted tenant and actor;
public reports hash those labels. Each observed identity must meet its completion
target, and every fully observed offered window must show progress. Owner reads
run concurrently with resume. Reports include read samples/failures, operation
timing, application rows and database bytes, and independent synthetic request
counts reconciled against public recorder deltas. Reaching a budget with unknown
usage never becomes reconciliation success. `stress` retains its existing
correctness/SLO fields and overload policy.

Recovery seeds a waiting normal fixture, a blocked unknown-usage fixture and
durable sequence/time markers, takes a consistent `pg_dump`, stops one exact owned replica to simulate
loss, and restores into a second database on the owned primary. RTO runs from
simulated loss through verified restored readiness. RPO compares the last
acknowledged marker to the last restored acknowledged marker; missing or
inconsistent marker/time evidence fails. Restored public owner views, revisions,
review/choices and unknown usage must match. The finite-budget unknown-usage
block and its revision survive restore; approval cannot clear that block.
Independent model counts must remain
unchanged through restore. No run starts or resumes during restoration. This is
logical backup/restore evidence for that fixture/profile, not HA, PITR or actual
primary destruction. Private dump and DSNs remain in the private owned directory
until verified cleanup.

`qualify-recovery --mode native` additionally requires allowances for eight
provider calls and six run records before seeding. Three actual HTTP-admitted
proposals create four native states: a composed structured-approval pause, a saved
receipt before checkpoint, a completed consequential tool and an uncertain tool
whose domain effect has persisted. The two legacy fixtures remain included.
Restored reads use a fresh replica process against the second database on the
same owned primary. Private bounded captures compare proposal/reference/bundle
identity, frozen attribution and inputs, snapshots/revisions, receipt documents,
interaction/usage, tool signatures/outcomes and domain rows. Completed journal
claims replay; uncertain claims grant no dispatch token. Provider and handler
counts cannot change during verification. Public output contains fixed
verification booleans and populated counts; missing evidence cannot qualify.
Original worker configuration is restored even if backup/restore fails.

After each replica restart, recovery inspects and verifies the same exact owned
container and its loopback port. The local endpoint and ownership manifest are
updated before readiness and owner reads, including the final restart on the
original configuration. Ephemeral port changes therefore do not become stale
readiness probes.

## Private staging inputs

```sh
.venv/bin/python -m lab_runner qualify-staging --config PRIVATE_FILE --staging-opt-in
```

Without opt-in the file is not read and no client opens. Missing/invalid inputs
return `not_qualified` with `missing_deployment_inputs`. Never substitute Keycloak
or ingress fixture success for deployment observations. No real staging command
has been run as part of this implementation.

The private configuration has exactly these keys: `version: 1`,
`suite: deployment-staging-v1`, `origin`, `approved_origins`, `token_file`,
`ca_file`, `signing_key_file`, `issuer`, `audience`, `maximum_token_lifetime_s`,
`maximum_calls`, `duration_s`, `maximum_report_bytes`, and `cases`. Origins are
exact approved HTTPS origins (up to eight). Files are owned regular files with
no group/other permissions and bounded reads; final symlinks are rejected. The
provided RS256 token must cryptographically verify against the supplied public
key and expected issuer/audience, with `iat`/`exp` and a bounded lifetime.

`cases` contains exactly `rotation`, `outage`, `backend_isolation` and `drain`.
Each operator-controlled observation has a boolean `passed`, a lowercase
64-character `evidence_sha256`, and `observed_at` within the last hour. The tool
does not manufacture those observations or execute rotation/outage operations.
It makes one bounded HTTPS readiness read with the supplied token and CA; all
redirects are rejected. An overall cancellation deadline covers connection, TLS
and response headers, with remaining time applied to HTTP operations. Readiness
uses status only: the response body limit is zero bytes, and the streamed response
and client close without consuming the body. Frequent header bytes cannot extend
the deadline; expiry returns `not_qualified` with a fixed reason. It acquires no
tokens, changes no issuer settings and
makes no paid inference calls. Public receipts include only configuration/case
digests, counts and fixed reasons; URLs, JWT claims, tokens and key paths remain
private. Qualification is limited to the supplied observations and that read.

The published Lab 0.3.0 matrix qualified the prior synthetic profiles; see
[public adoption](verification/public-release-adoption-2026-10-11.md). New native
fault/restore cases need their own exact-source matrix, recorded in the
[milestone ledger](verification/production-readiness-m1-m2-2026-10-11.md).
