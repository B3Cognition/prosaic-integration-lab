# Required release gates

CI runs unit/functional tests and owned `audit`, `identity`, `ingress`, `lago`,
`native-persistence`, `native`, `legacy-upgrade`, `qualification` and `conversation` lanes
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

Conversation qualification requires the full installed SDK API and complete
exact-source candidate lineage. It runs ordinary history/corrections, ordered
selection, quoted/fabricated approval denial, separate workflow usage, strict
authentication/body admission, restricted PostgreSQL roles, sealed capacity and
retained quotas, plus exact-owned worker loss at receipt and workflow barriers.
The HTTP surface uses saved JSON views; transient SDK streaming deltas are not a
Lab client protocol in this MVP. Every new case joins the exact count contract;
the historical eight-lane receipts remain unchanged.

Staged activation is explicit. The exact currently published SDK train has no
Conversation capability and retains the original eight released gates. Its
source job excludes only the three new installed conversation functional files;
all older functional tests and new pure host units still run. Explicit candidate
dispatch requires the coherent new five-package train, public capability, all
nine lanes, full source tests and distribution/demo checks. Once active released
pins point at that exact new train, released CI automatically requires the same
nine lanes and full conversation checks. Unknown/mixed versions fail admission;
the old train never emits a passing conversation receipt.

The separate distribution smoke installs both the Lab wheel and a wheel rebuilt
from its exact sdist in neutral environments, audits all five SDK payloads and
checks public capabilities/import ownership/CLI startup. Its optional required
stack execution uses the extracted sdist's owned assets and configuration. A
candidate distribution smoke is not ordinary public-index evidence, and missing
Docker/PostgreSQL cannot turn it into a successful skip.

Released CI also installs the exact supported five-package train in a separate
fresh environment through the ordinary PyPI resolver with dependencies enabled
and caches disabled. The verifier clears case-insensitive proxy variables,
bypasses system proxies and disables netrc/keyring authentication and prompts.
It verifies archive and installed-payload hashes, isolated
import ownership, CLI startup, `pip check` and public workflow construction. Its
sanitized receipt is exported separately; unpublished candidates cannot pass a
public-index adoption check by substituting their local artifacts.

The current collection contracts are audit88, identity20, ingress5, Lago25,
native-persistence26, native53, legacy-upgrade10 and qualification3 (230 per cell).
The Lab 0.3.0 released evidence below retains its original 216-case contract;
the added cases require fresh qualification of this source. Counts must
match exactly, with zero skips. Native persistence verifies actual SQL ownership,
immutable grants and storage bounds, concurrent migrations/reservations, every
supported JSON input type, journal fencing and lost acknowledgements. It requires
the same exact candidate lineage as the HTTP and recovery lanes.
Native exercises actual HTTP inference, two specialists and artifact
provenance, check/gate, structured approval, current grants and retained bundles,
fresh-process receipt adoption, finite budgets and a consequential fixture tool.
Thirteen further cases cover accepted provider reset, truncated JSON, 429/503,
malformed responses and deadline expiry before/after a committed tool, plus a
live worker's SQL partition, observed lease expiry, takeover and late-owner
fencing. Independent acceptance, usage and domain counts must reconcile; unknown
usage never authorizes retry. The proxy belongs to the exact-owned inventory.
The application owns that fixture's restricted SQL domain table with unique
namespace/business key; journal claims and commits use real PostgreSQL. Separate
observable barriers cover claim, handler entry, effect persistence and outcome
commit, including worker loss and lost acknowledgement. No expiry or automatic
reconciliation is permitted.
The native lane also runs the same adoption demo used by `demo --mode native`:
catalogue and proposal admission, idempotent start, a structured human pause,
invalid-response preservation, cross-replica completion, owner isolation and
two calls reconciled with the synthetic provider. Its public receipt excludes
fixture credentials, endpoints and private runtime state.
Every matrix cell separately runs the documented demo command after the eight
required lanes. This checks the fresh CLI entry point and its own verified
cleanup; the demo is a consumption example, not an extra qualification lane.
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
new serializers. A missing-usage run retains its original finite-budget block,
revision and unknown accounting even when approval is attempted; human choices
cannot authorize an inference retry or manufacture known usage. The public
summary contains only counts, outcome codes and
image/manifest/source digests; the private fixture stays under its owned directory.
An unavailable engine records `not_qualified`; host checks alone prove neither
PostgreSQL behavior nor either required Linux architecture.

The active release manifest now pins published Core 0.4.1, Runtime 0.9.0/recorder
0.3.0 and Harness 0.8.0/store 0.3.0 under the `b3-prosaic` distribution family.
The former patch family is preserved in `dependencies/releases-lab-0.4.0.json`.
The conversation lane is now required in released mode; fresh adoption results
are recorded in the [2026-10-13 ledger](verification/published-conversation-adoption-2026-10-13.md).
Actual PyPI and GitHub downloads match the original qualified bytes, including
the seven reliability fixes. The original 0.6 baseline is preserved in
`dependencies/releases-baseline-0.6.json`; previous failing receipts remain
historical evidence. Local candidate receipts cannot authorize a release.
The historical Lab 0.2.0 released-mode evidence is recorded in
[the release ledger](verification/release-train-2026-10-09.md), with its final native
results in the GitHub release notes. The earlier candidate train's successful
eight-lane matrix is recorded separately in
[the candidate verification ledger](verification/ecosystem-production-2026-10-10.md);
Lab 0.3.0 passed its separate released-mode matrix against the verified public
pins at source `59ea44b` in run `38119573605`. See
[public adoption](verification/public-release-adoption-2026-10-11.md) for its
exact source, original receipts and verified public release assets.
Repository rules must still require the
four matrix checks for future protected merges; publication does not configure
branch protection.

Do not publish a consumer image based solely on a green local candidate. Release
the upstream fixes first, update provenance deliberately, run the required native
matrix, then require all four checks in branch protection. Preserve failing
historical receipts and the prior pinned images for compatible pending-run
recovery. Runner process/daemon failure cannot be called verified cleanup.
