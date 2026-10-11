# Conversation Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove that a consumer can build a bounded natural-language assistant using installed public Prosaic packages, including safe workflow replies and durable recovery.

**Architecture:** Extend the existing authenticated FastAPI host with an opt-in public Conversation adapter and an app-owned creation/quota registry. Existing owned model/PostgreSQL/worker fixtures demonstrate actual dispatch and effect behavior. Candidate/released consumer images and optional live conformance produce separately labelled evidence.

**Tech Stack:** Existing Python 3.12+, FastAPI/Uvicorn, HTTPX, pytest, owned Docker/Podman PostgreSQL 16/18, installed checksummed SDKs. No new production server dependency.

**Spec:** [Approved conversation design](../../../../prosaic-harness/docs/superpowers/specs/2026-10-11-conversation-design.md).

## Global Constraints

- Use installed public SDK APIs; no sibling editable sources, private imports, monkey-patched engines or copied orchestrators.
- Runtime owns model execution; Conversation owns session advancement; Harness owns workflow advancement; the Lab owns authentication, current authorization and retained-session quotas.
- Namespace, environment, application, tenant, actor and billing account come from trusted host context. Client/model identity, roles, tool grants and binding definitions are rejected.
- No new repository, distribution, graph language, Markdown kind, chat product CLI, automatic summarization or background scheduler.
- Preserve old routes, `lab_app` schema v3, original upgrade evidence, release manifests and the unrelated committed Stripe design.
- Explicit separate conversation readiness/initialization and runtime role; no automatic schema migration or memory fallback.
- Limits are sealed SDK limits: 64 turns, 4 MiB history, 8 MiB snapshot, 16 KiB user, 64 KiB final answer, 128 KiB turn, 192 KiB actual request, 3 attempts/turn, 128/session, 8 MiB receipt, 64 MiB cumulative receipts/reservations.
- Host defaults: 128 retained sessions/deployment, 16/owner, including reservations/completed/failed/unresolved rows. Existing finite read/write/tenant concurrency stays in force.
- Synthetic lanes are credential-free. Live local/hosted calls require explicit opt-in, private configuration and one shared bounded allowance.
- Required Linux AMD64/ARM64 × PostgreSQL 16/18 lanes fail missing infrastructure/skips, audit installed payload/provenance and verify exact-owned cleanup.
- Use apply_patch and watched failing tests. Never prune unrelated engine resources or upload private logs/DSNs/prompts/backups.

## Review Focus

- A creation acknowledgement lost after SDK commit must recover the same opaque ID without duplicating a quota reservation (Task 1).
- Existing 8 KiB HTTP envelopes must not accidentally reject valid 16 KiB Unicode messages, or broadly relax other endpoints (Tasks 1 and 4).
- A stale successful approval from another turn must not authorize the current interaction, even if the model repeats it (Tasks 2 and 4).
- Installed worker crash at post-resume/pre-session-save must expose uncertainty without a second effect (Task 3).
- Candidate artifacts cannot pass the ordinary public-index lane by substituting local wheels; live evidence cannot borrow synthetic model claims (Task 5).

## SDK dependencies and public host shape

Implement only after the reviewed [Runtime plan](../../../../prosaic-runtime/docs/superpowers/plans/2026-10-11-conversation-turns.md) and [Harness plan](../../../../prosaic-harness/docs/superpowers/plans/2026-10-11-conversation-implementation.md) provide their public interfaces.

`ConversationExecution(host)` uses those exact controller signatures and returns only `ConversationReply.document`, with an explicit bounded owner-filtered history view. Methods:

```python
class ConversationExecution:
    def __init__(self, host): ...
    def create_request(self, principal, key) -> dict: ...
    def status_request(self, principal, session_id) -> dict: ...
    def history_request(self, principal, session_id) -> dict: ...
    def usage_request(self, principal, session_id) -> dict: ...
    def send_request(self, principal, session_id, *, message_id, message, expected_revision,
                     interaction_ref=None, on_event=None) -> dict: ...
    def recover_request(self, principal, session_id) -> dict: ...
    def retry_request(self, principal, session_id, *, expected_revision, acknowledge_effect_risk) -> dict: ...
```

