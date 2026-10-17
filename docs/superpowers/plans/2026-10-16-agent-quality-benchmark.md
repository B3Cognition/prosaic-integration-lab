# Agent Quality Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution, or superpowers:subagent-driven-development if the maintainer explicitly selects delegation. Steps use checkbox syntax for tracking.

**Goal:** Deliver a versioned task-quality benchmark with deterministic scoring, actual SDK execution, durable finite allowances, replayable private evidence and explicitly bounded model-profile comparisons.

**Architecture:** Integration Lab owns the cases, scorer and runner. Installed Runtime owns inference/tool dispatch and installed Harness owns agent attempts, review/repair transitions and checkpoints. A standalone CLI defaults to pure preflight; scripted HTTP providers exercise the same execution path as live profiles, with clearly distinct evidence origins.

**Tech Stack:** Python 3.12, stdlib JSON/hashlib/importlib.resources/http.server, existing jsonschema and pytest, public b3-prosaic 0.4.1 / Runtime 0.9.3 / Harness 0.8.2 APIs. No new production dependencies.

**Spec:** `docs/superpowers/specs/2026-10-15-agent-quality-benchmark-design.md` (maintainer approved 2026-10-16).

## Global Constraints

- Implement in Integration Lab; no copied engines, private imports or sibling editable SDK dependencies.
- Preserve serialized camelCase contracts and existing allowance formats.
- Runtime conformance, operational qualification and task quality remain separate suites.
- Keep answer assertions and answer-key differences out of model-visible input and feedback.
- No automatic retry of ambiguous interrupted provider requests.
- Default preflight must not read secrets, construct Runtime, probe tools, start containers or contact a provider.
- Fixture results never qualify a model. Unknown usage stays unknown and stops later live dispatch.
- Do not modify the twelve-request SharedLiveAllowance contract; create independent benchmark storage.
- Raw prompts, outputs, arguments, run state and credentials stay out of public summaries.
- Preserve unrelated dirty files and historic receipts; no release, publication or deployment is authorized.
- Keep live inference opt-in with secret-managed approved profiles and explicit shared finite ceilings.

## Review Focus

1. A correct-looking answer with fabricated, foreign or incomplete lookup evidence must fail scoring (Task 1).
2. A second process opening an allowance after a crash must not release pending/unknown reservations or dispatch the same sample again (Task 2).
3. A valid but incorrect answer must not become correct by revealing hidden answer-key differences during repair (Task 3).
4. A comparison containing missing cases, unknown usage or different policies must not present a complete baseline (Task 4).
5. Installed artifacts must contain every case, schema and prose asset, independently of the source checkout (Task 5).

## File ownership

New package `lab_runner/quality/`:

| File | Responsibility |
| --- | --- |
| `__init__.py` | Package declaration; no imports with execution side effects |
| `contracts.py` | Bounded JSON, closed report/evidence field validation, canonical digests |
| `suite.py` | Resource loading, ten-case admission, model-visible projections |
| `scoring.py` | Pure task/evidence scoring and tool-efficiency classification |
| `allowance.py` | Owned private durable benchmark reservations, sample claims and reconciliation |
| `execution.py` | WorkflowFactory construction, lookup journal, Harness execution and evidence extraction |
| `fixture.py` | Owned loopback scripted provider with independent request counts |
| `recovery.py` | Three public-store fault/reconstruction probes |
| `reporting.py` | Safe public summaries, aggregates, cost estimates and comparable identities |
| `data/evidence-review-v1.json` | Synthetic case inputs, records and private assertions |
| `data/answer.schema.json` | Closed structured answer contract |
| `data/review.schema.json` | Closed critic response contract |
| `data/reviewer.md`, `data/critic.md`, `data/author.md` | Neutral paired ALWAYS/NEVER prose |

