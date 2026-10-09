# Prosaic integration lab: design and machine-to-machine handoff

Date: 2026-10-09. Status: approved by the maintainer on 2026-10-09.

## Purpose and current checkpoint

Create a public repository named `B3Cognition/prosaic-integration-lab` containing
a small reference application and repeatable acceptance suite for multiuser
Prosaic Harness execution with PostgreSQL persistence and Runtime accounting.
The maintainer intends to continue implementation with Codex on another machine.

This document is the initial handoff artifact, not evidence of a working service.
The public repository contains this approved design and documentation-only
handoff. No service, container stack or acceptance suite has been implemented.
No production-readiness claim is made.

The agreed direction is a separate consumer repository, two identical service
replicas, shared PostgreSQL, synthetic inference by default, and explicitly
opt-in live inference. Existing library repositories remain unchanged.

## Repository boundary and alternatives

The selected approach is a separate integration lab. It proves the released
libraries work together as installed dependencies, while keeping authentication,
HTTP policies and deployment fixtures out of Harness and Runtime.

Keeping the service inside Harness would simplify coordinated edits but couple
the library to application policy and make accidental private imports easier.
A full production gateway would add identity-provider, queue and operational
requirements beyond the current testing purpose. Neither is the initial scope.

Harness retains its engine/storage unit and integration tests. Runtime retains
its execution/accounting tests. If the lab uncovers a library defect, reproduce
and fix it in the owning library with a regression; do not patch installed code
or duplicate library internals in this repository.

## Deployment

- Python 3.12 application image, with a thin FastAPI/Uvicorn HTTP service.
- Two instances of that exact image, each with one application process.
- One owned disposable PostgreSQL primary; exercise majors 16 and 18 in CI.
- One synthetic OpenAI-compatible HTTP model fixture for deterministic tests.
- A host-side test runner initially addresses both replicas directly. A later
  routing milestone adds a load balancer with no sticky sessions.
- Support Linux/arm64 and Linux/amd64. The next machine can build and run the
  container suite; this design has not validated either architecture.

Each replica embeds Harness, Runtime and Prosaic; no separate inference gateway
is needed. Identical immutable workflow/prose/schema/configuration assets live
at `/srv/lab/assets` in both replicas. Only PostgreSQL stores shared run state;
private writable tool scratch is replica/execution-local and never shared.

Use released core/adapter packages, not editable sibling checkouts. Initial
release baseline, verified through GitHub release assets on 2026-10-09:

| Package | Version | Source release |
| --- | --- | --- |
| prosaic-harness | 0.6.0 | B3Cognition/prosaic-harness v0.6.0 |
| prosaic-harness-postgres | 0.1.0 | same Harness release |
| prosaic-runtime | 0.6.0 | B3Cognition/prosaic-runtime v0.6.0 |
| prosaic-runtime-postgres | 0.1.0 | same Runtime release |

The implementation must retain downloaded-wheel SHA256 values and install each
core wheel before its adapter. Resolve and lock service/test dependencies and
record image digests. A release-update change must rerun the acceptance suite.
Do not assume PyPI availability or install the mutable upstream `main` branch.

## Identity and application-owned data

The lab uses generated bearer-token fixture identities, not production OAuth.
Tokens are generated for each stack, mounted through secret files and excluded
from Git and diagnostics. All published ports bind to loopback. Documentation
must explicitly label this authentication as lab-only.

Provide three principals: Alice and Bob in tenant A, and Carol in tenant B.
Each has a server-configured actor and billing-account mapping. Clients cannot
override tenant, actor, billing account, namespace, workflow path or model URL.
Runs and usage views are owner-only in the initial application policy; no
tenant administrator or sharing feature is included.

Application-owned PostgreSQL metadata records run ID, owner actor/tenant,
idempotency key and canonical request hash. A repeated key for the same owner
and identical request resolves to the existing run; a changed payload conflicts.
The uniqueness constraint and reservation are database-backed so A/B races
cannot allocate separate runs. This is distinct from Harness run-state writing.

Persist the ownership reservation before contacting Harness. Authorization must
be checked against that metadata before any run-state or accounting query.
App metadata and Harness creation are not one atomic transaction: retain an
explicit not-yet-started/uncertain reservation state. Do not redispatch merely
because the HTTP response or initial run checkpoint is missing. The detailed
reservation recovery algorithm is an implementation-plan review requirement.

Use a bounded deployment-level Harness namespace, not one pool per user.
Namespace strings and accounting IDs are attribution/addressing, not authority.
The service does not expose arbitrary operators' raw state or cross-tenant
report filters. Non-owner run requests return a uniform not-found response;
unauthenticated requests return 401, and neither may dispatch a model call.

## HTTP contract