HTTP routes are POST `/conversations` with empty strict body and owner-scoped Idempotency-Key; GET `/conversations/{id}`, `/history` and `/usage`; POST `/conversations/{id}/messages`, `/recover`, and `/retry`. The messages body is a closed camelCase object with `messageId`, `message`, `expectedRevision` and optional `interactionRef`. Retry accepts current expectedRevision and literal human `acknowledgeEffectRisk=true`; neither model text nor interpretation can populate it. No general workflow attachment endpoint: the trusted host chooses approved registration and verifies actual run ownership before invoking attach_workflow().

Inject the existing host recorder with Conversation(..., context=frozen_context, accounting=host.recorder). Conversation accounting uses application_id `integration-lab-chat`, trusted tenant/actor/billing, and session-correlated request_id/run_id. Freeze this context before the first turn; child IDs distinguish ordinary/interpretation attempts. The usage route authenticates/owner-filters first, calls the public recorder report API with every frozen attribution filter plus session request_id/run_id, and returns only `public_usage(report)` under `conversation`. A separately labelled `workflow` report requires current owned-run authorization and retains that run's original app/attribution/ID filters. Do not add workflow calls to conversation totals or return raw call/receipt bodies.

Add opt-in `lab_chat` schema version 1 containing durable owner-scoped creation reservations, a preallocated UUID-hex sessionId, frozen binding/version/scope and retained quota rows. Persist the ID/reservation before public controller create(session_id=...). Reconcile authoritative state on unknown acknowledgements; exact replay uses the same ID, scope and binding. No auto expiry/deletion or quota release for completed/failed/unresolved sessions. Authentication/current authorization occurs before replay/status/history/recovery/retry. Registry references do not authorize inference retries.

Provision `conversation_runtime` separately with access only to `prosaic_harness_conversations` and its own bounded DSN. Old harness_runtime receives no new privileges. Public PostgresSessionStore.initialize() runs only in the explicit operator path; application workers call check_ready(). Keep app-owned lab_chat grants separate from SDK session grants and retain all original lab_app migrations/roles.

### Task 1: Installed capability admission and authenticated host

**Files:** Create `src/prosaic_integration_lab/conversation_execution.py`, `conversation_registry.py`, `conversation_schema.py`; tests `unit/test_conversation_registry.py`, `unit/test_conversation_views.py`, `functional/test_conversation_http.py`; fixture support `tests/support/conversation_http.py` and `tests/functional/conftest.py`. Modify existing app/config/execution/http_guard/views/capacity, `scripts/provision.py`, `dependencies/public-build-inputs.json`.

**Interfaces:** Produce the host methods/routes above, opt-in `conversation` configuration and SDK readiness. Fixture `chat_client` uses real FastAPI lifecycle and installed SDK wheels; test registry fixtures own disposable PostgreSQL or an explicit unit protocol double.

- [ ] Write RED closed-body/auth/create-replay/capability tests:

```python
def test_message_cannot_supply_identity(chat_client):
    session = chat_client.create(owner="alice", key="create-1")
    before = chat_client.provider_calls()
    response = chat_client.post_message(session, owner="alice", body={
        "messageId": "m1", "message": "hello", "expectedRevision": session["revision"],
        "actor": "bob"})
    assert response.status_code == 422
    assert chat_client.provider_calls() == before
```

The fixture surface is create(owner,key), post_message(session,owner,body), provider_calls(), get_history(session,owner), get_usage(session,owner), restart_worker(), and ready(); each helper uses actual public HTTP requests and bounded waits.
- [ ] Run `.venv/bin/python -m pytest -q tests/unit/test_conversation_registry.py tests/unit/test_conversation_views.py tests/functional/test_conversation_http.py`; observe missing routes/contracts.
- [ ] Implement ownership reservation before SDK creation, exact create replay/reconciliation, retained quota enforcement and current grant checks. Use existing Execution.admitted/inspected/read and immutable bundle patterns; no host-owned session reducer. Fail unsupported capability and missing retained binding/readiness before dispatch.

