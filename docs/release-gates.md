# Required release gates

CI runs unit/functional tests and owned `audit`, `identity`, `ingress`, `lago`,
`native`, `legacy-upgrade` and `qualification` lanes
on PostgreSQL 16/18 and native AMD64/ARM64 Linux runners. Actions and container
dependencies are pinned. Third-party Python dependencies require hashes;
released Prosaic wheels require exact versions/checksums and installed-payload
audit. Jobs use read-only repository permissions, no paid provider credentials,
and publish only a whitelisted summary. Raw `.lab` directories, JUnit capture,
database backups, Docker logs, tokens and private configs are never uploaded.
Runner labels follow [GitHub's hosted runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

Run one architecture/database cell locally after building the corresponding image:

```sh
.venv/bin/python scripts/required_acceptance.py --postgres-version 16 --export reports/required-pg16.json
```

The gate requires exact test counts, no skips or errors, zero test process exit,
verified owned cleanup and matching database/dependency provenance. Every lane
runs the same snapshotted immutable consumer image ID, even if another build
retags the development image concurrently. Image labels must match the manifest
and dependency mode, and a separate offline owned job audits the installed wheel
payload before any database/network/model fixture is allocated. Candidate images
are rejected in the released lane even when retagged.
Every lane
runs even if another fails. Missing/incomplete receipts fail; `--candidate` is
an explicit development mode and requires a complete candidate manifest.
The optional candidate workflow dispatch requires three successful exact-source
`Publish SDK` run IDs and source commits. It downloads each original
`qualified-release` artifact, verifies all wheel/sdist hashes and the exact five
renamed distributions, and requires Runtime's embedded Core receipt and Harness's
embedded Core/Runtime receipts to match the chosen upstream candidates. Missing
cross-repository Actions access fails the candidate job. It uses a separate
digest cache, manifest and clean image; active and historical release manifests
remain unchanged. It never substitutes a branch checkout or published URL.
Updating the acceptance suite also requires reviewing its count contract.

The reviewed collection contracts are audit88, identity20, ingress5, Lago25,
native39, legacy-upgrade10 and qualification2. Counts must match exactly, with
zero skips. Native exercises actual HTTP inference, two specialists and artifact
provenance, check/gate, structured approval, current grants and retained bundles,
fresh-process receipt adoption, finite budgets and a consequential fixture tool.
The application owns that fixture's restricted SQL domain table with unique
namespace/business key; journal claims and commits use real PostgreSQL. Separate
observable barriers cover claim, handler entry, effect persistence and outcome
commit, including worker loss and lost acknowledgement. No expiry or automatic
reconciliation is permitted.
Two budget cases exercise a batch of two valid tool attempts under the registered
tool cap of one and a separate denied provider follow-up. Both retain the first
completed domain/journal effect and incurred usage; receipt failure reasons,
independent handler barriers and actual HTTP counts prove the cap stopped dispatch.
The lower provider cap is a fixture-only trusted host binding in the frozen policy.

The legacy lane builds immutable Lab0.2.0 commit
`59752bef3e6b3ffde0ecbf38f34815d184043e20` with the five exact historical wheels
from `dependencies/releases-lab-0.2.0.json`.
CI's pinned checkout fetches full history so that exact historical object is
available; a regression starts from a real depth-one clone, applies the configured
history acquisition and verifies the archived original manifest and assets.
Public routes and original critical fault gates produce five old states. All old replicas stop before explicit
application schema v2→v3 migration. New workers use the same owned database and
the five byte-identical retained historical assets, selected by original
assets_hash. Original SQL receipts/accounting are compared, never fabricated with
new serializers. The public summary contains only counts, outcome codes and
image/manifest/source digests; the private fixture stays under its owned directory.
An unavailable engine records `not_qualified`; host checks alone prove neither
PostgreSQL behavior nor either required Linux architecture.

The release manifest now pins Runtime 0.7.0/recorder 0.1.1 and Harness
0.6.1/store 0.1.1, including schema/grant readiness and atomic lease registration
fixes. The original 0.6 baseline is preserved in
`dependencies/releases-baseline-0.6.json`; previous failing receipts remain
historical evidence. Local candidate receipts cannot authorize a release.
Current released-mode evidence is recorded in
[the release ledger](verification/release-train-2026-10-09.md), with final native
results in the GitHub release notes. Repository rules must still require the
four matrix checks for future protected merges; publication does not configure
branch protection.

Do not publish a consumer image based solely on a green local candidate. Release
the upstream fixes first, update provenance deliberately, run the required native
matrix, then require all four checks in branch protection. Preserve failing
historical receipts and the prior pinned images for compatible pending-run
recovery. Runner process/daemon failure cannot be called verified cleanup.
