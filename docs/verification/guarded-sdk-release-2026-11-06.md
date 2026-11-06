# Guarded SDK release qualification — 2026-11-06

## Scope and current status

The maintainer authorized Runtime → Harness → Lab merge and publication after
Lab 0.9.5 completed. Lab 0.9.6 combines that release with the reviewed #45
blueprint and #46 guarded Harness companion, preserving both changes and all
historical evidence. The final Lab train is not yet qualified or published.

Runtime 0.9.14 is published from `58b6aeba941ef20702c6cd8e6584e11699a9803c`.
Candidate `42174683888` passed all 24 qualification records. Publication
`42178069476` completed after a diagnosed post-upload PyPI propagation race;
strict public downloads matched the original wheel and source archive.
An ordinary cache-free public-index install passed metadata/ownership, seven
saved value/magnitude cases, tagged-agent smoke and `pip check` without live calls.

Harness 0.9.9 is merged/tagged at
`580d56bf005e653e6066c872dbdf333311d1763f`. Candidate `42182110431` passed all
24 required records, including real PostgreSQL 16/18 cells, exact Core/Runtime
lineage and installed guarded cases. Publication `42184503091` completed on
attempt two after the same diagnosed PyPI visibility race. Strict public archive
downloads, anonymous GitHub receipts and a cache-free ordinary resolver install
match the qualified bytes. All 36 guarded cases, four unchanged saved Harness
compatibility regressions, ownership/metadata checks, smokes and `pip check`
passed. Initial missing simple-index visibility is preserved separately from the
successful post-propagation ordinary install; no uploaded bytes were replaced.

## Lab preparation evidence

- Host capability gates admit only the complete new SDK family and reject six
  partial/mixed upgrade variants. The initial new-family case failed, then passed.
- A separate regression initially failed when the previous Core 0.5 train lost
  its selectable provenance. Registering the preserved pre-guarded profile fixed
  it. The combined guarded-family, SDK selection and existing release gates
  passed 54 cases on macOS ARM64 using installed SDKs; these host-only tests are
  not final installed-train or real-stack qualification.
- Five prior manifests/provenance/freeze files were copied byte-for-byte to
  named pre-guarded snapshots and compared again with Lab 0.9.5's Git tree.
  Both active manifests now select the verified public SDK train. Current
  provenance/freezes bind it; historical snapshots stay intact.
- Current-lane provenance assertions now require exact released versions,
  source commits and hashes, public wheel URLs and installed payload audits.
  Historical candidate selection and receipt assertions remain separate. The
  new current-train and freeze assertions failed against the prior active pins,
  then passed after verified public pinning and freeze refresh. The complete
  focused provenance/admission/lineage set passed 74 cases.
- The installed Lab wheel passed 138 rule cases with the same three declared
  strict fee-grammar expected failures. Its first local run had one historical
  builder failure because this fresh environment lacked the pinned backend;
  installing the existing `rule-admission-build.lock` fixed the setup. The full
  lane then passed unchanged code/assertions. CI already installs that lock.
- Native acceptance passed 15 cases; installed reasoning acceptance passed 31
  with 58 scripted fixture controls, verified cleanup and zero live invocations.
  Frontend compilation/build and 16 source tests passed for the SDK badge update.
- Fresh wheel and rebuilt-source distribution consumers passed, including SDK
  payload audits, isolated imports, packaged assets, public-index adoption,
  construction, `pip check` and owned temporary cleanup. The independent ordinary
  public-index adoption verifier also passed for all five exact SDK pins.
- The fresh SDK-only macOS ARM64 / Python 3.12.15 source environment passed all
  2,096 unit/functional cases with one existing Starlette/httpx deprecation
  warning in 603.25 seconds. Command: `/private/tmp/lab-096-source-env/bin/python
  -m pytest -q --junitxml=/private/tmp/lab-096-source.xml`. The Lab application
  itself was absent from that environment; only exact released SDKs and the
  existing hash-locked third-party dependencies were installed.

Local Docker inventory previously timed out before resource mutation; no local
PostgreSQL pass is claimed. Local distribution proof explicitly records
`stack_executed=false`. Hosted mandatory real-stack and rule PostgreSQL cells
must supply the infrastructure evidence. Exact-head CI,
merge equality and postpublication public-consumer proof remain pending.
