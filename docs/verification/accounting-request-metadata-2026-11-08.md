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

## Final public SDK train

Runtime0.9.17 [PR22](https://github.com/B3Cognition/prosaic-runtime/pull/22)
merged/tagged source `eb0735e7cc2e70fdcff2fccd0bc80b3ec2850f0b`.
[Qualification42460821009](https://github.com/B3Cognition/prosaic-runtime/actions/runs/42460821009)
verified24required records and exact Core0.5.0 lineage. The promoted wheel SHA256
is `6ec49b8f94bac7c025fb4231ca4b1f64bd1d07d10caa82b1c69c5b18d67f4f33`;
source archive SHA256 `ec38b7478632c2a1e0f55f5bf98f341374e0d806d8160e999273d72c4019f419`.
Actual anonymous PyPI/GitHub bytes and original receipts/checksums match.
A fresh ordinary PyPI resolver installed original public companions, then117
installed metadata/compatibility cases, six synthetic smokes and pip check passed.
The immediate post-upload PyPI propagation race was diagnosed by strict matching
public downloads before one failed-job recovery; publication attempt2 succeeded.
No artifact was replaced. Merged Runtime overall CI is SUCCESS.

Only Runtime's active public pin advances. The other four exact SDK artifacts,
all five pre-metadata snapshots and all53previous blueprint resource files remain
unchanged. Current freezes retain corpus/prose/history/suite digests. New final
profile/freeze assertions had4watched failures, then44focused cases passed.
One additional strict active-pin assertion still expected0.9.16; its exact
version/source/hash expectations now select the verified0.9.17 while retaining
all four companion assertions. Its complete targeted file passed.

On macOS ARM64/Python3.12, actual-public-train native/reasoning controls passed46;
installed wheel rule cases passed141 and feature cases97 (including33metadata),
with pip check. Earlier Explorer16/browser10passed with current assets. A fresh
whole-branch consumer review found no Critical/Important defects; a minor Harness
field-versus-intent-envelope documentation error was corrected. Required hosted
PG cells and final full-source/distribution/public-consumer/post-merge evidence
remain release gates; no local Docker/PG pass or live-provider claim is inferred.

The actual-public-train isolated distribution command also passed wheel and
rebuilt-source consumers, ordinary public-index adoption, import/payload audits,
pip check and temporary cleanup. It did not run the unavailable local stack.
Eight required PG cases collect, including two new metadata cases; only hosted
infrastructure can certify their execution. The final source archive/CI proofs
must bind the exact final branch tree and retain the first stale-assertion failure.
