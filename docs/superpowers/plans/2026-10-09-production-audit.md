# Production blueprint audit

**Goal:** Test the installed integration stack aggressively and report what
blocks production adoption, what needs a fix, and what can be postponed.

**Authority:** The maintainer requested testing and a production-readiness
report. Execute tests and add reproducible consumer regressions now; retain
library source boundaries and do not release, deploy, push or spend model credits.

**Basis:** Approved integration design, current implementation ledger and
`AGENTS.md`. Native execution continues the already approved method. Independent
read-only audits cover service security and library recovery/accounting.

## Execution

- [x] Run lab units, recovery on PostgreSQL 16/18, load on 16 and accounting demo.
- [x] Run Prosaic, Runtime and Harness checkout suites; bootstrap Prosaic's
  frozen TypeScript oracle, distinguish test infrastructure failures from bugs,
  and preserve installed-release versus newer-checkout provenance.
- [x] Add an `audit` acceptance lane including existing recovery/load cases and
  disposable schema/privilege corruption, adversarial HTTP/identity inputs,
  conflict/quarantine accounting, overload reservation growth and public/log
  sentinel checks. Expected production properties remain assertions; discovered
  defects must fail, never become skips or expected-pass assertions.
- [x] Run the audit on both database majors, preserving sanitized failure names,
  and run finite multiuser baseline/overload workloads on fresh stacks.
- [x] Write a prioritized evidence report with reproduction commands, owning
  repository, fix acceptance criteria, deployment assumptions and residual gaps.

## Review focus

Missing ledger columns/grants must fail readiness without automatic DDL;
overload must bound database work as well as model execution; conflicting usage
must not amend accepted amounts; unknown usage cannot become zero; malformed or
unauthorized requests cannot dispatch; public responses/logs cannot leak private
inputs or mounted secrets. Reports must not call synthetic estimates invoices or
describe untested provider/tool/architecture behavior as certified.

## Rulings

- Testing/reporting is authorized; the report is not a promise to implement every
  production capability. Keep library defect fixes as upstream recommendations
  and reproducible failures in this consumer; no sibling tracked source edits.
- Existing unit suites lack local `.venv` in Prosaic/Harness. Use the lab's pinned
  Python environment and installed release CLIs on PATH, without editable
  installs or changing the lab dependency baseline.
- The frozen Prosaic oracle was required, not available in the first run.
  Bootstrap it and link the missing local CLI `.venv` path to the unchanged lab
  environment. Align newer Runtime checkout subprocesses to source via PYTHONPATH;
  separately freeze and test the installed Runtime source revision.
- Leave the production audit red for confirmed findings; this request is a
  test/report, not authority to release upstream fixes or deploy a hardened service.
- SDK budget tests cover missing final usage and validation budget exhaustion
  after reconstruction. Combined killed-worker/unknown-receipt budget acceptance
  stays an explicit gap rather than being inferred from those tests.
