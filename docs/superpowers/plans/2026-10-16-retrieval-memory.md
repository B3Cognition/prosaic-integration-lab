# Controlled retrieval memory implementation plan

> **For agentic workers:** Use superpowers:executing-plans; user approved native implementation. Continue task by task without another direction gate.

**Goal:** Qualify a read-only episodic retrieval/context contract and prepare a paired memory-on/off experiment.
**Architecture:** Separate lab_runner.memory package and CLI; public installed Runtime/Harness, immutable tenant-partitioned corpus and historical source store, one host retrieval before native source lookup. Keep existing quality code/resources unchanged.
**Tech Stack:** Python3.12, canonical JSON, jsonschema, public Prosaic Runtime/Harness, pytest.
**Spec:** docs/superpowers/specs/2026-10-16-retrieval-memory-design.md (approved by user "Approvt").

## Global Constraints

Read-only synthetic episodes; no embeddings, automatic memory writes, real history or Core/SDK edits. Tenant/asOf from trusted host. Max128episodes/256KiB corpus plus256KiB historical sources, top3/4096bytes, notes1024bytes,4refs. Local identities ignore valid foreign changes. Fresh sources remain required. No answer-target feedback. Two invocations/sample,4requests/2tools/8192tokens/600s.48samples,192/96/393216,28800s batch. All prior22ledgers remain charged; new live budget requires explicit approval after qualification.

## Review Focus

Foreign-only changes cannot alter local identity/context/resume. Malformed global admission fails before inference. Historical hashes authenticate synthetic source snapshots, not current facts. Freeze retriever/corpus/prose before evaluation authoring. Missing receipts never authorize redispatch. Private scorer/source annotations cannot enter prompts or public summaries.

### Task 1: Immutable retrieval and context

Files: lab_runner/memory/{__init__,corpus,context}.py; tests/unit/test_retrieval_memory.py.
Interfaces: Corpus(document,historical_sources).retrieve(tenant_id,query,as_of); tenant_digest(tenant_id); prepare(case,corpus,arm) returns frozen host envelope.
- [ ] Write tests for ordering, no hits, top3/bytes, future filtering, scope, hashes, duplicate/malformed fields, caller mutation and foreign noninterference; observe RED.
- [ ] Implement strict admission, canonical snapshot lineage and lexical retrieval; only scoped identities/results become context; run tests GREEN.

### Task 2: Public native execution and recovery

Files: lab_runner/memory/{execution,scoring,fixture}.py; development fixtures; tests/functional/test_retrieval_memory_execution.py.
Interfaces: materials/execute_case use prepared context and current source store; score validates request/receipt/journal joins and private assertions. Frozen context persists before dispatch and binds recovery version.
- [ ] Write actual HTTP payload/native lookup tests proving arm context and no oracle, wrong/missing/stale source rejection, retry feedback without target and exact counts; observe RED, then implement GREEN.
- [ ] Test persisted receipt adoption, missing receipt block and local corpus/source drift; foreign-only drift allowed. Use public RunStore wrappers only.

### Task 3: Runner, reports and ordered freeze

Files: lab_runner/memory/{suite,runner,reporting}.py; lab_runner/retrieval_memory.py; packaged corpus/prose/source fixtures; tests/unit/test_retrieval_memory_runner.py and functional CLI tests.
- [ ] Test pure no-network/no-secret preflight; alternating paired schedule; durable whole-sample reservations; unknown usage stop; safe metrics and replay; observe RED then implement GREEN.
- [ ] Qualify development fixtures, archive ordered freeze manifest for retrieval/context/prose/checks/corpus, then author12evaluation cases in6families and freeze separately. Evaluation outcomes must not tune the frozen inputs.
- [ ] Verify all48fixture samples, independent HTTP/tool/retrieval counts and no-provider byte-identical replay; label any post-freeze correction and replace eval set if needed.

### Task 4: Installed qualification, review and live boundary

Files: pyproject.toml package-data addition, scripts/retrieval_memory_smoke.py, docs/retrieval-memory.md, verification record, packaging tests.
- [ ] Packaging tests RED then package assets GREEN; full Lab pytest; wheel/sdist builds and isolated installed payload/smoke/fixture/recovery audit using exact qualified SDK manifest.
- [ ] Fresh whole-change review, fix important findings via failing regressions and necessary verification.
- [ ] Recompute all retained ledgers and graph-derived live allowance; prepare concrete48sample study, then request only required live extension. No live dispatch before approval. Preserve unpublished source/candidates/evidence.

## Execution ledger

Pre-flight: Task1 corpus/context feeds Task2 execution; Task2 evidence/scoring feeds Task3 runner; Task3 frozen assets feeds Task4 package audit. Shared canonical/allowance helpers read only. Existing isolated codex/agent-quality-benchmark worktree reused; unrelated dirty files preserved.
Ruling: No blanket staging or commits of historical benchmark/unrelated changes. Freeze via content-addressed manifests; any later commit may include only new memory files plus exact package-data hunk.
Ruling: Approved design supplies direction and native method; implementation plan is execution detail and does not re-open an approval gate. Live numerical budget remains separate.