New entry point `lab_runner/agent_quality.py`; new private-config example
`configs/agent-quality.example.json`; new usage guide `docs/agent-quality.md`;
new installed smoke `scripts/agent_quality_smoke.py`; new tests named below.
Modify `pyproject.toml` package-data only. Existing README/adoption changes stay
untouched. Record actual execution evidence in a new dated verification ledger.

## Task 1: Versioned cases and a pure scorer

**Files:** Create `quality/{__init__,contracts,suite,scoring}.py`, the six data
assets above, and `tests/unit/test_agent_quality_scoring.py`.

**Interfaces:** `load_suite() -> dict`, `public_case(case: dict) -> dict`,
`digest(value: dict | list) -> str`, `score_case(case: dict, evidence: dict) -> dict`.
Returned suite/case records are owned copies. No SDK construction or IO except
the explicit bounded resource read in `load_suite`.

- [ ] Write failing scorer tests, including this independent correctness witness:

```python
def test_case_inventory_and_hidden_assertions():
    from lab_runner.quality.suite import load_suite, public_case
    suite = load_suite()
    assert suite['suiteId'] == 'evidence-review-v1'
    assert len(suite['cases']) == 10
    assert len({case['caseId'] for case in suite['cases']}) == 10
    for case in suite['cases']:
        visible = public_case(case)
        assert 'expected' not in visible
        assert 'expected' in case
        assert set(visible) == {'caseId', 'task', 'recordIndex', 'draft'}
```

- [ ] Run `.venv-latest/bin/python -m pytest tests/unit/test_agent_quality_scoring.py -q`; confirm missing-module failure before implementation.
- [ ] Define a finite answer schema with `decision` (`approve`, `reject`, `insufficient`), unique `facts` identifiers and unique citation objects `{factId, recordId}`; deny extra keys. Define critic schema `{approved: bool, issues: [closed issue IDs]}`. Bound all strings, collections, JSON depth and bytes; reject duplicate JSON keys, nonfinite numbers, booleans as counts and oversized inputs.
- [ ] Author cases `combine-01/02`, `conflict-01/02`, `missing-01/02`, `injection-01/02`, `repair-01/02`. Use explicit numeric decision rules and record authority/revision rules so expected results can be independently calculated. Each case stores records, relevant/required record IDs, necessary dispatch lower bound, expected decision/facts/citation pairs and optional flawed draft. Include irrelevant records to measure avoidable reads.
- [ ] Implement evidence admission keyed by sample, invocation and call identity. Join persisted successful handler entries to matching Runtime tool completion events and invocation receipt digests. Check returned-record digests against immutable case records. A replay input supplies trusted host evidence; document that arbitrary forged host evidence is outside the scorer's attestation capability.
- [ ] Add parameterized witnesses: change only decision; change one fact; substitute a citation; omit a required read; duplicate a handler entry; substitute foreign sample/invocation; alter a record digest; repeat an irrelevant read; exceed the lower bound with a relevant verification read. Assert incorrect outputs fail and excess relevant reads are not mislabeled unnecessary.
- [ ] Implement pure verdicts `{state, reasons, toolMetrics}` with closed reason IDs; separate total/duplicate/irrelevant/excess lookup counts. Keep raw evidence out of verdicts. Run all scorer tests to green.

## Task 2: Durable shared benchmark allowances

**Files:** Create `quality/allowance.py` and `tests/unit/test_agent_quality_allowance.py`.

**Interfaces:** `BenchmarkAllowance(path: Path, *, identity: str, limits: dict)`,
`.reserve(sample_id: str, maximum: dict) -> dict`,
`.finish(sample_id: str, *, actual: dict | None, evidence_digest: str | None) -> dict`,
`.status() -> dict`. Reservation dimensions are provider requests, tool calls and
reported tokens. Wall time uses a persisted absolute batch deadline in addition
to monotonic per-process dispatch checks. A claimed sample is never re-reserved.

- [ ] Write the durable uncertain-reservation test first:

