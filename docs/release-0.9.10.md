# Lab0.9.10 — accounting request metadata blueprint

Adopts actual published Runtime0.9.17 with exact public URL/source/SHA256 while
retaining Core0.5.0, Harness0.9.12 and the original recorder0.3.0/store0.4.1 bytes.
All prior releases remain immutable. Previous active manifests/public SDK profile/
memory freezes are preserved verbatim as pre-accounting-metadata; only active
provenance/freezes advance. Corpus, prompts, scoring and live evidence are unchanged.

Adds a copyable `accounting-metadata` host, [guide](accounting-request-metadata.md),
installed both-wire acceptance and required real PG recovery. Trusted benchmark
run/variant labels are visible to recorder prepare before dispatch through the
versioned optional context extension, without raw request/prompt/header disclosure.
The host keeps benchmark labels separate from actual workflow UUID identity and
filters public state. All five earlier blueprint resource bytes stay intact.

**Compatibility/identity:** Empty metadata preserves exact legacy accounting
bytes/hashes; nonempty labels intentionally change accounting payload hashes and
sealed private contexts/receipts. No artifact/rule, prepared-turn or workflow/
bundle identity fields move. Saved Harness labels win despite new caller labels
or changed defaults; a new variant needs a new run. Same-intent replay remains
idempotent, same-call relabeling conflicts, and saved-receipt recovery is no-call.
Published recorder0.3.0 needs no DDL/new privileges/republish or old-row rewrites.
New labeled records need Runtime>=0.9.17 readers; old unlabeled records stay valid.
Metadata never grants authorization/rates/billing eligibility or retry consent.

Release requires fresh final source/frontend checks; ordinary public-index and
wheel/rebuilt-source distribution gates; all four LinuxAMD64/ARM64×PG16/18 ordinary
cells; all four installed rule/feature/PG cells; and both reasoning jobs. Exact
owned resource cleanup and restricted runtime-role persistence are mandatory.
Missing infrastructure fails rather than skipping. Local candidate/synthetic
checks do not replace hosted final-train evidence or certify live providers.

Require exact-head overall CI SUCCESS, original CI ZIP/source payload/count
verification, expected-head merge and equal tested/merged trees. Publish only
original successful CI wheel/source archives with sanitized qualification evidence,
then anonymous downloads, fresh installed wheel/rebuilt-source consumers and all
post-merge CI. Preserve earlier package bytes/tags/assets. No live inference.

Historical baseline downloads retain their exact manifests and checksums. A
bounded anonymous GitHub asset API fallback handles a diagnosed canonical-route
gateway failure; unavailable/mismatched/corrupt assets still fail qualification.
