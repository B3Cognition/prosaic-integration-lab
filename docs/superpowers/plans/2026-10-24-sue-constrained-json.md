# SUE constrained JSON implementation plan

> **For agentic workers:** Use superpowers:executing-plans for inline execution. The user's request authorizes implementation and the Qwen rerun.

**Goal:** Request the exact per-turn SUE JSON Schema through Runtime, preserving independent strict validation and immutable failed-run evidence.

**Architecture:** Runtime accepts a trusted, bounded `response_schema` option on its tool-free OpenAI-compatible invocation API and the public RuntimeAdapter delegate. It encodes `response_format` with `type=json_schema` and `strict=true`; it never repairs responses or retries without the schema. Lab enables this only through the explicit trusted `SueReviewSession(..., constrained_json=True)` option, binds it to saved review policy/identity, and passes the canonical engine's current schema. Existing ReviewSettings dataclass serialization stays unchanged for the frozen v1 consumer.

**Tech stack:** Python, installed candidate wheels based on Runtime v0.9.8 and Lab fcc5082; unchanged public Core/Harness/standalone SUE dependencies; real authenticated local Qwen2.5-Coder-7B/oMLX.

**Spec:** User request and `docs/verification/review-contract-fixes-2026-10-24.md`.

## Global constraints

- Memory, SUE, and constrained generation remain disabled by default.
- Keep canonical schema, semantic validators, guidance, raw JSON parsing, budgets, citation checks, scopes and provenance unchanged.
- Do not rewrite old stores, reservations, wheels, manifests or evidence.
- Keep direct/critic-author prompts, cases, keys, grading and all model settings unchanged; explicitly identify the Runtime candidate in the new experiment.
- Runtime owns encoding, transport and usage; Harness owns accepted state and receipts; SUE owns interpretation validity; Lab owns opt-in policy and evaluation.
- No push, release, SOAR, model runner in Castle or original Castle backport.

## Review focus

- Reject malformed/oversized/remote-reference schemas before model dispatch.
- A RuntimeAdapter cannot discard an outer caller's schema constraint or expand its grants/budgets.
- Unsupported providers/tools/acquisition fail before HTTP; HTTP rejection never causes an unconstrained retry.
- Providers can ignore schema requests: preserve raw responses and require independent SUE validation; inspect oMLX enforcement warnings.
- Disabled mode retains existing request and adapter identities; sealed review resume uses saved policy, never current configuration to upgrade old runs.

### Task 1: Runtime schema request and strict transport regressions

- [ ] Write `tests/test_response_schema.py` against real owned loopback HTTP and public Runtime/RuntimeAdapter APIs: exact schema wire equality, legacy json_mode/no-format compatibility, per-call isolation, unchanged raw output/usage, malformed admission, byte limits, unsupported combinations and no fallback on HTTP400.
- [ ] Witness RED against v0.9.8; implement bounded schema ownership in `src/prosaic_runtime/response_schema.py`, `runtime.py`, `adapter.py`, and `openai_compatible.py`.
- [ ] Run focused and full Runtime suite, document the additive public API; build direct and rebuilt candidate wheels using a local-only version and compare payloads.

### Task 2: Opt-in SUE integration and compatibility

- [ ] Write `tests/sue_review/test_constrained_json.py`: absent Runtime capability fails closed; candidate sends each exact dynamic schema, retry retains schema, invalid/missing/fenced/false-quote/future-turn responses are rejected, disabled remains legacy, frozen settings survive resume.
- [ ] Witness RED; implement the explicit boolean host option and omission of false policy in `session.py`, `workflow.py`. Keep `contracts.py` byte-identical; change adapter identity only when enabled.
- [ ] Run all enabled Lab source regressions plus default/absent-package boundaries against the appropriate installed SDK; build fresh Lab direct/rebuilt wheels and verify isolated consumers.

### Task 3: Same frozen comparison and evidence

- [ ] Run the 24-cell credential-free fixture comparison and installed PG16/18 memory/SUE acceptance, verifying inventory and cleanup.
- [ ] Freeze a new operator/plan/allowance with explicit candidate wheel hashes; same 24-cell rotating order and bounds: 30requests/65536tokens/120seconds per cell, SUE28calls/14turns/60seconds per invocation/two attempts, temperature0.2, max4096 output, thinking disabled.
- [ ] Run all arms on Qwen; record actual per-turn schemas and provider warning headers. No post-observation tuning, repair, extra retries or limit changes.
- [ ] Replay and audit with networking denied; reconcile physical calls/usage/receipts and exact schema/provenance matches. Compare controls and classify schema versus semantic failures.
- [ ] Review final diff, document results and limitations, seal a fresh archive with hashes and verify all previous archives unchanged. Keep all changes local.