```python
reservation = registry.reserve_creation(principal, key, binding_identity)
snapshot = controller.create(session_id=reservation.session_id)
registry.adopt_creation(reservation, snapshot.session_id)
return controller.status(snapshot.session_id).document
```

`reserve_creation`/`adopt_creation` are bounded app-registry operations in conversation_registry.py; each releases its database connection before SDK calls. Unknown create acknowledgement reloads exact reserved identity rather than generating a new one.
- [ ] Add an exact messages-route 100 KiB envelope ceiling, then measure raw message UTF-8 through SDK 16 KiB admission. Reject duplicate JSON keys/unknown fields, malformed IDs and supplied roles/transcripts/config/tools. Keep all existing route ceilings. Transcript export is owner-filtered, at most the bounded 4 MiB history plus fixed envelope overhead.
- [ ] Test missing conversation grants/schema/capability, no fallback, current grant revocation before duplicate replay, repeated creation at capacity, host crash after SDK create, wrong-owner usage/export, frozen recorder attribution and unchanged old HTTP startup. Review and commit.

### Task 2: Multi-turn journey and exact workflow replies

**Files:** Create `src/prosaic_integration_lab/conversation_workflows.py`, `assets/conversation/agents/assistant.md`, `assets/conversation/agents/interpreter.md`, `assets/conversation/schemas/interpretation.json`, `lab_runner/conversation_scenarios.py`, `lab_runner/conversation_demo.py`, functional and acceptance `test_conversation_journey.py`. Modify `lab_runner/model.py`, host, stack/runner mode selection, test conftest fixtures and public inventory.

**Interfaces:** Produce `conversation_configuration(namespace)->dict`, `capture_conversation(config)->dict`; add Lab runner `demo --mode conversation` and `test --mode conversation`. These are existing Lab test/demo modes, not a new SDK chat CLI. All new neutral prose uses paired ALWAYS/NEVER rules, with model IDs/endpoints in host configuration.

- [ ] Write RED credential-free journey tests with a real synthetic provider, a pure approved lookup tool and an admitted owned workflow:

```python
def test_second_result_targets_displayed_order(chat_journey):
    displayed = chat_journey.search(["player-a", "player-b"])
    reply = chat_journey.send("the second result", interaction_ref=displayed["reference"])
    assert chat_journey.selected_entity() == "player-b"
    assert reply["pendingInteraction"] is not None
    assert chat_journey.effect_count() == 0
```

`chat_journey` wraps public HTTP only and returns curated projections; helpers assert exact current revisions and observe fixture counters, not private SDK fields.
- [ ] Observe RED in functional journey tests. Implement preference → correction → lookup → ordered offered selection → explicit confirmation → owned workflow completion. Host registration uses original approved workflow/bindings, versioned run authorizer and confirmation rule. Register a consequential ordinary-session tool to make interpreter denial measurable.
- [ ] Use a closed explicit confirmation fixture accepting only whole current source text `approve` or `yes, approve` against the exact current reference, after interpretation/schema/membership/current authorization. Quoted, multiline, historical, assistant/tool and model-generated approvals fail. The interpreter receives no tool definitions, initial tool, acquisition, workspace or journal.
- [ ] Add failed correction followed by successful query, ambiguous clarification, offered-order refresh/stale refs, fresh-process session restoration, duplicate follow-up and direct external Harness decisions making old refs stale. Preserve unsuccessful status as user data; exclude partial assistant/tool groups.
- [ ] Run functional tests and bounded synthetic demo. Export sanitized counts/status/source/package/model-fixture identity only. Review and commit.

### Task 3: Owned persistence and recovery qualification

**Files:** Create `lab_runner/conversation_faults.py`, `tests/acceptance/test_conversation_recovery.py`, `test_conversation_persistence.py`, unit fault tests. Modify existing owned stack/model/gates/provisioning/candidate mode handling.

**Interfaces:** Consume public SessionStore, Conversation events `receiptSaved`, `turnCommitted`, `workflowCommandPrepared`, `workflowCommandReturned` and existing exact-owned worker/SQL fault fixtures. Events carry only bounded opaque correlation/status. Add observable fixture barriers via host event callback and public store delegates, never engine patches.

