# Lago implementation ledger — 2026-10-09

Plan: docs/superpowers/plans/2026-10-09-lago-billing.md. Design and native
execution approved by maintainer's Proceed.

- Baseline: 123 host tests pass; five installed release payloads verified;
  Docker Desktop aarch64. Existing codex/integration-lab branch.
- Ruling: use the current feature checkout under the existing approved native
  execution policy; preserve unrelated work and do not spawn implementer agents.
- Preflight: projection/scanner share immutable event/source identity; store
  and delivery share fenced claims; Lago fixture and runner share the existing
  intention-before-create manifest and exact-ID cleanup. No library changes.
- Task 1: 17 projection/scanner tests failed on absent modules, then passed.
  Covers strict cache quantities, exclusive reasoning semantics, scopes,
  stable identity across mapping revisions and 1001-call delayed rescan.
- Task 2: real outbox suite failed on absent module; first real Lago lane
  passed outbox durability/concurrency/fencing/role cases. Full task verification
  still pending readiness-negative cases and second PostgreSQL major.
- Task 3: HTTP boundary tests failed on absent module; 7 now pass. Fixture
  lifecycle regression failed before module creation, then passed.
- Ruling: use Lago's immutable bundled v1.55.0 demo image (source and index
  digest recorded in dependencies/lago.json) — contains PostgreSQL, Redis,
  API/worker/UI and supports arm64/amd64 — separate component image/version
  claims are not made. No upstream scripts are downloaded or executed.
- Host loader regression: first lane failed ModuleNotFoundError with cleanup
  verified. Host CLI now loads this lab's src explicitly; installed upstream
  wheel boundary remains intact. Two subprocess regressions pass.
- First actual Lago lane on PostgreSQL 16: 14 cases, 11 pass, 3 fail, zero skips,
  cleanup verified. Receipt eb44e52a0bf5486b9987e74de360f431 preserved. Investigating
  duplicate/reconciliation failures before expanding verification.
- Host suite: 150 pass with the existing Starlette deprecation warning.
- Duplicate failure root cause: event lookup serializes milliseconds while
  Runtime finished_at has microseconds. Watched precision regression fail, then
  fixed projection to freeze milliseconds before send. Exact comparison retained.
- Readiness negative tests: missing fencing grant, state constraint and integer
  attempts type each failed before checks were implemented. Restricted prompt
  reads and frozen event payload writes are denied.
- First green matrix: Lago lane 22 pass on PostgreSQL 16 and 18, zero skips,
  cleanup verified. Receipts 84c216a0b55648569e699f92946018d9 (16) and
  15f52a57eb0140629722562d035f8971 (18). Real SIGKILL barriers before send and
  after remote acceptance recover without model redispatch. Final review fixes
  require fresh matrix evidence below before completion.
- Reviewer found stale unresolved scans could poison newer complete evidence;
  unsupported provider/credential identities were admitted; open-period checks
  were missing; remote payload conflicts did not block sibling dimensions.
  Watched provider and actual PostgreSQL conflict regressions fail, then fixed
  admission, monotonic first-observation projection and source-wide conflicts.
- Ruling: distinguish absent observations from persisted unknown observations;
  only the first may advance. Ignore stale absent-observation snapshots only
  when immutable intent, locator, account scope and mapping all match.
- Ruling: pin current-usage period in durable mappings before model calls;
  gate delivery/reconciliation on unchanged bounds and original event timestamp.
  Out-of-period source failure blocks sibling delivery, never retimestamps usage.
- Test fixture correction: missing-usage observation had been copied for the
  pagination fixture. It now selects complete evidence and deterministically
  delays the 1001st sorted call. Independent synthetic token literals and a
  fractional-cent per-charge rounding case prevent mirrored-ledger false greens.
- Final review fix matrix: 25 required Lago cases pass on PostgreSQL 16 and 18,
  zero skips, cleanup verified. Final receipts f7fc3d9c87ce480c8ee09338f6dce3bb
  (16, 297.83 seconds) and 8c73867a44db45e9a9a6fe853ab6beff (18, 302.87 seconds).
  Both record immutable consumer/Lago/database images, released-manifest checksum
  and verified installed wheel payload audit. Fixture retail per-line half-up
  rounding is now pinned by 0.8c + 0.5c + 0.8c -> 3c actual Lago usage.
- Default-pool exhaustion caused one diagnostic setup and a Lago 18 setup to
  fail with unresolved network-create intentions. Original receipts retained;
  successful supplemental exact-owner inventories prove no surviving resources
  for 1b7ae4601c214cb0a73bc591855703cf and 3c4da6a7c9284cfbaaa457cd1b6b884d.
- Ruling: all new owned fixtures select an explicit free 10.250.x.0/24 subnet
  against Docker/Podman inventories — permits regression lanes when the engine's
  default pool is exhausted, without removing unrelated networks. Null Docker
  IPAM and Podman inventory regressions watched fail, then pass. Existing network
  manifests/resources stay untouched. Actual Podman/amd64 execution is unverified.
- Existing deterministic 16: 21 pass, no skips, cleanup verified; receipt
  6b8173e4384348ab81571ae99a1e6cea. Recovery 16: 27 pass, no skips, cleanup verified;
  receipt a377145b106a4ba0b381dd1b16997787.
- Latest host suite: 188 pass, one pre-existing Starlette deprecation warning.
  Wheel/sdist build passed; installed five-wheel payload re-audit passed;
  git diff --check passed. No third-party dependency changes or upstream fixes.
- Supplemental cases explicitly check rejected conflicting Runtime observations
  retain original evidence and frozen pricing/subscription mapping cannot change.
  Verified on PostgreSQL 16: 13 pass, zero skips, cleanup verified; receipt
  916eef62d90343f6b3eded271caf45ef. Fresh exact-owner inventories confirm no
  surviving containers/networks/volumes for either final matrix or supplemental
  run; generated secrets are absent and retained reports pass sentinel checks.
- Ruling: preserve the current feature branch and leave this change uncommitted
  while other authorized tasks are modifying the same runner files. A whole-file
  staging operation would capture unrelated image-provenance/release-gate work.
  No merge, push, release or deletion is part of this task.

## Completion

Tasks 1–5 complete with the rulings above. Required open-period fixture behavior,
durable failure delivery, Prosaic public-API integration, hostile/unknown evidence,
matrix and cleanup gates have executable evidence. Four important independent
review findings were reproduced and fixed in one regression pass. Rejected
observation writes and mapping immutability have supplemental actual-stack proof.
The machine-readable retained summary is `2026-10-09-lago-linux-arm64.json`.
No source changes were made in Prosaic core, Runtime or Harness.
