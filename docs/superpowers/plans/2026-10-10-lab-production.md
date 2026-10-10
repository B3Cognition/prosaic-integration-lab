# Integration Lab Production Milestones Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Qualify the renamed, installed Prosaic SDKs through an owner-authorized generated-workflow service and bounded operational exercises, preserving existing YAML clients and historical recovery evidence.

**Architecture:** The application owns authentication, current tenant entitlements, HTTP idempotency, retained host bundles and the demonstrator business-operation journal. Harness owns admission, orchestration and human decisions; Runtime owns inference, tool execution and usage evidence. Dependency preparation and operational qualification can proceed independently; native routes wait for the public SDK contracts and installed candidate wheels.

**Tech Stack:** Python 3.12 application/runner, FastAPI, Pydantic, httpx, psycopg 3, PostgreSQL 16 and 18, installed Python SDK wheels, Docker/Podman owned fixtures, native Linux AMD64/ARM64 CI.

**Spec:** [Approved ecosystem production design](../../../../prosaic/docs/superpowers/specs/2026-10-10-ecosystem-production-design.md). Also read AGENTS.md, docs/handoff.md, docs/superpowers/specs/2026-10-09-prosaic-integration-lab-design.md, docs/tracking-issue.md, docs/verification/progress.md and docs/verification/release-train-2026-10-09.md. Their earlier incomplete-stage statements are historical; the released Lab 0.2.0 manifest and receipts are the upgrade baseline.

## Global Constraints

- Python imports, CLI commands, repository names, canonical serialized camelCase contracts, and existing manifest/checkpoint/receipt formats remain compatible.
- Harness checkpoint v2 and Runtime receipt v1 remain unchanged; application schema advances explicitly from v2 to v3.
- Core 0.4.0 is b3-prosaic; Runtime 0.8.0 is b3-prosaic-runtime; recorder 0.2.0 is b3-prosaic-runtime-postgres; Harness 0.7.0 is b3-prosaic-harness; store 0.2.0 is b3-prosaic-harness-postgres; lab application target is 0.3.0.
- The application remains responsible for authentication, tenant entitlements, business authorization, HTTP idempotency, deployment configuration, and operator decisions.
- Use public installed APIs only. No sibling editable checkouts, private SDK imports, monkey-patching installed SDKs, callback hydration from proposals, or copied graph/schema engines.
- Candidate wheels require an explicit, checksummed candidate manifest and clean environment. Released qualification requires exact downloaded published bytes. Old and renamed distributions must never coexist in one environment/image.
- Existing 8 KiB run request limits remain. Only the proposal route accepts 64 KiB bodies; authentication precedes body receipt. Catalogue/interaction views use the SDK's 262144-byte cap and fail on oversize rather than truncate.
- Canonical proposal text uses json-sort-keys-utf8-v1: compact UTF-8 JSON, ensure_ascii=False, recursively sorted keys, no inserted graph defaults or host catalogue content.
- Inline instructions default to denied and are independent of composition grants. Omitted model_tier authorizes the host default regardless of the explicit tier allowlist; explicit tiers must be configured and allowed.
- Trusted host code chooses directories, endpoints, credentials, policy, bundle registrations, operation namespace and journal identity. Client/model identities and fingerprints grant no authority.
- Preserve frozen run owner, billing account, namespace and environment across resumes; usage is evidence, not consent, an invoice or authority to retry.
- An uncertain starting record never automatically redispatches. Journal uncertainty never expires or reclaims on timeout. Journal commit is fenced compare-and-set.
- Migration and runtime roles are separate. Runtime replicas never migrate, restore, receive owner credentials, or reconcile uncertain business effects automatically.
- Required acceptance fails on absent infrastructure, unexpected skips, timeout, missing/incomplete receipts, provenance mismatch or failed cleanup. Required native cells are AMD64/ARM64 × PostgreSQL 16/18.
- Fixtures use generated credentials, loopback published ports and exact ownership IDs. Never prune global resources or touch an existing shared database, issuer, gateway or paid provider by default.
- Missing staging/provider/deployment inputs produce not_qualified evidence. Synthetic correctness, overload or logical restore must never become live-provider, sustainable-capacity or HA/PITR certification.
- Retention copies are not consistent backups. No automatic deletion, idempotency expiry or uncertain-operation retirement is introduced.
- Preserve unrelated user changes and all historical failures/receipts. Root owns publication, version/channel promotion, external configuration and final release manifests; these task commits do not push or publish.

## Review Focus

1. Historical wheels left beside active renamed wheels: install only manifest-listed verified paths and reject conflicting installed distributions (L1).
2. High aggregate throughput with one tenant making no progress: fairness/starvation must fail independently; missing staging configuration must perform zero network requests (L2).
3. Same owner/key replay after a host-policy upgrade or JSONB key reordering: return the original proposal/reference, never rebind it to the new bundle (L3/L4).
4. Missing/altered historical bundle or stale/invalid human response: preserve state, revision, frozen attribution and zero extra dispatches (L4/L5).
5. Worker death after a synthetic effect or lost outcome-commit acknowledgement: preserve uncertainty or replay the committed outcome, never infer safe redispatch from lease expiry (L3/L5).

## File map and ownership

| Unit | Files | Responsibility |
| --- | --- | --- |
| Active dependencies | src/prosaic_integration_lab/dependencies.py; scripts/prepare_dependencies.py, install_dependencies.py, build_consumer.py, audit_install.py; containers/Dockerfile, Candidate.Dockerfile | Manifest validation, digest-addressed caches, exact installation, clean images and payload audits. |
| Qualification | lab_runner/qualification.py, recovery_qualification.py, staging_qualification.py; load_profile.py, model.py, __main__.py | Bounded profiles/evaluation, owned consistent restore, explicit staging opt-in and synthetic latency controls. |
| Application persistence | app_schema.py, migrations.py, metadata.py; proposals.py, bundles.py, tool_journal.py | Exact schema v3, owner-scoped immutable proposals/native reservations, retained host bindings and durable business journal. |
| Service integration | config.py, execution.py, app.py, http_guard.py, views.py, observability.py; native_execution.py | Trusted construction, route-specific bounds, pure proposal/input admission, filtered native views and execution. |
| Required acceptance | lab_runner/native_scenarios.py, legacy_upgrade.py; stack.py, gates.py, __main__.py; scripts/required_acceptance.py; .github/workflows/required-acceptance.yml | Synthetic native scenarios, actual historical release upgrade, required four-cell provenance and cleanup. |
| Delivery evidence | dependencies/releases-lab-0.2.0.json, releases.json; pyproject.toml, MANIFEST.in; README.md; docs/current-status.md, native-workflows.md, qualification.md; existing operator docs | Immutable baseline, deliberate release adoption, current entry point and factual qualification limits. |