```python
def test_reopen_preserves_unknown_reservation(tmp_path):
    from lab_runner.quality.allowance import BenchmarkAllowance
    limits = dict(providerRequests=4, toolCalls=4, reportedTokens=4096,
                  maxSamples=2, timeoutSeconds=60)
    path = tmp_path / 'allowance.json'
    first = BenchmarkAllowance(path, identity='a'*64, limits=limits)
    first.reserve('combine-01-p1-r1', dict(providerRequests=4, toolCalls=4,
                                         reportedTokens=4096))
    reopened = BenchmarkAllowance(path, identity='a'*64, limits=limits)
    assert reopened.status()['remaining']['providerRequests'] == 0
    assert reopened.status()['pendingSamples'] == 1
```

- [ ] Run that test to observe the absent implementation.
- [ ] Implement separate version-1 benchmark records with owned `0600` regular files, private parent, no symlinks, exclusive lock, bounded strict JSON, atomic replace/fsync and identity/limit binding. Do not touch `live_allowance.py`.
- [ ] Make pending/unknown claims retain all reserved dimensions. Release unused allowance only from matched complete receipt/handler evidence. A failure with complete usage may be reconciled as known; uncertainty is not inferred from success/failure alone. Settlement is idempotent only for identical values; conflicting reconciliation fails.
- [ ] Test concurrent reservations cannot exceed any dimension; reopen cannot change suite/schedule/policy/ceilings; corrupt/torn files fail closed; lower or higher actual counts outside reservation fail; zero calls remain known zero; unknown tokens cannot become zero; a duplicate sample cannot dispatch again; simulated death between reservation and evidence keeps the claim.
- [ ] Run the allowance tests to green and rerun Task 1 tests.

## Task 3: Execute and recover through installed SDKs

**Files:** Create `quality/{execution,fixture,recovery}.py`,
`tests/functional/test_agent_quality_execution.py` and
`tests/functional/test_agent_quality_recovery.py`.

**Interfaces:** `execute_case(case: dict, *, config, profile: str, output: Path,
sample_id: str, limits: dict) -> dict`,
`fixture_provider(*, scenario: str) -> context manager`,
`run_recovery_cases(output: Path) -> list[dict]`.
Private evidence conforms to Task 1; counts conform to Task 2 dimensions.

- [ ] Write an end-to-end test using the scripted HTTP context manager:

```python
def test_fixture_executes_lookup_and_scores_receipt(tmp_path):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    from lab_runner.quality.scoring import score_case
    case = load_suite()['cases'][0]
    with fixture_provider(scenario='correct') as provider:
        evidence = execute_case(case, config=provider.config,
            profile='fixture', output=tmp_path, sample_id='combine-01-p1-r1',
            limits=provider.case_limits)
        assert provider.requests == evidence['counts']['providerRequests']
        assert provider.handler_calls == evidence['counts']['toolCalls']
    assert score_case(case, evidence)['state'] == 'passed'
```

