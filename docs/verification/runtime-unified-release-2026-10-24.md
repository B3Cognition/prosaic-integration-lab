# Runtime unified-pool release adoption — 2026-10-24

## Scope and status

Runtime 0.9.8 is published on PyPI and GitHub; Lab adoption qualification follows
below. Runtime 0.9.8 packages the merged native
and unified pool support, replay-safety corrections and Darwin cleanup repair.
The release-preparation [PR #11](https://github.com/B3Cognition/prosaic-runtime/pull/11)
updates version metadata, version-bound checks, examples and release notes, and
adds the installed native smoke program to the existing release gate.

PR #11 passed all **26 platform/PostgreSQL checks** and merged as
`a9433a68f60eeecf1946a398267f749c7ff89d8e`. Tag `v0.9.8` selects that exact
commit. Its [qualification run](https://github.com/B3Cognition/prosaic-runtime/actions/runs/40070376023)
builds once and requires the full source, installed, native confinement,
PostgreSQL and dependency-floor gate before same-byte publication is permitted.
That qualification passed all 15 active jobs; the two publication jobs were
intentionally skipped on the tag build. All **24 required qualification records**
were downloaded and verified against the same unchanged build receipt and exact
source. Ordinary main/tag CI also passed before promotion was dispatched.

The qualified Runtime wheel SHA-256 is
`d9d416baf9a7f4b87328532d41b281a2f6dbc9bafc744f973661a5cf6015a540`;
the sdist SHA-256 is
`a585cf445d5cdcc2fd2387d06688d9e0baffaeb5922cd359b33b3129e07c8665`.
Same-byte promotion was dispatched using qualification run `40070376023` and
the original Core run `38077144248` at
`6ac6cfdfd47dc70ecf68e441aa004f07c3be3822`. These are still qualified artifact
identities; actual public downloads and publication completion were then verified.

## Verified public artifacts

[Promotion run 40072336620](https://github.com/B3Cognition/prosaic-runtime/actions/runs/40072336620)
passed all platform revalidation gates and published Runtime through the existing
OIDC publisher. Its first immediate post-upload index check saw a transient 404.
Before retrying, an independent `index-check` downloaded the now-visible public
wheel and sdist and returned `already_published` with both original hashes.
Only the failed publication/dependent jobs were rerun. The pre-upload conflict
guard and skip-existing path retained the verified bytes; no rebuild, replacement
or tag movement occurred. PyPI and GitHub publication then both passed.

- [GitHub release v0.9.8](https://github.com/B3Cognition/prosaic-runtime/releases/tag/v0.9.8).
- [PyPI Runtime 0.9.8](https://pypi.org/project/b3-prosaic-runtime/0.9.8/).
- The actual [public wheel](https://files.pythonhosted.org/packages/d8/6e/754bb355aac527d263210a80611f90317a4b0f584e3c1b624f3b6c2d5383/b3_prosaic_runtime-0.9.8-py3-none-any.whl)
  has the qualified SHA-256 `d9d416baf9a7f4b87328532d41b281a2f6dbc9bafc744f973661a5cf6015a540`.
- Downloaded GitHub assets verify against their release receipt. Public and
  qualified `release-receipt.json` and `upstream-receipt.json` are byte-identical.
- Active Lab manifest SHA-256:
  `36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.
  Only the Runtime artifact entry changed; all other four entries are identical
  to the archived pre-unified manifest.
- Fresh SDK-only environment: `.venv-release-098`, Python 3.12.15 on macOS ARM64.
  `prepare_dependencies.py`, `install_dependencies.py`, strict `audit_install.py`
  and `pip check` passed using the active public manifest.
- `verify_public_adoption.py` independently resolved ordinary PyPI installation,
  verified its pip report, all five public wheel hashes, installed payloads,
  import ownership, CLIs and dependency compatibility. Temporary cleanup passed.

Runtime stays in the 0.9 compatibility range required by recorder 0.3.0 and
Harness 0.9.4. Core 0.4.1, Runtime recorder 0.3.0, Harness 0.9.4 and Harness
store 0.4.0 retain their existing public artifact pins. Recorder builds in the
Runtime release are compatibility witnesses and are not republished.

## Preparation evidence

- Independent review of the Runtime release diff found no issues.
- Runtime full local suite against the staged release tree: **1,432 passed,
  2 existing skips**, 467.15 seconds. Clean archive distribution checks used the
  staged Git tree rather than the prior release commit.
- Lab's explicit 0.9.8 train regression failed before recognition was added;
  all **32 release-gate tests passed** afterward. Existing conversation, context,
  consumer, accounting, fairness and rejection gates remain required.
- The archived `dependencies/releases-pre-unified-2026-10-24.json` is byte-for-byte
  identical to the previous active manifest, SHA-256
  `fc4eef2c3d32b641a9c6e12cc7b012464132e0cfbf5e87bbc4e848c72b71b95b`.
- Public CI now requires installed native/unified acceptance for the released
  SDK train. Historical candidate recipes explicitly select the archived train.

## Frozen experiment lineage

Review caught that shared quality provenance is part of the retrieval-memory
development freeze. The old freeze must not silently validate changed SDK
selection code or new public artifact metadata. Original snapshots are retained
byte-for-byte as `development-freeze-runtime-0.9.7.json` (SHA-256
`eeee1f1d10f060bebd987af0d45187c89ec8af257aba478b86f3ac41bcf72868`)
and `evaluation-freeze-runtime-0.9.7.json` (SHA-256
`fe610c6b99e72b975a10b676284ff17f136dab11f3bb4f4f653d4639219044cd`).
Their original evaluation-to-development binding is preserved. Reproduce that
cohort with its original source revision and SDKs, rather than validating an
archived snapshot against the new checkout.

The new freeze inventory also binds the archived public SDK profile now consumed
by the closed selector. A tamper regression failed before that inventory entry
was added and passed afterward. After verified public adoption, the active
snapshots were regenerated as an explicit 0.9.8 qualification lineage. A watched
regression requires byte-identical archives, the same suite/corpus/history/prose,
unchanged implementation except the freeze inventory, and only the disclosed
quality provenance dependency changes. No old result is rebound, rescored or
presented as a new release measurement.

- New development snapshot raw SHA-256:
  `9caf6d007c286534d15bd7feb582d9a129ed1b6e44af4f9eb7207f9191b0e700`.
- New canonical development freeze digest:
  `3a987a27206ed73e59bcae9ccba4fcedbd4677e5951ad3e07e69af00832c09ac`.
- New evaluation snapshot raw SHA-256:
  `0044815167bf1f482c4c6f12571b60ca6f4371b89a46e18026cf4dc42d56eaaa`.
- Unchanged evaluation suite digest:
  `63b6f48c709b4c2ff384fc926916960824d686ea1b98218fa751989a272eaca5`.
- All 12 packaged evaluation cases load and validate. **91 focused tests passed**
  in 18.15 seconds, including closed current/historical/private SDK selection,
  the archived-profile tamper regression, snapshot/input preservation and
  memory receipt recovery.

## Lab validation

All **14 installed native/unified acceptance tests passed**, 34.16 seconds,
against the actual public Runtime 0.9.8 wheel. The immutable released-mode Linux
ARM64 consumer image is
`sha256:e9cbd8d8994f1f23c83b978bfa4c7b9388e1eaee72b9d7f6a8302bed9d1ad3f6`.

All **51 offline checks passed** in that exact released-mode image: 18 provider
rejection, 13 CLI, 11 unified API and 9 native. Every lane verified cleanup and
zero live invocations. Containers had no external network, a read-only root and
an executable bounded temporary filesystem. Each report attested the released
manifest, Runtime 0.9.8, the exact source commit and the public wheel hash.

The full Lab suite passed **1,892 tests** in 498.23 seconds, with one existing
Starlette deprecation warning. Clean Lab wheel and rebuilt-sdist adoption passed:
public index resolution, installed payloads, isolated imports, dependency checks,
public construction, packaged assets and temporary cleanup all verified. That
local distribution check did not execute the real stack.

Real-stack acceptance on Linux AMD64/ARM64 with PostgreSQL 16/18 remains required
on the exact adoption PR head before merge. CI runs all nine acceptance modes,
released native acceptance and distribution adoption in every required cell;
the clean-distribution real-stack check additionally runs on ARM64/PostgreSQL 16.

## Boundaries

No live model call, quota exhaustion, credential renewal or new model comparison
is included. The historical 27-run benchmark, Markdown, inputs, results and local
180-second deadline remain unchanged. Its original candidate provenance does not
become release evidence. Original dirty Runtime and Lab workspaces are preserved;
release preparation uses separate clean clones and scoped branches.