- [ ] Add RED accepted-call/receipt/handoff crash tests, reconciling independent provider acceptance, tool-handler and domain/journal counts:

```python
def test_saved_receipt_is_adopted_on_new_worker(chat_recovery):
    sid = chat_recovery.kill_at("receiptSaved")
    before = chat_recovery.counters()
    chat_recovery.replace_worker()
    result = chat_recovery.recover(sid)
    assert result["status"] == "completed"
    assert chat_recovery.counters() == before
```

- [ ] Implement exact-owned barriers/proxy faults and bounded process replacement. Exercise two messages on one revision, identical ID replay at stale original revision, changed-text conflict, disconnect/reconnect, lease expiry/takeover/late-owner return and frozen scope/accounting.
- [ ] Cover undispatched pending recovery, lost marker acknowledgement, committed receipt before adoption, unknown receipt writes, absent receipt after accepted request, explicit retry consuming another attempt, known and uncertain effect evidence and repeated reservation replacement. No callback/connection spans inference.
- [ ] Independently kill around interpretation receipt and workflowCommand save/return. After uncertain post-resume handoff, inspect actual run and assert needsResolution, zero re-interpretation and zero second resume/effect; never infer command success from matching response text.
- [ ] Run conversation acceptance against owned PG16 and PG18, verify separate role/grant/schema readiness and old RunStore-only behavior, immutable receipts and all counters/cleanup. Repeat on Linux AMD64/ARM64 CI; source unit tests alone do not qualify this task. Review and commit.

### Task 4: Hostile input, streaming and every capacity boundary

**Files:** Create `tests/acceptance/test_conversation_security.py`, `test_conversation_limits.py`, `tests/functional/test_conversation_streaming.py`; modify host/views/scenarios/gate collection.

**Interfaces:** Produce safe HTTP mappings for SDK limit/conflict/busy/unresolved errors, bounded streaming projections and exact negative acceptance evidence. Map session/context limits to 422 with safe code/limit, revision/message conflicts to 409, non-owned references to 404 and unavailable store to 503.

- [ ] Write RED cases for cross-actor/cross-tenant read/history/send/recover/retry/attachment/usage; fabricated interpreter call with zero handler/authorizer/resolver/journal dispatch; revoked grant, changed namespace/journal/config/authorizer and missing retained binding.

```python
def test_quota_counts_completed_and_uncertain(chat_capacity):
    chat_capacity.seed(statuses=["completed", "failed", "needsResolution"])
    result = chat_capacity.create_another()
    assert result.status_code == 422
    assert result.json()["detail"]["code"] == "sessionLimit"
    assert chat_capacity.retained_rows() == 3
```

The capacity fixture sets a trusted maximum of three retained sessions; seed performs public admitted operations and controlled faults, not fabricated checkpoints.
- [ ] Observe RED. Add raw Unicode/JSON escaping/duplicate-key/unknown-field tests and preserve exact endpoint ceilings. Verify history, snapshot, user/final/turn bytes, actual request context, attempts, receipt and cumulative receipt/reservation, provider/tool/session allowance limits independently.
- [ ] Test capacity before admission has no message/POST; context/output growth after one completed tool retains its effect/usage and unsuccessful user status. Exhaustion preserves history/evidence, duplicate replay and saved receipt adoption. Workflow request usage remains separate from session allowances; host shared allowance includes both.
- [ ] Streaming remains optional host transport: if exposed, provisional deltas never advance committed history; emit committed status only after SDK durable adoption. A reconnect reads saved status, no inference and no promise of durable SSE delta replay.
- [ ] Run functional negative/streaming suites plus real conversation acceptance. Freeze explicit collected lane count contracts; no skips, missing counts or cleanup uncertainty. Review and commit.

### Task 5: Live conformance, installed adoption and release evidence

