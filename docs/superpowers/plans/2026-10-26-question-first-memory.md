# Question-first memory generation candidate

Approved scope: implement the recommendations in
`docs/verification/qwen-serving-trace-2026-10-26.md`, then repeat the bounded
three-case Qwen preflight. This plan is the implementation brief; the serving
trace and existing memory benchmark design are its evidence and constraints.

Global constraints: strict canonical schema, scope/provenance validation and
scorer stay unchanged. Existing generation modes retain their behavior. Memory
and SUE stay disabled; no SOAR, publication, push or release. Preserve historic
archives and all six unknown-usage reservations. Keep installed candidates and
their evidence separate from previous environments.

### Task 1: Opt-in Runtime schema order

Interfaces: public `response_schema_order` option, default `canonical`, opt-in
`declared`; `json_schema_order_v1` capability; order-sensitive wire digest in
metadata. Canonical schema digest remains unchanged. Adapter inherits and cannot
replace an outer schema or its declared order. New local candidate version .3.

1. Add real HTTP tests for nested order, canonical compatibility, ownership,
   adapter inheritance/replacement and invalid admission; run RED.
2. Implement bounded ownership and transport of declared order; run focused and
   full Runtime tests, build a wheel and verify installed transport/identity.
   Expected: all pass; no weakened assertions or schema limits.

### Task 2: Frozen Lab profiles

Interfaces: `compact-question-first-v1` and `compact-question-focused-v1` are
explicit dataset generation profiles. Both require the new Runtime capability.
The first changes schema order only; the second focuses guidance on question
parts and distinct necessary claims. Existing profiles remain exact.

1. Add failing fixture tests for wire order, strict resolution, frozen identity,
   resume and capability admission. Implement question-first profile; verify.
2. Add focused guidance separately and verify complete source availability,
   canonical critic independence and unchanged strict validation/scoring.
3. Run full default Lab suite and installed candidate acceptance tests; build
   and qualify fresh checksummed wheels. Expected: all pass with defaults off.

### Task 3: Qualified Qwen preflight and evidence

Reuse the same model, three questions, source corpus, keys, retrieval policy,
60-second/4096-token calls, no tools/retries and strict scorer. Maximum 27
requests/884736 tokens, one shared allowance; unknown usage stops new calls and
retains its full reservation. Use the focused profile only after separate
mechanical verification of order-only behavior.

Run all nine samples only while allowance permits. Full 100-question live batch
is gated on all base/review answers accepted, known usage and semantic passes.
Preserve failures as results. Request one fresh final code review, fix important
findings with watched regression tests, collect source/build/test/live evidence
and a stable private archive. Expected: evidence reports actual outcomes, not a
claim of quality based on fixture or retrieval visibility alone.

Review focus: nested schema order and callback ownership; mode changes across
resume; order-sensitive workflow identity despite canonical JSON hashing;
source completeness and independent critic boundaries; truthful unknown usage
and retained old evidence. Leave changes local and uncommitted for review.