- `GET /healthz`: process liveness, no secrets.
- `GET /readyz`: database/schema/configuration readiness, sanitized failure.
- `POST /runs`: authorized predefined workflow, bounded JSON inputs and required
  owner-scoped idempotency key. Returns the run ID, filtered state and revision.
- `GET /runs/{id}`: authorized filtered state, revision and recovery status.
- `POST /runs/{id}/resume`: authorized choice/response or explicit interrupted
  retry consent, with the revision the user actually reviewed.
- `GET /runs/{id}/usage`: authorized recorder-derived usage and coverage for
  this run, constrained to its original owner/context.

Start/resume execute synchronously in a bounded worker pool for the first
milestone. No durable scheduler, background polling dispatcher or automatic
workflow failover is implied. Keep the ASGI event loop unblocked. Initially
admit at most two execution operations per replica, with no unbounded queue;
capacity exhaustion returns 503 and concurrent same-run ownership returns 409.
Stale revisions return 409 without advancement. Configure bounded inference
and client timeouts; disconnects never imply rollback or authorize redispatch.

Create a separate Harness per execution and construct stores after process
startup/fork. Reuse bounded store/recorder resources; drain admitted work before
closing. Both replicas reconstruct the same workflow/run identity for resume.

The filtered public state contains run ID, status, current step, revision and
approved public result/decision fields. It must not contain prompts, raw tool
arguments, private evidence, DSNs, internal history or arbitrary exception text.

## Accounting contract

Enable the existing Runtime PostgreSQL recorder and supply trusted
ExecutionContext separately from model arguments. Freeze application, tenant,
billing account, actor and request/run attribution across retries and resume.
Both replicas use the same accounting deployment namespace and environment.

One provider-call intent/observation is not the same thing as one workflow.
Tool loops and validation retries may cause multiple measured provider calls.
Usage incurred by a rejected output remains in the ledger. Harness recovery
adopting a saved receipt must not cause another provider call or another charge
estimate. Unknown/partial usage is not zero. Conflicting attribution/evidence
must be rejected or quarantined according to the public library contracts.

Workflow checkpoints and accounting records have separate transactions and
recovery boundaries even when hosted in the same database. Test their mismatch
and failure cases explicitly. The service must not treat an accounting record
as authority to approve a result or retry an interrupted invocation.

Use synthetic fixed decimal rate cards only in deterministic tests. Report
coverage and estimates, not customer charges. All existing assessments remain
billing-ineligible. Invoicing, billing exporters, paid tools, BYOK/native
subscription pricing and manual ledger amendments are outside this milestone.

## Provisioning and safety

The stack runner owns only explicitly labeled containers/networks/volumes and
fresh fixture databases. It performs explicit schema setup once using separate
migration credentials, then supplies restricted runtime credentials to replicas.
Neither service replica may perform automatic DDL or hold administrator DSNs.
Accounting and Harness permissions differ; apply each adapter's documented
grants rather than sharing a superuser role. Bind readiness checks to both.

Use unique ownership IDs and random loopback ports for each suite invocation.
Validate exact resource identity before crash/restart/cleanup. Do not use shared
development databases, broad name-prefix deletion, `docker system prune` or
host-global cleanup. Preserve the fixture volume within restart tests; use a
fresh isolated database for the next independent suite invocation.

Clock/lease margins, primary/WAL safety and unknown-commit reconciliation follow
the released adapters' contracts. Fencing does not undo remote tool effects;
use application-owned idempotency for effects and explicit retry consent for
uncertain provider requests. A lagging promoted primary can lose data; this
suite is not a zero-loss failover certification.

## Repeatable acceptance suite

The target commands, not yet implemented at this checkpoint, are:

- `python -m lab_runner test --mode deterministic`
- `python -m lab_runner test --mode recovery`
- `python -m lab_runner test --mode load`
- `python -m lab_runner test --mode live --allow-paid-calls --max-calls 10`

Deterministic mode brings up two replicas, PostgreSQL and synthetic inference,
runs assertions, exports sanitized JUnit/JSON results and cleans owned fixtures.
Recovery/load modes remain synthetic. Live mode requires explicit credentials,
uses the configured TokenProxy endpoint and obeys a shared suite call allowance;
it does not guarantee a monetary spending cap. No live calls run in default CI.

Required mode fails on missing infrastructure, readiness failure, unexpected
skips, timeout, failed cleanup or assertion failure. Preserve sanitized failure
diagnostics before teardown and record versions, seed, architecture and ownership
ID. Synchronize races through observable gates/barriers, not arbitrary sleeps.
The synthetic endpoint keeps independently queryable request counts and known
response IDs/usage so the tests can detect extra dispatches, not only database
rows that look correct.

Acceptance scenarios:

1. A starts; B inspects and resumes without shared writable files.
2. Alice/Bob/Carol run concurrently; content, tool context and usage stay isolated.
3. Non-owner read/resume/usage and identity-spoofing attempts are denied without
   disclosing private state or contacting the endpoint.
4. Simultaneous same-key starts produce one run; changed payload conflicts.
5. Simultaneous A/B execution admits one owner; stale approvals do not advance.
6. Overload remains bounded and rejects clearly; unrelated users remain isolated.
7. Replica restart preserves run state, authorization metadata and accounting.
8. Worker loss after receipt persistence is recovered without redispatch.
9. Missing receipt blocks with explicit retry consent; missing final usage stays
   unknown, and token-budget policy is not bypassed.
10. Each tool-loop/validation-retry provider call is measured once; rejected
    outputs keep their incurred usage and identical recorder replay is a no-op.
11. Accounting failure before dispatch prevents dispatch; observation failure
    after a provider call does not trigger another call.
12. Recovery on B keeps original attribution even after server defaults change;
    conflicting context or recorder scope fails safely.
13. Known synthetic token counts and decimal estimates match owner-scoped views;
    incomplete coverage is explicit, not a final zero-cost result.
14. Public responses/logs contain no private state or secrets.
15. Wrong asset/configuration versions fail before dispatch; unprivileged roles
    and missing schema are validated without automatic repair.
16. Load-balanced alternating requests work without sticky sessions.

## Suggested repository layout

```text
AGENTS.md                        # boundaries and continuation instructions
README.md                        # honest implemented/planned status and commands
pyproject.toml                   # lab-only service/runner/test dependencies
dependencies/                    # release wheel checksum manifest and lock
src/prosaic_integration_lab/      # HTTP, identity, app metadata, SDK integration
lab_runner/                      # exact-owned stack lifecycle and test commands
assets/                          # immutable neutral workflow/prose/schema fixtures
containers/                      # application image and stack configuration
tests/unit/                      # identity/filter/idempotency/configuration
tests/acceptance/                 # HTTP and cross-replica acceptance tests
tests/fixtures/                  # synthetic model and deterministic fault gates
docs/decisions/                   # approved boundary decisions and costs
docs/superpowers/specs/           # this reviewed design
docs/superpowers/plans/           # reviewed implementation plan
docs/handoff.md                  # exact next action and verification receipts
.github/workflows/               # required synthetic CI lanes
```

## Delivery stages and GitHub issue body

Tracking issue title: `Build repeatable multiuser and accounting acceptance lab`.
The tracking issue is linked from README.md and docs/handoff.md. Check items
only with corresponding committed verification evidence.

- [x] Review this written design and preserve approved decisions.
- [ ] Write/review the implementation plan and select execution method.
- [x] Create public B3Cognition/prosaic-integration-lab; publish README, license,
      AGENTS.md, design and handoff instructions.
- [x] Publish tracking issue #1 and link it from the repository documentation.
- [ ] Lock release dependencies/checksums and build a clean consumer image.
- [ ] Implement owned stack provisioning with explicit grants/readiness/cleanup.
- [ ] Implement fixture identity, durable ownership/idempotency and filtered APIs.
- [ ] Wire public Harness/PostgresRunStore and Runtime/PostgresRecorder SDKs.
- [ ] Add zero-model-call cross-replica approval acceptance proof.
- [ ] Add deterministic synthetic inference/accounting and isolation proof.
- [ ] Add fault-gated recovery/accounting-boundary tests.
- [ ] Add bounded load, repeatability and clean-resource evidence.
- [ ] Add non-sticky load-balancer acceptance proof.
- [ ] Add PostgreSQL 16/18 CI with required no-skip gates; verify Linux/arm64
      and Linux/amd64 separately and report any untested matrix entries.
- [ ] Add explicit live TokenProxy mode and document verified provider scope.
- [ ] Record final commands/results, dependency provenance and residual limits.

Next Codex session: read AGENTS.md, this design, docs/handoff.md and the tracking
issue before coding. There is no implementation plan yet: write it, obtain
maintainer review and select the execution method before implementation. Do not
infer that planned commands exist.
Work stage-by-stage with failing regressions before fixes, scoped commits and
fresh verification. Read each adapter's operator guide before provisioning:

- https://github.com/B3Cognition/prosaic-harness/blob/v0.6.0/adapters/postgres/README.md
- https://github.com/B3Cognition/prosaic-harness/blob/v0.6.0/docs/accounting.md
- https://github.com/B3Cognition/prosaic-runtime/blob/v0.6.0/adapters/postgres/README.md
- https://github.com/B3Cognition/prosaic-runtime/blob/v0.6.0/docs/accounting.md

The next development action is to write and review the implementation plan,
then implement the initial consumer/owned-stack milestone. The written design
is approved; service implementation has not started.