**Files:** Create `scripts/conversation_conformance.py`, `lab_runner/live_allowance.py`, `configs/conversation-conformance.example.json`, `tests/unit/test_conversation_conformance.py`, `tests/functional/test_conversation_conformance.py`, `tests/unit/test_conversation_distribution.py`, `scripts/conversation_distribution_smoke.py`, `docs/conversations.md`, `docs/verification/conversation-adoption-2026-10-11.md`. Modify `scripts/prepare_sdk_candidates.py`, `tests/unit/test_sdk_candidates.py`, `scripts/verify_public_adoption.py`, `dependencies/public-build-inputs.json`, `MANIFEST.in`, `scripts/required_acceptance.py`, `lab_runner/gates.py`, `tests/unit/test_release_gates.py`, `.github/workflows/required-acceptance.yml`, `pyproject.toml`, `README.md`, `CHANGELOG.md`, `configs/README.md`, `docs/release-gates.md`, `docs/handoff.md` and `docs/verification/progress.md`.

**Interfaces:** Conformance command accepts `--config PATH`, exactly one `--live-local`/`--live-hosted`, explicit `--max-calls N`, `--export PATH`. With no live flag it performs only synthetic/preflight validation and never contacts a model. Validate integer 1<=N<=12 and compute the complete schedule's worst-case 12 requests before any call; a smaller supplied allowance fails preflight with zero dispatch. Fixed balanced/strong sessions each make two ordinary turns under a sealed two-provider/one-tool cap (four turns × two = eight). Only the balanced session also exercises one selection interpretation (one request) and one confirmation interpretation plus a linked effect-agent turn (one + two = three). The linked workflow starts at a deterministic selection pause, selection advances to a confirmation pause without inference, and the effect agent has at most two provider requests/one tool. Total worst case is 8+1+3=12. Failed/unknown reservations are never automatically released or retried.

- [ ] Write RED no-opt-in/missing-config/allowance/concurrent-reservation/privacy tests:

```python
def test_unknown_attempt_keeps_shared_allowance(tmp_path):
    allowance = SharedLiveAllowance(tmp_path / "allowance.json", max_calls=2)
    token = allowance.reserve(maximum_requests=2)
    allowance.finish(token, actual_requests=None)
    with pytest.raises(AllowanceExhausted):
        allowance.reserve(maximum_requests=1)
```

`SharedLiveAllowance.reserve()` returns an opaque reservation token; `finish()` accepts trustworthy actual request counts or None, is idempotent and retains unknown maximums. Define both APIs and `AllowanceExhausted` in live_allowance.py; shared locks/atomic owned-file writes prevent concurrent overspend. Reserve the whole bounded public operation before calling it: ordinary send maximum two; selection send maximum one including its zero-model workflow advance; confirmation send maximum three including interpreter and effect-agent follow-up. No new SDK hook/private runtime wrapper is required. Settle only from adopted terminal status and matched frozen conversation/workflow recorder evidence; otherwise use None and stop. Release only unused trustworthy counts. Provider token caps remain retrospective, not a hard monetary guarantee.
- [ ] Implement local/hosted scripts using public installed APIs and existing local_routing_smoke preflight/proxy/secret/timeout patterns. Preflight actual configured Qwen and approved hosted profiles; bind agent/profile per session rather than switch a live session. Stop on first conformance failure or unknown completion. Do not use synthetic rates to claim real costs or reuse synthetic output as live evidence.
- [ ] Run synthetic functional tests on real wire formats and normal candidate installed SDKs. Only opted-in live execution may report actual provider/model/profile/history/tool behavior; report local Qwen and hosted tiers separately. Private endpoint/credential/body data remains outside exported summaries.
- [ ] Qualify candidate images with a separate complete checksummed five-package manifest, including unchanged Core original qualification. Runtime 0.9.0/recorder 0.3.0, Harness 0.8.0/store 0.3.0 and Core 0.4.1 are the planned train; Lab target is 0.5.0. Current released manifest stays at 0.4.1/0.8.1/0.2.1/0.7.1/0.2.1 until upstream publication.
- [ ] Update the curator's trusted exact-version contract and unit assertions for the new train; reject old/mixed/new-with-forged-lineage candidates. Preserve original historical manifests and require the same exact-source successful qualification receipts/embedded upstream bytes. Add the non-secret example config to MANIFEST.in's explicit config inventory.
- [ ] Run all existing eight required lanes plus conversation qualification on the four native architecture/database cells. Preserve existing historical 230-test-per-cell receipts and original image/source/artifact hashes. Record fresh exact collected counts and original immutable candidate lineage; missing infrastructure/cleanup cannot qualify a release.
- [ ] Publish upstream qualified versions in Runtime → Harness order through existing scoped publishers. Then update Lab's exact release manifest/checksums and qualify ordinary PyPI resolution with dependencies, installed payload audit, isolated imports, public construction, pip check and released-mode full matrix. Candidate wheels cannot stand in for public downloads.
- [ ] Build and qualify Lab wheel/sdist and 0.5.0 release, document install/upgrade/memory/durable/HTTP/workflow/limits/uncertainty/live invocation examples, update current handoff/progress only, independently review the complete adoption diff and save verified cleanup/evidence before merge/publish.
- [ ] `conversation_distribution_smoke.py` creates a neutral temporary venv, resolves the five exact manifest SDK wheels and Lab wheel with dependencies, runs pip check, isolated public imports/capability, `python -I -m prosaic_integration_lab --version`, and `python -I -m lab_runner --help`. Reject imports owned by sibling source roots. Extract the exact sdist into a separate owned directory, verify the new example/assets/docs are present, build its consumer and run the conversation demo/acceptance from that source distribution. Wheel modules do not contain the repository assets needed for stack commands; keep that existing limitation explicit. Unit tests cover the smoke's command/error/isolation contracts before an actual fresh consumer run.

