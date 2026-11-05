# Rule-admission blueprint lane

This separate candidate lane is the adoption example for Prosaic rule admission.
In it, prose declares which rules a host may check, the host registers guards
in Python, and a `required_guards` floor in operator config says what prose
may never weaken. It contains one copyable agent and an acceptance suite that
pins the whole mechanism against an owned synthetic provider. It makes no live
model calls and needs no credentials.

The lane consumes released Core and two exact, **unreleased** SDK candidates:

| SDK | Source | Why |
| --- | --- | --- |
| Core | Published 0.5.0, `67b3807` | Enforcement tag grammar: `parse_rules`, `strip_tags`, inspection `rules` |
| Runtime | `B3Cognition/prosaic-runtime` PR #16 `498ffc7` | Fixed value-source boundaries and signed multiples |
| Harness | Companion `5b3f0f2` | Guards, owned policy/composed rules, ruleViolation and private rule receipts |
| Runtime recorder, Harness store | Published 0.3.0 and 0.4.0 | Unchanged from the reasoning lane |

Both candidates keep their base version numbers (Runtime 0.9.13, Harness
0.9.8), so only their pinned bytes identify these feature builds. Installing
the published versions alone does not enable this lane. The ordinary `releases.json` train,
the reasoning lane and all historical evidence are unchanged.

## Install the exact lane

From the Lab repository root, in a fresh environment:

```sh
python3.12 -m venv .venv-rules
LAB_RULES_PY="$PWD/.venv-rules/bin/python"
"$LAB_RULES_PY" -m pip install --require-hashes -r dependencies/requirements.lock
"$LAB_RULES_PY" -m pip install --require-hashes -r dependencies/rule-admission-build.lock
"$LAB_RULES_PY" scripts/build_rule_admission_candidates.py
"$LAB_RULES_PY" scripts/prepare_dependencies.py --manifest dependencies/rule-admission-candidate.json
"$LAB_RULES_PY" scripts/install_dependencies.py --manifest dependencies/rule-admission-candidate.json
"$LAB_RULES_PY" -m pip install --no-deps .
"$LAB_RULES_PY" scripts/audit_install.py --manifest dependencies/rule-admission-candidate.json
"$LAB_RULES_PY" -m pip check
```

Before the Harness companion commit is pushed, build it from its explicit local
Git checkout with the same command plus
`--local-repository B3Cognition/prosaic-harness=/absolute/path/to/harness`.
The builder fetches and archives only the manifest commit, ignores working
changes, and still verifies the wheel hash. CI uses the remote commit, so that
commit must be pushed before this lane can run on another machine.

`build_rule_admission_candidates.py` builds each candidate in four steps:

1. Fetch exactly the recorded 40-character commit from its public repository.
2. Run `git archive` on it.
3. Build the wheel with the hashed backend in `rule-admission-build.lock`,
   with no build isolation and `SOURCE_DATE_EPOCH` set to the commit time.
4. Refuse any wheel whose SHA-256 differs from
   `dependencies/rule-admission-candidate.json`.

Verified wheels go into the manifest's wheel cache, where
`prepare_dependencies.py` expects explicit candidate wheels. The payload audit
then checks every installed SDK file against those exact wheels.

## Run the checks

```sh
"$LAB_RULES_PY" -I -m pytest -o pythonpath= tests/rule_admission_acceptance -q
"$LAB_RULES_PY" -I -m lab_runner.rule_admission.blueprint.coverage
```

The `Rule admission integration` workflow runs the same steps on Linux AMD64
and ARM64 with Python 3.12, rebuilding the candidate wheels from the pinned
commits in CI. It is **not a required check** until the manifest is re-pinned
to released SDKs. These tests live outside the default `testpaths`, because the
ordinary Lab suite admits only its recorded SDK train.

## Copy the blueprint

The installed Lab wheel includes
[`lab_runner/rule_admission/blueprint`](../lab_runner/rule_admission/blueprint/README.md).
Its README walks through copying it: rename the agent, write prose rules, tag
them, register guards and set the floor.

```sh
LAB_RULES_BLUEPRINT=$("$LAB_RULES_PY" -c "from lab_runner.rule_admission import BLUEPRINT; print(BLUEPRINT)")
cp -R "$LAB_RULES_BLUEPRINT" src/yourapp/catalogue_desk
```

## What the acceptance suite pins

