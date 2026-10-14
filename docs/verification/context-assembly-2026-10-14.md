# Optional context assembly verification

Implementation consumes installed public SDK APIs. The host counter uses exact
JSON byte units for the two synthetic fixture models only. No production
tokenizer or live provider is qualified by these results.

## Local evidence

Host: macOS arm64, Python 3.12.14. Runtime source suite: 1153 passed, two explicit
live gates skipped. Harness: 823 passed, two explicit live gates skipped. Lab:
972 passed, one existing Starlette deprecation warning. Independent review found
retry allowance, native construction timing and endpoint-control admission gaps;
regressions and fixes are being requalified in the final candidate train.

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
