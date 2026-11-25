# Production consumer requests — 2026-11

These requests come from a production consumer of the Prosaic family. It runs a
domain assistant: a host planner routes each user message to finite specialist
workflows that call host-owned, read-only search tools and return reviewed
navigation and filter actions. It currently runs Core 0.5.1.post1, Runtime
0.9.26, Harness 0.9.19, Runtime PostgreSQL 0.3.0 and Harness PostgreSQL 0.4.5.

The consumer is moving onto the supported path described by this Lab (public
installed APIs only, no private imports, no copied engines), so that SDK
upgrades stop breaking it. The audit found a few places where the supported
path does not yet cover a production need. They are listed below in priority
order, with the evidence we have and the shape of change we would find useful.
Each request is phrased so that it applies to every consumer. This file is meant
as a counterpart to the Cerebro request logs in prosaic-harness and
prosaic-runtime.

Application changes remain in the consuming service. None of these requests
asks Prosaic to adopt domain semantics.

## 1. Host-driven conversation sessions, and session retention and erasure (Harness, Harness PostgreSQL)

**Need.** Durable, ordered, owner-scoped conversation records for a product
whose per-message execution is already a host-admitted workflow.

**Current behaviour.** `Conversation.send()` always performs a model turn, and
`attach_workflow()` routes replies through an interpreter model
(`prosaic-harness/docs/conversations.md`). A host that already runs a finite
workflow per message would add one model request per turn, and change its
execution semantics, to use the session record. The consumer therefore keeps
its own conversation table beside its Harness run store.

The same docs state that there is no automatic TTL, deletion or eviction and
that the host owns retention. `PostgresSessionStore` and `SessionStore` expose
no delete, expiry or export operation, so a host can only enforce retention or
honour an erasure request with raw SQL against Prosaic tables, which is off the
supported path. That prevents a host with retention or erasure obligations from
keeping conversations in Prosaic storage.

**Requested.**

