# Rule-admission blueprint candidate lane — 2026-11-05

Scope: local, synthetic verification of a draft. This is not a release
qualification, a Linux qualification or live-provider certification.

## Environment and inputs

- macOS 26 arm64 (Darwin 25.5.0), CPython 3.12.13, fresh venv `.venv-rules`.
- Lab base: main `3cf2d64`.
- Core candidate: `B3Cognition/prosaic` `9d5a02f87469da373ba35e1e599b456b45459cd2`
  (main, PR #4 merged), wheel `b3_prosaic-0.4.1-py3-none-any.whl`, SHA-256
  `c42efc9fc9deae68417ac2cabfc769b81db229c85220ac7fb971cef97a061c74`.
- Runtime candidate: `B3Cognition/prosaic-runtime`
  `65ba15d7e93ee058e22bececdb2e528cef2a474a` (PR #16 head after review changes,
  open), wheel `b3_prosaic_runtime-0.9.12-py3-none-any.whl`, SHA-256
  `121604f7516d54122f4f3d89e0fe53956745d5767c1f8126201bf18bb813c300`.
  The first pin was `4082e72` (SHA-256 `4079b601…`); results below up to the
  re-pin section were recorded against it.
- Recorder 0.3.0, Harness 0.9.4 and Harness store 0.4.0: published bytes
  copied unchanged from `releases-reasoning.json`.
- Neither candidate commit had a `Publish SDK` Actions run when checked; each
  had only CI or test runs. The exact-source candidate tool
  (`prepare_sdk_candidates.py`) therefore could not be used.

## Commands and results

| Check | Command | Result |
| --- | --- | --- |
| Reproducible build | `build_rule_admission_candidates.py --report`, twice, in separate temp dirs | Identical digests both times |
| Verified build into cache | `build_rule_admission_candidates.py` | Both digests match the manifest |
| Prepare, install, audit | `prepare_dependencies.py`, `install_dependencies.py`, `audit_install.py` with `--manifest dependencies/rule-admission-candidate.json`; `pip check` | All five payloads match; no broken requirements |
| Capability | `ProsaicRuntime.capabilities` and `prosaic.parse_rules` | `rule_admission_v1` present; `parse_rules` present |
| Watched failure | `pytest tests/rule_admission_acceptance` before implementation | 38 failed (missing blueprint modules), 4 passed (manifest, audit, builder, Core fact) |
| Lane, source tree | `pytest tests/rule_admission_acceptance -q` | 42 passed; 79 after the review below |
| Lane, installed wheel | `-I -m pytest -o pythonpath= tests/rule_admission_acceptance -q`, with the Lab wheel installed | 79 passed; blueprint loaded from site-packages |
| Review regressions | New tests run before any fix | 22 failed, 15 passed; all 79 passed after the fixes |
| Builder after refactor | `build_rule_admission_candidates.py` (re-fetch, rebuild, `place`) | Both digests match the manifest |
| Mutation | Custom guard made to always pass | Exactly 2 failures: the `before_tool` fix and the companion `after_tool` fail |
| Packaging | `python -m build --wheel` and `--sdist` | Both contain the blueprint, including `.prosaic/subagents/*.md` |
| Copy recipe | Copy into `src/yourapp/catalogue_desk`; run its coverage, `prosaic inspect` and a scripted turn | Works; same fingerprint as in the Lab location |
| Lint | `ruff 0.14.3 check` and `format --check`, `--line-length 120`, single quotes, new Python files only | Pass |
| Default suite | Fresh `.venv-main` from `dependencies/releases.json` (Lab not installed, venv `bin` on `PATH`); `pytest -q` | 2,077 passed. An earlier run with the Lab installed and `bin` off `PATH` had 4 environmental failures; clean main fails the same way under that setup. |

## Adversarial review: defects, causes and prevention

Each defect is pinned by a test in `test_review_regressions.py` or
`test_candidate_builder.py`. Each test was observed failing before its fix.

| # | Defect | Root cause | Prevention rule |
| --- | --- | --- | --- |
| 1 | `"days": 28.0` skipped the `before_tool` fix; a 28-day loan ran and the turn succeeded | The guard checked `type(days) is int`; JSON Schema `integer` admits whole-number floats | Guards compare JSON numbers by value (finite `int`/`float`, never `bool`) |
| 2 | `after_tool` passed a placed loan reporting `35.0`, `"35"`, `true`, null or no period | The same type check, failing open | Guards on effects fail closed when the effect cannot be confirmed |
| 3 | Coverage said "admitted" (exit 0) for a malformed tag that admission refuses | Coverage re-implemented admission and did not pass tag issues | Coverage takes its verdict from Runtime admission, never a re-implementation |
| 4 | Coverage refused a path-setting guard that admission admits | `project_root` was not passed to `compile_rules` | The same as rule 3; compile with admission's own inputs |
| 5 | A binding superseded by a stronger cross-file binding was shown as enforced at its weaker action | Coverage did not compare declared with effective bindings | Report `superseded` and the binding warnings |
| 6 | An unregistered required guard was reported as `invalidArtifact` | Coverage never constructed the real runtime | Report `startup` when construction fails |
| 7 | A dangling symlink in the wheel cache was written through | `exists()` is false for a dangling link and `copyfile` follows links | Check `is_symlink()` first; write to a temp file then `os.replace` |
| 8 | `compose` accepted the agent or a companion twice, and dropped companion bundle resources silently | No input validation | Refuse duplicates and refuse what cannot be composed fully |
| 9 | A missing build backend escaped as a raw `PackageNotFoundError` | Unhandled metadata lookup | Turn it into a clear refusal before any fetch |

The guard keeps version `loan-period-v1`: its behaviour changed before any
release or stored fingerprint existed. Bump it on any change after release.

## Re-pin 1: Runtime `4082e72` to `65ba15d`

| Check | Result |
| --- | --- |
| Reproducible build of `65ba15d`, twice | Identical SHA-256 `121604f7…` |
| Verified build, prepare, install, payload audit, `pip check` | Pass |
| Unchanged lane (79) on `65ba15d` | 77 passed; the 2 failures were the test's own expected Runtime commit, not an API change |
| New `conflicting-settings-cross-file` variant | Passes on `65ba15d`; fails on `4082e72`, which kept the stronger binding |

API observations for #16's review thread (none broke a blueprint test):

1. `no_wrapped_links`, `args_reference_seen_ids` and `value_in_tool_output`
   changed behaviour but kept their `-v1` versions, so `rules_fingerprint` is
   identical across both heads (`141cdb82…` for this blueprint). A host folding
   the fingerprint into workflow identity cannot see the change.
2. `tool_results` entries are now projected facts without the
   `{status, result}` envelope, while `tool_result` at `after_tool` is still the
   raw envelope (documented). A guard reading both handles two shapes.
3. Cross-file bindings with different settings at one stage are now refused
   whatever the actions (previously the stronger action's binding replaced the
   other, settings included).
4. `value_in_tool_output` now reads `€1,20` and `eur 1.20`; `1.20 EUR`,
   `1.20 euros` and `120 cents` still pass with an invented fee.

## PR #45 review

Each comment became a test in `test_pr_review.py` or a new coverage variant,
observed failing (34 failures) before the fixes.

| Comment | Fix |
| --- | --- |
| P1: the floor did not cover the custom guard; prose could raise `max_days` or drop it | `runtime.yml` pins `loan_period_within_policy` (`fix`, `max_days: 21`, no stage) |
| P2: the id rule promised search results only; the guard also accepts ids from the message | The rule text names both sources; the borrower-named and search-query laundering cases are tests |
| P2: `prosaic apply` distributed the companion as a standalone agent | The companion moved to `companions/` as plain rules without frontmatter, read with `parse_rules` |
| P2: `fix` at `after_tool` was admitted and then faulted | `REPAIR_STAGES` declares where the guard repairs; `host.compose` refuses others before any request; coverage reports `hostPolicy` |
| P2: invented fees in common formats passed | Caught formats asserted; missed formats are strict expected failures against #16; README limits line |
| P3: an enormous integer `days` faulted | `isfinite` only on floats; refused values bounded for delivery; 401- and 3001-digit cases repaired |
| P3: `superseded` relied on behaviour under review | Re-pin 1 changed it as predicted; the variants pin both outcomes; re-pin note added |
| General: `require_sdk()` only ran in tests | The blueprint package checks the SDKs on import with a clear message |
| General: the 21-day limit in four places could drift | Admission refuses tag settings that differ from the floor; a test ties the prose text and `LOAN_TERMS` to it |

## Limits

- Linux reproducibility was not checked locally (no Docker); the
  `Rule admission integration` workflow rebuilt both candidates on Linux AMD64
  and ARM64 with matching digests.
- The synthetic provider proves hook wiring on the actual OpenAI-compatible
  request and response path. It does not show that a live model follows retry
  feedback.
- No Harness workflow: Harness 0.9.7 lacks `ruleViolation` in `_FAILURES`
  (it raises after provider spend), and its conversation path drops
  `required_guards`, composed rules and guards.
- The Runtime pin goes stale if PR #16 changes in review. That is expected: the
  lane is the integration test for the review.
