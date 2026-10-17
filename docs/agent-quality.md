# Agent task quality

The `evidence-review-v1` benchmark measures checkable synthetic evidence-review
tasks using installed Core, Runtime and Harness. It complements provider
conformance and operational qualification; those suites retain their own gates.
The initial suite contains eight ordinary cases and two seeded critic/author
repair cases. It covers numeric decisions, conflicting revisions, missing facts
and hostile instructions in evidence. No external business operation is enabled.
Each agent receives the complete public output schema in its instructions,
including field types and required keys. The prose identity hashes those effective
instructions. Hidden expected answers are used only by the final scorer.

The public-checks workflow uses consumer-owned validators to parse the closed
public task grammar and assess only the records fetched in the current attempt.
Missing current records require another lookup in the permitted retry; truly
absent required facts force insufficient. Review validation compares every draft
field against a clean answer derived from public rules/evidence, including correct
draft controls. Structured publicCheck feedback guides the existing bounded retry;
the host never substitutes model output. Unsupported task grammar or ambiguous
latest revisions fail closed. Validator source is bound to workflow identity and
recovery versions. This is a validated workflow track, separately identified from
historical prompt-only runs; it does not demonstrate unaided model improvement.

## Preflight and fixture baseline

Use the audited installed SDK environment from the consumer guide. From this
checkout, these commands need no provider key:

```sh
.venv-latest/bin/python -m lab_runner.agent_quality
.venv-latest/bin/python -m lab_runner.agent_quality --fixture --output "$PWD/reports/agent-quality-fixture"
```

The default command only reads packaged resources and installed package metadata.
It does not create state, open secrets, construct Runtime or contact a service.
Fixture mode starts owned loopback HTTP providers, exercises actual native tool
calls and Harness receipt persistence, and produces an independently counted
baseline for all ten cases. It also runs three separate recovery probes: saved
receipt adoption, missing-receipt blocking and bounded schema rejection.

Output directories must be absolute, private and free of symlink components.
The runner creates new directories with mode 0700 and private files with 0600.
Use ignored `reports/` or `runs/` paths. `summary.json` is the bounded public view;
individual sample JSON, lookup journals and Harness stores are private evidence.
`cost-estimates.json` contains safe per-sample estimates when a rate card exists.
Do not publish raw evidence, even when a test uses synthetic inputs.

Repeating the same command with the same schedule/output adopts existing matched
evidence without more inference. Claimed samples without complete evidence block
further progress rather than automatically retrying an uncertain call. Changing
suite, prose, schedule, policy or SDK versions requires a new benchmark identity
and new output/allowance. Never delete an allowance to obtain more capacity for
an interrupted run.

## Explicit live comparison

Copy `configs/agent-quality.example.json` to a private location. Set
`runtimeConfig` to the approved operator Runtime YAML, select existing profile
aliases, and set an absolute private `allowanceFile`. Provide secret references
in Runtime YAML, never in agent Markdown or command arguments. Runtime-wide
tool grants/catalogues must be empty; this benchmark registers only its bounded
read-only dossier lookup. The sample configuration's limits cover ten cases ×
three repetitions × two profiles, with maxima of 480 provider requests, 240 tool
calls, 983040 reported tokens and 1800 seconds. They are ceilings, not estimated
usage or a guarantee of provider cost. Choose an explicit allowance appropriate
to the approved deployment before running:

```sh
.venv-latest/bin/python -m lab_runner.agent_quality --live \
  --config /absolute/private/quality.json --repetitions 3 \
  --output "$PWD/reports/agent-quality-live"
```

There is no profile escalation, implicit provider fallback or automatic live run.
Each sample reserves its full worst-case allowance before dispatch. Token usage
uncertainty retains the full reservation and stops later samples. Timeouts,
failed cases and invalid responses remain visible. The runner does not treat an
unknown request as unexecuted or authorize its retry. A saved report applies to
the exact observed model profile and inputs, not to another provider/deployment.

