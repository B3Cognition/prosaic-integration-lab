# Implementation ledger — 2026-10-09 integration lab plan

Plan and native execution authorized by maintainer's “proceed” after local
endpoint credentials were identified. Branch: `codex/integration-lab`.

- Preflight: Tasks 1/2 share image/provenance; Tasks 2/3 share explicit schema
  provisioning; Tasks 3/4 share immutable owner attribution and assets; Tasks
  4/5 share observable fixture gates; Task 6 consumes runner/result contracts.
- Ruling: Work on a feature branch in the current checkout, preserving the
  uncommitted reviewed plan/config additions; no sibling source modifications.
- Ruling: Prosaic v0.3.1 tag resolves to Runtime's pinned commit. Install the
  original five release wheels with dependency resolution disabled after
  hash-locked third-party installation. Preserve original VCS METADATA and
  audit every installed wheel payload; this avoids mutable VCS resolution
  without rewriting upstream distribution contracts.
- Authenticated local model discovery succeeded. Select 7B Qwen Coder for
  optional local smoke. No key contents were printed or copied into Git.
- Dependency verifier: observed five failures before implementation, then five
  passing tests. All five downloaded wheels match release SHA256SUMS.
- Docker Desktop started; daemon reports Linux/aarch64. Python host 3.12.14.
- Consumer image and host installed-release payload audits passed. Original
  upstream METADATA is retained unchanged.
- Unit suite: 21 passing tests. HTTP acceptance failed against the scaffold,
  then 13 checks passed after public SDK implementation.
- PostgreSQL 16/18 deterministic acceptance: 20 checks passing, no skips,
  cleanup verified. Covers owner isolation, cross-replica progression, stale
  decisions, key races, uncertain starts, asset drift, exact decimal estimates,
  rejected-output usage and missing final usage.
- PostgreSQL 16 load lane: 22 passing checks, no skips, cleanup verified.
  Two blocked executions reject excess work; B remains usable.
- PostgreSQL 16/18 recovery: 25 passing checks, no skips, cleanup verified.
  Receipt-persisted worker loss recovers without dispatch; missing receipt
  requires explicit consent. Prepare failure prevents dispatch, observation
  failure does not redispatch, exact replay does not duplicate estimates.
  Evidence owners: `a2e758e966fe4c9985ff7f057045f462` (16),
  `68e0ae3e885e489592ccb89b86871fd2` (18).
- Ruling: Gate public Harness `on_event` at `accepted`, after receipt
  persistence and before the next checkpoint. Fixture receives event type
  only, never private event payloads.
- Ruling: Docker reassigns ephemeral ports on restart. Re-read ports from the
  same verified container ID. Reproduced this failure before fixing the test.
- Local smoke: exit 0, no timeout, expected output, 85 reported tokens. Initial
  artifact discovery used the wrong source; corrected via public `source`
  constructor option. No library code changed.
- Host Python 3.12.14/libpq 18.0.6; Docker Linux/arm64. Wheel/sdist builds passed.

## Remaining plan coverage

Tasks 1–4 have an executable first slice; Task 5 has fault/load coverage but is
not complete against the full spec. Missing-schema/adapter-corruption negative
cases, tool loops, quarantined/conflicting evidence, token-budget recovery,
changed-default/scope recovery, public-log sentinels, non-sticky proxy and
CI/architecture matrix remain. Task 6 is unimplemented; Task 7 is disabled and
requires separate live-provider authorization. The design and historic issue
body remain unchanged; partial milestones do not complete the full checklist.
