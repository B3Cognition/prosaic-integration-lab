# Host-resolved answer-span transport implementation

Approved intent: the maintainer's “Ok proceed” following the recommendation to
fix proof addresses/ID constraints and qualify full-size latency. Execute inline,
with a fresh design builder check and one final implementation review. Do not
repeat authorization questions already answered by that instruction.

Spec: `docs/superpowers/specs/2026-10-31-answer-span-host-refs-design.md`.
Base: d7c55ac. Reuse the existing attached isolated worktree and draft PR38.

## Task1: frozen reference catalog and codec

Create `lab_runner/answer_span_refs/{__init__,contracts}.py` and
`tests/unit/test_memory_span_audit_refs.py`. Never edit the legacy audit package.

Produces: `RefsPacket`, `freeze_refs(review)`, `canonical_packet(packet)`,
`catalog(packet, include_answer=False)`, `source_view(packet)`,
`answer_view(packet)`, `ledger_schema(packet)`, `audit_schema(packet,ledger)`,
`resolve_ledger(wire,packet)`, `resolve_audit(wire,packet,ledger)`.
Catalog has immutable serialized proof maps and source/answer model views;
callers receive owned copies. No draft-dependent field in source view/schema.

- Watch absent module failure, then implement packet/catalog and exact lossless
  source reconstruction with Unicode/CRLF, aliases and no header proof.
- Watch unknown/wrong-kind/duplicate reference failures; implement closed wire
  decoding, finite IDs and canonical resolution through unchanged validators.
- Test wrong draft part key in audit schema, exact selected citations, full
  claim coverage, false limitations, contradictory status, packet mutation and
  wire/canonical/envelope byte limits. Both schemas fail closed on extra keys.

## Task2: native two-stage workflow and evidence

Create `lab_runner/answer_span_refs/{workflow,fixture,__main__}.py`, and
`tests/memory_benchmark_candidate/test_span_audit_refs.py`.
Consumes Task1 functions. Produces `build_workflow(config,packet,directory)`,
`run_audit(config,packet,directory,accounting=None)` and explicit fixture CLI.

- Watch real loopback workflow failures before implementation. Generate with
  wire schemas, persist native results, resolve only successful outputs, bind
  accepted envelopes to records and revalidate canonical values with v1 checks.
- Test all four native fixture cases, failed wire/proof preservation, no retries,
  raw/envelope/catalog/endpoint-feature tampering, unknown hold and zero-call
  completed resume. Never fabricate successful Results or alter native usage.
- Keep common lifecycle logic within consumer code; reuse existing local
  accounting checks where appropriate; import no private SDK engine APIs.

## Task3: package/docs/CI and complete verification

Update audit CI paths and qualify installed refs fixture commands beside existing
commands. Extend the CI golden without replacing existing assertions. Add
`docs/answer-span-resolved.md`, link from README and add a current handoff entry.

- Require all legacy protected package bytes unchanged from base. Run relevant
  legacy/new tests, then full released/candidate profiles with complete executed
  union and zero skips. Build direct/sdist-rebuilt wheels; verify installed
  isolated fixtures, raw records, same limits and disabled defaults.
- Get one fresh whole-change review; fix Important/Critical findings with watched
  regressions and green suites; record deferred minors. Commit/push related
  changes and retain exact-head CI evidence. Do not merge/publish.

## Task4: one fresh full-payload qualification

- Preserve/check all32 earlier archives and14 holds. Reuse packet029's original
  canonical context/draft under a new refs-profile packet and separate private
  authorization/allowance; never change earlier evidence or retry packet028.
- Declare2 calls/65,536 tokens/270s,120s per call,4,096 output tokens,16,384 bytes
  per wire/canonical/envelope stage,0 tools/retries. Record read-only serving
  fingerprint, exact installed payloads/input sizes, stage latency/native usage.
- Stop on unknown/timeout/overrun/drift; preserve all holds and failed evidence.
  Successful completion must verify original unchanged and zero-call resume.
- Seal a new durable private archive. Report mechanics/performance separately
  from semantic quality and leave defaults off and PyPI unpublished.

Review focus: a reference must not manufacture semantic support; source-view
deduplication must be lossless; dynamic schemas must use accepted ledger IDs;
raw native output/usage must survive host adaptation; envelope/raw/catalog
tampering cannot permit resume/dispatch; both byte ceilings remain strict;
legacy code/bindings and default modes remain unchanged.
