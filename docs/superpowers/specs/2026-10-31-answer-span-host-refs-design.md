# Host-resolved proof transport for the optional answer-span audit

The maintainer approved host-resolved proof addresses, stage-specific identifier
constraints and full-payload latency qualification after the stopped comparison.
The original source ledger changed question ranges/source whitespace, a later
audit confused draft and ledger question-part IDs, and a subsequent audit call
timed out with unknown usage. Preserve that run and all fourteen logical holds.

## Ownership and compatibility

Add `lab_runner.answer_span_refs`, an independently selected experimental host
transport profile. Keep every file under `lab_runner.memory_benchmark` and the
protected critic byte-for-byte unchanged. Existing APIs, modes, frozen bindings,
package version and released SDK pins remain unchanged. Memory and SUE default
off; SOAR, retrieval, author generation and repair remain outside this path.

Runtime executes the two constrained model calls; Harness persists acceptance
and accounting; Lab resolves finite proof references. Use installed public SDK
APIs only. No copied library engines, monkey-patching, fuzzy quotes or automatic
retry. No merge or PyPI publication.

## Frozen inputs and proof catalog

`freeze_refs(review_packet)` wraps an unchanged v1 AuditPacket with a new profile,
resolver/schema/source binding and immutable digest. Reconstruct and validate the
original packet through its existing public functions; never modify a historic
packet to fit new code. Changes to inputs, SDK payloads, resolver, wire schemas,
endpoint features or policy refuse resume.

The source stage sees the exact question and all authorized source body text,
without draft text, selected citations, canonical draft segmentation or labels.
Offer host references for the full question and its non-whitespace tokens.
For source bodies, cut only at existing body/independent quote-candidate bounds.
Deduplicate exact body text, preserving every occurrence, body order and source
address as aliases. Present each unique body's ordered text fragments once with
opaque IDs. Rejoining fragments must exactly reproduce every original body,
including Unicode and CRLF; nothing is summarized, omitted or truncated.
Headers/metadata are addresses, not facts. References resolve to frozen full-frame
hashes and exact character ranges inside an authorized body.

After the source ledger is accepted, add references for actual complete claims,
limitations and the exact selected citation spans. These draft-dependent
references never enter the source stage. A reference cannot change kind, source,
scope, text, digest or range. Reject unknown, duplicate and wrong-kind references.

## Wire forms and canonical validation

The model emits reference IDs instead of hashes, offsets or copied quotations.
Source ledger question-part and obligation IDs come from finite host pools (16
and 32); their membership and semantic rules still pass the existing validator.
Audit obligations, claims and question parts are closed objects keyed by the
accepted ledger/original claim IDs. Each claim's citations are a closed object
keyed by its exact selected evidence IDs. Required keys ensure full membership;
no draft question-part ID can substitute for a ledger key. Rename displayed
draft segmentation to `draftCoverage` to distinguish its role.

The host supplies only identities and exact proof addresses. It never supplies
a verdict, proposition, coverage judgment, reason, source selection or repair.
Resolve wire output into the original canonical ledger/audit shape and invoke
the unchanged `validate_ledger` / `validate_audit`. Preserve all selected-citation,
positive full-claim coverage, scope, limitation, conflict and status checks.
Structurally valid references do not establish semantic truth or completeness.

Persist the exact native Result before host transformation. Harness accepts a
closed envelope containing the canonical object and the raw-record/catalog/wire
schema digests. Validators re-resolve that raw record and require exact equality;
dependent model stages receive its validated reference ledger, with its canonical
form retained in Harness. Accepted-result metadata also binds the raw record.
When a native policy failure discards host metadata, a separate capture seal
binds raw bytes and the native snapshot for blocked-run inspection only; that
capture can never become accepted proof. Native usage/timeout/error evidence
remains intact. Refuse changed records, envelopes or catalogs before resume;
never convert a failed or unknown native call into successful execution.

## Limits and lifecycle

Keep two calls, 120s/call, 270s/audit, 65,536 reported tokens, 4,096 output tokens,
zero tools and retries. Wire, expanded canonical object and accepted envelope
each have a 16,384-byte maximum; envelope overhead therefore counts against the
same stage ceiling. No truncation or fallback to accepting raw canonical output.
Keep the 262,144-byte packet/input ceiling and existing part/obligation limits.

Completed resume is zero-call. Blocked/unknown runs never redispatch. Preserve
the complete reservation on unknown usage/completion and compare accounting to
native receipts. Binding failures refuse before dispatch. Public result retains
the original answer and a separate accepted canonical sidecar; raw state remains
operator-only. Explicit fixture CLI cases cover omitted, complete, unavailable
and unknown usage; invocation without a command executes nothing.

## Verification and qualification

Use watched regressions for wrong copied question ranges/source whitespace and
ledger-versus-draft IDs, plus forged IDs, wrong kinds/scopes, duplicate keys,
headers, selected-citation escapes, false positive coverage, contradictory
status, unknown usage, over-limit expansion, raw-record tampering and resume.
Prove lossless reconstruction and source-stage draft independence. Compare v1
protected bytes and behavior before/after. Run both SDK regression profiles with
executed default coverage, installed direct/rebuilt wheels and fixture cases.

Then prepare one new full-payload qualification using the original, known-usage
packet029 context/draft. Do not retry unknown packet028. Keep labels/scorer and
the original46-case cohort immutable. Predeclare two calls/65,536 tokens/270s,
120s/call,4,096 output tokens and16,384 bytes/stage,0 tools/retries; no new46-case
comparison. Verify current serving metadata and pin its effective settings.
Stop on unknown usage, timeout, overrun or drift and retain the new hold.
Record actual projected bytes, stage latency, native tokens, acceptance and
zero-call replay. Cache-dependent timing cannot establish causal speedup.
This qualifies transport/performance only; packet029's semantic label remains
disputed and no answer-quality/repair improvement follows.

Builder calls: exact catalog enumeration and finite ID names, envelope encoding,
public API factoring, fixture organization and test distribution are implementation
choices. Choose fail-closed behavior when a bound cannot be met.