L1 and L2 can execute independently. L3 waits for installed public WorkflowBundle/WorkflowReference and ToolClaim contracts; L4 waits for L3 plus Harness H2–H5 and Runtime invocation budgets/context. L5 consumes L1–L4. L6 is last and waits for root-confirmed published artifacts and required native evidence. Shared files, particularly runner CLI/stack, execution and CI, have one active editor at a time.

### Task 1: L1 — Manifest-driven installation and cache-isolated payload audit

**Files:** Modify src/prosaic_integration_lab/dependencies.py, scripts/prepare_dependencies.py, scripts/audit_install.py, containers/Dockerfile, containers/Candidate.Dockerfile, lab_runner/stack.py, lab_runner/verify_candidate.py, .github/workflows/required-acceptance.yml and README.md. Create scripts/install_dependencies.py, scripts/build_consumer.py and dependencies/releases-lab-0.2.0.json. Test tests/unit/test_dependencies.py, test_payload_audit.py, test_released_provenance.py and tests/functional/test_dependency_install.py.

**Interfaces:** Preserve verify_dependencies(manifest_path, artifact_dir). Add manifest_digest(manifest_path: Path) -> str, cache_directory(manifest_path: Path, cache_root: Path) -> Path, verified_wheel_paths(manifest_path: Path, artifact_dir: Path) -> tuple[Path, ...]. The installer consumes one manifest and its resolved artifact directory, never directory globs. scripts/build_consumer.py consumes --manifest, --tag and --dependency-mode released|candidate, validates exact artifacts and emits the immutable built image ID.

- [ ] L1.1 Preserve the current manifest as dependencies/releases-lab-0.2.0.json byte-for-byte before changing any active pins. Add the watched cache-selection regression:

~~~python
import hashlib
import json
from prosaic_integration_lab.dependencies import cache_directory, verified_wheel_paths

def test_historical_neighbor_is_not_an_install_input(tmp_path):
    root = tmp_path / "wheels"
    manifest = tmp_path / "releases.json"
    payload = b"active verified bytes"
    manifest.write_text(json.dumps({"artifacts": [{
        "distribution": "b3-prosaic", "version": "0.4.0",
        "filename": "b3_prosaic-0.4.0-py3-none-any.whl",
        "sha256": hashlib.sha256(payload).hexdigest()}]}))
    cache = cache_directory(manifest, root)
    cache.mkdir(parents=True)
    active = cache / "b3_prosaic-0.4.0-py3-none-any.whl"
    active.write_bytes(payload)
    (root / "prosaic-0.3.1-py3-none-any.whl").write_bytes(b"historical")
    assert verified_wheel_paths(manifest, cache) == (active,)
    assert cache.name == hashlib.sha256(manifest.read_bytes()).hexdigest()
~~~

- [ ] L1.2 Run .venv/bin/python -m pytest tests/unit/test_dependencies.py::test_historical_neighbor_is_not_an_install_input -q. Record the expected missing-symbol failure. Add duplicate filename/distribution, traversal/backslash, wrong hash, missing file and same-version conflicting payload cases before implementation.
- [ ] L1.3 Implement immutable manifest selection and pre-install verification:

~~~python
def manifest_digest(manifest_path):
    return hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()

def cache_directory(manifest_path, cache_root):
    return Path(cache_root) / manifest_digest(manifest_path)

def verified_wheel_paths(manifest_path, artifact_dir):
    verify_dependencies(manifest_path, artifact_dir)
    data = json.loads(Path(manifest_path).read_text())
    return tuple(Path(artifact_dir) / item["filename"] for item in data["artifacts"])
~~~

Validate manifest byte/cardinality/filename/hash limits before reading payloads; stream hash downloads/files and retain bounded download time/size. Strict active SDK manifests have five unique distribution names and valid wheel identities/versions; keep the existing generic verifier usable by its small fixtures. Add the strict SDK validation at install/build/audit entry points, not by weakening old checksum tests. Write new downloads through a temporary file in the digest cache and atomically rename after checksum validation.
- [ ] L1.4 Implement the installer with subprocess arguments, no shell:

~~~python
paths = verified_wheel_paths(manifest, artifact_dir)
subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps",
                *(str(path) for path in paths)], check=True)
~~~

Before installation reject old/renamed same-module distribution mixtures, including unrelated prosaic in a renamed environment. Audit installed distribution name/version, wheel METADATA and each actual installed payload; fail on unexpected active SDK distributions and conflicting shared import files. Derive the expected family from the selected manifest, so a clean historical fixture environment remains auditable.
- [ ] L1.5 Give the image build one validated digest-addressed wheel directory. Build_consumer passes the validated digest as a Docker build argument and snapshots exact manifest bytes into the build context; a concurrent manifest change aborts rather than relabels another payload. Replace broad COPY/install globs with this structure:

~~~dockerfile
ARG SDK_MANIFEST_SHA256
COPY .cache/wheels/$SDK_MANIFEST_SHA256/ /srv/wheels/
RUN python scripts/install_dependencies.py --manifest dependencies/releases.json --wheel-dir /srv/wheels
RUN python scripts/audit_install.py --manifest dependencies/releases.json --wheel-dir /srv/wheels
~~~

The build helper selects the exact manifest copied to dependencies/releases.json in its isolated public build context; its digest must match SDK_MANIFEST_SHA256. Keep immutable image/manifest labels. Candidate builds install a complete candidate family into a fresh base image, not renamed SDKs over the legacy SDK image. Update host CI installation and payload-audit arguments to use the selected digest cache. Preserve the old audit positional CLI and add --manifest/--wheel-dir, resolving the digest cache automatically when --wheel-dir is absent.
- [ ] L1.6 Add a subprocess regression that intercepts pip invocation, proving the historical neighbor is absent from argv and a checksum failure launches no pip process. Add an installed-payload regression for correct version but modified code bytes. Run:

~~~sh
.venv/bin/python -m pytest tests/unit/test_dependencies.py tests/unit/test_payload_audit.py tests/unit/test_released_provenance.py tests/functional/test_dependency_install.py -q
.venv/bin/python -m pytest -q
.venv/bin/python scripts/prepare_dependencies.py --manifest dependencies/releases.json
.venv/bin/python scripts/install_dependencies.py --manifest dependencies/releases.json
.venv/bin/python scripts/build_consumer.py --manifest dependencies/releases.json --dependency-mode released --tag prosaic-integration-lab:dev
~~~

The prepare/install defaults remain the active releases.json manifest and digest-addressed cache. Preparing a candidate requires an explicit candidate manifest; no fallback to editable sources.
- [ ] L1.7 Review diff/provenance, record commands and commit only L1 files with message "fix: isolate installed SDK wheels by manifest identity". No pin promotion or external publication occurs here.

### Task 2: L2 — Bounded fairness, soak, restore and staging qualification

**Files:** Create lab_runner/qualification.py, recovery_qualification.py, staging_qualification.py, configs/qualification.synthetic.json and docs/qualification.md. Modify lab_runner/load_profile.py, model.py, __main__.py, stack.py, docs/capacity-retention.md, persistence.md, identity.md and ingress.md. Test tests/unit/test_qualification.py, test_recovery_qualification.py, test_staging_qualification.py; tests/functional/test_qualification_cli.py; tests/acceptance/test_operational_qualification.py.

**Interfaces:** qualification.validate_profile(data: dict) -> dict; qualification.evaluate(profile: dict, observations: dict) -> dict; qualification.run(config, profile, events) -> dict. recovery_qualification.run(stack, profile) -> dict accepts only a verified OwnedStack. staging_qualification.run(config: dict | None, *, enabled=False) -> dict does no network work unless enabled and complete private configuration passes validation. CLI: lab_runner qualify --profile FILE --postgres-version 16|18; lab_runner qualify-recovery --profile FILE --postgres-version 16|18; lab_runner qualify-staging --config PRIVATE_FILE --staging-opt-in. These independent tools use the existing released SDK baseline until L1 deliberately selects candidates.

- [ ] L2.1 Add version-1 profile validation and a counterexample where aggregate completion hides starvation:

~~~python
from lab_runner.qualification import evaluate

def test_aggregate_success_does_not_hide_tenant_starvation():
    profile = {"version": 1, "suite": "synthetic-capacity-v1",
               "minimum_tenant_completion_ratio": .8, "p95_target_s": 2,
               "maximum_rejection_ratio": .05}
    observations = {"offered": 22, "completed": 20, "errors": 0,
        "rejected": 0, "approval_deferred": 2, "client_shed": 0,
        "latencies_s": [.1] * 20, "accounting_reconciled": True,
        "tenant_counts": {"a": {"offered": 20, "completed": 20},
                          "b": {"offered": 2, "completed": 0}},
        "starved_windows": 1, "read_failures": 0}
    result = evaluate(profile, observations)
    assert result["fairness_passed"] is False
    assert result["qualified"] is False
~~~

- [ ] L2.2 Run the focused test and record RED. Add NaN/bool/negative/unbounded profile cases; no-arrival and no-latency cases; independent call/ledger mismatch and unknown usage; overload correctness true with qualification false; maximum-size observations and hostile labels.
- [ ] L2.3 Implement strict profile keys. Bounds: duration 1..3600 seconds, arrivals/second >0..100, client concurrency 1..64, offered arrivals <=10000, maximum provider calls 1..10000, maximum application records 1..10000, finite output/report bytes <=262144. Require declared p95/rejection/minimum-tenant-completion targets and observation windows. Longer soak stops on the earliest duration/call/record limit and reports which bound stopped it; zero or omitted evidence never qualifies.

~~~json
{"version":1,"suite":"synthetic-capacity-v1","duration_s":20,
 "arrivals_per_second":1,"concurrency":2,"users":6,
 "maximum_calls":40,"maximum_records":40,"maximum_report_bytes":262144,
 "window_s":10,"p95_target_s":2,"maximum_rejection_ratio":0.05,
 "minimum_tenant_completion_ratio":0.8,"provider_latency_s":0,
 "tool_latency_s":0,"maximum_rpo_s":0,"maximum_rto_s":60}
~~~

Keep fixed-arrival/no-mutation-retry behavior. Key fairness by tenant+actor, not actor alone. Record offered/accepted/completed/start-rejected/approval-deferred/client-shed separately, per-tenant normalized completion and zero-progress windows, concurrent owner-read liveness and database row/byte growth. Reconcile independent synthetic requests against public usage deltas. A budget halt with unknown usage remains explicit; it is not a reconciliation success.
- [ ] L2.4 Add synthetic provider latency through the existing owned model /control endpoint, validated to 0..5 seconds and reset in finally. Enforce the shared maximum call allowance atomically at the synthetic model dispatch boundary, so concurrent starts cannot overshoot it; report rejected allowance attempts separately from dispatched calls. Add tool-latency observations through an owned synthetic operation fixture; this is fixture timing, not consequential-tool certification. The runner has finite HTTP deadlines and no hidden retry queue. Preserve stress command compatibility and its separate correctness/SLO result fields.
- [ ] L2.5 Add the missing staging regression:

~~~python
from lab_runner.staging_qualification import run

