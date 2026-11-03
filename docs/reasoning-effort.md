# Reasoning-effort integration lab

This separate lane consumes published Runtime 0.9.12 and checks canonical prose
through actual SDK HTTP requests and owned Claude/Codex CLI fixtures. It supplies
copyable blueprints and an optional bounded live runner. The ordinary
`dependencies/releases.json`, quality benchmarks, PostgreSQL/service gates and
historical evidence remain separate.

Core inspects Markdown, Runtime maps effort to provider controls, and Harness
owns admitted workflow state. Native profiles consume Prosaic prose directly;
they do not require `prosaic apply` or copies in Claude/Codex directories.

## Install the exact lane

Use a fresh environment. `releases-reasoning.json` selects Core 0.4.1, Runtime
0.9.12, recorder 0.3.0, Harness 0.9.4 and store 0.4.0. It changes only Runtime
relative to the ordinary Lab manifest. Newer Harness 0.9.6/store 0.4.1 releases
are not silently adopted or certified by this lane.

From the Lab repository root:

```sh
python3.12 -m venv .venv-reasoning
LAB_REASONING_PY="$PWD/.venv-reasoning/bin/python"
"$LAB_REASONING_PY" -m pip install --require-hashes -r dependencies/requirements.lock
"$LAB_REASONING_PY" scripts/prepare_dependencies.py --manifest dependencies/releases-reasoning.json
"$LAB_REASONING_PY" scripts/install_dependencies.py --manifest dependencies/releases-reasoning.json
"$LAB_REASONING_PY" -m pip install --no-deps .
"$LAB_REASONING_PY" scripts/audit_install.py --manifest dependencies/releases-reasoning.json
"$LAB_REASONING_PY" -m pip check
LAB_REASONING_WHEELS=$("$LAB_REASONING_PY" -c "from pathlib import Path; from prosaic_integration_lab.dependencies import cache_directory; print(cache_directory(Path('dependencies/releases-reasoning.json'), Path('.cache/wheels')).resolve())")
mkdir -p .lab/reasoning
```

Preparation downloads the exact public wheel URLs and checks SHA256 values.
The payload audit verifies all five installed SDKs. No editable SDK installs,
private SDK APIs, vendor authentication or inference are needed for fixtures.

Run the ordinary Lab suite in its original environment. Its quality/provenance
guards intentionally admit only their recorded SDK trains; installing Runtime
0.9.12 there does not qualify that train or replace those guards. The reasoning
tests live outside the default unit/functional collection for this reason.

## Run credential-free control checks

```sh
"$LAB_REASONING_PY" -m pytest tests/reasoning_acceptance -q
"$LAB_REASONING_PY" -I -m lab_runner.reasoning_eval test \
  --manifest dependencies/releases-reasoning.json --wheel-dir "$LAB_REASONING_WHEELS" \
  --output .lab/reasoning/fixture.json
```

Use a new receipt filename on subsequent runs. Reports are exclusive, private
files and are never overwritten. The `Reasoning effort integration` workflow
runs installed-Lab checks on Linux AMD64/ARM64 with Python 3.12, no Docker or
live calls. Remote CI results are separate from local verification.

Fixtures inspect every neutral effort against exact OpenAI-compatible model IDs
for OpenAI, DeepSeek V4 Pro, Qwen 3.8 Max, local ThinkingCap Qwen, Nemotron NIM
and Gemma. They check actual JSON controls, unsupported levels with zero requests,
profile-default precedence and omitted effort. Owned native clients inspect
Claude `--effort` and Codex `model_reasoning_effort`, including Codex-only ultra.
Native fixture capabilities are explicit properties of the fake clients; actual
native profiles use Runtime's bounded automatic model discovery.

Fixture results verify control wiring against synthetic peers. They do not
qualify live provider compliance, model quality, budgets or OS confinement.

## Copy reusable blueprints

The installed wheel includes the same assets as
[`lab_runner/reasoning_eval/data`](../lab_runner/reasoning_eval/data):

```sh
LAB_REASONING_BLUEPRINTS=$("$LAB_REASONING_PY" -c "from lab_runner.reasoning_eval import DATA; print(DATA)")
cp -R "$LAB_REASONING_BLUEPRINTS" ./my-reasoning
export PATH="$PWD/.venv-reasoning/bin:$PATH"
prosaic inspect subagents/medium.md --source ./my-reasoning --json
prosaic-harness validate ./my-reasoning/workflow.yml
```

There are seven `subagents/*.md` effort variants, API/native configurations,
a strict answer schema and a one-call API-backed Harness workflow. Their README
contains direct Runtime/Harness recipes and an effort support table. Inspection
and validation above are offline; the README's execution commands make real calls.

