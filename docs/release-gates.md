# Required release gates

CI runs unit/functional tests and owned `audit`, `identity`, `ingress` and `lago` lanes
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
an explicit local development mode and requires the candidate manifest hash.
CI has no candidate fallback and never upgrades dependencies to make a red gate
green. Updating the acceptance suite also requires reviewing its count contract.

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