def test_missing_staging_configuration_is_not_fixture_success(monkeypatch):
    monkeypatch.setattr("httpx.Client.request",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")))
    result = run(None, enabled=True)
    assert result["qualification"] == "not_qualified"
    assert result["reason"] == "missing_deployment_inputs"
~~~

Private staging configuration supplies exact HTTPS approved origins, private token/CA references, expected issuer/audience/lifetime and bounded calls/time/report limits. Validate ownership/permissions and origin allowlist before opening a network client; reject redirects outside it. Do not acquire tokens, change issuer settings, rotate keys, stop gateways or create paid provider calls automatically. Rotation/outage/backend-isolation/drain cases consume explicitly supplied operator-controlled observations or an explicitly owned staging fixture. Missing case inputs remain not_qualified; never substitute Keycloak/fixture results. Public receipts contain digests and fixed reasons, not URLs, tokens or raw JWT claims.
- [ ] L2.6 Add owned logical restore measurement using durable marker sequence/time records alongside existing ownership/checkpoint/usage fixtures. Capture last acknowledged marker before the simulated loss, restore a consistent pg_dump into a second owned database, and measure time through verified restored readiness. Report observed RPO from missing acknowledged markers and RTO from loss to readiness; missing markers/timings fail qualification instead of producing zero. Assert restored owner, revision, receipt and unknown usage; compare independent model counts before/after restore and never invoke start/resume during restoration. This qualifies only logical backup/restore for the recorded fixture and profile, not HA/PITR.
- [ ] L2.7 Run focused units/CLI regressions, then both owned majors:

~~~sh
.venv/bin/python -m pytest tests/unit/test_qualification.py tests/unit/test_recovery_qualification.py tests/unit/test_staging_qualification.py tests/functional/test_qualification_cli.py -q
.venv/bin/python -m lab_runner qualify --profile configs/qualification.synthetic.json --postgres-version 16
.venv/bin/python -m lab_runner qualify --profile configs/qualification.synthetic.json --postgres-version 18
.venv/bin/python -m lab_runner qualify-recovery --profile configs/qualification.synthetic.json --postgres-version 16
.venv/bin/python -m lab_runner qualify-recovery --profile configs/qualification.synthetic.json --postgres-version 18
.venv/bin/python -m pytest -q
~~~

Record actual latency/growth/fairness/RPO/RTO, profile and immutable image/manifest identities, bounded workload and verified cleanup. Soak uses a separate explicit profile; default CI uses short deterministic cases. No qualify-staging command with real configuration runs as part of this task.
- [ ] L2.8 Commit reviewed L2 files with message "feat: add bounded operational qualification profiles".

### Task 3: L3 — Schema v3, immutable proposals, retained bundles and business journal

**Files:** Create src/prosaic_integration_lab/proposals.py, bundles.py, tool_journal.py. Modify app_schema.py, migrations.py, metadata.py, config.py, scripts/provision.py, lab_runner/__main__.py and stack.py. Test tests/unit/test_proposals.py, test_bundles.py, test_tool_journal.py, test_app_schema.py, test_migrations.py; tests/acceptance/test_native_persistence.py and test_tool_journal.py.

**Interfaces:** Public SDK dependencies: WorkflowBundle(version, factory), prepare_json(text) -> PreparedWorkflow with workflow/proposal_json/reference; reconstruct(proposal_json, reference) -> Workflow; WorkflowReference.to_dict()/from_dict(); ToolClaim(state, signature, claim_token=None, outcome=None). Lab APIs: proposals.canonical_proposal(text: str | bytes) -> str; ProposalStore(dsn).owned(principal, proposal_id), .replay(principal, key, request_digest), .reserve(principal, key, prepared, *, maximum_records, maximum_tenant_records); BundleRegistry.register(bundle), .resolve(version, identity); Metadata.reserve_native(principal, key, proposal, inputs, *, namespace, environment, max_runs, max_tenant_runs). PgToolJournal(dsn, *, identity) exposes plain identity and contract_version="tool-journal-v1", claim(namespace,key,signature) and commit(namespace,key,claim_token,bounded_outcome).

- [ ] L3.1 Write proposal replay tests before storage implementation. Preserve exact original canonical text and public reference serialization:

~~~python
def test_proposal_replay_after_bundle_upgrade_keeps_original_reference(proposals, principal, prepared_v1, prepared_v2):
    original = proposals.reserve(principal, "same-key", prepared_v1,
                                 maximum_records=100, maximum_tenant_records=100)
    replay = proposals.replay(principal, "same-key", original["request_digest"])
    assert replay["proposal_id"] == original["proposal_id"]
    assert replay["proposal_json"] == prepared_v1.proposal_json
    assert replay["reference"] == prepared_v1.reference.to_dict()
    assert replay["reference"] != prepared_v2.reference.to_dict()
~~~

Define fixtures in tests/acceptance/test_native_persistence.py: proposals uses the owned restricted app DSN, principal is the existing fixture owner, and prepared_v1/v2 use public bundles with distinct host policy versions and the same accepted proposal. Add same-key concurrent A/B insertion, changed body conflict, other-owner 404, canonical Unicode/key-order, cap exhaustion replay and no mutable record update/delete grants.
- [ ] L3.2 Run focused tests to RED. Add schema-v2 migration fixtures preserving every original runs field, namespace/environment and reserved/starting/started phases. Existing v1 tests must still require exact authoritative scope records; do not derive old scopes or assets from new service defaults.
- [ ] L3.3 Implement v3 as additive application tables, preserving the runs table and its legacy request-hash recipe byte-for-byte:

~~~sql
CREATE TABLE lab_app.proposals (
  proposal_id text PRIMARY KEY,
  tenant_id text NOT NULL, actor_id text NOT NULL,
  idempotency_key text NOT NULL, request_digest text NOT NULL,
  proposal_json text NOT NULL,
  bundle_version text NOT NULL, bundle_identity text NOT NULL,
  policy_digest text NOT NULL, workflow_fingerprint text NOT NULL,
  reference jsonb NOT NULL,
  UNIQUE (tenant_id, actor_id, idempotency_key),
  UNIQUE (proposal_id, tenant_id, actor_id),
  CHECK (octet_length(proposal_json) <= 65536)
);
CREATE TABLE lab_app.native_runs (
  run_id text PRIMARY KEY REFERENCES lab_app.runs(run_id),
  proposal_id text NOT NULL, tenant_id text NOT NULL, actor_id text NOT NULL,
  FOREIGN KEY (proposal_id, tenant_id, actor_id)
    REFERENCES lab_app.proposals(proposal_id, tenant_id, actor_id)
);
CREATE TABLE lab_app.tool_operations (
  operation_namespace text NOT NULL, operation_key text NOT NULL,
  signature text NOT NULL, claim_token text NOT NULL,
  state text NOT NULL CHECK (state IN ('uncertain','completed')),
  outcome jsonb,
  PRIMARY KEY (operation_namespace, operation_key),
  CHECK ((state='uncertain' AND outcome IS NULL)
      OR (state='completed' AND outcome IS NOT NULL))
);
~~~

Bound all text/reference/outcome fields in application admission and schema constraints, including 262144-byte journal outcome and 4096-byte serialized reference caps. A committed claim row starts uncertain; "new" is returned only to its successful inserting worker, never reconstructed as dispatch permission from a stored row. Maintain exact table/column/constraint readiness checks for v3 and explicit archived contracts for v1/v2. Upgrade under the existing transaction advisory lock; validate old shape first, add tables/grants, advance version last, commit atomically. Runtime gets SELECT/INSERT on immutable proposals/native_runs and journal SELECT/INSERT plus UPDATE(state,outcome); no proposal mutation or schema-owner powers. Keep new operation markers in owned qualification fixtures separate from production service schema.
- [ ] L3.4 Implement proposal lookups using owner+key and SHA256 of exact canonical proposal bytes. An existing matching row returns unchanged before any new bundle admission or retention-cap check. New proposals undergo public bundle admission before INSERT. Resolve an insert race by reading the winner and checking its request digest, not by returning a locally prepared losing reference. canonical_proposal enforces raw and canonical UTF-8 bytes <=65536, depth <=64 and expanded nodes <=65536, duplicate keys, nonfinite numbers and malformed Unicode through a strict transport JSON parser before json-sort-keys-utf8-v1 encoding. Parser recursion/number errors become fixed invalid_request without snippets. This parser is transport validation only and must not duplicate SDK graph/schema admission. Verify canonical_proposal and public PreparedWorkflow.proposal_json have identical bytes for accepted numeric/Unicode/key-order fixtures.
- [ ] L3.5 Implement BundleRegistry as a trusted in-process registry keyed by (version, identity), populated at host startup. Register immutable SDK bundles from packaged host artifacts/configuration references/semantic callback versions; resolve exact identities only. No client-provided module name, callback, directory or endpoint is loaded. Changed/missing material returns the app's fixed bundle_unavailable or bundle_conflict condition. Native reservations atomically INSERT runs and native_runs under the same ownership/capacity lock as legacy reservations; inputs are already prepared. New native request hashes cover {"proposal_id": ..., "inputs": ...} using a distinct versioned canonical recipe. Do not change canonical_request for existing YAML keys. Legacy runs remain addressed by their retained original assets hash.
- [ ] L3.6 Add the public journal contract and watched fencing regression:

~~~python
def test_uncertain_claim_never_reclaims_and_stale_token_cannot_commit(journal):
    from prosaic_runtime import ToolClaim
    first = journal.claim("tenant-a", "owned-operation", "a" * 64)
    assert isinstance(first, ToolClaim) and first.state == "new"
    repeated = journal.claim("tenant-a", "owned-operation", "a" * 64)
    assert repeated.state == "uncertain"
    assert repeated.claim_token is None
    with pytest.raises(ValueError):
        journal.commit("tenant-a", "owned-operation", "stale-token",
                       {"status": "ok", "result": {"applied": True}})
    journal.commit("tenant-a", "owned-operation", first.claim_token,
                   {"status": "ok", "result": {"applied": True}})
    replay = journal.claim("tenant-a", "owned-operation", "a" * 64)
    assert replay.state == "replay"
    assert replay.outcome == {"status": "ok", "result": {"applied": True}}
~~~

Claim uses INSERT ON CONFLICT DO NOTHING, an opaque random fencing token and transactionally reads the winning signature/state. A signature mismatch raises a fixed conflict; an existing uncertain row never dispatches. Commit updates WHERE namespace/key/token match AND state='uncertain', with rowcount exactly one. A failed/lost acknowledgement is not permission to retry the effect; a subsequent claim can discover a committed replay. Same keys in different trusted namespaces remain independent. Do not add lease expiry or a runtime reconciliation route. Domain no-effect/fencing evidence remains an explicit operator obligation.
- [ ] L3.7 Run units and owned journal/migration races on both majors:

~~~sh
.venv/bin/python -m pytest tests/unit/test_proposals.py tests/unit/test_bundles.py tests/unit/test_tool_journal.py tests/unit/test_app_schema.py tests/unit/test_migrations.py -q
.venv/bin/python -m lab_runner test --mode native-persistence --postgres-version 16
.venv/bin/python -m lab_runner test --mode native-persistence --postgres-version 18
.venv/bin/python -m pytest -q
~~~

Add native-persistence mode to runner using only test_native_persistence.py and test_tool_journal.py and the same owned provisioning/cleanup path. Test runtime role migration denial, same-scope concurrent claims, changed signatures, lost acknowledgement, oversized/post-effect-invalid results and unchanged uncertain rows. Record evidence and commit L3 files with message "feat: persist admitted proposals and fenced tool operations".

### Task 4: L4 — Native catalogue/proposal/run routes and generic human views

**Files:** Create src/prosaic_integration_lab/native_execution.py, assets/native/agents/finder.md, reviewer.md and schemas/found.json, reviewed.json, decision.json; configs/native.example.json; docs/native-workflows.md. Modify app.py, http_guard.py, execution.py, config.py, views.py, observability.py and lab_runner/model.py. Test tests/unit/test_native_execution.py, test_native_views.py; tests/functional/test_native_http.py, test_http_auth.py, test_start_admission.py and test_http_guard.py.

**Interfaces:** NativeExecution owns ProposalStore, trusted BundleRegistry and current policy projection. Expose catalogue(principal), propose(principal,key,text), start_request(principal,key,proposal_id,inputs), harness(reservation), status(reservation), resume(reservation,revision,choice,response,retry). Execution delegates workflow="native" records to this unit and preserves legacy execution. It consumes public factory.describe/proposal_schema, Workflow.prepare_inputs, Harness.run(inputs), interaction(...).to_dict(), resume(choice=..., response=..., expected_revision=..., retry_interrupted=...) and safe HumanResponseError/WorkflowAdmissionError. The SDK registry does not own app authentication or persistence.

- [ ] L4.1 Add a credential-free native graph factory fixture with two packaged specialists and host-only validators:

~~~python
def approved_proposal():
    return {"definition": {"version": 1, "start": "find", "steps": {
        "find": {"kind": "agent", "agent": "finder", "schema": "found", "next": "review"},
        "review": {"kind": "agent", "agent": "reviewer", "schema": "reviewed",
                   "inputs": ["find"], "next": "checked"},
        "checked": {"kind": "check", "from": "review", "validators": ["approved"],
                    "pass": "gate", "fail": "rejected"},
        "gate": {"kind": "gate", "from": "review", "field": ["approved"],
                 "equals": True, "pass": "confirm", "fail": "rejected"},
        "confirm": {"kind": "pause", "question": "Accept the synthetic review?",
                    "choices": {"accept": "done", "reject": "rejected"},
                    "requires": ["find", "review"], "response_schema": "decision"},
        "done": {"kind": "finish", "requires": ["find", "review"]},
        "rejected": {"kind": "finish", "outcome": "rejected"}
    }}}
~~~

Package deterministic ALWAYS/NEVER specialist prose and closed object schemas: found has entity_id:string<=64; reviewed has entity_id and approved:boolean; decision has confirmed:boolean, all required and additionalProperties=false. Register approved Validator with explicit semantic version and predicate over reviewed.approved. Composition-granted tenant allows both agents and approved schemas/validator; another tenant lacks composition; inline grant is a separate trusted setting. Runtime endpoint is the owned model fixture selected by private host config. Public metadata is explicit synthetic description, never prose inference.
- [ ] L4.2 Write HTTP tests with forbidden model/validator/store callbacks during catalogue/proposal admission and invalid run-input preparation:

~~~python
def test_invalid_inputs_allocate_no_run(native_client, proposal, counters):
    response = native_client.post("/native-runs",
        headers={"Authorization": "Bearer tenant-a-token", "Idempotency-Key": "bad-input",
                 "Content-Type": "application/json"},
        content='{"proposal_id":"' + proposal["proposal_id"] + '","inputs":{"x":Infinity}}')
    assert response.status_code == 422
    assert counters["reservations"] == counters["models"] == counters["validators"] == 0
~~~

Also test a valid finite JSON value exceeding workflow input bytes, invalid graph envelope and rejected privilege fields, with no fresh proposal/run records or Harness state. Define native_client using TestClient and the actual installed public factory, replacing only application storage/model transport boundaries with synthetic test fixtures; never patch SDK admission.
- [ ] L4.3 Implement routes and exact payloads:

| Route | Payload/result | Error boundary |
| --- | --- | --- |
| GET /workflow-catalogue | {"bundle_version": ..., "manifest": factory.describe(), "proposal_schema": factory.proposal_schema()} | Host-selected tenant factory; no schemas/private data unless explicitly approved. |
| POST /workflow-proposals | Exact raw {"definition":...,"inline_agents":...?}; Idempotency-Key header; result {"proposal_id":..., "reference": reference.to_dict()} | 64 KiB authenticated body; safe admission code/location; owner/key replay before new admission. |
| POST /native-runs | {"proposal_id": bounded text, "inputs": finite JSON}; Idempotency-Key header | 8 KiB body; owner lookup, current entitlement and exact retained bundle; prepare_inputs before writes. |
| GET /runs/{id} | Existing curated status; native adds interaction.to_dict() or null | Owner check before any SDK status/accounting query; outputs excluded by default. |
| POST /runs/{id}/resume | expected_revision, optional actual choice, optional JSON response, retry_interrupted=false | Strict extra-forbid fields; current entitlement, SDK revision/schema/validator check; safe response codes/issues. |
| GET /runs/{id}/usage | Existing frozen owner-scoped public usage | No current principal/billing substitution. |

Keep /runs StartRequest workflow Literal approval|synthetic and its legacy task semantics. Widen resume choice to bounded string for native choices, add response JSON, and retain original legacy approve/reject behavior. Unknown responses never become retry consent. HttpGuard chooses 65536 only for exact POST /workflow-proposals and 8192 for other POST routes; update owned ingress location-specific body size too, so 64 KiB proposals work through the gateway.
- [ ] L4.4 Wire start sequentially through current entitlement, exact retained reference reconstruction, owned input snapshot, admitted worker capacity, atomic reservation, claim_start and Harness.run(inputs=owned_inputs). Matching existing native-run keys return their original reservation before new defaults/cap checks, with current authorization still enforced. Unknown starting records return the existing operator-reconciliation view and no redispatch. Context derives exclusively from frozen reservation fields. Configure public WorkflowBindings(config=..., custom_tools=..., validators=..., operation_namespace=..., tool_journal=...) from the retained host bundle. Native Harness constructs InvocationScope from persisted invocation/run/step references and the sealed namespace; clients never supply scope or journal identity. Pass remaining workflow time/tokens and host per-invocation provider/tool caps through SDK policy; max_calls remains workflow invocations.
- [ ] L4.5 Project human interaction from the SDK's single verified snapshot. Host selection includes only approved review step IDs; application then filters their fields to entity_id/approved. Never publish arbitrary full agent outputs, input bindings, evidence/history or operator status. response schema is opt-in only when host-approved. Invalid response leaves revision/state unchanged; stale revision returns 409; safe HumanResponseError becomes 422 with bounded code/issues. Preserve legacy review projection and interrupted-retry consent.
- [ ] L4.6 Move optional metrics to observer=, using only closed/redacted SDK records. Keep fixture_event on_event critical evidence gates for receipt-crash tests; an ordinary monitoring exception cannot suppress accepted work. Add actual committed pause/revision observer assertion. Do not transform arbitrary exception text into observer/public labels.
- [ ] L4.7 Run watched focused tests to green and full host suite:

~~~sh
.venv/bin/python -m pytest tests/unit/test_native_execution.py tests/unit/test_native_views.py tests/functional/test_native_http.py tests/functional/test_http_auth.py tests/functional/test_start_admission.py tests/unit/test_http_guard.py -q
.venv/bin/python -m pytest -q
~~~

Tests include tenant projection, zero-callback admission, composition/inline independence, omitted host-default tier, configured+allowed explicit tiers, input copy ownership, proposal-key replay under changed policy, body/key limits, private sentinels, invalid/stale human choices and current revocation before native start/resume. Commit reviewed L4 files with message "feat: serve owner-scoped generated native workflows".

### Task 5: L5 — Required native service and actual legacy release upgrade acceptance

**Files:** Create lab_runner/native_scenarios.py, legacy_upgrade.py; tests/acceptance/test_native_workflows.py, test_native_effect_recovery.py, test_legacy_release_upgrade.py; tests/unit/test_legacy_upgrade.py and test_native_gate.py. Modify lab_runner/stack.py, model.py, gates.py, __main__.py, scripts/required_acceptance.py, .github/workflows/required-acceptance.yml, MANIFEST.in and docs/release-gates.md.

**Interfaces:** Runner modes native and legacy-upgrade use exact snapshotted immutable consumer images and the standard ownership/receipt/cleanup contract. legacy_upgrade.generate(stack, *, baseline_manifest, baseline_image) creates evidence using actual Lab 0.2.0 code and wheels; .verify(stack, fixture) checks new schema/image recovery without redispatch. Fixture is private to the owned run directory and contains original public run IDs/revisions, private retained assets/configuration and accounting snapshots. Public summaries expose only counts/digests/outcomes.

- [ ] L5.1 Add alternating-replica acceptance against actual HTTP inference, not patched SDK run methods:

~~~python
def test_native_graph_cross_worker_pause_and_approval(lab):
    import httpx
    from lab_runner.native_scenarios import approved_proposal
    headers = {"Authorization": "Bearer " + lab["tokens"]["alice"]}
    proposal = httpx.post(lab["a"] + "/workflow-proposals",
        headers={**headers, "Idempotency-Key": "native-proposal"},
        json=approved_proposal(), timeout=10).json()
    waiting = httpx.post(lab["a"] + "/native-runs",
        headers={**headers, "Idempotency-Key": "native-run"},
        json={"proposal_id": proposal["proposal_id"], "inputs": {"entity_id": "sample-1"}},
        timeout=30).json()
    assert waiting["status"] == "waiting"
    interaction = waiting["interaction"]
    assert set(interaction["choices"]) == {"accept", "reject"}
    completed = httpx.post(lab["b"] + "/runs/" + waiting["run_id"] + "/resume",
        headers=headers, json={"expected_revision": interaction["revision"],
                               "choice": "accept", "response": {"confirmed": True}},
        timeout=10).json()
    assert completed["status"] == "completed"
    assert httpx.get(lab["model"] + "/stats", timeout=5).json()["calls"] == 2
~~~

Check HTTP statuses before decoding in the finished test, and compare independent call-count deltas rather than absolute counts when sharing a lane. Fixture synthetic responses inspect the actual second invocation artifacts.find and dependency bindings, and reject missing/stale provenance. Add fresh-process replica restart before resume, check/gate failure, response-schema error, graph revisit freshness, finish requires and budget exhaustion preventing the next provider/tool dispatch.
- [ ] L5.2 Add owner isolation for catalogue/proposal/runs/human/usage; distinct tenant namespaces and same operation keys; current revocation; altered policy/assets/configuration/callback semantic version/journal identity; missing retained bundle; no default fallback. Test omitted model tier with an empty explicit allowlist. Verify inline grant does not imply composition or tools. SDK references supplied by a client never hydrate registration code.
- [ ] L5.3 Add observable crash barriers around native receipt persistence and journal claim/effect/outcome commit. Fresh workers adopt saved receipts with no additional model calls; interrupted provider calls require explicit consent and preserve unknown usage. A synthetic consequential operation stores its domain effect in an app-owned fixture table with UNIQUE(namespace,key), so the effect and business idempotency can be verified independently of journal and recorder. Crash after effect/before journal commit stays uncertain and blocks dispatch. Lost commit acknowledgement can replay a completed result. Concurrent claims dispatch one handler; stale fencing tokens cannot overwrite. Changed arguments/version conflicts retain the original evidence. No automatic expiry/reconciliation API.
- [ ] L5.4 Generate the legacy fixture from dependencies/releases-lab-0.2.0.json in a separate clean baseline image whose app checkout is immutable v0.2.0 commit 59752bef3e6b3ffde0ecbf38f34815d184043e20. Verify all five historical wheel hashes before startup; no renamed SDK packages may be installed there. Use public legacy service routes and existing critical HTTP fault gates to create:

| Original state | Upgrade expectation |
| --- | --- |
| Approval waiting, committed revision | New image reads same owner/revision and approves with no model call. |
| Synthetic waiting plus complete usage | Frozen billing/namespace/environment and original assets identity persist. |
| Saved agent receipt before acceptance | New worker adopts receipt; independent provider count and ledger totals do not increase. |
| Missing final usage after a provider call | Unknown coverage remains unknown; never zero or automatic retry. |
| Starting reservation with uncertain dispatch | New image returns operator condition and does not create another invocation. |

Drain/stop baseline replicas before schema migration. Retain exact legacy assets/configuration in the new image's host registry keyed by original assets_hash; do not regenerate them from current defaults. Run explicit v2→v3 migration with migration credentials, start a fresh new worker on the same owned database, compare original ownership/request/idempotency/hash/accounting fields, and exercise cross-worker public recovery. Do not fabricate a historical receipt with new SDK serializers.
- [ ] L5.5 Add negative upgrade cases: incompatible schema/shape aborts transaction; runtime role cannot migrate; wrong baseline manifest/image audit fails before allocating stack resources; missing historical assets does not dispatch; changed current actor/billing defaults never replace stored attribution; reordered persisted reference JSON reconstructs from exact canonical proposal text.
- [ ] L5.6 Extend required gates while retaining audit/identity/ingress/lago lanes. Register native mode for test_native_workflows.py and test_native_effect_recovery.py; legacy-upgrade for test_legacy_release_upgrade.py; qualification for the short deterministic cases in test_operational_qualification.py. These new lanes have reviewed exact collected counts, zero skips, immutable image/manifest identities and verified owned cleanup. Update count contracts from actual pytest collection after tests land; never accept any positive count or lower a count to hide failures. Increase bounded per-lane/job deadlines for measured added work only. Pin actions, keep read-only repo permissions and upload whitelist summaries only; private backups/configs/logs remain excluded.
- [ ] L5.7 Run focused host and owned lanes, then all required gates on both PostgreSQL majors:

~~~sh
.venv/bin/python -m pytest tests/unit/test_legacy_upgrade.py tests/unit/test_native_gate.py -q
.venv/bin/python -m lab_runner test --mode native --postgres-version 16
.venv/bin/python -m lab_runner test --mode native --postgres-version 18
.venv/bin/python -m lab_runner test --mode legacy-upgrade --postgres-version 16
.venv/bin/python -m lab_runner test --mode legacy-upgrade --postgres-version 18
.venv/bin/python scripts/required_acceptance.py --postgres-version 16 --export reports/required-pg16.json
.venv/bin/python scripts/required_acceptance.py --postgres-version 18 --export reports/required-pg18.json
.venv/bin/python -m pytest -q
~~~

Root dispatches required four-cell native CI after review. Local architecture success cannot stand in for another architecture. No paid provider lane or shared staging configuration is required for these gates.
- [ ] L5.8 Commit reviewed L5 files with message "test: qualify native workflows and released legacy upgrades". Preserve baseline manifest/images and receipts independently of active SDK cache.

### Task 6: L6 — Published dependency adoption and current delivery evidence

The user's follow-up requests a usable Lab adoption path while package-index
publisher registration is pending. Implement the explicit candidate setup
profile and native demo first: reuse verified original SDK artifacts and the
owned stack, drive catalogue/proposal/start/structured response through public
HTTP APIs, export only checked synthetic fields, and retain verified cleanup.
Document host bindings and service integration, and qualify the same demo
helper and CLI on all four native cells. This is candidate onboarding; L6.2's
published pins and L6.3's 0.3.0 release still require actual ordered publication.

**Files:** Modify dependencies/releases.json, pyproject.toml, MANIFEST.in, README.md, docs/handoff.md, release-gates.md, capacity-retention.md, persistence.md, recovery.md, identity.md and ingress.md. Create docs/current-status.md and docs/verification/ecosystem-production-2026-10-10.md. Add sanitized JSON receipts only after actual executions. Tests: tests/unit/test_released_provenance.py and test_release_gates.py; source/wheel installed checks.

**Interfaces:** Root supplies downloaded, qualified published artifacts and immutable source/tag/checksum/verification identities. Active manifest continues the existing artifacts contract (distribution, version, filename, sha256, source_commit, url, checksum_url), with b3-prosaic family names and exact release versions. Historical releases-lab-0.2.0.json is never overwritten. Status index links current evidence and labels prior documents as historical checkpoints without rewriting old measurements.

- [ ] L6.1 Add the active-family invariant:

~~~python
def test_active_manifest_selects_only_the_qualified_new_sdk_family():
    import json
    from pathlib import Path
    data = json.loads(Path("dependencies/releases.json").read_text())
    assert {(item["distribution"], item["version"]) for item in data["artifacts"]} == {
        ("b3-prosaic", "0.4.0"), ("b3-prosaic-runtime", "0.8.0"),
        ("b3-prosaic-runtime-postgres", "0.2.0"),
        ("b3-prosaic-harness", "0.7.0"),
        ("b3-prosaic-harness-postgres", "0.2.0")}
    assert all(len(item["sha256"]) == 64 and len(item["source_commit"]) == 40
               for item in data["artifacts"])
~~~

Run it RED against the preserved current manifest. Do not insert predicted artifact hashes or mutable branch URLs to make it pass.
- [ ] L6.2 After root confirms final Milestone 7 code/qualification and publishes the SDK train, download and verify exact GitHub/index bytes. Compare published wheel digests across channels; matching same-version bytes are idempotent success, differing bytes require a new version. Update active manifest from verified assets only; retain prior manifests/caches/images. Rebuild a fresh active environment/image through L1. Lab itself remains a GitHub application/source distribution by default; no PyPI lab upload is implied.
- [ ] L6.3 Set lab application version 0.3.0 and document the b3-prosaic distribution/import naming distinction and fresh-environment migration. Include new source assets, scripts, profiles and docs in MANIFEST.in; audit clean-tag source/wheel contents against tracked/public allowlists. Exclude untracked research, caches, private run/backup/configuration data and local proof outputs. Keep exact installed SDK audit and import/CLI compatibility.
- [ ] L6.4 Build and test the extracted source archive and clean installed consumer wheel with locked dependencies and only manifest-listed SDK wheels:

~~~sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/audit_install.py --manifest dependencies/releases.json
.venv/bin/python -m build
.venv/bin/python scripts/build_consumer.py --manifest dependencies/releases.json --dependency-mode released --tag prosaic-integration-lab:dev
.venv/bin/python scripts/required_acceptance.py --postgres-version 16 --export reports/released-pg16.json
.venv/bin/python scripts/required_acceptance.py --postgres-version 18 --export reports/released-pg18.json
~~~

The audit command resolves cache_directory from exact manifest bytes. Root reruns four native CI cells against these final published pins; candidate receipts are not reused as released evidence.
- [ ] L6.5 Write docs/current-status.md with implemented/released versions and links to current verification, native API examples, operational profiles and retained legacy upgrade. Record commands, architecture, image/manifest/source IDs, counts, cleanup and limitations. Clearly separate required synthetic service qualification, measured capacity profile, logical restore, actual identity/ingress staging, live provider capabilities and external PyPI ownership/readiness. Unexecuted or missing-input deployment lanes stay not_qualified. Update current README entry links and supersession notes on historical handoff/progress documents; preserve original historical evidence text.
- [ ] L6.6 Run git diff --check, review source/installed payload evidence and commit L6 with message "release: adopt qualified SDK train and lab 0.3.0 evidence". Root owns the final merge/tag/publication and records downloaded lab artifacts; no task publishes independently.

## Self-review and execution handoff

- [x] Coverage: SDK observer consumption is L4; public catalogue/input/human/bundle contracts are L3/L4; generated owner service is L3–L5; journal recovery is L3/L5; invocation budget consumption is L4/L5; package/cache provenance is L1/L6; load/fairness/soak/restore/staging qualification is L2/L5; actual old-release upgrades are L5.
- [x] Contract consistency: use public PreparedWorkflow.workflow/proposal_json/reference, WorkflowReference.to_dict()/from_dict(), PendingInteraction.to_dict(), Harness.run(inputs=...), ToolClaim.state/signature/claim_token/outcome and plain journal identity/contract_version. SDK production implementations belong upstream, not in lab fixtures.
- [x] Review-focus coverage: each of the five listed conditions has a watched regression in its owning task; required-gate malformed/incomplete receipts and cleanup failures remain explicit failures.
- [x] No placeholders or guessed release evidence: exact published pins/hashes are filled only from root-verified artifacts; count contracts come from real collected tests; no future statement is represented as a completed result.
- [x] Execution is already authorized by the human with autonomous parallel work and no additional design handoff. Start L1/L2 within their file ownership; wait for installed public SDK prerequisites before L3/L4; review each completed task independently and finish with whole-change review and required native gates.
