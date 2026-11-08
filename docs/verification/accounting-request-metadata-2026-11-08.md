# Accounting request metadata implementation and qualification

Maintainer-authorized Runtime0.9.17 implementation/testing/merge/release and a new
Lab blueprint/release. Native plan/spec are in the Runtime repository under
2026-11-08-accounting-request-metadata. No live inference or Cerebro application
edits. Original dirty user checkouts/companion worktrees and historical release
bytes are preserved.

Lab preparation: unit RED4failed/5passed for absent family/resource; blueprint
RED30failed for absent resource/new SDK. Candidate environment explicitly uses a
local Runtime0.9.17 wheel, not a released artifact. Final published pins and
qualification are pending and cannot be inferred from those development tests.

New blueprint both-wire/file tests passed30; complete family/copy/history units
passed15. Host benchmark labels are separate from actual Harness UUID run IDs;
fixtures initially mixed them and were corrected while preserving the existing
identity refusal. Reopen tests retain original labels despite changed defaults/
caller labels, and adopt saved receipts without extra HTTP.

Five previous active manifest/provenance/freeze snapshots are preserved verbatim.
Historical selector registration was watched RED1failed/14passed then GREEN15.
Distribution routing and public build inventory were watched fail, then all56
focused routing/build/profile cases passed. The new PG file collects2required
both-wire cases; it has not run locally and no PG pass is claimed. CI must prove
restricted-role persistence/reopen/conflict/no-call recovery and exact database/
role cleanup on PG16/18 across both Linux architectures.

Before publication, replace this pending status with actual final source/counts,
published SDK lineage, all ten hosted jobs, original artifact/tree proof, anonymous
public downloads and wheel/rebuilt-source consumers. Active memory freezes refresh
only after real final SDK pins. No prompt/corpus/scoring or old snapshot changes.
