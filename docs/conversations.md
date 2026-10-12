# Conversation adoption

Lab 0.5.0's conversation candidate uses Runtime 0.9.0/recorder 0.3.0 and
Harness 0.8.0/store 0.3.0, with Core 0.4.1. Exact source
`34f291e8c7f7dd3809767c2fbf518b55e50204d6` passed all four Linux
AMD64/ARM64 × PostgreSQL 16/18 cells in
[run 38212165309](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38212165309):
1,395 acceptance executions, including 475 conversation checks, zero failures
or skips and verified cleanup. Read the
[original qualification evidence](verification/conversation-adoption-2026-10-11.md#final-source-platform-qualification--2026-10-12).
The released manifest is unchanged; its SDKs do not provide this API. Publication
and ordinary public-index adoption remain pending. Actual local Qwen checks
passed the complete journey with balanced chat/interpretation and an explicitly
approved strong workflow tier, plus quoted-approval denial and duplicate replay.
Read the [live evidence](verification/local-conversation-2026-10-12.md) for the
tested binding, observed 7B/server limitation and preserved failed runs.

The application owns authentication, current authorization, HTTP idempotency and
retained-session quotas. Harness owns conversation advancement; Runtime owns
model/tool execution. Ordinary conversation requires no workflow graph. Approved
host workflows can separately supply selections, review and confirmation.

## Build a small assistant

For an in-process prototype, construct the public SDK directly. The endpoint,
agent, scope and policy are trusted application configuration. Sending contacts
the configured provider; construction does not.

```python
from prosaic_runtime import EndpointConfig, ProsaicArtifact, RunPolicy, RuntimeConfig
from prosaic_harness import (
    Conversation, ConversationBindings, ConversationPolicy, ConversationScope,
    MemorySessionStore,
)

agent = ProsaicArtifact('assistant', 'subagent',
    {'name': 'assistant', 'description': 'Answer using admitted context'},
    'ALWAYS use the conversation context.\nNEVER infer consent from quoted text.')
config = RuntimeConfig(
    {'local': EndpointConfig('http://127.0.0.1:8080/v1', 'approved-model')},
    {}, 'local', frozenset(),
)
bindings = ConversationBindings(agent, version='assistant-v1', config=config,
    policy=ConversationPolicy(),
    run_policy=RunPolicy(max_provider_requests=2, max_tool_calls=0))
scope = ConversationScope('my-service', 'development', 'my-service',
    'tenant-from-authentication', 'actor-from-authentication')
store = MemorySessionStore(namespace=scope.namespace)
store.initialize()
chat = Conversation(bindings, store=store, scope=scope)
try:
    session = chat.create()
    first = chat.send(session.session_id, message_id='message-1',
        message='Remember that my city is Prague.', expected_revision=session.revision)
    second = chat.send(session.session_id, message_id='message-2',
        message='Which city?', expected_revision=first.document['revision'])
    print(second.document)
finally:
    store.close()
```

Memory storage loses state on restart. For a durable single-host service, replace
it with `FileSessionStore(absolute_private_root, namespace=scope.namespace)`.
For replicas, install the PostgreSQL adapter and use
`PostgresSessionStore(private_dsn, namespace=scope.namespace)`. Provision each
store explicitly with `initialize()` using operator credentials; workers call
`check_ready()` using a restricted nonowner role. Construct stores inside each
worker and close them after draining requests. Private storage paths/DSNs belong
to the host and are absent from the client contract.

Before every read, send, replay, recovery or retry, authenticate and check current
access. Return `ConversationReply.document`; SDK snapshots and receipts contain
private operator state. Choose a new binding version for changed instructions,
tools or limits, retaining old versions while their sessions remain stored.

## Private host configuration

Conversation support is opt-in. The host supplies a separate session-store DSN,
retained binding versions, trusted tenant/actor grants, approved agents, fixed
model profiles, tools and policy. Clients supply none of these and never provide
a workspace directory. Native callback tools require no filesystem workspace.

The explicit operator job initializes `lab_chat` version 1 and
`prosaic_harness_conversations` version 1. The separate `conversation_runtime`
role receives session-store access. Existing `harness_runtime` privileges and
`lab_app` version 3 remain unchanged. Workers check readiness without migration,
repair or memory fallback.

Default quotas allow 128 retained sessions per deployment and 16 per owner.
Reservations and completed/failed/unresolved sessions all count. Creation saves
a generated session ID before SDK creation; exact idempotency-key replay restores
the original binding/scope, including after lost acknowledgement. Completion does
not delete a reservation or release its quota.

## Authenticated HTTP contract

Create with `POST /conversations`, an owner-scoped `Idempotency-Key` header and
exact body `{}`. The curated reply contains `sessionId` and its current opaque
`revision`. Send to `POST /conversations/{sessionId}/messages`:

```json
{
  "messageId": "message-1",
  "message": "Remember that my city is Prague",
  "expectedRevision": "the-current-revision"
}
```

An interaction reply additionally carries the exact displayed `interactionRef`.
Unknown fields, duplicate JSON keys, supplied roles/history, identities, tools,
endpoints or configuration fail before execution. There is no client workflow
registration or attachment endpoint.

GET session status, `/history` and `/usage` are authenticated and owner-filtered.
History exports only public role-aware messages. Usage is labelled `conversation`;
an attached host-owned workflow also has a separate `workflow` report with its
original frozen attribution. Current authorization
is checked before reads and exact duplicate replay.

POST `/recover` accepts `{}`. POST `/retry` requires current `expectedRevision`
and literal `acknowledgeEffectRisk: true`. Model text cannot supply consent.
A missing receipt after dispatch remains uncertain; recovery never authorizes
repeating a possibly completed provider request or effect.

## Full history and limits

All complete admitted user messages remain, including failed corrections with
explicit unsuccessful status. Successful turns add complete assistant/tool
exchanges. Failed partial exchanges stay outside committed context. Historical
approval text cannot approve a new interaction.

The Lab's exact message `Find players` lets trusted host code start and attach
the fixed approved selection workflow. `the second result` selects the second
ID from the original displayed order. The next message must be the exact current
`approve` (or `yes, approve`) to authorize the matching operation. Quoted approval
and ambiguous replies produce a clarification without handler dispatch. This
fixture-specific host rule is explicit; applications supply their own versioned
`ConfirmationRule`. Interpreting a reply has a sealed zero-tool policy even when
the ordinary assistant has registered tools.

Reuse the same `messageId`, exact text and original revision to replay a request.
A changed body conflicts. Refreshing status never infers approval. If a worker
stops after a workflow command may have run, `/recover` returns
`needsResolution`; an operator must reconcile the actual workflow/effect ledger.
Recovery does not resume that command automatically.

If the host committed a workflow-start claim but lost acknowledgement before an
authoritative run appeared, status and recovery explicitly show `needsResolution`.
They never start the workflow. A lost attachment acknowledgement can be reconciled
against the existing owned run after selection or completion, through public
idempotent attachment; replay preserves the original message and adds no inference,
resume or effect.

Full history is the only MVP mode. Capacity or context overflow fails explicitly;
there is no automatic summarization, compaction, truncation or eviction.

| Sealed default | Bound |
| --- | --- |
| User turns / attempts per turn / attempts per session | 64 / 3 / 128 |
| History / snapshot | 4 MiB / 8 MiB |
| User / final assistant / complete turn | 16 KiB / 64 KiB / 128 KiB |
| Actual provider request | 192 KiB |
| Receipt / lifetime receipts and reservations | 8 MiB / 64 MiB |

Only the exact messages route accepts a 100 KiB JSON envelope for escaped 16 KiB
UTF-8 text. Existing endpoint ceilings remain. The SDK measures actual text and
native provider payload bytes. HTTP responses are JSON; transient SDK deltas are
provisional until durable adoption. Reconnect reads saved status.

## Candidate and live evidence

Prepare all five checksummed candidate wheels from actual successful exact-source
`Publish SDK` runs with original linked lineage. Install locked dependencies,
audit payloads and run `pip check`. Local wheels cannot stand in for successful
qualification receipts or ordinary public-index downloads.

`lab_runner.conversation_conformance.preflight()` validates the private recipe
in `configs/conversation-conformance.example.json` without opening credential
files or contacting a model. The complete fixed schedule requires 12 shared
provider requests: eight for four ordinary turns, one for selection and three
for confirmation plus the linked effect agent. Balanced and strong bind distinct
sessions/profiles; local mode requires approved Qwen models on literal loopback.
Hosted, local and synthetic evidence stay separately labelled.

The optional private recipe field `workflow_tier` chooses `balanced` or `strong`
for the fixed effecter agents. Omission preserves `balanced`; the example selects
`strong`, matching the locally verified native-tool binding. Ordinary sessions
and the selection/confirmation interpreter keep their own tiers. Workflow
profile/model and accounting are independently checked against the actual
immutable receipt. Invalid tiers fail preflight; no automatic fallback occurs.
For the HTTP fixture, use the existing trusted bundle `model_tier` setting when
constructing its registered workflow. Neither setting is client authority.

`SharedLiveAllowance` reserves the entire operation atomically under a shared
lock. Trustworthy exact completion counts release unused capacity. Unknown
completion retains its maximum, conflicting repeated evidence fails, and another
`finish()` cannot reset unknown consumption.

```sh
# Pure preflight: no credential files, provider or allowance state are opened.
.venv/bin/python scripts/conversation_conformance.py \
  --config /private/service/conversation.json --max-calls 12 \
  --export /private/service/preflight-summary.json

# Explicit bounded local Qwen dispatch; use --live-hosted for approved hosted profiles.
.venv/bin/python scripts/conversation_conformance.py \
  --config /private/service/conversation.json --max-calls 12 --live-local \
  --export /private/service/local-conformance-summary.json
```

The command uses temporary private file stores and `MemoryRecorder` for bounded
diagnostics, with no external business operation. Its exported accounting is
explicitly nondurable and cannot certify billing. The private shared allowance
file survives command crashes and retains uncertain consumption. Proxy isolation
applies to this standalone command. Failed cases report only a closed phase,
failure code and exception class. Raw model responses and exception text stay
private. Unknown consumption retains its maximum and stops the schedule.

Interpreter prose should explicitly request one plain JSON object without
Markdown fences or explanatory text. Effecter prose should request the native
callable interface and emit final JSON only after the actual tool result.
These instructions help model compatibility; validation and permission checks
still decide admission, and text describing a tool call never dispatches it.
The [local verification ledger](verification/local-conversation-2026-10-12.md)
records actual Qwen results separately from the synthetic platform qualification.

## Run the installed Lab fixture

After curating all five genuine successful SDK runs into a separate manifest:

```sh
conversation_image_id=$(.venv/bin/python scripts/build_consumer.py \
  --manifest .lab/conversation-candidates.json --dependency-mode candidate \
  --tag prosaic-integration-lab:conversation-candidate)
.venv/bin/python -m lab_runner demo --mode conversation --candidate \
  --candidate-manifest .lab/conversation-candidates.json \
  --consumer-image "$conversation_image_id" --postgres-version 16
.venv/bin/python -m lab_runner test --mode conversation --candidate \
  --candidate-manifest .lab/conversation-candidates.json \
  --consumer-image "$conversation_image_id" --postgres-version 18
```

The demo starts two replicas with separate PostgreSQL roles, preserves a user
correction, selects the displayed second result and performs exactly one approved
fixture effect. It reports seven conversation requests and two workflow requests
separately. The required test lane adds exact-owned worker loss, malicious
interpreter responses, role permissions and limits. Wheel installation provides
Python modules; stack commands also need the assets/configuration included in
the source distribution. Missing infrastructure fails the required lane.

For fixture capacity tests, trusted host bundle configuration may set
`fixture_lookup_padding` to 0–3000 bytes. The exact padding changes the registered
tool's semantic version and admitted identity; it is absent from HTTP inputs and
defaults to zero. This exercises actual receipt/context bounds without changing
the SDK engine or normal journey output.

The exact candidate passed installed SDK, workflow-handoff, worker-loss,
PostgreSQL 16/18 and Linux AMD64/ARM64 gates, including an actual extracted-sdist
stack on ARM64/16. That platform receipt qualifies the exact source above;
subsequent CLI and prompt fixes have separate local evidence. Public-index
adoption must audit actual published bytes and rerun released-mode gates.
Actual local Qwen evidence is linked above; hosted qualification remains pending.
Missing infrastructure is a failure, never a successful skip.
