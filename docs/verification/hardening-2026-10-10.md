# Seven-fix SDK hardening adoption — 2026-10-10

This patch train fixes seven reproduced reliability defects. There is no public
API or format change. Lab application behavior, validators and acceptance counts
remain unchanged. Public SDK publication and Lab 0.3.0 remain pending.

## Fix scope

1. Core aborts filesystem mutation when nested enumeration or primary-file reads
   are incomplete, preserving existing generated output and manifest bytes.
2. Core replaces generated files atomically, retaining the old bytes on failure.
3. Core derives repeated backup paths from a canonical project root, including
   when the project is accessed through a symlink alias.
4. Runtime rechecks cancellation and absolute deadlines immediately before
   provider dispatch, after observers and accounting preparation.
5. Runtime bounds JSON and partial SSE reads by the invocation deadline and
   cancellation state, including continuous drip-fed bodies.
6. Runtime retains completed usage when a later native turn fails before an
   actual attempt, including Anthropic credential-file failures.
7. Harness tears down interrupted or failed lease-renewal setup without leaking
   local admission capacity or yielding an execution session.

## Qualified original SDK artifacts

| SDK | Exact qualified source | Successful run | Qualification records |
| --- | --- | --- | --- |
| Core | `6ac6cfdfd47dc70ecf68e441aa004f07c3be3822` | [38077144248](https://github.com/B3Cognition/prosaic/actions/runs/38077144248) | 15 |
| Runtime and recorder | `3566731c39a3fff2837acd93a96baa2187764206` | [38079159494](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38079159494) | 24 |
| Harness and store | `cba77d09d1844ff624911295aecd58021b457c08` | [38079961529](https://github.com/B3Cognition/prosaic-harness/actions/runs/38079961529) | 18 |

Qualification covers native source and installed-wheel checks, dependency floors,
and owned PostgreSQL 16/18 on Linux AMD64/ARM64. Runtime additionally runs macOS
on Python 3.11–3.13; Core includes Windows filesystem ownership checks. Original
source payloads, release receipts and upstream lineage were independently audited.

| Original wheel | Version | SHA256 |
| --- | --- | --- |
| `b3-prosaic` | 0.4.1 | `07710a5b9c94e3f3877241a4f5138d9b777d724098eb8e24b9738fb3cea28c51` |
| `b3-prosaic-runtime` | 0.8.1 | `3f74da0c7598c9e13f05de6b9080d6f1058bed3e1ca7ba0f960201bd34d3a1ae` |
| `b3-prosaic-runtime-postgres` | 0.2.1 | `f06e6e3d95ad5c182b9b3d5329b6cff0b3e7be997168d2bed59fa37741f32a30` |
| `b3-prosaic-harness` | 0.7.1 | `7cb170ad52f9170221360f2d0eac868c667d9e531dd39236db0bf46987c18db2` |
| `b3-prosaic-harness-postgres` | 0.2.1 | `e7dfcdd04ab1105be99ed8cc26e569d3b39d962046c6dbd3d885e641f75f1008` |

The Lab's exact-profile CLI downloaded the successful runs' original artifacts,
verified closed inventories, wheel/source hashes, canonical receipts and nested
Core→Runtime→Harness lineage, and selected only these five wheels. Fresh
`.cache/sdk-hardening/manifest.json` SHA256:
`f34ee296265038aa94a87519591103cbcb098f03a84f3b9724cf7394e744d34c`.
Candidate lineage SHA256:
`2ef782680e4f9f9a3e63856a1a86f36795408ed090b8eb453a5a1f9805e21e34`.

## Consumer verification and native gate

A fresh Python 3.12.14/macOS ARM64 environment installed the unchanged hash-locked
third-party graph and the five original patch wheels, with no editable SDK
checkout. All 537 source tests pass with no failures or skips. The existing
Starlette/httpx deprecation warning remains. The isolated Lab wheel and source
archive preserve all 51 Python modules and 79 public build inputs; the installed
wheel matches those module bytes. All nine copied native-client tests pass
outside Git against the installed application. Public factory admission and
reference reconstruction pass with zero validator callbacks and no model or
database execution. The installed CLI starts outside the checkout; SDK payload
audit and `pip check` pass after these imports.

The exact outside-Git archive of adoption source
`90efab0164e518089768e360291d9e4b884bd21b` passed all 537 source tests with
the explicit historical Git-only input. Its archive SHA256 is
`cb38080d2bdfb92c2bffb71c0316914df0fd5d389da475a2bd952d4d283307fc`.
Its isolated wheel SHA256 is
`1a3fae256bc67cf07ebbed327693a4b58883e2cf4c3bf5de4375c3c86562c815`;
source distribution SHA256 is
`54715549f48f1c99df0b283f2ac918134f06045acf0f3005cce59b9f10dada9d`.
The documentation-only correction at
`94f313e49707a09e7d0f3abbf818a9861bd6b14a` preserved all 51 module bytes,
79 public build inputs and candidate profile. Its exact Git archive SHA256 is
`4e18d2912f4b0d0b7a59428a70cacc7a4533a50fffc1ff4174f777d63cf30037`.
Archive documentation and inventory parity were checked separately; the 537
outside-Git test result belongs to `90efab0`.

## Native hardening closure

[Required run 38080612477](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38080612477)
succeeded at exact Lab source `94f313e49707a09e7d0f3abbf818a9861bd6b14a`.
All four Linux AMD64/ARM64 × PostgreSQL 16/18 cells passed 216 required cases:
864 total, zero failures, errors or skips. All 32 lane cleanups and four separate
native demo cleanups were verified. Each cell also passed 537 source tests with
one existing deprecation warning. Each demo independently observed two synthetic
model calls and remained billing-ineligible.

Original Actions API run/job/artifact records, four safe artifact archives and
logs were retained and independently checked against the closed provenance,
payload, image, count, baseline, migration and cleanup predicates. Their exact
manifest and lineage hashes match the profile above.

| Cell | Original artifact ID | Archive SHA256 | Receipt SHA256 |
| --- | --- | --- | --- |
| ARM64 / PostgreSQL 16 | 11679969523 | `553a748b855ba76a33ed95557f76e7dfd85553991e6155e7aa26e90a23a36ec9` | `25ecf7429b899cd7b193896af7e387bd4958142c30ee2b55b6d49ff357ac6eb5` |
| ARM64 / PostgreSQL 18 | 11680363917 | `2e9baaa23c297e3832c3e73b6652ba34af993ce725717dcc94a2106ba513bced` | `dc4d6b277351d3b33502e39e7348701560432a91858422215f9c8c7b3267f89c` |
| AMD64 / PostgreSQL 16 | 11680238760 | `5d2d6852ef0392d4cb5013e066c576c8a1d5f66eed30e1f670cb90d6b7fea32d` | `a72ad02f8ae0773f07f53f0c9277687a6eafff85c2f43e5460a793fd1f5034ce` |
| AMD64 / PostgreSQL 18 | 11680935264 | `6f40b6384a7d185726b5b29601a72e1a5b8ad374479fd9873a64188d3f0e0824` | `86537a5b8706a5c5f8b99d0d374f4629405edd8493fdc6219d17be0ad4a9088b` |

| Cell | Immutable consumer image |
| --- | --- |
| ARM64 / PostgreSQL 16 | `sha256:aa471dde603c629eeae80bb04559f0a78da3f3371edd96767fe1918ec103d6d4` |
| ARM64 / PostgreSQL 18 | `sha256:3c79e880960dc5fa395ee5753bea041214be085c2b24641e369ab12010ce908f` |
| AMD64 / PostgreSQL 16 | `sha256:7c227c77d2b40eff09bdf5f2e9a661586e0fbbc43eec0ec5b7f3bf7f62dae9bd` |
| AMD64 / PostgreSQL 18 | `sha256:ff0f8fe6381c2578c2491183d47534970991683c98227fb6a79fb049e78c3b6b` |

Both PostgreSQL 16 cells used
`postgres:16@sha256:ca0bd484cb98bf4b24eb1010e73fb3fcbd6714d240fbc1a10eea5b7dbecb641d`;
both PostgreSQL 18 cells used
`postgres:18@sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336`.
The immutable Lab 0.2.0 baseline source remains
`59752bef3e6b3ffde0ecbf38f34815d184043e20`, with manifest SHA256
`f972db9d828b6ab0ffcf6ca210082e5cbc3b7678f5a1b8f42bbc482b9aafb472`.
All ten legacy-upgrade cases per cell retained the explicit schema v2→v3
migration and recovery checks.

Documentation updates after this run record the qualified `94f313e` source;
they do not create a new native qualification claim.

The earlier [ecosystem ledger](ecosystem-production-2026-10-10.md) and
[native adoption ledger](native-adoption-2026-10-10.md) retain their original
sources, bytes and receipts. All historical verification documents, three
public/baseline manifests and the original `.cache/sdk-candidate/manifest.json`
remain unchanged. The earlier candidate manifest SHA256 remains
`e963b7a1e4b00194b8fdf6fbebb1d0dbcba659befe96a7144ebf204a608dfc1b`.

## Failed qualification retained

Runtime [38077973408](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38077973408)
at source `bfcb3e82e38f9b95c2c8d03e11503882246fd45c` failed two macOS Python
3.13 HTTP-timeout fixtures. Those CI logs reported zero server requests but did
not print actual attempts, so they do not establish whether preparation exhausted
the 30 ms budget or loopback delivery was delayed. A controlled reproduction
with 50 ms of preparation verified zero actual attempts after that budget
expired. This demonstrates a valid preparation-expiry path; no production
defect was demonstrated by the original CI failure. The final source adjusts
only that fixture to a 500 ms budget and 1.5 s provider delay, asserting one
actual attempt and elapsed time below one second. Production timeout checks,
retry behavior, selectors and skips were unchanged. The failed run is preserved
and is not selected by the recipe.

Sandbox-only verification failures are retained privately: the historical
`.venv` lacks current public SDK APIs; restricted loopback binds and PyPI DNS
also prevented initial checks. Authorized owned-fixture/network reruns passed.
These synthetic checks do not certify a live provider, customer billing,
production deployment, HA, PITR or long soak capacity.
