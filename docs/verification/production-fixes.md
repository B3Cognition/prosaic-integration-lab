# Production fix queue

The maintainer authorized filing the audit blockers and fixing them sequentially
with unit, functional and integration regressions. No paid inference, remote
push, library publication or production deployment is implied.

| Order | Issue | Scope | State |
| --- | --- | --- | --- |
| 1 | [Runtime 3](https://github.com/B3Cognition/prosaic-runtime/issues/3) | Accounting schema/grant readiness | Locally verified candidate; publication pending |
| 2 | [Lab 2](https://github.com/B3Cognition/prosaic-integration-lab/issues/2) | Application readiness | Locally verified |
| 3 | [Lab 3](https://github.com/B3Cognition/prosaic-integration-lab/issues/3) | Bounded metadata admission | Locally verified; Harness candidate dependency |
| 4 | [Lab 4](https://github.com/B3Cognition/prosaic-integration-lab/issues/4) | Early authentication and HTTP bounds | Locally verified |
| 5 | [Lab 5](https://github.com/B3Cognition/prosaic-integration-lab/issues/5) | Non-root immutable deployment | Locally verified |
| 6 | [Lab 6](https://github.com/B3Cognition/prosaic-integration-lab/issues/6) | Safe approval view | Locally verified |
| 7 | [Lab 7](https://github.com/B3Cognition/prosaic-integration-lab/issues/7) | Production identity/TLS/rotation | OIDC/Keycloak locally verified; service ingress in issue 11 |
| 8 | [Lab 8](https://github.com/B3Cognition/prosaic-integration-lab/issues/8) | Persistent upgrades/backup restore | Locally verified |
| 9 | [Lab 9](https://github.com/B3Cognition/prosaic-integration-lab/issues/9) | Operational recovery | Locally verified |
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

## Admission and lease registration

Writes now acquire bounded admission before ownership reservation, with one
active write per trusted actor per replica. Reads have a separate bounded pool.
Client cancellation holds admission until the actual worker exits. Unit and
functional suites: 54 passed. Real admission and cross-tenant fairness tests pass.

A concurrent 500-run receipt `f991fa5e443346c3baac9f97c0263b02` retained one
pre-dispatch failure; 499 calls reconciled. Its original cause cannot be proven
from the available receipt. Investigation independently reproduced a Harness
capacity race: an acquired lease was briefly counted as both acquiring and
registered. [Harness issue 3](https://github.com/B3Cognition/prosaic-harness/issues/3)
tracks its atomic transfer fix, commit `052cc779653a30039bebed3e675ba69c146073f9`
in `.lab/worktrees/harness-registration`. The deterministic PostgreSQL regression
failed before the fix (`d52bc99df4724a77809de9dbba99d822`). Its unit and real database
tests now pass on both majors (`2d58d6bce7e144cda1c8d0ef71ced52b` /
`58969458f11d4114a243d7167ab8224c`); Harness core: 172 passed.

Candidate manifest now pins both adapter wheels, retaining the three original
core wheels. Harness wheel SHA256:
`7617bb3af272e82be526dd481daab7397e4036b11b1fcd2ce25b21169ec431e8`.
Manifest SHA256:
`6dd1eb2e1196a6741ad805255dbbdb7768185206a07e8dd33f2ebceb6b5745b0`.
Candidate image `sha256:7f30e987fb1905d8156d693d79fa04be403d836f3755c37ae588b83a45116545`
completed 500/500 workflows with zero errors/rejections and 500 independently
reconciled calls while an audit ran concurrently (`5e4658a6fa3f4dddbb7a949d46ca9211`).
Audit on each major: 61 tests, 58 passed, only early-auth/root/writable-root
failures remain (`cf6ec5e1b7164013acc3307e4bb11d1b` /
`883daef3f7724ec7b6fb2e7df7c3813a`). All these fixtures verified cleanup.
Minimal sanitized stage diagnostics were brought forward from issue 13 to aid
failure investigation; broader operational metrics remain queued.

## HTTP guard verification

Authentication precedes body reads and parsing. Per replica: 32 HTTP operations,
2-second whole-body deadline, 8 KiB body, 16 KiB headers, 100 requests/second
with burst 200 per trusted actor. `http_bounds` can configure finite capacity,
deadline, rate and burst. Health/readiness bypass the protected HTTP pool;
database readiness still has its separate bounded read pool. Rejections close
connections. Uvicorn uses concurrency/backlog 64 and 5-second keep-alive.
An ingress header deadline remains in issue 11; these are application bounds.

The malformed unauthenticated POST functional regression failed with 422 before
the guard, then passed with 401. Unit tests verify no body read before auth or
admission/rate rejection, timeout release, health availability, trusted actor
rate separation and body replay. Local suite: 60 passed. Raw TCP partial bodies
with Content-Length/chunked framing return 401 immediately; authenticated partial
body returns 408 without a model call. Candidate audit: 63 tests, 61 passed and
only root/writable-root failures remain on both majors; zero skips, cleanup
verified (`06bcb3041d5449578e1d8f3507db0779` /
`f13a79592f4f4324955a64f9cda2b393`). Image:
`sha256:2f4c3f518a5322ae125b3dc61ed6c5440b7a1cd7e1e30aca88f067b73c273f8d`.

## Immutable deployment verification

Replicas and model fixture run as UID/GID 10001, with read-only root, dropped
capabilities, no-new-privileges, bounded private tmpfs scratch and CPU/memory/pid
limits. The migration job remains separately privileged, without replica access
to migration credentials. An exact-owned offline delivery job copies only
runtime config to a private named volume (directory 0700, file 0400 owned by
10001); replicas mount it read-only. Host secrets remain directory 0700/file 0600.
Explicit job restart atomically replaces credentials; service restart loads them.
The scope fault test uses this delivery path rather than the obsolete host bind.

Initial delivery permission-order failures retained receipts
`0070fc9df6d5414693c61a5706b6e579` / `d38ac9e68c7947e3923c6e78ac9875e8`.
After correcting permission-before-ownership transfer, the first full runs only
failed the obsolete drift injection (`6c2ad859432741989e28ebf16f1df212` /
`49ac812282d1456da4349ed76188ffcd`). All failed fixtures verified cleanup.

Local suite: 62 passed. Current audit: **64/64 passed on PostgreSQL 16 and 18**,
zero skips, cleanup verified (`aa8863ec5d724995905c867345aaeb14` /
`101b593776274dacaef54238ab1ca3d8`). Recovery, cross-replica approval/accounting,
effective UID, read-only root and private secret delivery all pass. Image:
`sha256:40fc5daf9af6aea241fe5cf0dcf396fa607e8253a403ff4558f78f1ad4ac94b2`.
Independent read-only review found no critical/important defect. It noted that
a killed delivery process can leave `.next`, blocking rotation; interrupted
delivery recovery coverage is assigned to issue 9 rather than silently deleting
an unexplained staging file.

Green synthetic candidate audit does not complete wider adoption issues 6–14
or publish the upstream adapter fixes. Released-package accounting readiness
remains dependent on their eventual publication.

## Approval review verification

Only explicit approval/synthetic workflows expose a `review` while at their
approval pause: trusted fixed question, exact revision and schema-approved
author result (`result` string, max 256, no extra properties). Other inputs,
outputs, history and raw question remain private. Invalid output removes choices
and the HTTP resume boundary rejects approval before invoking Harness. Result
text is JSON data; a UI must render it as text, never HTML. The HTTP test verifies
application/json for script-like text without exposing operator state.

Projection regressions failed before implementation. Local suite: 70 passed.
Owner-only cross-replica review, stale post-decision approval and an old review
revision against different result material all pass using real SDK fencing.
Candidate audits: 66/66 passed on both database majors, zero skips and verified
cleanup (`ea916cce168d4020be76576ec8c5da7c` /
`cfc369b22d9747d0b446c65a190a01f1`). Image:
`sha256:27ce0d15f0f63403aad3db0415c1f5c7158d65e6a16ff696a18157cbd9a5f761`.

## Configurable OIDC identity verification

The production identity profile requires configurable HTTPS OIDC issuer/audience,
JWKS, online uncached introspection and server-owned subject bindings. It rejects
fixture bearer maps, unsupported algorithms, missing/expired/future claims,
unknown subjects and inactive tokens. Claims/forwarded headers cannot override
tenant/actor/account. PyJWT 2.15.1 and cryptography 50.0.2 are hash-locked; existing
lock pins stayed unchanged. Authentication has a whole 2-second deadline, eight
outbound connections, 64 KiB response/32-key limits and bounded key refresh/cache.
Cached expired keys never survive a failed refresh; token URLs are ignored.

Unit regressions initially failed for absent OIDC implementation; a heterogeneous
keyset regression additionally failed before allowing unrelated encryption keys.
Current local suite: 90 passed, including real RSA verification, rotation/removal,
response/deadline/cooldown bounds, outage and HTTP revocation-before-body behavior.

Owned Keycloak 26.8.0 TLS reference uses generated private credentials and a
generated certificate, never the maintainer's deployment. Both real lanes pass
18/18 tests, zero skips, verified cleanup (`00b7a6e796b9486ea8756c580381242d` /
`f6bff6a10d81418090629a9dcf1fdb79`), including actual signing-key rotation,
cross-replica frozen accounting, spoofed billing claim, logout and issuer outage.
Keycloak image:
`quay.io/keycloak/keycloak:26.8.0@sha256:b0f60d489d51c5d113390bdf5461d4c06e6051be026c05549f2e1e10ec352bcc`.
Consumer image:
`sha256:9c08d80d0f63d9972d8d3f3008782ffb3e9443784a2bb2f4940f63a64cf8b7eb`.

The fixture-auth audit remains green on PostgreSQL 16: 66/66, no skips, verified
cleanup (`290e1ddfd6064ce682f762e7e24beba1`). A parallel PostgreSQL 18 fixture failed
at Docker network creation before any tests (`16732a9bb8024aedbccb8a67ef77c39e`),
with unresolved original cleanup. Its subsequent exact-owner inventory is empty;
the original failed receipt stays unchanged. The sequential rerun passed 66/66,
zero skips and verified cleanup (`2f88329d45ab4f00a06bd87ce2567c64`).

Independent read-only review found no critical/important authentication defect.
Interrupted CA/config generation delivery and staging residue recovery remain
assigned to issue 9. Service TLS ingress/drain remains issue 11. The deployment
identity profile still uses synthetic sandbox execution; it is not production
inference or billing certification. Configuration and CLI examples are in
[identity.md](../identity.md).

## Persistent upgrades and restore

An explicit operator CLI creates schema v2 or transactionally upgrades v1 under
an advisory lock. Nonempty legacy rows require exact per-run archived scope
records; ambiguous attribution aborts. Identity/idempotency/request/assets/phase
remain unchanged. V2 reruns reject conflicting scope. Runtime roles cannot
update the version ledger, and replicas never invoke migrations. Fresh fixture
provisioning delegates application DDL to this versioned implementation.

Unit and functional CLI tests failed before implementation; current local suite
has 100 passing tests. Initial persistence lanes passed 24/24 on each major
(`5ae556e4dd884fd7839f81b9e66b8410` / `02a85cabf5ca4874bc29e9c945c7428d`).
Review identified a fresh-database edge: supplied legacy records were silently
ignored. Real regression failed (`0e660490cfd342faa603e19fd4462f7b`) before adding
exact empty-database validation. Original failed receipt and verified cleanup
are preserved.

Final full audits: **70/70 on PostgreSQL 16 and 18**, no skips, cleanup verified
(`e8367df3a0d3411bb0f943033524a6bf` / `39c6958060434a799c772fb4719d816e`).
Image: `sha256:ffd91a647b16b7d9394bc505f1f989d739bc4da933279af22b44f306a891c651`.
Owned pg_dump/restore into a second database preserves waiting review/revisions,
unknown usage and uncertain starts. A restarted replica verifies and resumes a
restored approval without inference; the original database remains independent.
All original fields survive v1→v2 and idempotent migration rerun. The protected
backup is deleted only with the owned fixture, never exported as public evidence.
Rollback is reviewed backup plus compatible pinned image, not destructive scope
removal. Deployment-specific HA/PITR/RPO/RTO qualification is separate; see
[persistence.md](../persistence.md).

## Constrained recovery and credential generations

Owner terminal `recover` inspects filtered run/usage views; mutations require
named action and exact reviewed revision. Tokens come from environment, origins
require HTTPS or explicit loopback lab mode, responses are bounded and redirects
are refused. There is no mutation retry/revision-refresh loop. Uncertain starts
allow inspection only; interrupted retry requires explicit effect-risk consent
and remains subject to the SDK budget. Lost mutation replies report unknown
outcome rather than assuming failure. Receipt recovery adds no provider call.

Credential delivery now stages complete private config/CA generations and
atomically switches the existing service.json path. Pinned CA paths retain a
matching generation through restart. Process abort leaves the prior generation
active and does not block a later fresh staging name. Old/orphan generations are
retained privately for reviewed retirement. File metadata, generation child and
parent directories sync before pointer publication, followed by volume root.
Review caught missing generation-parent sync and pre-owner file sync; both actual
filesystem ordering regressions failed before the correction and now pass.
Process-abort proof does not certify physical storage/host-power-loss behavior.

New unit/CLI tests failed before implementation. The previous image failed the
delivery-abort integration contract (`36fb3035fbb042309c3325d939074f35`, cleanup
verified), while its terminal receipt recovery already passed. Current local
suite: 113 passed. An unexpected dispatch regression also failed before curated
HTTP handling; real database errors containing private row details now emit only
safe class/stage/SQLSTATE and never raw ASGI tracebacks. This portion of issue 13
was brought forward to make recovery diagnostics safe.

Final audits **75/75 on both PostgreSQL majors**, no skips, verified cleanup
(`686d5cae7841415ca004ee03c9b93f45` / `85c0c06ac3524628a2f9551e99738841`).
Image: `sha256:3cceb301752e9e60a70a69f0bb2d5a7720d92929e76959e4770f5fd33d73faee`.
Keycloak TLS lane: 19/19 with a staged different-CA abrupt exit and successful
old-generation authentication after B restart. PostgreSQL 16 final receipt
`383ff7826f99458b85438be9608dfda6`; PostgreSQL 18 earlier process-abort receipt
`d5f2e60af07b405c97596d2c2c4b775c` preceded the durability-only correction.
Independent review reports no remaining important finding. Runbook and concrete
terminal commands are in [recovery.md](../recovery.md).
