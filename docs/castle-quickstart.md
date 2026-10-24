# Castle memory: start here

Castle lets a workflow recall **material you previously imported**: project
notes, source files and exported development conversations. Prosaic selects
relevant evidence, saves an exact copy, and lets Harness resume from that copy.

**Memory is off by default.** Installing the Lab does not start Castle or add
memory to existing chats. This integration is an explicit host API/operator
workflow. There is no new public HTTP endpoint, automatic coding-tool recorder
or model-facing memory tool grant.

## When is it useful?

| What you need | How Castle helps | What you still need to check |
| --- | --- | --- |
| “Why did we choose SQLite last month?” | Retrieve imported design notes or development transcripts with source references. | Whether that decision is still current. |
| Return to a project after a break | Recall earlier investigations, attempted fixes and constraints. | Current repository files, tests and open issues. |
| Onboard another developer | Find the recorded explanation behind an unfamiliar design. | Whether the relevant sessions were actually imported. |
| Resume a reviewed workflow | Keep the exact evidence used before the pause, even if Castle changes or goes offline. | The saved run owner, review revision and workflow deadline. |

Castle only knows what was captured and imported. Your colleague's Castle skill
or MCP setup may collect more sources; enabling this provider does not install
those capture hooks. Memory text is evidence to inspect, never permission to
approve an action or an instruction the agent should obey. Use current tools
to check current facts.

Castle's standalone `castle memory` fast-memory sidecar is a separate source.
This provider reads the explicitly prepared LanceDB palace. Records held only
in that sidecar do not automatically appear here; use the source-file or
exported-conversation import steps below for the material you want it to recall.

## 1. Get the right packages

Run these commands from this repository's root, using Python **3.12** on macOS
or Linux. The worker currently requires POSIX process groups. You need a folder
containing all seven wheels listed in
[`dependencies/memory-release-candidates-2026-10-24-r4.json`](../dependencies/memory-release-candidates-2026-10-24-r4.json).
The first five are the Lab's normal public SDK versions. The Castle adapter and
worker are **unpublished candidates**: obtain the exact qualified wheel bundle
from the maintainer. If you only have this repository, stop here and request
that bundle; a generic `pip install cognitive-castle` is not a verified substitute.