- [ ] Run the functional test and confirm the expected missing implementation.
- [ ] Build approved ProsaicArtifact agents, schemas, CustomTool and validators using public WorkflowCatalog/WorkflowBindings/WorkflowPolicy/WorkflowFactory. Register only the bounded case lookup tool. A host-owned `with_context` handler records invocation, input record IDs, returned digests and call identity before returning synthetic records. No answer assertions are accessible through the tool or passed in arguments.
- [ ] Construct an ordinary agent/check/finish-or-bounded-repair graph and a critic/author/check/finish-or-bounded-repair graph. Include paired ALWAYS/NEVER prose. Required successful lookup is checked through execution evidence; final deterministic checks use closed feedback categories. Critic comments can only name public issue codes. No validator leaks the expected answer in feedback.
- [ ] Capture each actual Harness invocation receipt and Runtime events, with monotonic timing, known/unknown usage and profile binding. Save private evidence before allowance settlement. Score failed attempts too; preserve a complete first-attempt outcome independently of later repairs. Avoid using successful HTTP status as proof of task or tool success.
- [ ] Implement a bounded stdlib ThreadingHTTPServer fixture accepting OpenAI-compatible requests at a literal loopback address with generated synthetic credentials. Queue tool-call/final responses; count provider requests independently. Its scripted answers may use the oracle, but that fixture code never enters the live execution path.
- [ ] Exercise every case through real installed Runtime/Harness, including correct, plausible wrong, missing usage, invalid JSON, simulated tool text, wrong record ID and hostile record scenarios. Inspect captured provider payloads for private-answer leakage. Verify one successful critic rejection/repair and one exhausted repair.
- [ ] Implement recovery probes via a delegating public RunStore wrapper that injects failure at save-receipt/checkpoint boundaries without changing SDK code. Reconstruct Harness with the same workflow/store/run identity. Adopt a saved receipt once; block missing receipts without retry; preserve invalid-output failure evidence. Check independent request/handler counts before and after reconstruction.
- [ ] Run both functional files to green, then Tasks 1–2 tests. Failed expected crash scenarios are reported separately from ordinary task-quality failures.

## Task 4: CLI, profile comparisons and safe reports

**Files:** Create `quality/reporting.py`, `lab_runner/agent_quality.py`,
`configs/agent-quality.example.json`, `tests/unit/test_agent_quality_reporting.py`
and `tests/functional/test_agent_quality_cli.py`.

**Interfaces:** `summarize(schedule: list[dict], results: list[dict], *, identity: dict,
origin: str, recovery: list[dict]) -> dict`, `compare(reports: list[dict]) -> dict`,
`main(argv: list[str] | None = None) -> int`.

- [ ] Write the default CLI contract before implementation:

```python
def test_default_command_is_unexecuted(capsys):
    import json
    from lab_runner.agent_quality import main
    assert main([]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report['origin'] == 'unexecuted'
    assert report['executedSamples'] == 0
    assert report['scheduledSamples'] == 10
    assert report['baselineComplete'] is False
```

- [ ] Run the failing test. Add subprocess sentinels proving no Runtime/Harness construction, secret reads, socket calls, executable probes, allowance files or output directories in default mode. Strict-load public config only when supplied; live credentials are opened only during explicit live execution.
- [ ] Implement mutually exclusive default / `--fixture` / `--live` modes, `--config`, bounded `--repetitions`, explicit private `--output`, and `--compare` for bounded existing public reports. Reject unexpected keys and incompatible modes. Invalid configuration exits 2; executed failed/incomplete suite exits 1; successful fixture or fully measured live baseline exits 0. Preflight exits 0 but is always unexecuted.
- [ ] Config fields: `version`, `runtimeConfig`, `profiles`, `allowanceFile`, `limits`, optional `rateCard`. Select approved profile aliases from RuntimeConfig. Require finite explicit live `providerRequests`, `toolCalls`, `reportedTokens`, `maxSamples`, `timeoutSeconds` plus per-case caps. Compute a schedule identity before creating reservations. Reserve each whole sample; never expand a limit or switch profiles automatically.
- [ ] Implement public reports with suite/scorer/SDK-manifest/case/prose/tool/policy/profile digests, closed sample identities, origin, coverage, state counts, first-pass/repair measures, tool-efficiency counts, known usage and durations. Preserve missing/unknown values. Success rate includes all attempted task outcomes and reports its numerator/denominator. Full schedule coverage is required for `baselineComplete`.
- [ ] Implement integer-unit rate-card estimates with explicit currency, rate-card digest and known-coverage counts. Reject negative/nonfinite rates; absent rates or usage yield null estimates. Keep latency median/range and sample counts; nearest-rank p95 only when count is at least 20. Recovery rows are not mixed into task-success denominators.
- [ ] Compare only matching suite/scorer/case/prose/tool/policy/schedule shapes and SDK provenance. Permit differing profile fingerprints while explicitly identifying the variable. Reject mixed fixture/live origins, duplicate sample IDs, foreign policies, missing case sets and zero-observation claims of a complete baseline. Distinguish incomplete diagnostic comparison from a complete comparative baseline.
- [ ] Canary tests put paths, endpoint URLs, credentials, raw model text and exception strings in private evidence; assert none appear in serialized summaries or error output. Exercise oversized reports, duplicate JSON keys, invalid origins and incompatible comparison identities. Finish all Task 4 tests to green.

