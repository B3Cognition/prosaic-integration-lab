# Your first Prosaic integration

Start with a result you can inspect, then add the pieces you need. Steps 1–2
need Python 3.12 and internet access to install packages. They need no Docker,
model account, API key or local LLM. Step 3 adds Docker. Steps 4–5 explicitly
invoke real models and can consume provider quota.

Use a terminal on macOS or Linux; commands below use a POSIX shell. Windows
shell and Docker host setup are not covered by this walkthrough. Lab 0.7.0
includes this guide, `examples/first_workflow.py` and Explorer; the SDKs remain
released packages. Earlier 0.6.2 artifacts retain their original contents.
The [0.7.0 verification ledger](verification/release-0.7.0-2026-10-25.md)
records clean public-wheel/rebuilt-source checks with Runtime 0.9.8, including
installed visual docs, playback and bounded synthetic execution controls.

## Setup once

Install Python 3.12 first. Choose a new checkout/environment; the legacy
`prosaic` distributions and current `b3-prosaic` distributions share import
paths and must not be mixed. Run every section from the Lab repository root
in the same terminal, so `LAB_PY` and `WHEEL_DIR` remain available.

```sh
git clone https://github.com/B3Cognition/prosaic-integration-lab.git
cd prosaic-integration-lab
umask 077
python3.12 -m venv .venv-lab
LAB_PY="$PWD/.venv-lab/bin/python"
"$LAB_PY" -m pip install --require-hashes -r dependencies/requirements.lock
"$LAB_PY" scripts/prepare_dependencies.py
"$LAB_PY" scripts/install_dependencies.py
"$LAB_PY" -m pip install --no-deps .
"$LAB_PY" scripts/audit_install.py
"$LAB_PY" -m pip check
export PATH="$PWD/.venv-lab/bin:$PATH"
WHEEL_DIR="$PWD/.cache/wheels/$("$LAB_PY" -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("dependencies/releases.json").read_bytes()).hexdigest())')"
"$LAB_PY" -m prosaic_integration_lab --version
```

