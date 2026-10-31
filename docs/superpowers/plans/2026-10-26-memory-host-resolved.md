# Host-resolved question and frame bookkeeping

Approved scope: the user's request to implement the host-resolved format and
rerun the same Qwen diagnostic. Native execution in the existing isolated Lab
worktree; no SDK changes, publishing, default enablement or historical repair.

1. Add opt-in `compact-host-resolved-v1` with watched failing tests. Wire question
   parts retain exact quote and claim/missing-evidence references but omit numeric
   offsets. Resolve only a unique, exact Unicode substring, including overlapping
   matches; reject missing/ambiguous/normalized/empty quotations. No fuzzy match.
2. Wire frame reviews retain frame identity, reason and `unreferencedDisposition`
   (`duplicate`, `irrelevant`, `insufficient`). Derive `used` and claim IDs from
   exact selected evidence. Apply the supplied disposition only to frames without
   linked evidence. Retain every-frame coverage and reject extra/foreign fields.
   Used-frame claim IDs have deterministic claim-array order in this new profile.
3. Keep canonical schema and final validator unchanged. New-profile encoding of
   canonical drafts verifies semantic roundtrip, normalizing only the declared
   used-frame link order. Old profiles retain exact request/schema/prompt behavior.
   Bind profile and schema identity across freeze, review and resume.
4. Add focused negative/positive tests, public Runtime/Harness fixture coverage,
   documentation and an independent final review. Run focused and full Lab tests;
   build wheel/sdist, install into a fresh environment using qualified SDK wheels,
   verify package payload and run installed fixtures. Preserve existing envs.
5. Precommit one new 360-second Qwen diagnostic: same q001 packet, frames, model,
   sampling and 4096 output tokens; change only the explicit generation profile
   and corresponding prompt/schema. One request, 32768-token reservation, no
   retry/repair, strict canonical gate. Record cache usage; no cold/quality claim
   from a warmed mechanical pass. Preserve failed evidence and old reservations.

Verification focus: Unicode/overlap ambiguity, foreign evidence/frame identities,
duplicate IDs/JSON keys, missing frame coverage, contradictory legacy-field
injection, frozen source equality, draft encode/decode and Harness validation.

Execution ledger:
- Initial: scope approved; existing linked worktree reused; prior modes retained.
- Resolver: watched missing-profile failures, then 42 focused tests passed.
  Public SDK/fixture runner format mismatch reproduced before synthetic support;
  all 70 focused/candidate tests and 36 subtests passed afterward.
- Schema ownership: a watched mutation test exposed aliasing of canonical schema
  fragments; new-profile schema now returns an owned deep copy. All 22 new unit
  cases pass. Existing canonical schema and validator functions stay unchanged.
- Fresh final reviewer: no actionable findings in scoped implementation. Review
  excluded live results/packaging (verified separately), unrelated existing work,
  and documentation not yet written at review time (guide now added).
- Final verification: full released-SDK source suite 2187 passed +73 subtests;
  installed candidate lanes 92 passed +36 subtests; diagnostic fixtures 7 passed.
  All 238 Lab payloads and 133 payloads across seven qualified SDK packages match.
  Candidate default full-suite 45 guard/environment failures reproduce unchanged
  against the old installed package. No guards or assertions were weakened.
- Live: same frozen q001 packet, explicit new profile, one 360-second Qwen call.
  Timed out, first reasoning-channel text 184.731 s, no terminal content/usage.
  No accepted output or retry; full 32768-token/one-request reservation retained.
  All prior evidence and ten old reservation files reverified. Defaults remain off.
