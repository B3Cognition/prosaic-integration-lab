# SUE design review — 2026-10-24

Reviewed the original design/plan commit `58a647c`, then revised both documents.
Two independent reviewers checked SDK/recovery feasibility and source/ownership/
reporting contracts. This is a design review, not implemented workflow acceptance.

## Findings and corrections

1. **P1: Required dependencies grew exponentially and prevented fourteen turns.**
   Original design lines 115–117 and plan lines 136–138 required every previous
   answer at every step. Public Harness recursively copies prior bindings into
   each accepted binding, then serializes those trees into the next invocation.
   The retained probe reproduces rejection at turn 12: **301,122 argument bytes**
   against the unchanged **262,144-byte** cap, with empty answers/request. At turn
   14 the original structure reaches 1,204,324 bytes. Corrected graph requires
   only the immediate predecessor and transports older answers as optional
   inputs. Their full ordered presence is still mandatory in host folding and
   validation; the required chain transitively preserves freshness. The same
   minimal turn-14 probe is **13,553 bytes**. No size cap or source check weakened.

2. **P2: Active-time promise did not match the SDK deadline.**
   Original design lines 150–152 and plan line 31 claimed 900 active seconds.
   Harness sets an absolute deadline at run creation; approval waiting and offline
   time consume it. The revised design explicitly uses a **900-second wall-clock
   lifetime**, without clock resetting on resume. An expired zero-call approval
   remains zero-call and needs an explicit new review. Longer asynchronous
   approval/active-time accounting would require a separate supported design.

3. **P2: Retry consent could not recover missing receipts under the token guard.**
   Original design lines 173–177 and plan lines 165–169 promised explicit retry
   consent plus another slot. Harness retains an abandoned attempt with unknown
   usage, then blocks on usage_unknown under the mandatory max_tokens guard.
   Version 1 now exposes **no missing-receipt retry path**. Recoverable receipts
   can be adopted without repeating that attempt; missing receipts retain the
   stop and original uncertainty/reservation. Accounting rows are not substitute
   workflow receipts. Later legitimate steps may execute only within the
   original approval/deadline/remaining limits.

4. **P2: The specified request digest omitted provenance-only changes.**
   Original design lines 108–111 enumerated text/line inputs without explicitly
   including retained revision/reference and Castle provenance. Revised identity
   covers complete frozen source records, original bundle identity and trusted
   host capture context as well as seed/lens/policy/engine. The plan now tests
   revision/reference/provenance/scope-only conflicts with identical text.
   This was a specification gap, not an observed consumer implementation bug.

Two related implementation requirements are now explicit:

- A bare Castle SourceBundle has no owner/namespace attestation. The trusted
  capture operation attaches registry-derived identity and scope; its hash does
  not authorize a caller. Memory's existing internal scope/revision checks remain.
- RuntimeAdapter clears failed stdout. Preserve available within-limit output in
  private metadata with the failed result; oversized output gets a digest/length
  and bounded diagnostic. Never turn failure into success to preserve text.

The design also specifies the full frozen-input cap independently of raw text
size and retains versioned read-only bindings independently of the enable flag.
Absent retained bindings are explicitly unavailable, never a reason to dispatch.

## Evidence and method

The [contract probe JSON](data/sue-design-contract-probe-2026-10-24.json) records
all fourteen sizes for both dependency shapes, public wheel hashes, admission
of a generic 32-step graph, paused deadline expiry and abandoned unknown-usage
classification. Original probe source/raw output are retained locally under
`reports/sue-design-review-20261024/`, with hashes in the committed record.

The probe placed all five original public SDK wheels ahead of installed modules
on Python's import path and verified every wheel against dependencies/releases.json.
It executed no provider calls, Runtime invocations, store operations or SUE
dialogues. It built generic declarations and exercised bounded serialization
and resource classification only. No monkey-patching of installed SDKs was used.

Key source evidence inside the exact public wheels:

- Harness 0.9.4 engine.py: binding construction lines 720–724; invocation snapshot
  lines 791–806; ledger/freshness lines 516–543; absolute deadline lines 380–387;
  unknown usage and token guard lines 545–557; missing-receipt recovery 488–507.
- Runtime 0.9.8 adapter.py: failure stdout clearing lines 124–128, public adapter
  and one-execute callback contract below that block.
- Castle source 58f4242 memory_types.py: SourceBundle and MemorySource definitions;
  memory.py snapshot identity includes both source metadata and texts.

The SDK reviewers also verified installed engine.py/factory.py/adapter.py byte
equality against those exact public wheel payloads. Distribution version labels
alone were not treated as artifact identity.

## Assessment and remaining proof

The corrected boundaries remain appropriate: optional advisory consumer in Lab,
existing pure SUE policy in Castle, single model attempts in Runtime, accepted
state/recovery in Harness, and no SUE/SOAR in memory retrieval. Memory and review
remain independently disabled by default. The existing Castle PR heads and r7
release selection were not changed.

The initial builder check missed these SDK-specific problems; it does not
replace this deeper contract review or implementation testing. The corrected
design was rechecked by both reviewers; neither found a remaining important
contradiction in its SDK/recovery or source/authorization scope. Minor wording
was aligned for bounded output preservation and canonical numbered-step order
independent of JSON map insertion. The design is feasible at the checked
contract/admission level. Complete fourteen-
turn SUE execution, byte-limit boundaries with real content, full optional
dependency installation, crash recovery, PostgreSQL/platform CI and wheel/sdist
consumer tests remain implementation acceptance requirements. Synthetic answers
will not establish live review quality, speed or benefit over one-pass review.