| # | Behaviour | Tests |
| --- | --- | --- |
| 1 | Tags at `before_tool`, `after_tool`, `before_answer` and `final`; a `prose-only` rule; one guard bound once per file at a different stage in a companion file; the model receives only Core's `strip_tags` text | `test_blueprint_prose.py` |
| 2 | Four generic guards plus the custom `loan_period_within_policy` (version, stages, `fixes`, closed settings schema); refusal of invalid settings, unsupported stages, `fix` without `fixes` and unregistered guards | `test_guard_registration.py` |
| 3 | `required_guards` in both forms; refusal with `invalidPolicy` and an exact host-wording detail when prose weakens, omits or conflicts with a pin; a pinned stage applies across composed files; startup failure for an unregistered required guard | `test_required_guards.py` |
| 4 | `fix`, with arguments rewritten before the tool runs, a link unwrapped and a recheck; `retry`, with user-role feedback carrying the rule text and echoed values; `fail`, with a safe result, `ruleViolation` and no effect; the companion's `after_tool` failure keeps the real effect evidence | `test_actions.py` |
| 5 | `TurnResult.rules_fingerprint` equals the compiled bindings' fingerprint. It changes with a binding's action or a guard version while every request byte stays the same, and does not change when a line is added above the rules. | `test_fingerprint.py` |
| 6 | The coverage report and command, agreement with `ProsaicRuntime.rule_coverage` and unregistered guards named | `test_coverage.py` |
| 7 | The tag-stripped agent sends identical request bytes with or without guards, and the same bytes as the tagged agent when no guard fires; the floor still refuses it | `test_untagged_identity.py` |
| | Candidate provenance: exact commits, bytes differing from the published Core, payload audit and refusal of a Core without `parse_rules` | `test_candidate_install.py` |
| | Review regressions: whole-number float loan periods repaired; `after_tool` fails closed on unreadable periods; coverage equals real admission across eleven variants (malformed tag, path-setting guard, superseded and conflicting cross-file bindings, raised loan limit, `fix` at `after_tool`, weaker floor, unregistered custom or required guard, stripped agent under the floor); duplicate companions refused | `test_review_regressions.py` |
| | PR review: the floor protects the custom guard; the id rule says what the guard enforces; the companion is never distributed as an agent; `fix` where the guard cannot repair is refused before any request; fee formats (still-missed formats are strict expected failures against #16); enormous periods repaired; the blueprint refuses an SDK without rule admission | `test_pr_review.py` |
| | Builder cache: dangling or live symlinks refused and never written through; bytes that differ from the manifest refused; a missing build backend refused before any fetch | `test_candidate_builder.py` |
| | Harness: the floor, host registrations, before-tool repair, composed after-tool failure, retry exhaustion, private rule receipts, reopen/replay and saved-receipt recovery on both wires | `test_harness.py` |
| | Independent malformed-source and strict-sign regressions through Harness, plus three explicit magnitude controls | `test_value_source_regressions.py` |

Turns that are compared byte for byte use a fixed public `InvocationScope`,
because Runtime derives opaque tool-call ids from it. Runtime's own untagged
golden capture does the same.

## Re-pin after release

This lane is the integration test for prosaic-runtime#16 in review. If the PR
head moves, re-pin, and expect failures that show what changed. Report each
broken test's API change on #16 before adapting the blueprint.

The first re-pin, from `4082e72` to `65ba15d`, broke no blueprint test. It
pinned one behaviour change: the same guard at the same stage in two files with
different settings is now refused, whatever the actions; previously the
stronger action's binding silently replaced the other. A same-settings stronger
binding still supersedes, and `coverage` reports the weaker one as
`superseded`. If Runtime changes that rule again, the
`superseded-cross-file` and `conflicting-settings-cross-file` variants will
fail on re-pin by design. The three fee formats Runtime does not yet read are
strict expected failures, so they fail on re-pin as soon as Runtime reads them.

1. Runtime `498ffc7` resolves the two value-source bugs reproduced at `65ba15d`.
   Harness `5b3f0f2` closes its policy/rule/registration/receipt gaps. Keep those
   commits exact until successor candidates have passed this lane.
2. **After Runtime #16 and the Harness companion merge and release:** replace
   both candidate entries with the published `url`, `checksum_url`, `sha256`,
   `source_commit` and versions. Drop the `qualification` field, the build step
   and `rule-admission-build.lock`, and update `test_candidate_install.py` and
   `require_sdk()`'s version range.
3. Make the workflow a required check if the maintainer wants it to gate main.

## Limits

- Rule hooks exist only for conversation turns. `run()`, `NativeRuntime` and
  `UnifiedRuntime` refuse enforce-tagged prose. The copyable `blueprint/harness.py`
  uses graph-free Harness conversations with the exact companion candidate.
  Published Harness 0.9.8 and earlier do not support guarded conversations;
  upgrade every worker sharing these sessions before using the new receipts.
- The synthetic provider checks that hooks are wired to the real
  OpenAI-compatible request and response path. It does not qualify a live
  model's compliance with retry feedback.
- These exact candidate wheels rebuilt byte-identically twice on macOS arm64.
  Linux AMD64/ARM64 CI is configured and awaits pushing the Harness companion;
  earlier Linux results belong to the historical candidate train.
