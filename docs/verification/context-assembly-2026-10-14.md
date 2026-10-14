# Optional context assembly verification

Implementation consumes installed public SDK APIs. The host counter uses exact
JSON byte units for the two synthetic fixture models only. No production
tokenizer or live provider is qualified by these results.

## Local evidence

Host: macOS arm64, Python 3.12.14. Final Runtime source suite: 1159 passed, two
explicit live gates skipped (359.80s). Harness: 831 passed, two explicit live
gates skipped, one existing fork warning (130.80s). Lab against the final audited
installed wheels: 975 passed, one existing Starlette deprecation warning
(78.46s). Independent review found retry allowance, native construction timing
and endpoint-control admission gaps. All were fixed with regressions; a further
asymmetric-policy retry regression was fixed and re-reviewed. Final reviewer
found no material residual findings.

Final local development image:
`sha256:d261e95268043e5736dcc26b348804f68f9da75e98f4bfe7c80096a8884bd3b7`.
Final development manifest SHA256:
`ed9dd2554b64654da9423b4efb2427283965e73b10c1daf83ffc3186b33f0c5a`.
Final image PostgreSQL16 acceptance owner `0b7798cd048040d79b205fd3d80b4ee8`
and PostgreSQL18 owner `4a5666cd35094cc9b68f3f6e17feab4f` each passed103
tests with zero skips and verified cleanup (465.81s / 467.49s).

Full Harness PostgreSQL16/18 adapter and lifecycle lanes each passed186 tests
with no skips (128.38s / 123.86s), including schema1 migration, old-worker
refusal, owner/runtime role checks, recovery and fencing. Both exact standalone
fixture ownership manifests were cleaned with the ownership-validating helper.
Python3.11.15 macOS arm64 clean wheel dependency-floor smoke passed for both
SDKs and memory/file context storage; `pip check` passed. This is not Linux or
multi-platform CI evidence.

| Local wheel | Source | SHA256 |
|---|---|---|
| Runtime0.9.4 | 20489c1e891ced4512619dcef5e5eaf68eca2ec4 | d19fd15e1209a876b79cddd19bf5e5b813e746c22b48c73a9434dea00ca1d67d |
| Harness0.9.0 | cac445727b7258dea7334ae75f75b6bd8752ac74 | 0fc3396568299f2a714e6f10f58e65c1a17b5355a2f811c6ae6e44da1088eba8 |
| Harness PostgreSQL0.4.0 | cac445727b7258dea7334ae75f75b6bd8752ac74 | aa3bfd37f6d2bfd4e6cbb4adc506c0e75796b82b9a359604ccfeec1488e3677b |

Candidate curation preserves the original Core0.4.1 and Runtime PostgreSQL0.3.0
public payloads. It verifies exact-source successful Actions run metadata and
receipt/upstream lineage for the new SDK candidates before selection. Rebuilt
same-version Runtime adapter bytes never replace the original Lab release wheel.

Draft PRs: Runtime[#6](https://github.com/B3Cognition/prosaic-runtime/pull/6),
Harness[#7](https://github.com/B3Cognition/prosaic-harness/pull/7),
Lab[#16](https://github.com/B3Cognition/prosaic-integration-lab/pull/16).
Runtime exact-source qualification run
[38542535522](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38542535522)
is in progress. User approved pushes, draft PRs and CI; merge/publication remain
pending. Local results do not replace successful required CI receipts.

Development consumer image:
`sha256:00eb9c706df54def11a195cc60694c1f61ec17fc6d186567134dd733d503564b`.
Development manifest SHA256:
`563441e7f76eecbb9c037d6a192c331fdc9c48bb11095bd7459f50d05a94bdf9`.
These are local development artifacts, not released or Actions-qualified bytes.
The public release manifest is unchanged.

| Lane | Resource owner | Result | Cleanup |
|---|---|---|---|
| PostgreSQL 16 acceptance | b6208f75a69c405fbe7cbf7e5d77591b | 103 passed, zero skips | verified |
| PostgreSQL 18 acceptance | 144083400e864b8da368b3a85c2db070 | 103 passed, zero skips | verified |
| PostgreSQL 16 demo | cf0765dc51fd42ce93192f64d6a0c946 | comparison captured | verified |
| PostgreSQL 18 demo | a8a6dbc5e0be421b846c3aca635cd788 | comparison captured | verified |

Each private `.lab/<owner>` evidence directory retains its image/provenance,
result and cleanup records. Both acceptance processes returned zero with empty
failed-test lists. Their outer release receipts correctly remain
`not_qualified`: development candidates lack successful exact-source Actions
lineage. Both demos made nine independent fixture calls and captured the
four-case quality comparison, including an older-preference `lostContext` case.

Initial PostgreSQL 16 run exposed two assertion mistakes: volatile accounting
`as_of` timestamps and a fixture usage expectation of 5 instead of 125. Fixed
assertions compare stable accounting counts and the actual fixture usage;
production admission and receipt validation were unchanged.

## Writer rollout

Keep context policies absent while draining old writers. Explicitly migrate
existing file namespaces with `migrate_context_storage()` and PostgreSQL
conversation storage with owner-role `migrate-conversations`. Verify version-2
readiness and runtime-role permissions before enabling either purpose's policy.
Old PostgreSQL workers reject the new contract. Existing version-1 records stay
readable; context-enabled new sessions use version 2. Preserve full source
history and frozen selections across recovery. Explicit retries require the
existing effect-risk acknowledgment.

## Remaining release qualification

Review fixes must pass fresh source and installed-wheel checks. Complete the
existing Python/platform and PostgreSQL 16/18 release lanes using successful
exact-source artifact receipts; retain original Core and Runtime PostgreSQL
wheel bytes. Promote only authorized qualified artifacts, verify public hashes,
archive the previous Lab manifest and rerun public consumer adoption. Until
then, this evidence supports synthetic development validation only.
