# Guarded Harness integration qualification — 2026-11-05

The maintainer authorized closing the Harness/Lab gaps after reviewing Runtime
#16 and Lab #45. Work is isolated from the author's branches and unrelated local
changes. No live model providers or production databases are used.

## Exact source and package identity

- Lab base: PR #45 `44539fdb8737bfe292256652d9fa36fc6f454a45`.
- Core: released 0.5.0, `67b3807281ed0cdfd345fff84c56b236ec82cfb1`.
- Runtime candidate: `498ffc78c6b215bc425847c8fbc645c20e9b2d05` (0.9.13).
- Harness companion: `5b3f0f2e2899b29c4f2b457875af2cb522140c03` (0.9.8).
- Two adapters remain the published wheels in the reasoning train.

The candidate version strings are not feature-release claims. The manifest's
exact commits and SHA-256 values distinguish them. Both candidates were rebuilt
from git archives twice with setuptools 80.9.0 and SOURCE_DATE_EPOCH; hashes
matched. The builder's explicit local-repository override uses the exact commit,
never working-tree files. The Harness commit must be pushed before remote CI
can fetch it; the local override is not an implicit editable dependency.

## Regression evidence

- Original saved Harness regressions: 3 failures / 1 pass before implementation,
  all 4 pass after. Expectations unchanged.
- New Harness regression file: 14 initial failures before implementation.
- Independent review found path-root/CWD drift, older Runtime conversion losing
  rule metadata, legitimate faulted-without-violated results, duplicate IDs and
  source-directory symlink escape. Each was reproduced in a failing test before
  fixing it; fresh review found no remaining important issues.
- Full committed Harness suite: 1,035 passed, no skips, including 3 real
  PostgreSQL 18 lifecycle cases. One existing Python fork deprecation warning.
- Lab's new both-wire Harness and value-source cases: 15 passed from source.
- Guarded and ordinary five-wheel installed payload audits both passed.
- Installed Lab candidate acceptance: 137 passed, 3 strict expected failures.
- Installed Harness rule regressions: 36 passed. Native workflow, ordinary
  conversation and context conversation wheel smoke gates passed.
- Installed five-wheel Lab PostgreSQL recovery: 2 passed on PostgreSQL 16 and
  2 on PostgreSQL 18, covering both provider wires. Harness lifecycle suites
  additionally passed all 3 cases on each version.
- Candidate/default environments both pass pip check; coverage reports admitted,
  five enforced rules and one prose-only rule, with no tag issues.
- Default full suite: 2,076 passed, one setup-sensitive failure in
  `test_native_recovery_cli_loads_current_application_in_sdk_only_subprocess`.
  The initial environment incorrectly installed the Lab app, contradicting that
  test's explicit SDK-only premise. Removing only the installed Lab app corrected
  the environment; the unchanged case then passed (1 passed). The full suite was
  not repeated after that isolated environment correction. No default production
  files or assertions changed. One existing Starlette deprecation warning.
- Final installed Lab wheel recheck: 137 passed, 3 expected failures; unchanged
  saved Harness/value-source regressions: all 11 passed. Wheel and source archive
  include the copyable Harness host, primary agent and companion rules.
- Owned PostgreSQL 16/18 containers and their exact anonymous volumes were removed;
  no global cleanup was used. Normal user checkout branches and local changes,
  all original saved regression hashes, and both author PR heads are unchanged.

## Commands

In a clean Python 3.12 environment, install the locked dependencies, run
`scripts/build_rule_admission_candidates.py` (with the explicit local Harness
checkout until pushed), then prepare/install/audit with
`--manifest dependencies/rule-admission-candidate.json`. Install the Lab wheel.

Run the installed acceptance suite with `python -I -m pytest -o pythonpath=
tests/rule_admission_acceptance -q`; run the separate PostgreSQL suite with the
same command targeting `tests/rule_admission_postgres` and an explicitly owned
`PROSAIC_RULE_POSTGRES_DSN`. The latter creates and removes only uniquely named
`rule_lab_*` databases. Missing infrastructure fails that lane; it is not skipped.

The ordinary suite runs in a separate environment using the unchanged
`dependencies/releases.json` train. It must never silently consume these candidates.

## Limits

- The three strict expected failures track suffix currency codes/words and minor
  units (`1.20 EUR`, `1.20 euros`, `120 cents`) outside Runtime's readable grammar.
  They are distinct from the two reviewed value-source/sign defects, now fixed.
- Guarded graph-free conversations are supported by this exact companion, while
  legacy graph `run()` remains outside the Runtime hook contract.
- Qualification is local macOS arm64 plus owned PostgreSQL containers. The CI
  matrix is configured for Linux AMD64/ARM64 and PostgreSQL 16/18; it cannot run
  on this unpublished local Harness commit until that commit is pushed.
- No published SDK or deployment is changed by this work.