## Task 5: Packaging, full verification and baseline delivery

**Files:** Modify `pyproject.toml`; create `scripts/agent_quality_smoke.py`,
`docs/agent-quality.md`, `tests/functional/test_agent_quality_packaging.py` and
`docs/verification/agent-quality-benchmark-2026-10-16.md`.

- [ ] Write packaging test that builds/inspects a wheel and sdist for all six data assets; fail before adding package-data. Pin files under the new quality package only, without changing existing asset ownership.
- [ ] Add `[tool.setuptools.package-data]` with `"lab_runner.quality" = ["data/*.json", "data/*.md"]`. Run the packaging test to green.
- [ ] Implement isolated installed smoke: assert import ownership outside the checkout, read all ten cases via importlib.resources, prove pure preflight, score a correct and incorrect witness and complete one real fixture workflow. Smoke has no provider key or external service dependency.
- [ ] Write the guide with runnable commands for preflight, fixture baseline, explicit live config, profile comparison, private evidence inspection and recovery. Explain metric denominators, unknowns, cost estimates, baseline completeness and fixture/live boundaries. Add expected finite sample/call limits, not an uncapped example.
- [ ] Run `.venv-latest/bin/python -m pytest -q` for the complete Lab unit/functional suite and `.venv-latest/bin/python -m build`. Run the smoke from a fresh wheel environment and again from the extracted sdist using installed manifest-selected SDKs. Audit installed SDK ownership with existing `scripts/audit_install.py --manifest dependencies/releases.json`.
- [ ] Build the released consumer image with `scripts/build_consumer.py --manifest dependencies/releases.json --dependency-mode released --tag prosaic-integration-lab:quality`. Run owned native and conversation acceptance on PostgreSQL 16/18 using the existing documented runner commands. Record exact source, manifest/image IDs, architecture, test totals and cleanup. Do not treat absent infrastructure or narrow unit tests as stack evidence.
- [ ] Produce the all-ten-case fixture baseline with independently reconciled provider/handler counts and all three recovery probes. Save a bounded public receipt and private raw evidence. Re-score that evidence offline and assert unchanged verdicts without network activity.
- [ ] For the live comparative deliverable, use only explicitly approved existing model profiles and a supplied finite allowance. Run the recommended ten cases × three repetitions × two profiles in bounded batches, retaining failures and unknown usage. If approved live inputs/allowance are unavailable, report that dependency explicitly and keep the overall goal incomplete; never relabel fixture results as the live baseline.
- [ ] Self-review the entire diff for unintended changes, answer leakage, private SDK imports, budget reset paths, missing packaged assets and false qualification claims. Run `git diff --check`. Commit only the benchmark-owned files if committing; preserve unrelated staged/unstaged changes. No publication or deployment.

## Coverage audit and handoff

Task 1 covers cases, schema, private answer assertions, pure replay and tool
efficiency. Task 2 covers finite durable budget reservation, concurrency and
unknown outcomes. Task 3 covers actual public-SDK execution, repair and recovery.
Task 4 covers CLI preflight/live boundaries, profile identity, metrics and privacy.
Task 5 covers distribution, full-stack evidence, guide and comparative baseline.

No implementation action has been taken by this plan. Next: maintainer reviews
this plan and chooses native or delegated execution. Recommend native execution
because the five tasks share evidence and identity contracts and this checkout
contains unrelated local edits that should remain with one implementer.
