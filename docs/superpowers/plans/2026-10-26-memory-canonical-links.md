# Unique evidence and host-owned frame usage

Authorized: fix duplicate evidence and inaccurate frame-review reason, retain
strict validation/16384 canonical bytes, and rerun one identical-case 600s Qwen
diagnostic. Preserve evidence/reservations; defaults off; no publication.

Root cause: aliases allow one quote under multiple evidence IDs; free-text reason
duplicates host-computed used status and can contradict it. A regex cannot safely
validate arbitrary prose usage assertions. Post-generation dedup/rewriting would
conceal invalid raw answers. Use an explicit new wire profile instead.

`compact-host-canonical-links-v1`: evidence is a unique list of host quote IDs;
claim evidenceIds reference the same IDs. No alias remapping during resolution.
FrameReview wire entries contain frameId/unreferencedDisposition only. The host
derives canonical reason/used status/claimIds deterministically from exact links;
unused classification stays model-owned and is labeled as such. Free-form model
frame explanations are absent in this mode; it provides bookkeeping reasons,
not a semantic explanation of relevance. All frames still require a review.
Other profiles, their schemas/prompts and canonical validators stay unchanged.
Encoding a valid canonical draft may rename evidence IDs to exact quote IDs for
transport, preserving all support links; duplicate exact quote aliases fail closed.

- [ ] RED: duplicate quote rejection, no contradictory reason field, exact host
  reasons for used/unreferenced frames, source provenance distinctions retained,
  all required supports/facts preserved, prior modes byte-identical.
- [ ] GREEN: generation profile/codec, prompt selection, synthetic fixture support.
- [ ] Full released-SDK suite, installed candidate workflows/resume, package/source
  equality, observer fixtures and fresh scoped review.
- [ ] New one-request32768-token protocol, same frozen q001/manual packet, Qwen,
  temp0/max4096, Runtime600/observer615. Profile/wire ownership explicitly changed;
  sources, scope, canonical contract, scorer and 16384-byte limit unchanged.
- [ ] Run once, exact-proof author completeness check, manifest seal/private copy.

Existing isolated worktree reused. Runtime/Harness/Castle/SUE unchanged. Preserve
all prior model outputs; do not reinterpret old answers under the new schema.
