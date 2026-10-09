# Release train — 9 October 2026

The maintainer authorized committing all changes, version bumps and publication
across all four repositories. Releases use GitHub assets with SHA256SUMS,
immutable source commits and downloaded-wheel verification. No paid inference.

| Repository | Release | Included distribution | State |
| --- | --- | --- | --- |
| Prosaic | Existing 0.3.1 | Core 0.3.1 | Unchanged; verified at release tag ee145ef |
| Runtime | [0.7.0](https://github.com/B3Cognition/prosaic-runtime/releases/tag/v0.7.0) | Recorder 0.1.1 | Published; native 11-job matrix and downloaded assets verified |
| Harness | [0.6.1](https://github.com/B3Cognition/prosaic-harness/releases/tag/v0.6.1) | Store 0.1.1 | Published; native five-job matrix and downloaded assets verified |
| Integration lab | [0.2.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.2.0) | Application and terminal runner | Local released gates verified; final native promotion record is in release notes and VERIFICATION-0.2.0.json |

## Evidence and rulings

- Prosaic: 432 Python tests, 55 frozen TypeScript-reference tests, wheel/sdist
  build and ten installed-wheel CLI checks passed. No source changes or version
  bump are needed; main already equals its existing 0.3.1 release tag.
- Runtime: reviewed readiness fix integrated into main. Local core final suite:
  456 passed, one framework-interpreter-specific skip. Recorder 39/39 on each
  PostgreSQL major, no skips, verified cleanup. Initial setup failures were due
  to driver privileges/import path, corrected without a production change.
- Runtime's first native CI run `37959748276` passed ten jobs; macOS Python 3.13
  exposed the 40 ms heartbeat test scheduling assumption. Controlled 80 ms
  startup reproduced it; actual observed-output/stopped-thread checks now pass.
  The unpublished draft was updated to final commit
  `109df2c350b9b0baa2c4074bb23aa7e8222c9395`. Final native run
  [37961267252](https://github.com/B3Cognition/prosaic-runtime/actions/runs/37961267252)
  passed all eleven jobs: three operating-system/architecture targets, Python
  3.11/3.12/3.13, and PostgreSQL 16/18. Downloaded assets matched before publication.
- Harness: preserved upstream documentation, integrated the atomic registration
  fix, and moved its regression onto the upstream owned fixture. Core 172/172;
  final adapter matrix 82/82 on both majors, no skips, verified cleanup.
  Wheels pin Runtime commit `109df2c350b9b0baa2c4074bb23aa7e8222c9395`.
  Native run [37964022649](https://github.com/B3Cognition/prosaic-harness/actions/runs/37964022649)
  passed all five jobs; source/tag commit `58404f5b20681911906b617466973a51fd960862`.
  All downloaded assets matched checksums before publication.
- Lab: committed all approved Lago work as `4ebb493`. Full host suite 239 passed
  against the newly downloaded published wheels; all five installed payloads
  matched the immutable release manifest and wheel bytes.
  Added required pinned-Lago acceptance (25 cases) and a 900-second outer budget
  around its 600-second test process, with watched negative regressions. All
  previous red audit/candidate/native receipts are preserved.
- Parallel local Harness qualification exposed Docker default-pool exhaustion
  and a network list/inspect teardown race. Explicit nonoverlapping fixture
  subnets and bounded inventory rereads have watched negative regressions.
  The same confirmed-disappearance rule covers lab inventory; stable engine
  failures propagate and cleanup scope remains exact-owned.
- Previous dependency bytes and the original manifest remain preserved in
  ignored cache history and `dependencies/releases-baseline-0.6.json`.

## Lab release qualification

Released mode on Docker Desktop Linux/arm64 passed **138/138 on each PostgreSQL
16 and 18**: audit 88, identity/Auth0 20, TLS ingress 5, pinned Lago 25. No skips,
failed cases or cleanup failures. Installed payload audit verified on every lane.
Consumer image: `sha256:c38bef7c89eaedcd165144e3211e26ef0748dc2b6dfd152fb163f7bbead73e80`.
Release manifest SHA256:
`f972db9d828b6ab0ffcf6ca210082e5cbc3b7678f5a1b8f42bbc482b9aafb472`.

Commands: `.venv/bin/python scripts/required_acceptance.py --postgres-version
16|18 --consumer-image IMAGE --export reports/release-0.2.0-pg16|18.json`.
Safe lane receipts are included in the release verification asset. Private raw
run directories and database credentials remain ignored and local.

The wheel imports/version checks passed in a clean environment installed from
locked third-party dependencies and all five published wheels. Source archive
inspection initially found missing runner assets; explicit public files now
include scripts, manifests, configuration examples, fixtures, documentation and
build exclusions. Extracted-source tests also exposed a missing workflow used
by a functional gate; the source manifest includes it. The wheel is a Python
module distribution; the checkout/source archive provides the complete runner.
The rebuilt extracted archive passes the complete **239-test** host suite.

Publication requires the final source commit's four native AMD64/ARM64 ×
PostgreSQL 16/18 CI cells, each with all 138 required integration tests. The
published GitHub release notes and `VERIFICATION-0.2.0.json` record the final
native head SHA, job results and sanitized receipts, plus downloaded-asset
checksum verification. This source ledger records the pre-publication checkpoint
without treating a local candidate as native evidence.

## Qualification boundaries

Published artifact/native test verification is separate from production
deployment. Actual Keycloak/Auth0 tenant settings, managed certificates/private
networking, monitoring, database HA/PITR/RPO/RTO and longer capacity qualification
remain operator acceptance. Repository required-check enforcement must be
configured for future protected merges. Synthetic provider estimates and Lago
fixture charges do not certify customer invoices or payment collection.