- A host-driven session mode: append a host-produced assistant turn (for
  example a completed workflow's admitted reply) and attach its run reference,
  with the same ordering, `message_id` idempotency, `expected_revision`,
  ownership scope and recovery guarantees, and no provider request.
- Store operations for retention: owner-scoped delete of a session and its
  receipts, an optional per-session expiry, and an enumeration of sessions by
  owner for export and erasure, all respecting leases and unresolved evidence.
- A Lab blueprint that runs a host workflow per message on top of such a
  session.

## 2. Prompt cancellation of an in-flight provider request (Runtime)

**Need.** A user presses Stop, or a request deadline passes, while the provider
connection is silent.

**Current behaviour.** Cancellation is cooperative and is observed between
socket reads (`prosaic_runtime/http_bounds.py`, `openai_compatible.py`). The
per-read socket timeout is the remaining deadline, so a silent connection holds
the turn until the whole deadline expires. The only host-side workaround is to
run each Runtime turn in an isolated process that the host can terminate. No Lab
blueprint covers process isolation, and terminating a process produces
unknown-effect outcomes that need reconciliation.

**Requested.** One of:

- bound each blocking read by a short poll interval so `cancelled` is observed
  promptly, or
- close the transport from another thread when the turn is cancelled, with the
  outcome recorded as cancelled rather than unknown;

plus a sentence in `execution-lifecycle.md` on the expected stop latency.

## 3. Written identity guarantee (Runtime, Harness) — supports Cerebro request 6

**Need.** Saved continuations and pending reviews that survive a routine SDK
upgrade when the workflow's semantic bindings did not change.

**Current behaviour.** The consumer fingerprints workflows with
`Workflow.current_fingerprint()` and, until recently, the internal
`prosaic_harness.workflow.runtime_identity`. New SDK configuration fields and
material can change the fingerprint, and saved continuations are then
rejected, so pending reviews have to be recreated after an SDK upgrade.
Cerebro's request 6 ("Written identity guarantee") is marked Deferred in
`prosaic-harness/docs/cerebro-requests.md`.

**Requested.** The same as Cerebro request 6: enumerate the identity fields,
default/absent omission, golden old/new fixtures, and an identity-impact line in
every release note. Additionally, a public way for a host to obtain the
configuration identity that a workflow seals, so hosts do not import
`runtime_identity`.

## 4. A written public-API boundary, and supported helpers for common needs (all packages)

**Need.** Consumers can tell which imports are supported before they depend on
them, instead of finding out when an upgrade removes a symbol.

**Current behaviour.** No repository states what is public. In practice it is
`__all__` in `prosaic_runtime` and `prosaic_harness`, plus a few submodule
imports that the docs happen to name (`prosaic_runtime.mcp`,
`prosaic_runtime_postgres.PostgresRecorder`). `prosaic` and
`prosaic_runtime_postgres` have no `__all__`. Only Core's changelog claims
SemVer. The consumer had about 20 imports from undeclared modules, and one past
Harness upgrade already removed a private helper it used.

To stay on the supported path, the consumer now keeps its own copies of three
small helpers it had imported from `prosaic_harness.workflow`, which declares no
public API:

- `digest` (SHA-256 of canonical JSON) — used to fingerprint product data such
  as plans, prompts and host contracts. Owning it means product fingerprints
  change only when the product decides, not when Harness changes its internal
  encoding.
- `UniqueLoader` (YAML `SafeLoader` that refuses duplicate keys) — used to read
  the product's own workflow file.
- `runtime_identity` (fingerprint projection of a `RuntimeConfig`) — copied
  only as a stopgap; see request 3. Unlike the other two it encodes SDK
  identity rules, so a copy can drift from the SDK and should not be permanent.

The copies were byte-identical to Harness 0.9.18 when made, so no sealed record
changed.

**Requested.**

- A short "public API and compatibility" section in each package README or
  `docs/releases.md`: which modules and names are supported, how deprecations
  are announced, and how long a deprecated name keeps working. An `__all__` in
  `prosaic` and `prosaic_runtime_postgres` would make this checkable.
- Either publish small supported helpers for the two common needs above (a
  canonical-JSON digest and a duplicate-key-refusing workflow YAML loader), or
  state in the Lab that consumers are expected to own such helpers. Both are
  fine for us; we would like to know which is intended.

## 5. Public, versioned workflow block reasons (Harness)

**Current behaviour.** Hosts map blocked or failed runs to user-facing
recovery by matching strings such as `attempt_limit`, `run_deadline`,
`token_limit` and `visit_limit`. The Lab keeps its own closed list in
`lab_runner/trajectory.py`, and observer v1 maps unknown reasons to `unknown`.

**Requested.** An exported, versioned enumeration (or typed outcome) of block
and failure reasons on run status, with a documented compatibility rule for
adding values.

## 6. Restricted-role privilege manifest (Harness PostgreSQL, Runtime PostgreSQL)

**Current behaviour.** Schema owners run `initialize()` and migrations; the
runtime role needs exact grants on `prosaic_harness.*`,
`prosaic_harness_conversations.*` and `prosaic_metering_*` objects. Consumers
hard-code those lists, and so does the Lab (`lab_runner/memory_fixture.py`).
Each storage marker migration can silently invalidate them.

**Requested.** A published, versioned privilege manifest per storage marker, or
a `grant --role <name>` / `doctor --role <name>` command in the PostgreSQL CLIs,
so consumers can grant and verify least privilege without naming internal
tables.

## 7. Guarded recovery with a custom `RuntimeAdapter` (Harness, Runtime)

**Need.** Use the supported per-step hook and guarded recovery together.

**Current behaviour.** `RuntimeAdapter` (`prosaic-runtime/docs/runtime-adapters.md`)
is the public boundary for host argument projection and output normalisation,
attached with `WorkflowBindings(runtime_adapter=...)`. Harness 0.9.19 notes that
custom adapters support only the default recovery policy, so a workflow that
needs an adapter cannot also bind `rule_retries` or
`correct_malformed_tool_calls`. The consumer is replacing a hand-written runtime
stand-in with the supported pieces: direct tool steps for deterministic host
contracts, explicit graph steps for stronger model tiers, and a
`RuntimeAdapter` for request projection and output normalisation. It then
loses guarded recovery on exactly the agent steps that need it.

**Requested.** Forward the declared recovery options through the adapter's
`execute(...)` (as fixed, identity-bound options the hook cannot change), or
document the supported way to combine host projection with guarded recovery.
This blocks the last step of the consumer's migration below.

## 7a. Document the preconditions for workflow rules (Harness, Lab)

Found while adopting guarded recovery on Runtime 0.9.25 / Harness 0.9.19. A
workflow step that binds a rule is admitted only if all of the following hold,
but neither `guarded-recovery.md` nor the blueprint README says so, and
admission reports only `invalid_definition at $`:

- the policy sets explicit `max_provider_requests_per_invocation` and
  `max_tool_calls_per_invocation`;
- the agent body and resources contain no `{{args}}` (guarded steps run as
  conversation turns, where task data is user-role input; Runtime refuses
  interpolation with `invalidArtifact`);
- the step has no terminal tool, acquisition or required reads.

Also, a run whose rule retries are exhausted blocks with reason
`rule_violation`, which no document lists (see request 5).

**Requested.** A "Preconditions" section in `guarded-recovery.md` and the
Harness workflow docs listing these, and an admission error code or location
that names the failed precondition. Please also state whether rules on steps
with terminal tools are intentionally unsupported or planned: the consumer has
a terminal-search mode whose agents share prose with guarded steps, and because
enforcement tags are per artifact rather than per step, the same prose cannot
serve both.

## 7b. Bug: bounded tool recovery blocks every guarded step (Runtime, Harness)

**Reproduction.** A native workflow step with `initial_tool`, policy
`bounded_tool_recovery=True`, and an agent that binds a `final`-stage guard.
The model calls the required tool once, it succeeds, the model returns valid
JSON and the guard accepts it. The run still blocks with
`tool_recovery_blocked`.

**Cause.** A guarded step runs as a conversation turn. On that path Runtime
emits `tool_started` with `provisional: true` and no `tool_version`;
`tool_completed` carries the version. Harness `_tool_recovery` requires
`tool_version` on both events and requires the start and completion identities
to match, so it rejects valid evidence.

**Requested.** Emit `tool_version` on conversation-turn `tool_started` events
(or have Harness accept provisional starts), plus a combined acceptance case
for guarded recovery with bounded tool recovery. Until then the consumer leaves
the one agent that needs `initial_tool` unguarded.

## 8. Lab coverage and documentation freshness (Lab)

- **Blueprints for terminal completion and direct tool steps.** Both are
  shipped (`TerminalCompletion`, `allowed_terminal_tools`; `kind: tool` with
  `WorkflowPolicy.allowed_direct_tools` since Harness 0.9.5) and the consumer
  relies on them, but no qualified Lab blueprint exercises them. A copyable
  host for a model-free, receipt-bearing deterministic step would also answer
  the open question in the candidate
  [host-composed read blueprint](host-composed-read-blueprint.md).
- **`bounded_tool_recovery`** appears only in candidate material.
- **Stale train references** that confused our audit: `conversations.md` and
  `native-workflows.md` (Harness 0.8.2), `consume-native-workflows.md`
  (Lab 0.6.2), `tool-evidence.md` (lists shipped features as follow-ups),
  `feature-blueprints.md` (sub-agents as "next"), `current-status.md` (no Lab
  0.9.18 entry), and `release-gates.md` (a paragraph citing Core 0.4.1 and
  Runtime 0.9.0 as active).

## 9. Housekeeping

`prosaic-runtime` issue #37 (forward `rule_retries` and
`correct_malformed_tool_calls` through Harness, carry outcomes into receipts)
appears to be delivered by Runtime 0.9.25, Harness 0.9.19 and Lab 0.9.18
(guarded recovery) but is still open.

