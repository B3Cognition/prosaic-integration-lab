# Production fix queue

The maintainer authorized filing the audit blockers and fixing them sequentially
with unit, functional and integration regressions. No paid inference, remote
push, library publication or production deployment is implied.

| Order | Issue | Scope | State |
| --- | --- | --- | --- |
| 1 | [Runtime 3](https://github.com/B3Cognition/prosaic-runtime/issues/3) | Accounting schema/grant readiness | Locally verified candidate; publication pending |
| 2 | [Lab 2](https://github.com/B3Cognition/prosaic-integration-lab/issues/2) | Application readiness | Locally verified |
| 3 | [Lab 3](https://github.com/B3Cognition/prosaic-integration-lab/issues/3) | Bounded metadata admission | In progress |
| 4 | [Lab 4](https://github.com/B3Cognition/prosaic-integration-lab/issues/4) | Early authentication and HTTP bounds | Queued |
| 5 | [Lab 5](https://github.com/B3Cognition/prosaic-integration-lab/issues/5) | Non-root immutable deployment | Queued |
| 6 | [Lab 6](https://github.com/B3Cognition/prosaic-integration-lab/issues/6) | Safe approval view | Queued |
| 7 | [Lab 7](https://github.com/B3Cognition/prosaic-integration-lab/issues/7) | Production identity/TLS/rotation | Queued; configurable OIDC, Keycloak reference |
| 8 | [Lab 8](https://github.com/B3Cognition/prosaic-integration-lab/issues/8) | Persistent upgrades/backup restore | Queued |
| 9 | [Lab 9](https://github.com/B3Cognition/prosaic-integration-lab/issues/9) | Operational recovery | Queued |
| 10 | [Lab 10](https://github.com/B3Cognition/prosaic-integration-lab/issues/10) | HTTP token-budget crash recovery | Queued |
| 11 | [Lab 11](https://github.com/B3Cognition/prosaic-integration-lab/issues/11) | Non-sticky ingress/drain | Queued |
| 12 | [Lab 12](https://github.com/B3Cognition/prosaic-integration-lab/issues/12) | Required CI/release gates | Queued |
| 13 | [Lab 13](https://github.com/B3Cognition/prosaic-integration-lab/issues/13) | Sanitized operational evidence | Queued |
| 14 | [Lab 14](https://github.com/B3Cognition/prosaic-integration-lab/issues/14) | Capacity SLOs/retention qualification | Queued |

## Execution contract

Use the audit report's required changes and acceptance criteria as the approved
fix brief. First reproduce each failure, then add unit and functional coverage,
implement the smallest complete fix, run its owned PostgreSQL/container lane,
and commit/record verification before advancing. Preserve historical red receipts.
Readiness introspects the real catalog and privileges without DDL. Admission
bounds metadata before dispatch while retaining idempotency and uncertain starts.
HTTP guards authenticate before body streaming. Deployment separates migration
privileges from immutable replicas. Public approval exposes only approved fields.

Library source fixes belong in an isolated Runtime worktree. Integration testing
of unpublished wheels must be explicitly marked as a candidate with checksums;
the released-package lane remains separate. Never patch installed library files
or silently make production depend on a sibling checkout. Publishing/updating a
release is a concrete final approval step once its code and tests are reviewable.

The wider adoption issues require the same test layers, not just documentation.
Identity is configurable OIDC behind TLS if no existing deployment preference
is supplied. The maintainer confirmed Keycloak, preferring configurable providers.
Recovery never assumes a missing receipt means no remote effect;
retention never deletes unresolved evidence. Unknown usage remains unknown and
all synthetic estimates remain billing-ineligible.

## Readiness verification

Runtime fix commit `fbd6efba5cc40e6094675e197caa122cfe24dc2f` is on isolated
branch `codex/accounting-readiness`, at `.lab/worktrees/runtime-readiness`.
Eight catalog unit regressions, seven real database fault regressions and the
twenty existing recorder regressions passed on PostgreSQL 16 and 18: 35 tests
per owned fixture, zero skips, verified cleanup. Receipts:
`f53e48c737204d8bb6e8eee88ade7f45` / `7ef4d80282f84dcdb087f2a895d710e4`.
The Runtime default suite also passed 456 tests after the fix.

The unpublished 0.1.1 wheel has SHA256
`25b22b0423afaa870991bcd04c50cacfd878a541e1ff6773733a38f45b945c2e`.
`dependencies/accounting-candidate.json` retains the other four original release
wheels and pins this candidate. The image verifies every wheel and installed
payload; `--candidate` checks its immutable manifest label before creating
engine resources. Normal commands continue using the original release wheels.

Application readiness now validates its actual logged tables, types/nullability,
phase/key constraints and SELECT/INSERT/phase-UPDATE privileges in a read-only
snapshot. Seven unit contract cases passed. Existing HTTP schema/grant failures
became green without repair; added wrong-json-type and phase-grant negatives
also passed.

Combined candidate audit: 60 tests, 56 pass and four remain red on each database
major, zero skips, verified cleanup. Receipts:
`447a9e796e364dbf9f82b53fc84f7f83` / `9fa4fb03c7c14f3aaa9ac7b5b0631ddb`.
Candidate consumer image:
`sha256:58cc0e833ac1c1e969f912eda21ce78b48bec25e16b0ce235f416e816554ce4e`.
This is candidate integration evidence, not an upstream release claim.