The `pip install --no-deps .` step installs the Lab consumer from this checkout;
it does not install editable or sibling SDK sources. Preparation downloads
checksummed public SDK wheels; the audit verifies their
installed payloads. Expected versions: Core 0.4.1, Runtime 0.9.8, recorder 0.3.0,
Harness 0.9.4, store 0.4.0. `pip check` should report no broken requirements.
If any command fails, stop and use [troubleshooting](#when-something-goes-wrong).
No model server is contacted by these install/audit commands.

Prefer a visual walkthrough? Run `"$LAB_PY" -m lab_runner.explore` after setup.
Start in **Documentation**, select a component, and switch between **User** and
**Developer** explanations. **Simulation** plays eight illustrative scenarios
without contacting models. The [Explorer guide](explorer.md) covers dedicated
live controls, permissions and retained evidence. Explorer is included in 0.7.0;
the chat/workflow service below remains separate.

## 1. Build your first workflow

```sh
"$LAB_PY" -I -B examples/first_workflow.py
```

You should see JSON with `status: "prepared"`, a workflow `fingerprint`, the
steps `find`, `review`, `done`, `rejected`, and review choices `accept`/`reject`.
There is no model answer yet: this demonstrates validating/admitting a graph
and preparing its input snapshot. It does not execute the graph, reach the
human pause or call a model/tool. No database, credential or endpoint is needed.

Open [the complete example](../examples/first_workflow.py). It registers approved
Markdown instructions, a closed result schema, a model binding and finite host
policy. The endpoint deliberately uses `.invalid`; construction does not contact
it. Your application replaces the binding before authorized execution.

**Why this helps:** a client can propose a graph while your host controls the
available agents, schemas, permissions and budgets. Use the workflow fingerprint
to identify the admitted definition. Do not treat this example as authentication
or a completed agent run.

## 2. See safe fallback without model accounts

First verify pool behavior, then inspect a provider-shaped failure demonstration:

```sh
"$LAB_PY" -m lab_runner.native_eval unified-cli-test \
  --manifest dependencies/releases.json --wheel-dir "$WHEEL_DIR"
mkdir -p reports
"$LAB_PY" -m lab_runner.native_eval unified-fallback-test \
  --manifest dependencies/releases.json --wheel-dir "$WHEEL_DIR" \
  > reports/first-fallback.json
"$LAB_PY" -m json.tool reports/first-fallback.json
```

Expected: `passed: true`, `caseCount: 13` for the CLI lane and `caseCount: 18`
for fallback, `liveInvocations: 0`, `cleanup: "verified"`. These commands create
their own fake vendor executables, loopback model fixtures and temporary
workspaces. They do not run your installed Claude/Codex or local model.

Read `scenarios` in the saved fallback receipt:

| Scenario | What you should see | What it demonstrates |
| --- | --- | --- |
| `double-quota` | Attempts `claude`, `codex`, `local`; task passes | Both fake native providers reject before work; the API fixture completes the repair |
| `persisted-cooldown` | Only `local` attempted; native profiles skipped | Learned cooldowns survive a subsequent CLI process |
| `claude-tool-partial` / `codex-tool-partial` | Failure with `recoveryRequired: true`; no later API request | Partial effects stop execution instead of replaying work elsewhere |
| `claude-text-partial` / `codex-text-partial` | Failure with `recoveryRequired: true` | Partial model output also prevents automatic replay |
| `api-tool-partial` | Task output exists but the overall invocation fails | Valid output alone does not prove safe completion |

Some scenarios deliberately fail their agent invocation. The overall test command
succeeds when those failures stop as expected. The CLI lane also checks the
all-unavailable case: prompt `capacity_unavailable`, no wait or automatic replay.
These are synthetic correctness checks, not real quota exhaustion or a model
quality comparison. [Pool contracts and Python/CLI examples](unified-runtime-pools.md)
explain the real execution policy.

## 3. Run the service or open the browser

Optional: install/start Docker and confirm `docker info` succeeds. The first
build downloads container images and can take several minutes. The Lab owns
disposable loopback services, PostgreSQL and fixture credentials; it is not
production authentication. No real inference is used by the commands below.

```sh
"$LAB_PY" scripts/build_consumer.py \
  --manifest dependencies/releases.json --dependency-mode released \
  --tag prosaic-integration-lab:dev
"$LAB_PY" -m lab_runner demo --mode native --postgres-version 16
"$LAB_PY" -m lab_runner demo --mode conversation --postgres-version 16
```

The automated native demo discovers approved specialists, admits a workflow,
runs two specialists with synthetic responses, pauses for structured review and
resumes through another HTTP replica. The conversation demo adds retained chat
and an approved player-lookup workflow. Successful commands print a `completed`
journey and a report path. Each also prints `Evidence: .../.lab/<owner>`;
open that directory's `result.json` to check `passed: true` and
`cleanup: "verified"`. A nonzero exit needs investigation.

For an interactive browser:

```sh
"$LAB_PY" -m lab_runner.chat
```

Try the page's suggested "Find players" prompt, then follow the displayed
selection and approval interaction. Scripted replies are deterministic rather
than a general assistant. The launcher opens the chat page and labels its mode;
if browser opening fails, open the printed **Connection file** locally and use
its `url` field privately. The printed plain `Chat:` URL alone does not include
the single-use connection code. Do not share the connection file. Press Ctrl+C
in the launching terminal when done and check cleanup. A launch link expires
after 10 minutes and is single-use; restarting gives a new link.

The browser uses scripted responses or an explicitly configured local Qwen API
profile. It does **not** expose unified Claude/Codex/local pool selection.
[The browser reference](reference-guide.md#converse-in-the-browser) covers local
Qwen opt-in and session/reload behavior. In this Lab, "native workflow" means
host-admitted Harness execution; "native backend" means Claude Code/Codex CLI.

## 4. Connect real models (explicit opt-in)

This section executes real work. Start only when you want to consume provider
quota or local compute. Runtime 0.9.8 supports both its Python API and CLI.
Install/authenticate vendor CLIs separately. The checked-in native example
requires Claude Code ≥2.1.248 and Codex CLI ≥0.154.0; verify with `claude --version`
and `codex --version`. Model access is account-dependent.

Choose an unused private directory; if it exists, choose another rather than
overwriting a working profile:

```sh
PRIVATE_DIR="$HOME/prosaic-lab-profiles"
mkdir -m 700 "$PRIVATE_DIR"
cp configs/native-runtime.example.yml "$PRIVATE_DIR/"
cp configs/runtime-comparison-local.example.yml "$PRIVATE_DIR/"
cp configs/unified-runtime.example.yml "$PRIVATE_DIR/"
chmod 600 "$PRIVATE_DIR/"*.yml
```

Edit the copied files before running anything:

- Native: choose accessible Claude/Codex models and authenticated login/config
  directories. Replace `your-accessible-codex-model`. Keep `effort: low` if you
  want the measured Codex setting.
- Local/API: choose your model, authenticated numeric-loopback `/v1` endpoint
  and private `api_key_file`; start your own compatible model server separately.
  The Qwen/oMLX file is an example, not an automatic model download or installer.
- Unified: keep the aliases consistent with both files and choose pool order.
  Capacity files now live beside these private configs. Profiles sharing a real
  account/quota must share its quota key. Aliases do not multiply subscriptions.

For a first real pool run, the source is a tiny checked-in Markdown repair agent.
Create an unused workspace containing only a deliberately wrong calculator:

```sh
WORKSPACE="$PWD/first-agent-workspace"
mkdir -m 700 "$WORKSPACE"
printf 'def add(a, b):\n    return a - b\n' > "$WORKSPACE/calculator.py"
prosaic-runtime subagents/repair.md --source "$PWD/lab_runner/native_eval/data" \
  --config "$PRIVATE_DIR/unified-runtime.example.yml" --pool agents --cwd "$WORKSPACE" \
  --timeout 300 --max-attempts 3 --max-native-attempts 2 \
  --native-permissions workspace-write --native-timeout 60 \
  --enable-api --api-timeout 180 --max-api-requests 8 \
  --max-api-tool-calls 7 --max-tool-rounds 8 --max-api-reported-tokens 65536 \
  --allow-tool read_file --allow-tool write_file --allow-tool edit_file \
  --read-root "$WORKSPACE" --write-path "$WORKSPACE/calculator.py"
cat "$WORKSPACE/calculator.py"
```

On success, `add` returns `a + b`; inspect the CLI result and changed file.
Native CLI permissions cover its workspace; the API write grant is the exact
calculator path. They are independent scopes. The pool can use at most 3 profile
attempts, including 2 native attempts. API request/tool/reported-token caps do not
bound native internal loops or subscription spend. Tool access is real in this
workspace; native backends can run tools permitted by their vendor sandbox.

Exit 0 means success,1 execution failure,2 invalid config/authority,130 interruption.
After partial or uncertain work, inspect/reconcile before authorizing another
run; rerunning this command is new execution authority, not receipt recovery.
Authentication errors and timeouts stop; only proven pre-work rejection permits
fallback. All-cooled returns `capacity_unavailable` plus earliest `retry_at`.
Raw Runtime result metadata may be private; the Lab benchmark filters reports.

For API-only/native-only policies or Python embedding, use the complete
[unified Runtime guide](unified-runtime-pools.md#configuration-and-invocation).
Only one real Claude account was available on the measured host; distinct-account
live switching has not been established by those measurements.

## 5. Compare your models

After private native/local setup, follow the [benchmark recipe](realistic-runtime-benchmark.md).
It requires both native profiles and the local default profile. It reuses release
brief, incident handoff and invoice SQL Markdown tasks with synthetic inputs and
fixed graders. Choose a new output directory under an existing private parent:

```sh
mkdir -m 700 "$PRIVATE_DIR/studies"
"$LAB_PY" -m lab_runner.native_eval unified-benchmark \
  --manifest dependencies/releases.json --wheel-dir "$WHEEL_DIR" \
  --runtime-config "$PRIVATE_DIR/native-runtime.example.yml" \
  --local-config "$PRIVATE_DIR/runtime-comparison-local.example.yml" \
  --repetitions 3 --timeout 60 --local-timeout 240 --live \
  --output "$PRIVATE_DIR/studies/first-240s"
```

Remove `--local-timeout 240` for the 180s default. Accepted values are finite
1–300s; the total pool deadline remains 300s and native deadline 60s. Three
trials produce 27 assignments if availability/uncertainty permits completion,
with a maximum 243 mixed dispatch units. These units are not token/cost equivalents.

Inspect `report.json`: success rate, latency, selected profiles, skips, fallback
events and allowance. A controlled cooldown skip is different from provider
rejection after dispatch. Uncertain consumption remains reserved and can stop
the study. Never delete evidence merely to reset an allowance. The existing
[live observations](verification/unified-cli-lab061-local240-2026-10-25.md)
are small factual-task studies, not guarantees of quality or speed on your model.

## 6. Integrate the pieces in your application

Use [the small standalone example](../examples/first_workflow.py) as the admission
starting point, then choose the execution pattern:

| Your application | Public APIs / example | What you replace or supply |
| --- | --- | --- |
| Run one Markdown agent | `UnifiedRuntime`, `PoolPolicy` in [pool guide](unified-runtime-pools.md) | Inspected artifact, private profiles, workspace, native/API permissions and limits |
| Build and execute reviewed workflows | `WorkflowFactory`, `WorkflowCatalog`, `WorkflowBindings`, `WorkflowPolicy`, `Harness` in [consumer guide](consume-native-workflows.md) | Approved registrations, authenticated host context, execution bindings, stores and review UI |
| Embed a chat assistant | `Conversation` and session stores in [conversation guide](conversations.md#build-a-small-assistant) | Model profile, owner identity, session storage and allowed workflow bindings |
| Add durable replicas and usage views | PostgreSQL stores/recorder in [persistence guide](persistence.md) | Separate migration/runtime roles, namespaces, attribution and filtered owner-only views |

There is no automatic promise that every Harness/Conversation binding accepts
`UnifiedRuntime`; the existing Lab service and browser use their documented API
bindings. Use the standalone pool pattern for native CLI execution until an
explicit service integration is implemented and qualified.

Keep tenant, actor, billing identity, tools, provider URLs and grants in trusted
host code. Clients propose logical work; they do not grant themselves execution
authority. A saved usage receipt does not authorize retry or prove an effect was
completed. For end-to-end HTTP request bodies, see
[the native HTTP contract](native-workflows.md#catalogue-proposal-execution-and-human-response).

## Optional capabilities

After the basic path works, explore [tool approval](tool-approval.md),
[failure isolation and receipt recovery](failure-isolation.md),
[sandboxed CLI admission](sandboxed-tools.md),
[trajectory evaluation](trajectory-evaluation.md) and
[Castle memory](castle-quickstart.md). These consumer blueprints have separate
qualification and limits. Memory/correction are experimental and opt-in; offline
fixtures do not establish model benefit. The [reference index](reference-guide.md)
retains advanced acceptance/operations recipes and historical evidence.

## When something goes wrong

| Symptom | First action |
| --- | --- |
| `python3.12` missing | Install Python 3.12; create the environment again with that interpreter |
| Import, SDK version or audit failure | Check `LAB_PY`, run the version command/audit, and rebuild a fresh environment from the manifest; do not mix legacy/editable SDKs |
| Wheel directory missing | Rerun preparation and recompute `WHEEL_DIR` from the exact manifest |
| `prosaic-runtime` missing | Export the environment's `bin` directory to `PATH` as in setup |
| Docker unavailable | Steps 1–2 still work; start Docker before the service/browser step |
| Browser reload or expired launch link fails | Restart the launcher for a new link; do not reuse an expired/single-use bootstrap URL |
| Native authentication failure | Authenticate the exact configured vendor profile outside the Lab; an auth error does not authorize switching/replay |
| Local endpoint/model failure | Check the configured port, model name, private key file and running server; no model is automatically installed |
| `capacity_unavailable` | Inspect availability/retry time; wait or deliberately change eligible profiles without clearing genuine cooldown evidence |
| Invalid grants/budgets | Use separate native permissions and API grants; do not widen them simply to silence an error |
| Timeout or partial work | Preserve output/receipts and reconcile effects before explicitly authorizing another run |
| Existing workspace/study output | Choose a fresh directory; preserve previous results/accounting |
| Failed cleanup or nonzero fixture command | Keep the sanitized receipt; inspect only the owned resource IDs and fix the cause rather than globally pruning Docker |

For reproducible bug reports, include command, SDK versions, platform and a
filtered receipt. Exclude credentials, session IDs, private provider streams and
raw customer prompts.