## 10. A migration path from a host-driven structured loop to Runtime's tool loop (Runtime, Lab)

**Need.** Use Runtime's parallel read tools (0.9.21), safe tool events and
checked citations (0.9.20) and bounded sub-agents (0.9.23) from a host that
already drives tools itself.

**Current behaviour.** The consumer drives tools with `StructuredToolLoop`. Each
model step is a separate `runtime.run(...)` with `max_tool_rounds=1` and no
allowed tools, and the host executes the requested tool between calls with its
own admission: grants, scope checks, a read cache, required reads and a
completion contract (results, clarification or blocked). Because Runtime never
sees the tools, none of the features above can take effect, and every tool round
trip costs a full model request. On the consumer's slowest requests the tool
reads take about 0.1 s each, while single model steps take 30–40 s.

**Requested.** A documented path, and ideally a Lab blueprint, for moving such a
host onto Runtime's tool loop while keeping host-side admission: which hooks
replace per-call grant and scope checks, how a host read cache and required-read
rules map onto tool contracts and evidence, and how a host completion contract is
enforced. If keeping `StructuredToolLoop` is intended, please state which of the
features above it is expected to support.

## 11. Sub-agent scope and concurrency (Runtime)

**Current behaviour.** Bounded sub-agents (Runtime 0.9.23) provide one level of
serial delegation (`sub_agents.py`) with shared budgets for provider requests,
tool calls and tokens, and the README describes them as being "for role-aware API
turns".

**Requested.** Please document:

- whether sub-agents are supported from a host-driven structured loop and from
  native/CLI providers, or only from API turns;
- whether concurrent delegation (fan-out of independent read-only sub-tasks) is
  planned. Serial delegation helps context isolation for multi-part questions
  but adds model turns, so it does not help latency-bound requests.

## What the consumer is changing on its side

Each step has its own qualification.

Done:

1. Removed private SDK imports and passed cooperative `cancelled=` through.
2. Moved to the guarded-recovery train (now Runtime 0.9.26, Harness 0.9.19) and
   replaced product repair code with `Guard`, `rule_retries` and
   `correct_malformed_tool_calls`.

In progress:

3. Replace a hand-written runtime stand-in with direct tool steps and
   `WorkflowFactory` admission, and stop editing inspected prose after
   inspection (step `model_tier` and versioned host validators instead).
4. Resume reviews through `Harness.interaction()` / `resume()` and read
   evidence through `recovery_evidence()` instead of raw run state.
5. Time each model call, then pilot Runtime's tool loop for the slowest
   workflow (request 10).

The conversation table (request 1) and the process isolation (request 2)
remain as documented deviations until the corresponding capability exists.

## Acceptance when revisiting

Exercise both supported synthetic provider wires where applicable, source and
installed-wheel consumers, persisted resume and identity across an upgrade,
erasure with leases and unresolved evidence, and stop latency against a silent
provider fixture. No live inference without explicit authorisation.
