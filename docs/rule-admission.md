# Rule-admission blueprint lane

This lane demonstrates rule admission through the released Prosaic SDKs.
Prose declares rules, the host registers guards in Python, and a
`required_guards` floor says what prose may never weaken. The copyable agent
and graph-free Harness host are tested against owned synthetic providers;
no live model calls or credentials are required.

The active `dependencies/releases.json` manifest records exact public wheel
URLs, source commits and checksums for this complete family:

| SDK | Release | Purpose |
| --- | --- | --- |
| Core | 0.5.0 | `parse_rules`, `strip_tags` and composed inspection rules |
| Runtime | 0.9.14 | Guard admission/enforcement, corrected value-source boundaries and signed multiples |
| Harness | 0.9.10 | Host policy/guard preservation and durable rule receipts |
| Runtime recorder / Harness store | 0.3.0 / 0.4.1 | Published persistence adapters |

Runtime 0.9.13 and Harness 0.9.8 do not provide these guarded-conversation
contracts. Upgrade every worker sharing guarded sessions together. Historical
manifests, candidate hashes and verification ledgers retain their original bytes.

## Install the exact lane

From this release's source archive or checkout, in a fresh environment:

```sh
python3.12 -m venv .venv-rules
LAB_RULES_PY="$PWD/.venv-rules/bin/python"
"$LAB_RULES_PY" -m pip install --require-hashes -r dependencies/requirements.lock
"$LAB_RULES_PY" -m pip install --require-hashes -r dependencies/rule-admission-build.lock
"$LAB_RULES_PY" scripts/prepare_dependencies.py --manifest dependencies/releases.json
"$LAB_RULES_PY" scripts/install_dependencies.py --manifest dependencies/releases.json
"$LAB_RULES_PY" -m pip install --no-deps --no-build-isolation .
"$LAB_RULES_PY" scripts/audit_install.py --manifest dependencies/releases.json
"$LAB_RULES_PY" -m pip check
```

The SDKs come from checksum-pinned public wheels. The installed payload audit
checks every SDK file against those archives. No sibling checkout or mutable
upstream branch supplies execution code.

## Run the checks

```sh
"$LAB_RULES_PY" -I -m pytest -o pythonpath= tests/rule_admission_acceptance -q
"$LAB_RULES_PY" -I -m lab_runner.rule_admission.blueprint.coverage
```

The `Rule admission integration` workflow requires all four Linux AMD64/ARM64
× PostgreSQL 16/18 cells, using the same released manifest. Each cell runs both
synthetic provider wires, installed payload checks, file-store recovery and real
PostgreSQL guarded-receipt recovery. These SDK integration tests remain outside
the default unit-test collection; a passing unit suite does not replace them.
All four rule cells join the ordinary acceptance and reasoning release gates.

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
| | Released provenance: exact versions/source/checksums, installed payload audit, refusal of a Core without `parse_rules`, and preserved historical candidate selection | `test_candidate_install.py` |
| | Review regressions: whole-number float loan periods repaired; `after_tool` fails closed on unreadable periods; coverage equals real admission across eleven variants (malformed tag, path-setting guard, superseded and conflicting cross-file bindings, raised loan limit, `fix` at `after_tool`, weaker floor, unregistered custom or required guard, stripped agent under the floor); duplicate companions refused | `test_review_regressions.py` |
| | PR review: the floor protects the custom guard; the id rule says what the guard enforces; the companion is never distributed as an agent; `fix` where the guard cannot repair is refused before any request; fee formats (still-missed formats are strict expected failures for documented Runtime grammar limits); enormous periods repaired; the blueprint refuses an SDK without rule admission | `test_pr_review.py` |
| | Builder cache: dangling or live symlinks refused and never written through; bytes that differ from the manifest refused; a missing build backend refused before any fetch | `test_candidate_builder.py` |
| | Harness: the floor, host registrations, before-tool repair, composed after-tool failure, retry exhaustion, private rule receipts, reopen/replay and saved-receipt recovery on both wires | `test_harness.py` |
| | Independent malformed-source and strict-sign regressions through Harness, plus three explicit magnitude controls | `test_value_source_regressions.py` |

Turns that are compared byte for byte use a fixed public `InvocationScope`,
because Runtime derives opaque tool-call ids from it. Runtime's own untagged
golden capture does the same.

## Historical candidate qualification

The original lane reviewed Runtime #16 at `498ffc7` and Harness companion
`5b3f0f2`, before their distinct feature releases existed. Its manifest remains
`dependencies/rule-admission-candidate.json`; the exact-commit builder and hashed
backend lock remain available for historical reproduction. Use the corresponding
historical Lab source when reproducing those receipts, rather than treating
base-version candidate wheels as the newer public releases.

The [original rule ledger](verification/rule-admission-2026-11-05.md) and
[guarded Harness ledger](verification/guarded-harness-2026-11-05.md) record the
candidate behavior and prior failures. In particular, different settings for the
same guard at the same stage are refused across files; a same-settings stronger
binding may supersede a weaker one. The coverage and regression cases retain
those assertions. The current lane downloads released SDK bytes and never
rebuilds a candidate implicitly.

## Limits

- Rule hooks exist only for conversation turns. `run()`, `NativeRuntime` and
  `UnifiedRuntime` refuse enforce-tagged prose. The copyable `blueprint/harness.py`
  uses graph-free Harness conversations with the released guarded SDK family.
  Published Harness 0.9.8 and earlier do not support guarded conversations;
  upgrade every worker sharing these sessions before using the new receipts.
- Both synthetic provider wires check that hooks are wired to real
  OpenAI-compatible and Anthropic request/response paths. It does not qualify a live
  model's compliance with retry feedback.
- Fee formats `1.20 EUR`, `1.20 euros` and `120 cents` remain strict expected
  failures documenting the generic Runtime value guard's grammar limits. A
  passing synthetic suite does not qualify unsupported financial formats or a
  live model's compliance.
