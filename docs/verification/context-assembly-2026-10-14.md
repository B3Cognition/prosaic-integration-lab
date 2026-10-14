# Optional context assembly verification

Implementation consumes installed public SDK APIs. The host counter uses exact
JSON byte units for the two synthetic fixture models only. No production
tokenizer or live provider is qualified by these results.

## Local evidence

Host: macOS arm64, Python 3.12.14. Final Runtime source suite: 1159 passed, two
explicit live gates skipped (359.80s). Harness: 831 passed, two explicit live
gates skipped, one existing fork warning (130.80s). Lab against the final audited
installed wheels: 977 passed, one existing Starlette deprecation warning
(75.89s). Independent review found retry allowance, native construction timing
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
Runtime first exact-source qualification run
[38542535522](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38542535522)
passed its four PostgreSQL cells but failed stale 0.9.3 expectations in installed
wheel gates. Those expectations and ordinary CI wheel paths were repaired;
production wheel smoke and mandatory installed metadata acceptance passed
locally. Replacement exact-source qualification
[38544660074](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38544660074)
at `5f0a02b923173286debd8c2c01951aba35d84377` is in progress.
The extracted-source distribution gate now also requires the context demo flag
and 103 acceptance cases; its process-double rejection/success regressions and
related gates passed68 tests. The staged capability-output expectation was
updated and passed7 functional tests, then the full977-test suite.
Final PostgreSQL16/18 demo owners `ef8b4e6f97984a4ca8fa0d5b18cd23ce` and
`ed04d3316a3f4cab8626b2b2373c2c2d` captured the comparison with nine independent
fixture calls each, and verified cleanup (38.61s / 38.49s).
User approved pushes, draft PRs and CI; merge/publication remain
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

## Release qualification and promotion

### Qualified exact-source candidates

Runtime qualification
[38544660074](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38544660074)
at `5f0a02b923173286debd8c2c01951aba35d84377` passed all nine native platform
cells, four PostgreSQL cells, dependency floors and the artifact gate. Harness
qualification
[38546680530](https://github.com/B3Cognition/prosaic-harness/actions/runs/38546680530)
at `1db61abf1b648affe1d67a5069f15ce9c9b4c9d3` passed the equivalent full matrix.
Both explicitly skipped package publication and GitHub release jobs.

Exact-source Lab candidate qualification
[38548867472](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38548867472)
at `32665dbb9d966efb257509ccd5fcca0fd61dc5ec` passed all four Linux AMD64/ARM64
and PostgreSQL16/18 cells. Each cell passed all nine required acceptance modes,
including 103 conversation/context cases. The ARM PostgreSQL16 cell also
qualified the extracted source distribution with the context demo and103 cases.
Baseline compatibility
[38545575978](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38545575978)
passed all four cells against the currently published train.

Real curation initially exposed a source-bootstrap import failure that pytest
had masked. An isolated subprocess regression reproduced it; `32665db` includes
the source-root bootstrap repair. Related curation/bootstrap/functional tests
passed26 cases and actual three-run curation then succeeded. No release lineage
was invented or substituted.

Qualified candidate manifest SHA256:
`0315cf67102b505d4a6593e76da7fe91e1b39896ea07b5dd306a22dc80c77782`.
Lineage SHA256:
`c29db44b88418e053e378018c98b85e74babb99c362c0f7d6e4d855e88755be9`.
Local consumer image built from those exact qualified wheels:
`sha256:8d44b544415853614c61b09498f4a8bec8e1079dd49f96a9e76a3695f2257fbb`.
All five installed payloads were audited; dependency consistency passed.

| Qualified wheel | SHA256 |
|---|---|
| Core0.4.1, original bytes | 07710a5b9c94e3f3877241a4f5138d9b777d724098eb8e24b9738fb3cea28c51 |
| Runtime0.9.4 | f2f88630933217cda791792d3a3341a36485690bbb39b81890a8f22ef2c4bde3 |
| Runtime PostgreSQL0.3.0, original bytes | 5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca |
| Harness0.9.0 | 6c9d2c2bcfcb6ac5720547db492d64526074431fa639ec2e030f88b2a633309c |
| Harness PostgreSQL0.4.0 | 35b6b9c4493b13187eed070403a45abe1f47522e5e0fd563b4514b492bd1703a |

Qualified local PostgreSQL16 owner `b5fcc8e476cd4d6f9d187ee873af9730` and
PostgreSQL18 owner `2fc454ce651c4a04be8ed169c5589924` each passed103 cases,
zero skips, and verified cleanup (455.21s / 456.20s). Qualified demos owners
`d54ca0d095f947988ab08a4d30c1254d` and `0156ddaad3454c9587170639f71e7ab4`
passed with verified cleanup (37.69s / 37.06s). Each captured nine independent
main-demo calls plus the34-request four-case comparison. Both reports explicitly
set `productionCounterQualified` to false. Exact qualified clean-wheel native
execution passed28 tests on both providers; v2 memory/file lifecycle smoke and
dependency checks passed.

All material independent-review findings are closed. Runtime0.9.4 stays in the
0.9 series so the original Runtime PostgreSQL0.3.0 dependency bound remains
valid. File migration is explicit, like PostgreSQL migration, to prevent old
writers from silently accepting the new contract. Binding admission validates
counter/endpoint declarations without untracked counter callbacks. Source-only
Lab CLI qualification uses SDK wheels with no installed consumer. These rulings
retain their consequences and historic evidence in the execution ledger.

### Promotion remains pending

Qualification is complete for synthetic context assembly. User authorization so
far covers branch pushes, draft PRs and CI; merging and package publication
remain pending. The active public release manifest still selects Runtime0.9.3,
Harness0.8.2 and Harness PostgreSQL0.3.0. A production tokenizer is not qualified.

Promote only authorized qualified artifacts, verify the actual public hashes,
archive the previous Lab manifest and rerun public consumer adoption. Retain
original Core and Runtime PostgreSQL wheel bytes. The development receipts above
remain historical evidence; the final exact-source receipts qualify synthetic
context assembly and its SDK/storage implementation, not a production tokenizer.
