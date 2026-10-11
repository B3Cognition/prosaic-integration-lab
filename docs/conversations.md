# Conversation adoption preview

This branch targets Runtime 0.9.0/recorder 0.3.0 and Harness 0.8.0/store 0.3.0,
with unchanged Core 0.4.1. These are development candidates. The existing released
manifest stays unchanged and its SDKs do not provide this API. Installed SDK and
owned PostgreSQL qualification must pass before consumers can adopt this preview.

The application owns authentication, current authorization, HTTP idempotency and
retained-session quotas. Harness owns conversation advancement; Runtime owns
model/tool execution. Ordinary conversation requires no workflow graph. Approved
host workflows can separately supply selections, review and confirmation.

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
History exports only public role-aware messages. Usage is labelled `conversation`
and does not mix workflow accounting into session totals. Current authorization
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

`SharedLiveAllowance` reserves the entire operation atomically under a shared
lock. Trustworthy exact completion counts release unused capacity. Unknown
completion retains its maximum, conflicting repeated evidence fails, and another
`finish()` cannot reset unknown consumption. No live dispatch command has been
qualified yet.

Required installed SDK, workflow-handoff, worker-loss, PostgreSQL 16/18 and Linux
AMD64/ARM64 lanes remain release gates. Unit checks are development evidence;
missing infrastructure is a failure, never a successful skip.
