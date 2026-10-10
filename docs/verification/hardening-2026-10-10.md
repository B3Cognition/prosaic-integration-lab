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
audit and `pip check` pass after these imports. The exact committed archive
check will be recorded with the final source and native proof.
New Lab native qualification remains pending: Linux AMD64/ARM64 × PostgreSQL
16/18 must each run the unchanged 216 required cases and a separate native demo.
The target total is 864 cases, 32 lane cleanups and four demo cleanups. These
counts are requirements, not a claim that the new native run has passed.

The earlier [ecosystem ledger](ecosystem-production-2026-10-10.md) and
[native adoption ledger](native-adoption-2026-10-10.md) retain their original
sources, bytes and receipts. All historical verification documents, three
public/baseline manifests and the original `.cache/sdk-candidate/manifest.json`
remain unchanged. The earlier candidate manifest SHA256 remains
`e963b7a1e4b00194b8fdf6fbebb1d0dbcba659befe96a7144ebf204a608dfc1b`.

## Failed qualification retained

Runtime [38077973408](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38077973408)
at source `bfcb3e82e38f9b95c2c8d03e11503882246fd45c` failed two macOS Python
3.13 HTTP-timeout fixtures. A 30 ms invocation budget legitimately expired
during preparation before dispatch, so the fixture's one-request expectation
was invalid. The final source adjusts only that fixture to a 500 ms budget and
1.5 s provider delay, asserting one actual attempt and elapsed time below one
second. Production timeout checks, retry behavior, selectors and skips were
unchanged. The failed run is preserved and is not selected by the recipe.

Sandbox-only verification failures are retained privately: the historical
`.venv` lacks current public SDK APIs; restricted loopback binds and PyPI DNS
also prevented initial checks. Authorized owned-fixture/network reruns passed.
These synthetic checks do not certify a live provider, customer billing,
production deployment, HA, PITR or long soak capacity.