Get the matching **r4** stack bundle and its native Linux AMD64/ARM64 × PostgreSQL
16/18 verification status from [Lab PR #26](https://github.com/B3Cognition/prosaic-integration-lab/pull/26).
The [r4 stack preparation record](verification/castle-linux-release-r4-2026-10-24.md)
identifies its exact source and wheel hashes. Earlier candidate bundles remain
separately archived; choose the bundle that matches this manifest exactly.

Use two environments. The host runs Prosaic; the worker runs Castle. Set the
wheel folder to its actual absolute path:

```sh
export CASTLE_WHEELS=/absolute/path/to/qualified-wheels
python3.12 -m venv .venv-castle-host
.venv-castle-host/bin/python -m pip install --require-hashes -r dependencies/requirements.lock
```

Verify the bundle **before** installing it:

```sh
.venv-castle-host/bin/python - <<'PY'
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path('src').absolute()))
from lab_runner.castle_memory import memory_artifacts
memory_artifacts(Path('dependencies/memory-release-candidates-2026-10-24-r4.json'), Path(os.environ['CASTLE_WHEELS']))
print('All seven wheel identities and checksums match.')
PY
```

Install the five public SDKs, the adapter and this Lab checkout into the host:

```sh
.venv-castle-host/bin/python scripts/install_dependencies.py --manifest dependencies/releases.json --wheel-dir "$CASTLE_WHEELS"
.venv-castle-host/bin/python -m pip install --no-deps "$CASTLE_WHEELS/b3_prosaic_memory_castle-0.1.0-py3-none-any.whl"
.venv-castle-host/bin/python -m pip install --no-deps .
.venv-castle-host/bin/python -m pip check
```

Create the separate worker environment:

```sh
python3.12 -m venv .venv-castle-worker
```

For Linux CPU hosts, installing Torch from its CPU index before Castle avoids
unneeded CUDA packages:

```sh
.venv-castle-worker/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Then install Castle and check its dependencies:

```sh
.venv-castle-worker/bin/python -m pip install "$CASTLE_WHEELS/cognitive_castle-3.4.2-py3-none-any.whl"
.venv-castle-worker/bin/python -m pip check
```

Castle's package currently includes neural dependencies, so installation can
be large. FTS reads load no embedding models. SUE and SOAR are not needed.

This release preparation keeps older candidate manifests and receipts intact; do not mix
same-version adapter wheels from different bundles. Host snapshots use public
Runtime 0.9.8. The adapter's separate model-facing `memory_tools()` API requires
a future qualified Runtime with its explicit error capability.

## 2. Try the local walkthrough first

This uses a **real Castle worker**, synthetic notes and a local fixture response.
It makes no paid model call and does not import your files. Choose a new absolute
directory; the example refuses to overwrite an existing directory.

```sh
.venv-castle-host/bin/python examples/castle_memory_demo.py --enable --worker-python "$PWD/.venv-castle-worker/bin/python" --directory /tmp/castle-demo-1
```

The output should contain:

```json
{
  "status_before_review": "waiting",
  "status_after_resume": "completed",
  "memory_status": "available",
  "source_changed_after_pause": true,
  "resumed_with_memory_disabled": true,
  "frozen_snapshot_preserved": true,
  "model_calls": 1
}
```

You will also see the original “Atlas chose SQLite” quote. The example changes
the stored source to PostgreSQL after the pause and stops the provider. Resume
still uses the saved SQLite evidence. The response generator is a fixture,
not an LLM; this demonstrates the integration, not answer quality.

Running the example without `--enable` prints
`{"enabled": false, "executed": false}` and starts no Castle worker.
The demo directory contains only its synthetic palace and run state; keep it
for inspection, or remove that specific directory when finished.

## 3. Connect your own Castle palace

A **palace** is Castle's local database directory. A **wing** is a named source
group within it. A **namespace** binds that palace to the host's chosen owner
scope. Start with the existing palace your colleague uses, or initialize one
with Castle's standard project setup:

For legacy NLP import features, provision the compatible spaCy model first:

```sh
.venv-castle-worker/bin/python -m spacy download en_core_web_sm
```

Use an approved compatible model wheel for offline setup. Standard Castle
import can also require its configured embedding weights. FTS reads require
no model weights and never download them during a query.

```sh
export CASTLE_PALACE=/absolute/path/to/your-palace
.venv-castle-worker/bin/castle --palace "$CASTLE_PALACE" init /absolute/path/to/your-project --yes
.venv-castle-worker/bin/castle --palace "$CASTLE_PALACE" status
```

Skip `init` when using an existing populated palace. Standard Castle import can
use its configured local models; it is separate from the FTS read provider.
Check the actual wing names shown by Castle. To import exported coding sessions
into a wing named `project`, run this separately:

```sh
.venv-castle-worker/bin/castle --palace "$CASTLE_PALACE" mine /absolute/path/to/exported-sessions --mode convos --wing project --skip-kg
```

Only import sources you intend this owner to access. This command does not
continuously capture future sessions. Configure capture through the coding
tool's existing Castle integration, then import new material as needed.

Explicitly prepare the populated palace for provider reads:

```sh
.venv-castle-worker/bin/castle provider prepare --palace "$CASTLE_PALACE" --namespace project-memory --config-dir "$HOME/.castle"
```

Use the same namespace and the same config file in the next step. Preparation
can create the FTS index; provider reads do not silently repair or migrate a
store. For an older incompatible palace, use Castle's explicit migration/repair
instructions and retain its backups.

## 4. Enable one trusted host binding

Copy [`configs/memory-provider.example.json`](../configs/memory-provider.example.json)
to a private operator file. Replace its contents with the following, changing
**every absolute path, the model name, owner IDs and wing names** to your values.
The local model server must already be running and support this workflow's JSON
schema. The operator CLI permits only loopback synthetic/local endpoints.

```json
{
  "namespace": "castle-workflows",
  "principal": {"tenant_id": "tenant-a", "actor_id": "alice", "billing_account_id": "payer-a"},
  "store": {"kind": "file", "path": "/absolute/private/castle-runs"},
  "runtime": {"base_url": "http://127.0.0.1:8000/v1", "model": "YOUR_LOCAL_MODEL_NAME"},
  "memory_required": false,
  "memory": {
    "enabled": true,
    "bindings": [{
      "tenant_id": "tenant-a", "actor_id": "alice", "billing_account_id": "payer-a",
      "namespace": "project-memory",
      "palace_path": "/absolute/path/to/your-palace",
      "config_path": "/absolute/path/to/your/home/.castle/config.json",
      "worker_command": ["/absolute/path/to/this/checkout/.venv-castle-worker/bin/python", "-I", "-m", "cognitive_castle.provider_worker"],
      "allowed_wings": ["project"],
      "profile": "memory-fts-v1",
      "recency_boost": false
    }]
  }
}
```

Use the venv's `bin/python` path directly; do not replace it with the system
Python path it may link to. Choose a private directory for host config, requests
and run state, and restrict the config file:

```sh
chmod 600 /absolute/private/castle-host.json
```

The three owner IDs in `principal` must match the binding exactly. In an
application, these IDs come from authentication and host policy. Do not let a
chat message or model choose identities, database paths, wings or worker commands.

## 5. Ask, review and resume

Create `/absolute/private/castle-request.json`:

```json
{"task": "Explain our earlier SQLite decision and cite the saved evidence.", "query": "SQLite offline persistence"}
```

Start a run and save its returned ID/revision:

```sh
.venv-castle-host/bin/python -m lab_runner.memory_workflow start --config /absolute/private/castle-host.json --request /absolute/private/castle-request.json > /absolute/private/castle-start.json
```

Expected: `status` is `waiting`; `memory_status` says what was captured. The
workflow has saved its snapshot and has made **zero model calls** at this point.
This example has a **60-second lifetime including review time**. Complete the
next step promptly; longer review requires a different host workflow policy.

Resume using the saved values, without copying them by hand:

```sh
.venv-castle-host/bin/python - <<'PY'
import json, subprocess, sys
from pathlib import Path
saved = json.loads(Path('/absolute/private/castle-start.json').read_text())
subprocess.run([sys.executable, '-m', 'lab_runner.memory_workflow', 'resume',
    '--config', '/absolute/private/castle-host.json', '--run-id', saved['run_id'],
    '--expected-revision', saved['revision'], '--choice', 'continue'], check=True)
PY
```

Expected: `status` becomes `completed`, and `answer` contains the structured
answer and its memory status. `--choice reject` finishes without a model call.
`status --config ... --run-id ...` reads the saved status. Do not blindly repeat
a model call after a failure; inspect the saved run and usage evidence first.

Resume uses the frozen bundle. Changing a source, enabling another profile or
turning memory off does not replace evidence already saved in that run. A new
run ID is needed to deliberately capture newer evidence.

## What do the four memory statuses mean?

| Status | Meaning | With `memory_required: true` |
| --- | --- | --- |
| `available` | Scoped evidence was captured successfully. | Continue to review. |
| `empty` | Castle is healthy but the query found no eligible evidence. | Continue to review; this is not proof the event never happened. |
| `disabled` | Memory is off for this workflow. | Stop before creating the run. |
| `unavailable` | The provider could not safely supply evidence. | Stop before creating the run. |

With the default `memory_required: false`, disabled/unavailable memory allows an
explicitly labeled degraded answer. The model cannot claim a different memory
status: the workflow validates it against the saved input.

## Common problems

| Symptom | Check |
| --- | --- |
| “Directory exists” in the demo | Choose a new demo directory; it never overwrites your existing data. |
| Invalid configuration | Use absolute paths, mode `0600`, real owner IDs and a loopback model URL. A disabled memory block must contain only `{"enabled": false}`. |
| `memory_forbidden` / not found | The authenticated tenant, actor and payer must match an allowed host binding/run owner. |
| `unavailable` / incompatible store | Confirm the worker Python exists, Castle is installed there, config path is correct and `provider prepare` used the same palace/namespace. |
| `empty` | Confirm sources were imported, the wing is allowed and the query includes words actually present in them. |
| Run is blocked on resume | Check its deadline, revision, model endpoint and output schema. The demo workflow expires after 60 seconds. |
| No memory in an existing chat | This workflow is opt-in. Your application must call `execution.memory_session(...)`; setting a flag does not retrofit existing chat/native workflows. |

To disable memory for new runs, use `"memory": {"enabled": false}` with no
bindings, or omit `memory`. Existing saved snapshots remain usable by their owner.

The default `memory-fts-v1` preserves raw FTS ranking and uses no recency boost.
Set `recency_boost: true` only when you want newer material favored. Dense/hybrid
retrieval is a separate `profile: "memory-v1"` choice requiring its models to be
provisioned in the worker first. SUE and SOAR remain outside this path. See the
[host/operator reference](optional-memory.md) for boundaries and qualification.
