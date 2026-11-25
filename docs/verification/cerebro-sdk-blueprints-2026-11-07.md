# Lab 0.9.8 SDK and blueprint qualification

## Authorized scope

The maintainer requested a new Lab release with the latest released SDKs and
blueprints for each added feature. Work is isolated on
`codex/lab-098-sdk-blueprints` from main
`5da9abe3c10703ae6d3d4691e3fc9d2c6d37e155`. Original companion worktrees and
normal dirty checkouts remain untouched. Native execution follows the approved
Lab design and [release plan](../superpowers/plans/2026-11-07-latest-sdk-blueprints-release.md).

## Exact dependencies and historical preservation

- Runtime 0.9.16: source `f108405aea29ec894e0892222a00461b938a2e98`, public wheel
  `d2c569a1bfe233497518519f79f673023f8238ab25e053006b1e781d726db1af`.
- Harness 0.9.11: source `294e935f70e2cfcce2c4ca80dbed5d8aa3977b83`, public wheel
  `2d9482cae429bd04587c0d58f111906019de9f068834f04727088815c70ca62f`.
- Core 0.5.0, recorder 0.3.0 and store 0.4.1 retain their existing public bytes.
  The five installed distributions passed the strict payload/ownership audit.
- Both previous manifests, public provenance and current freezes were copied
  byte for byte before advancement; hash regressions pin all five snapshots.
  Current freezes preserve corpus, prose, suite/scoring and historical-source
  digests. The old train remains selectable through its archived profile.

## Observed local verification

- Python 3.12.15 on Darwin arm64, isolated virtual environment. Initial system
  Python was 3.9 and could not install the lock; only the newly created private
  environment was replaced. Locked build tooling is installed separately.
- Current main's complete ten-job post-merge CI was green before this branch.
  Fresh focused baseline checks passed 38 cases. Explicit `--runxfail` reproduced
  the three historical fee failures under Runtime 0.9.14 (four controls passed).
- New train tests first failed 9 cases, with 5 negative controls passing.
  Admission, archives and profile selection then passed all 14 cases.
- The same unchanged fee assertions passed all 7 cases on Runtime 0.9.16.
  Only obsolete active-lane xfail marks were removed; historical expectations
  and the independently saved upstream review regressions were not weakened.
- Current/archived profile and memory lineage tests first reported four
  expected failures after repinning, then all 50 focused cases passed after
  explicitly advancing the active profile and freeze lineage.
- Copy-out acceptance first failed all 15 missing-blueprint cases. The expanded
  suite passed 29 cases, covering real HTTP delivery/body isolation, explicit
  tool grants, rejection/repair/version/freshness cases, CLI opt-in and caps.
  The copied runner required an explicit local `runpy` load under isolated
  Python; interpreter policy must retain the SDK's 30-second/one-round limits.
  These are consumer example fixes, not SDK engine modifications.
- Final copy-out acceptance passed 29 cases in the source environment and
  29 cases from a fresh installed wheel under isolated Python. Both wheel and
  source archive contain all 30 new blueprint resources, including dot-files.
  The final SDK/profile/freeze/image-inventory group passed 51 cases.
- The first full source run reported 2,120 passes and two environment failures:
  its isolated SDK-only subprocess assertions found Lab installed editable.
  Removing only that Lab editable installation made both unchanged tests pass;
  a complete rerun is required below. SDKs remained public wheels throughout.
- The installed rule run exposed two stale candidate/fee-gap prose checks and
  a missing locked historical-builder backend. Historical PR provenance was
  restored, the current documentation check now requires ordinary fee passes
  and explicit v2 readmission, and the locked backend was installed. All three
  focused checks passed; the complete final rule run remains required.
- Frontend: 16 tests passed and the committed offline asset build succeeded.
  Local Docker preflight was unavailable before engine mutation; no local
  image, real PostgreSQL or live-provider pass is claimed.
- Final rebuilt-wheel acceptance passed all 141 rule cases with zero xfails or
  skips, and all 29 copied feature cases. Installed native/unified and reasoning
  acceptance passed 46 cases. Pip check passed.
- Fresh wheel and rebuilt-source distribution qualification passed public-index
  verification, exact payload/ownership audits, isolated imports, copied feature
  execution, native/unified controls, sandbox controls and temporary cleanup.
  Its local receipt explicitly records `stack_executed=false`.
- Fresh whole-branch review found no implementation defects. Its one README
  version mismatch was corrected with a watched consistency failure/pass.
- Complete corrected source suite: 2,122 passed, zero failures or skips, in
  575.78 seconds; one existing Starlette/httpx deprecation warning. The two
  SDK-only subprocess assertions passed unchanged in this run.
- Initial hosted rule run `42398553681` passed all 141 rules in each cell,
  then exposed one copied-runner defect in each feature lane: `Workflow.load`
  tried ambient `prosaic` instead of the explicitly invoked Python environment's
  CLI. No PG continuation pass is claimed for that failed run. A strengthened
  local test with no ambient executables reproduced the same failure. Selecting
  the sibling Core CLI fixed it; all 29 source feature cases then passed. This
  is a Lab-owned host example fix; SDK engines and assertions remain intact.
  All 29 isolated installed-wheel feature cases and the complete fresh wheel/
  rebuilt-source distribution gate passed after the fix, including the new
  no-ambient-PATH condition, payload/ownership audits and cleanup.

## Required remaining evidence

Hosted consumer image and real PostgreSQL matrix; exact-head ten-job CI;
original qualified archive hashes and equal merged trees; publication and actual
public-download/fresh-consumer proof remain pending at this checkpoint.
No local Docker or live-provider pass is claimed. No live calls are authorized.