## Verification commands and release handoff

Commands below use existing entrypoints; new conversation mode becomes available in Tasks 2–3:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m build
.venv/bin/python -m lab_runner demo --mode conversation --postgres-version 16
.venv/bin/python -m lab_runner test --mode conversation --postgres-version 16
.venv/bin/python -m lab_runner test --mode conversation --postgres-version 18
.venv/bin/python scripts/build_consumer.py --manifest dependencies/releases.json --dependency-mode released --tag prosaic-integration-lab:dev
.venv/bin/python scripts/verify_public_adoption.py --manifest dependencies/releases.json --export reports/conversation-public-adoption.json
.venv/bin/python scripts/required_acceptance.py --postgres-version 16 --export reports/conversation-required-pg16.json
.venv/bin/python scripts/required_acceptance.py --postgres-version 18 --export reports/conversation-required-pg18.json
```

During candidate development pass explicit --candidate/--candidate-manifest and complete qualified lineage to the existing candidate machinery; do not silently edit released pins or bypass dependency resolution. Actual live calls use the new conformance command with explicit opt-in and its bounded private configuration. Publish consumer-readiness claims only after new upstream bytes are public and all released consumer/platform gates pass. No tests or model calls have run during this planning stage.

Candidate preparation uses a private verified `core/runtime/harness` run/source profile, followed by the builder's distinct candidate flags:

```sh
.venv/bin/python scripts/prepare_sdk_candidates.py --profile .lab/conversation-sdk-profile.json --manifest .lab/conversation-candidates.json
.venv/bin/python scripts/install_dependencies.py --manifest .lab/conversation-candidates.json
.venv/bin/python scripts/audit_install.py --manifest .lab/conversation-candidates.json
.venv/bin/python -m pip check
conversation_image_id=$(.venv/bin/python scripts/build_consumer.py --manifest .lab/conversation-candidates.json --dependency-mode candidate --tag prosaic-integration-lab:conversation-candidate)
.venv/bin/python -m lab_runner test --mode conversation --candidate --candidate-manifest .lab/conversation-candidates.json --consumer-image "$conversation_image_id" --postgres-version 16
.venv/bin/python -m lab_runner test --mode conversation --candidate --candidate-manifest .lab/conversation-candidates.json --consumer-image "$conversation_image_id" --postgres-version 18
```

The private profile is written from actual successful exact-source qualification IDs at execution time; never invent IDs or replace source lineage with branch names. Install the locked third-party dependencies before the exact five candidate SDKs; pip check and payload audit must succeed before host tests. The captured builder output is an immutable sha256 image ID, verified again by every lane rather than selected by a mutable tag. Released/public-index commands use the published train and released manifest, not this candidate cache.
