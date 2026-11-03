# Reasoning-effort lane verification — 2026-11-03

This update consumes released SDKs and adds Lab fixtures/blueprints. No new
live inference, database migration, hosted-provider qualification or publication
is claimed. The original Qwen/Gemma live evidence remains in Runtime v0.9.12.

## Package identity

`dependencies/releases-reasoning.json` selects Core 0.4.1, Runtime 0.9.12,
recorder 0.3.0, Harness 0.9.4 and store 0.4.0. Public wheel downloads and the
five installed payloads passed the Lab auditor. The ordinary manifest stays
unchanged. Reasoning tests require an installed Runtime wheel, not editable SDKs.

## Local execution

Host: macOS ARM64, Python 3.12.15. Commands ran in isolated worktrees/environments.

- Final `python -m pytest tests/reasoning_acceptance -q`: **31 passed**.
- The same tests against the installed Lab wheel with `-I -o pythonpath=`:
  **31 passed**.
- Installed `python -I -m lab_runner.reasoning_eval test`: **58 control cases
  passed**, zero live invocations, owned fixture cleanup verified.
- Wheel and source archive builds passed from frozen tracked-source trees. The
  rebuilt-sdist wheel also passed all **31 tests**, with all **58 control cases**
  passing from outside the checkout. Seven Markdown assets/configs were present.
- Documented Core inspection and Harness workflow validation passed without
  provider authentication. Current published Harness 0.9.6/store 0.4.1 also
  installed in a separate documentation-check environment; CLI help passed.
- Current Runtime 0.9.12 public-wheel ownership/CLI and synthetic conversation
  smoke checks passed in the fresh SDK environment.
- Relative links in 28 changed/new Markdown files across Core, Runtime,
  Harness and Lab were checked: no missing local targets at this checkpoint.

The tests were observed failing before implementation. Additional RED/GREEN
checks caught receipt-path admission after dispatch and effort-specific names
that would change metadata beyond effort. The final variants have identical
body/metadata except the effort field.

## Ordinary Lab baseline

An initial run incorrectly used the new Runtime in the ordinary Lab environment:
54 failed, 1,986 passed, 37 errors. Closed quality/provenance guards rejected the
unqualified SDK train. Those guards were preserved; the reasoning lane uses its
own environment/manifest.

The original Runtime 0.9.8 baseline then ran 2,074 passing tests with three
failures: two pip-transport tests lacked pip in the fresh uv-created environment,
and `test_direct_human_stop_preserves_correct_role_qualification[handoff]`
failed its existing role-quality assertion. After installing the missing test
oracle, all five parametrized affected cases passed. A complete baseline rerun
is required before claiming a green full suite; its final result is appended
when available. No unrelated baseline implementation was changed.

## Independent review and corrective checks

The independent reviewer reproduced partial allowance exhaustion after one
completed request leaving an empty receipt. The review also found a positive
control-verification flag on failed fixture reports. The latter was treated as
an Important evidence-classification issue because failed controls must not be
certified. Both were addressed in one correction pass.

Six new regression cases were observed failing before the fix: partially
exhausted allowance, competing consumers, an exception after a completed SDK
sample, and failed/empty fixture summaries. Batch admission is now atomic;
completed observations are retained, unknown attempts hold their reservations,
and failed fixtures cannot claim verified controls. No SDK monkey-patching or
live provider was used for these checks.

The final post-review ordinary Lab baseline passed **2,077 tests** in 570.23s,
with one existing Starlette/httpx deprecation warning and no failures/skips.
The separate reasoning source/wheel/rebuilt-sdist selections each passed **31**
tests. These checks retain the ordinary SDK provenance guard and original pins.

## Remote CI and qualification limits

The new [reasoning workflow](https://github.com/B3Cognition/prosaic-integration-lab/actions/workflows/reasoning-effort.yml)
produces separate installed-SDK reports on Linux AMD64/ARM64 for its selected
commit. Consult those run-specific checks and receipts for remote results;
the local checkpoint above does not claim Linux, service/container acceptance,
PostgreSQL or live provider qualification. No live inference or publication was
performed for this update.
