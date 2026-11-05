# Rule-admission blueprint lane

This separate candidate lane is the adoption example for Prosaic rule admission.
In it, prose declares which rules a host may check, the host registers guards
in Python, and a `required_guards` floor in operator config says what prose
may never weaken. It contains one copyable agent and an acceptance suite that
pins the whole mechanism against an owned synthetic provider. It makes no live
model calls and needs no credentials.

The lane consumes **unreleased** SDK code:

| SDK | Source | Why |
| --- | --- | --- |
| Core | `B3Cognition/prosaic` main `9d5a02f` (PR #4) | Enforcement tag grammar: `parse_rules`, `strip_tags`, inspection `rules` |
| Runtime | `B3Cognition/prosaic-runtime` PR #16 head `4082e72` | Rule admission for conversation turns |
| Runtime recorder, Harness, Harness store | Published 0.3.0, 0.9.4 and 0.4.0 | Unchanged from the reasoning lane |

Both candidates keep their released version numbers (Core 0.4.1, Runtime
0.9.12), so only their bytes distinguish them from the published wheels. The
published Core 0.4.1 has no `parse_rules`. The ordinary `releases.json` train,
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
| | Review regressions: whole-number float loan periods repaired; `after_tool` fails closed on unreadable periods; coverage equals real admission across eight variants (malformed tag, path-setting guard, superseded cross-file binding, weaker floor, unregistered custom or required guard, stripped agent under the floor); duplicate companions refused | `test_review_regressions.py` |
| | Builder cache: dangling or live symlinks refused and never written through; bytes that differ from the manifest refused; a missing build backend refused before any fetch | `test_candidate_builder.py` |

Turns that are compared byte for byte use a fixed public `InvocationScope`,
because Runtime derives opaque tool-call ids from it. Runtime's own untagged
golden capture does the same.

## Re-pin after release

This lane is the integration test for prosaic-runtime#16 in review. If the PR
head moves, re-pin, and expect failures that show what changed.

1. **Before release, optionally:** a maintainer dispatches `Publish SDK` on
   Core `9d5a02f` and Runtime `4082e72`, or later heads. The resulting
   action-built wheels and receipts can replace the local candidates through
   `scripts/prepare_sdk_candidates.py`. That script's version table would need
   an entry for this train.
2. **After Core releases `parse_rules` and #16 merges and releases:** replace
   both candidate entries with the published `url`, `checksum_url`, `sha256`,
   `source_commit` and versions. Drop the `qualification` field, the build step
   and `rule-admission-build.lock`, and update `test_candidate_install.py` and
   `require_sdk()`'s version range.
3. Make the workflow a required check if the maintainer wants it to gate main.

## Limits

- Rule hooks exist only for conversation turns. `run()`, `NativeRuntime` and
  `UnifiedRuntime` refuse enforce-tagged prose. No Harness workflow is included:
  Harness 0.9.7 and earlier reject the `ruleViolation` failure code after
  provider spend.
- The synthetic provider checks that hooks are wired to the real
  OpenAI-compatible request and response path. It does not qualify a live
  model's compliance with retry feedback.
- The candidate wheels were built reproducibly on macOS arm64. Byte-identical
  rebuilds on Linux are proven by the CI workflow, not locally.
