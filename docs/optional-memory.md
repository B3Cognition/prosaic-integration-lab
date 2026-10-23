# Optional Castle memory candidate

Memory is disabled when the `memory` key is absent or is `{"enabled": false}`.
The default path imports no adapter, launches no worker and loads no embedding
model. Existing HTTP/native/conversation workflows keep their current behavior.
The new workflow is an internal host API and operator CLI; it grants no new
public HTTP operation or model tool.

The Lab owns authenticated identity, namespace, provider configuration and the
optional/required decision. Castle owns scoped retrieval and exact evidence
snapshots. Harness owns durable state, revision checks, review and resume.
Runtime owns the single model execution and metering. Core remains unchanged.
SUE and SOAR are outside this path. FTS ranking is preserved by default;
`recency_boost: true` is explicit and dense `profile: "memory-v1"` is separate
opt-in. Existing Castle modes are unchanged.

## Host wiring

`Execution.memory` owns lazy clients and closes them during shutdown.
`execution.memory_session(authenticated_principal, runtime_config)` constructs
a `MemoryWorkflowSession` using the host's store, namespace and recorder.
Supply a host-generated UUID hex as `run_id`, then call
`start(run_id, task=..., query=..., required=False)`. No request/model value may
select a tenant, actor, payer, worker, palace, namespace or wing.

Enable only in trusted host configuration, with one binding per exact
tenant/actor/payer tuple:

```json
{"memory": {"enabled": true, "bindings": [{
  "tenant_id": "tenant-a", "actor_id": "alice", "billing_account_id": "payer-a",
  "namespace": "owner-memory",
  "palace_path": "/absolute/private/palace",
  "config_path": "/absolute/private/config/config.json",
  "worker_command": ["/absolute/worker-env/bin/python", "-I", "-m", "cognitive_castle.provider_worker"],
  "allowed_wings": ["approved"], "profile": "memory-fts-v1",
  "recency_boost": false, "startup_timeout": 30, "operation_timeout": 10
}]}}
```

The Palace must already be explicitly prepared through Castle's public provider
setup API for this namespace. Install the adapter in the host environment and
Castle in a separate worker environment from the exact selected artifacts.
Enabling an unbound identity fails closed; it does not fall back to another
owner. A missing adapter or unavailable worker is explicit unavailability.

Start searches at most three records and freezes a 64 KiB maximum evidence
bundle with expected revision and text digest checks. Scope, ingest completion
and provenance validation remain in the provider. The bundle is saved in
Harness input before the review pause and before any model call. Resume checks
the frozen owner and revision and reads only saved evidence; Castle may be
offline, changed or disabled. Repeated start with the same request returns the
existing state; conflicting input fails. Concurrent creates use the public
store's conflict behavior; callers must not automatically redispatch.

`available`, `empty`, `disabled` and `unavailable` remain distinct. With optional
memory, missing evidence allows an explicit degraded answer; with required
memory, disabled/unavailable blocks before a run is created. Healthy zero hits
means `empty`, including under required policy. The model receives evidence as
untrusted user data, has no tools, and a deterministic validator requires its
reported memory status to match saved state. Run storage contains source text
and must stay private; public status returns only filtered fields.

This small synthetic workflow permits one call, 4096 tokens and a **60-second
wall-clock lifetime including review time**. Delayed resumes block at the
Harness deadline. A production workflow needs an explicitly chosen review
lifetime and its own policy/validation; this lane is not live certification.

## Operator CLI

Copy `configs/memory-provider.example.json` to a private file, use an absolute
store path, and set mode `0600`. It is trusted host configuration, not a client
request. The CLI accepts only loopback synthetic model endpoints. PostgreSQL
stores use `{"kind":"postgres","dsn_env":"LAB_MEMORY_RUNTIME_DSN"}`; optional
accounting uses `{"dsn_env":"LAB_MEMORY_RUNTIME_DSN"}`. Initialize schemas with
separate owner credentials; the runtime role must have only documented grants.

```sh
python -m lab_runner.memory_workflow start --config /private/host.json --request /private/request.json
python -m lab_runner.memory_workflow status --config /private/host.json --run-id RUN_UUID_HEX
python -m lab_runner.memory_workflow resume --config /private/host.json --run-id RUN_UUID_HEX --expected-revision REVISION --choice continue
```

Request JSON has only `task` and `query`. Save the returned run ID and revision.
`reject` completes the review without a model call. Never use a blind retry to
recover a model call or unknown usage outcome.

## Explicit qualification

The unchanged `dependencies/releases.json` remains the normal release lane.
`dependencies/memory-candidates.json` selects a separate exact-checksummed
candidate family, including the candidate Runtime error contract and adapter.
These candidates are not published releases. Obtain/build exactly the listed
wheel bytes; a rebuilt wheel with a different digest must not silently pass.

From this checkout or an extracted sdist, with its built Lab wheel installed
and all six host SDK wheels installed from the selected wheel directory:

```sh
python -m lab_runner.memory
python -m lab_runner.memory --enable --manifest dependencies/memory-candidates.json --artifacts /absolute/wheels --worker-python /absolute/worker-env/bin/python --postgres-version 16 --output /private/memory-pg16.json
python -m lab_runner.memory --enable --manifest dependencies/memory-candidates.json --artifacts /absolute/wheels --worker-python /absolute/worker-env/bin/python --postgres-version 18 --output /private/memory-pg18.json
```

The first command starts nothing. Explicit qualification verifies wheel hashes
and installed Python payloads before allocating an owned PostgreSQL container,
separate migration/runtime roles and loopback fixtures. It requires six actual
cases with zero skips and verified cleanup. It covers File/SQL stores, exact
Unicode/CRLF evidence, foreign/partial record exclusion, process restart after
source mutation and worker shutdown, owner denial, metering attribution,
no-repeat resume, disabled default and optional/required unavailability.
Receipts contain artifact hashes, resource identities and counts, without
DSNs, source text, private state or raw failure logs. Cached PostgreSQL 16/18
images and Docker are required; missing infrastructure fails this explicit lane.

Build the offline installed consumer overlay using an explicit cached base
image ID, the same wheel directory and the built Lab wheel:

```sh
python scripts/build_memory_consumer.py --base-image sha256:FULL_LOCAL_IMAGE_ID --manifest dependencies/memory-candidates.json --artifacts /absolute/wheels --lab-wheel dist/prosaic_integration_lab-0.5.0-py3-none-any.whl --output /private/memory-image.json
```

The overlay uses no index/network and runs the installed disabled smoke as a
non-root user with no network, a read-only root and dropped capabilities. Castle
and neural dependencies stay outside the consumer image. The selected cached
base provides third-party dependencies; this smoke is not a fresh dependency
resolution or a full Linux memory workflow qualification.
