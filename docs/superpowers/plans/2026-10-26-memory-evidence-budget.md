# Evidence selection and canonical byte budget

User-authorized scope: fix evidence over-selection without sacrificing completeness,
retain the canonical 16384-byte limit, and rerun the same one-case 600-second Qwen
diagnostic. Memory/SUE default off. No publication, retries or historic edits.

Observed cause: all 80 indexed paragraphs were selected and linked to each of five
claims; the 8283-byte wire expanded to 45260 canonical bytes. The compact request
did not expose canonical expansion costs. No unused-evidence pruning would help.

Small change: the explicit host-resolved profile receives advisory evidenceBudget
metadata outside the unchanged source packet, with exact host-serialized per-quote
and per-citation costs. Guidance requires minimal sufficient, claim-specific
support and reuse, preserving all distinct facts, qualifiers and contradictions.
No count cap, filtering, ranking, gold facts, pruning, retries or validator changes.

- [x] RED: tests for cost accuracy including Unicode/escaping, identical source
  indexes, multiple necessary supports retained, legacy guidance unchanged, and
  unchanged canonical size rejection. Preserve failing output.
- [x] GREEN: generation.py only, host-resolved request metadata and guidance.
- [x] Verify focused + full released-SDK suites and installed candidate workflows;
  build and compare wheel/sdist/install payloads. Fresh review of the small diff.
- [x] Freeze new operator protocol: same case, frames, schema, Qwen model, temp0,
  max4096 output, 600-second Runtime/615 observer, one request/32768 tokens.
  Only evidence guidance/cost metadata and code identity differ. Unknown usage
  retains the whole new allowance, all 11 old unknown reservations stay untouched.
- [x] Run once, validate without repair, preserve failures and explicitly distinguish
  mechanics from semantic completeness. Seal/archive with exact-file verification.

Execution uses the existing isolated worktree. The explicit user request authorizes
the small implementation and live comparison. Product SDKs and canonical validator
stay unchanged. Tests are synthetic; private live evidence stays outside Git.

Result: full2192 +73 subtests; installed97 +36 subtests; operator7. Fresh review
clean. Live297.170s, known14388 tokens, canonical5233 bytes/four evidence/five
claims. Original answer facets2/2 under author exact-proof adjudication. Residual
duplicate support and one inconsistent frame-review reason remain documented.
All prior reservations/evidence preserved; sealing uses a manifest-listed copy.