Models and credentials belong in operator config, never Markdown. Omitted prose
uses the profile default; explicit prose overrides it. Unsupported efforts fail
rather than being silently lowered. `none` requests an off control, while `low`
requests positive thinking. Gemma's low/medium/high/xhigh/max all select one on
switch. Local ThinkingCap Qwen supports none/low/medium/xhigh; ultra is Codex-only.
The earlier server called "Gemma 4.1" advertised the Gemma **4** model ID
`gemma-4-31B-it-oQ4e-mtp`; do not infer capabilities from a server nickname.

Lab 0.9.3 removes an ambiguous reasoning prohibition from all seven agents.
Their JSON restrictions govern the returned answer; native thinking is selected
by effort and provider capabilities. A bounded prompt comparison found wording
sensitivity without an arithmetic accuracy improvement from this deletion.
Keep control compliance, JSON format and answer correctness separate.

## Opt in to bounded real-provider runs

Edit the copied API config for the actual server/model, including a separate
Gemma LAN endpoint if applicable. Supply `REASONING_API_KEY` privately, or use a
private Runtime secret file. Authenticate native CLIs separately and reuse real
account quota keys. These commands make inference calls:

```sh
"$LAB_REASONING_PY" -I -m lab_runner.reasoning_eval live --live \
  --manifest dependencies/releases-reasoning.json --wheel-dir "$LAB_REASONING_WHEELS" \
  --kind api --config ./my-reasoning/api.yml --profile gemma \
  --effort none --effort low --max-calls 12 \
  --allowance "$PWD/.lab/reasoning/allowance.json" \
  --timeout 240 --output .lab/reasoning/gemma.json

"$LAB_REASONING_PY" -I -m lab_runner.reasoning_eval live --live \
  --manifest dependencies/releases-reasoning.json --wheel-dir "$LAB_REASONING_WHEELS" \
  --kind native --config ./my-reasoning/native.yml --profile codex \
  --effort low --effort high --max-calls 12 \
  --allowance "$PWD/.lab/reasoning/allowance.json" \
  --timeout 240 --output .lab/reasoning/codex.json
```

For Qwen, use API profile `qwen-local` with none/low/medium/xhigh. For Claude,
use native profile `claude` and its admitted levels. Choose a fresh receipt path
each time. Share the same persistent allowance across profiles and reruns; its
maximum is immutable and exhaustion does not reset it. Never delete the file to
hide failed/uncertain attempts. Unknown outcomes retain their reservations.

The whole requested batch is reserved atomically before its first dispatch.
If capacity is insufficient, the failed receipt records the allowance state and
no request is made. Completed observations survive execution exceptions or
cancellation. An unknown dispatch conservatively retains the entire batch's
reservation; the report does not manufacture a known zero for it.

API efforts permit one tool-free, nonstreaming request, at most 4,096 output
tokens and a finite 1–300 second deadline. Unsupported API batches fail before
reservation or dispatch. Native units count host invocations, **not vendor-internal
model requests**; read-only permissions are not exact path isolation, a token cap
or a cap on native subagent calls. No fallback or automatic retry is performed.
Execution failure stops the batch; completed incorrect answers remain recorded.

## Interpret evidence

Live receipts separate completion, strict JSON format and arithmetic correctness.
They include aggregate timings/reported usage, omitting URLs, credential locations,
raw prompts, model answers and native stderr. A fenced correct answer can have
`answerCorrect: true` and `formatCorrect: false`. Missing usage remains unknown.

Live receipts deliberately say `controlsVerified: false`: an HTTP success or
reasoning-token count alone cannot prove that the server honored effort. This
arithmetic task does not certify general model quality or a monotonic token budget.
The [historical live Qwen/Gemma report](https://github.com/B3Cognition/prosaic-runtime/blob/v0.9.12/docs/live-reasoning-2026-11-02.md)
used server tokenization and rendered-prompt evidence to verify controls. It
retains Qwen's incorrect none/xhigh answers and Gemma's equivalent positive
prompts. This new lane does not rerun or relabel that historical evidence.
See the [Runtime effort contract](https://github.com/B3Cognition/prosaic-runtime/blob/v0.9.12/docs/native-execution.md#reasoning-effort-from-prose)
for capability discovery, custom aliases and adapter restrictions.

## Troubleshooting

`reasoning_lab_failed` is deliberately sanitized. Check that all five installed
SDK payloads match the reasoning manifest, that the receipt parent is writable
and the chosen filename is new. Live mode additionally requires `--live`, an
explicit profile/effort list, finite timeout and an absolute allowance path.
An exhausted allowance or changed maximum is a stop, not permission to reset it.
For unsupported levels, use the exact model's supported values or review an
explicit operator capability override. Fixture failures retain the adapter,
effort and observed control in their safe report; no live credentials are needed
to reproduce those checks.