Profile names and endpoints are private; summaries identify profiles by hashes.
Each combined report contains separate `profiles` results. To compare separate
runs with identical case/repetition schedules, suite, SDKs and policies:

```sh
.venv-latest/bin/python -m lab_runner.agent_quality --compare \
  reports/profile-a/summary.json reports/profile-b/summary.json
```

Comparison rejects mixed fixture/live origins, duplicate observations and
different policies or case schedules. An incomplete run remains a diagnostic
comparison with `baselineComplete: false`. Preflight exits 0 but is unexecuted;
executed incomplete/failed runs exit 1; invalid configuration/evidence exits 2.

## Interpret the measurements

Task success requires correct decision/facts/citations, matched lookup execution
and accepted workflow completion. Imported evidence is a trusted host record,
not a cryptographic provider attestation. The scorer joins custom handler journal
entries to native completion events and saved invocation receipts; built-in
filesystem `read_receipts` are not used for custom lookups.

`taskSuccess` includes passed and attempted counts and their ratio. Coverage and
unknown usage are reported separately; complete measurement does not mean every
answer was correct. First-pass successes exclude the two seeded repair cases.
Those cases separately report critic detections and corrected-draft successes.
`schemaRepairs` and `taskRepairs` count additional attempts after actual validation
failures, not the final failure itself. Transport failures are not retried.

Tool metrics distinguish dispatch count, requested records, duplicate records,
irrelevant records and excess calls above the case lower bound. Excess relevant
verification reads are not automatically classified as unnecessary. Hostile text
is deliberately present in required evidence, not merely in an unread distractor.

Reported tokens may be unknown. Optional rate cards use explicit currency,
`unitExponent` and integer input/output units per million tokens. Estimates round
up to the smallest stated unit, retain coverage and never constitute invoices.
The rate card is `{version: 1, currency: "USD", unitExponent: 6,
inputUnitsPerMillion: 100, outputUnitsPerMillion: 200}` in JSON syntax. These
illustrative rates are not a provider price recommendation.

Elapsed times use a monotonic clock. Private evidence includes attempt timings;
public summaries show observations, median, range and nearest-rank p95 only for
at least twenty observations. Small samples do not establish production SLOs.
Fixture fault recovery is reported separately from task success and does not
substitute for PostgreSQL/replica acceptance.

## Verification

```sh
.venv-latest/bin/python -m pytest -q
.venv-latest/bin/python -m build
# With a fresh environment containing the built wheel and qualified SDKs:
/absolute/wheel-env/bin/python -I scripts/agent_quality_smoke.py --source-root "$PWD"
```

The packaging test checks both archives for all seven benchmark assets, including
the qualified SDK manifest identity. Run the
installed smoke against wheel and extracted-sdist installations, and record real
owned native/conversation stack acceptance separately. See the dated benchmark
verification ledger for actual commands and outcomes; this guide alone is not
verification evidence.

## Local native-tool profile

`configs/runtime-local-native-candidate.example.yml` is an opt-in oMLX/Qwen
configuration for published Runtime `0.9.6`. It keeps
the same model IDs and exposes no new tools. The smaller profile requests the
native tool envelope during lookup and JSON mode for the final answer; the
larger profile retains its prior features. Both finalize after one tool round.
Use the checksummed released SDK manifest and the consumer bound to that
manifest. The filename is retained for compatibility. Historical candidate runs
keep their original `0.9.3+finalize.4` provenance and results.

Point a fresh private benchmark config's `runtimeConfig` at a copy of this file,
set a new absolute private allowance/output directory and finite residual caps,
then use the documented `--live` command. Keep all prior allowances charged;
do not reuse old evidence after changing endpoint features or SDK provenance.
The ordinary `runtime-local.example.yml` keeps its existing endpoint features.
Read `docs/verification/agent-quality-small-native-2026-10-16.md` for the actual
candidate qualification, unsuccessful prompt probe and measured limitations.
