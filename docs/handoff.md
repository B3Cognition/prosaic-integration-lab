# Codex handoff

Checkpoint: 2026-10-09, first working synthetic consumer on a local feature branch.

## Completed

- Maintainer approved the separate integration-lab design.
- Public repository and Apache-2.0 license created.
- Approved design, README, agent instructions and remaining-work checklist saved.
- [Tracking issue #1](https://github.com/B3Cognition/prosaic-integration-lab/issues/1)
  published with staged work and acceptance requirements.
- No existing Prosaic/Harness/Runtime library sources changed for this handoff.

## Implementation checkpoint

Native implementation was authorized by the maintainer's “proceed”. Branch
`codex/integration-lab` contains the consumer image, wheel provenance/audit,
owned runner, explicit grants, owner-only HTTP APIs, zero-call approval and
synthetic inference/accounting. PostgreSQL 16 and 18 acceptance ran on Docker
Desktop Linux/arm64 with verified cleanup. Read `verification/progress.md` for
exact receipts and remaining coverage. No push or release is implied.

The optional host-side local model reads `~/.omlx_token`; its 7B Qwen Coder smoke
succeeded and reported 85 tokens. No cloud/TokenProxy model calls were made.

## Historic initial handoff

At the initial documentation-only handoff, no Python application, dependency lock, image, PostgreSQL fixture, workflow asset,
model stub, test runner, load balancer or CI job exists yet. No container or model
was started. No acceptance test, architecture matrix or live endpoint was run.
Commands in the design are target interfaces, not commands available today.

## Initial next action (superseded)

Read the [approved design](superpowers/specs/2026-10-09-prosaic-integration-lab-design.md)
and [tracking issue #1](https://github.com/B3Cognition/prosaic-integration-lab/issues/1).
Review the [written implementation plan](superpowers/plans/2026-10-09-prosaic-integration-lab.md)
and its execution ledger. The plan was prepared and approved in this checkout
on 2026-10-09. Native execution starts with released-dependency provenance and
exact-owned provisioning. No paid calls are needed for synthetic milestones.

Do not re-request approval of the already approved project direction unless a
material change is needed. The written implementation plan is now approved.

Recommended milestone order:

1. Clean released-package consumer image and exact-owned stack lifecycle.
2. Trusted identity, durable ownership/idempotency and filtered HTTP endpoints.
3. Zero-model-call cross-replica workflow approval.
4. Synthetic inference, public SDK accounting and multiuser acceptance.
5. Fault-gated recovery, overload, accounting failures and repeatability.
6. Non-sticky load balancing and PostgreSQL 16/18 CI on Linux/arm64 and amd64.
7. Explicit live TokenProxy mode and its separate evidence/limitations.

Each milestone needs independently executable tests and a commit with evidence.
Pay particular attention to app ownership reservation versus Harness creation:
they are not one transaction. Never reinterpret a missing response/checkpoint
as permission to redispatch a possibly completed request.

## Released dependency baseline

Initial baseline verified from release metadata on 2026-10-09:

| Distribution | Version | Release source commit |
| --- | --- | --- |
| prosaic-harness | 0.6.0 | 2bd14fd8aa17f30c957ff29f886ffd16b2af52ca |
| prosaic-harness-postgres | 0.1.0 | same Harness source commit |
| prosaic-runtime | 0.6.0 | b13a62eac955b19b13fe2c9dc646a188069f72f2 |
| prosaic-runtime-postgres | 0.1.0 | same Runtime source commit |

- [Harness v0.6.0 assets](https://github.com/B3Cognition/prosaic-harness/releases/tag/v0.6.0)
- [Runtime v0.6.0 assets](https://github.com/B3Cognition/prosaic-runtime/releases/tag/v0.6.0)

Both releases include core/adapter wheels, source archives and
`SHA256SUMS-0.6.0.txt`. Download the artifacts, verify their checksums and save a
dependency manifest during implementation. Assets have not been downloaded or
checksum-verified by this new repository's handoff task. Install each core
before its adapter and lock the complete service/test dependency graph.

Harness 0.6.0 pins Runtime 0.6.0, which installs Prosaic transitively. Review the
resolved dependency provenance rather than adding a second interpreter or an
editable sibling dependency.

## Operator references

- [Harness PostgreSQL provisioning/grants](https://github.com/B3Cognition/prosaic-harness/blob/v0.6.0/adapters/postgres/README.md)
- [Harness accounting attribution/recovery](https://github.com/B3Cognition/prosaic-harness/blob/v0.6.0/docs/accounting.md)
- [Runtime PostgreSQL recorder contract](https://github.com/B3Cognition/prosaic-runtime/blob/v0.6.0/adapters/postgres/README.md)
- [Runtime measurement and coverage](https://github.com/B3Cognition/prosaic-runtime/blob/v0.6.0/docs/accounting.md)

Read these before defining roles or interpreting unknown evidence. Shared
PostgreSQL does not make workflow and accounting writes atomic. Namespaces are
not authorization, leases are not external-effect idempotency, and estimates
are not customer charges.

## Historic initial verification record

At handoff, verification is limited to documentation/file consistency, Git
publication and public repository/issue visibility. Implementation-specific
test results must be recorded by the next session; do not inherit upstream
test counts as proof that this service works.
