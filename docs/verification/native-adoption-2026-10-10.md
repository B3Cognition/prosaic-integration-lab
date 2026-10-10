# Native workflow adoption verification

Checkpoint: 2026-10-10. The Lab adoption implementation is committed at
`60c6e7bc306b965b5074a536f2bb612d7d567322`. It adds a candidate-first setup
recipe, the native demo and a client/host consumption guide. Public SDK
publication and Lab 0.3.0 remain pending matching PyPI publisher setup.

Start with the [quickstart](../../README.md#try-the-native-workflow) and
[consumption guide](../consume-native-workflows.md). The demo drives the actual
catalogue, immutable proposal, idempotent start, human interaction, cross-replica
resume and owner-scoped usage APIs. It checks invalid/stale responses and foreign
ownership, caps the synthetic provider at two calls, exports only checked fixture
fields and requires verified cleanup. It does not receive a qualification label.

## Artifact and host checks

- Complete source suite: **537 passed**, zero failures/skips.
- Fresh Python 3.12.14 environment: hash-locked third-party installation, all
  five original SDK wheels, installed payload audit, public admission/reference
  reconstruction, private-binding redaction and `pip check` passed. Admission
  invoked no validator callback or model. Omitting the model tier exercised the
  host default under a named-tier-only policy.
- Isolated Lab build and fresh installation: **51 Python modules** match source,
  sdist, wheel and installation; **79 public build inputs** match source/sdist.
  The candidate profile and consumption guide ship in the source archive;
  private and ignored paths are excluded.
- Installed demo/CLI/cleanup boundary tests outside Git: **9 passed**.
- Exact committed source archive outside Git: **537 passed**. Its historical
  object regression uses the explicit `LAB_HISTORY_TEST_REPOSITORY` input; SDK
  imports come from the installed original wheels and app code from the archive.
  The first invocation omitted that input (536 passed, one failure); its output
  is retained. The subsequent SDK payload/bytecode-cache audit passed unchanged.

The locked test client emits one existing Starlette/httpx deprecation warning.
These local checks prove artifact consumption, not native SQL or deployment.

| Verification artifact | SHA256 |
| --- | --- |
| Lab verification wheel | `a84f9c981588f17da3365040adbba14d2a575494db185298e8e46868cfd45d5a` |
| Lab verification sdist | `70ca86a0137ae49d5fa1d637a52cd9d21250d355b8a23cb05d54b4fd8c70a8ce` |
| Exact committed Git archive | `5972a035bfc57f8be8d3386d925568a1dbd1cce60fa1a96f81b92eaf88526088` |

These artifacts verify source `60c6e7b`; they are not a new Lab release. Later
documentation-only evidence updates do not alter its qualified executable bytes.

## Native qualification

[Run 38065626859](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38065626859)
checks this exact source on Linux AMD64/ARM64 with PostgreSQL 16/18. The reviewed
collection contract is 88/20/5/25/26/40/10/2 across the eight required lanes:
216 cases per cell. Every cell additionally runs the documented native demo CLI
with its own owned stack and cleanup. The run completed **successfully** in all
four cells: **864 required cases, zero failures/errors/skips, all 32 required
lane cleanups and four separate demo cleanups verified**. Each cell also passed
537 source cases. Every CLI demo completed with two synthetic model calls,
two complete ledger calls, no unresolved usage, billing-ineligible estimates,
all seven protocol checks and the same audited immutable consumer as its lanes.
The demos contain no qualification or test-count claim.

| Native cell | Required cases | Original safe receipt SHA256 |
| --- | --- | --- |
| [ARM64 PostgreSQL 16](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38065626859/job/114252556187) | 216 | `943366aa2f1743dc125e59604c99c30fb3bbaf85843f5eb1707e4b9e78396c8f` |
| [ARM64 PostgreSQL 18](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38065626859/job/114252556208) | 216 | `22831c3c849d0ade5ced23d6c04af388771ee66323496d989d28ccae9ebb27c6` |
| [AMD64 PostgreSQL 16](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38065626859/job/114252556169) | 216 | `b54e624e90c1ae520d4ef810a9c1ee72b9f6b639dccc3534db8cd4911ab8034c` |
| [AMD64 PostgreSQL 18](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38065626859/job/114252556009) | 216 | `ec75e6d143dbe7b01d944e4d143319c9e30704f829863c6f2836188ff5940ae4` |

Independent verification and a fresh root verification checked the four original
artifact archive digests, run/source identity, all eight closed count/provenance
contracts, installed payload and original SDK lineage, pinned database and
immutable consumer images, exact historical Lab 0.2.0 generation and v2→v3
migration, and the separate CLI result/report pairs. Full original safe receipts,
artifact metadata and private proof logs are retained in ignored local evidence.
CI publishes only whitelisted gate summaries as artifacts; private configuration,
database backups and local proof logs remain outside those exports.

The historical baseline remains source
`59752bef3e6b3ffde0ecbf38f34815d184043e20`, manifest SHA256
`f972db9d828b6ab0ffcf6ca210082e5cbc3b7678f5a1b8f42bbc482b9aafb472`.
Every cell generated the five original fixtures and passed ten recovery checks.

The candidate setup profile reverified the unchanged original three SDK runs,
their successful source identities, all original artifacts and embedded upstream
receipts. Candidate manifest SHA256 is
`e963b7a1e4b00194b8fdf6fbebb1d0dbcba659befe96a7144ebf204a608dfc1b`;
lineage SHA256 is
`34b5769f7ae7ef5f8a620d99549c0a442226707c28df8c301359fa289cb0b721`.
The [prior ecosystem checkpoint](ecosystem-production-2026-10-10.md) records
their exact sources, versions and five wheel hashes, plus the preserved old
860-case Lab qualification at its original source. It is not reused as evidence
for this new executable demo.

## Release boundary

Automatic released-mode PR run
[38065613338](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38065613338)
actually failed each source suite with 17 failures, 441 passes and 79 errors
against the preserved historical SDK pins: their public APIs lack `ToolClaim`,
`WorkflowBindings` and `WorkflowBundle`. No real-stack/demo step ran there. This
gate will close through actual ordered SDK publication and verified public-pin
adoption; an explicit candidate success does not substitute released-byte proof.

The active/historical manifests and Lab 0.2.0 version are unchanged. CI artifacts
are a temporary consumption channel with 90-day SDK retention. No paid provider,
live authentication/TLS deployment, soak/HA/PITR or customer invoice is qualified
by these synthetic examples.
