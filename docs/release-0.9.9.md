# Lab0.9.9 — workflow enforcement blueprint

Adopts the actual published Harness0.9.12 wheel with exact public URL, source
commit and SHA256, while retaining published Core0.5.0, Runtime0.9.16,
recorder0.3.0 and store0.4.1 bytes. No upstream engine or adapter is republished.
Prior active manifests/public SDK profile/memory freezes are archived verbatim
as `pre-workflow-enforcement`; older selectors, corpus, prompts, scoring and
historical/live evidence remain intact. Only active provenance/freezes advance.

Adds the separate `workflow-enforcement` blueprint, installed acceptance and
[guide](workflow-enforcement.md). It demonstrates content-versioned Guards bound
to final-review tags, access to accepted first-review/revision outputs, bounded
repair, explicit human acceptance, stale/version refusal and no-call receipt
recovery. Existing Validator V1, request headers, fee formats and input-cap
blueprints remain supported. New features require a blueprint, installed tests
and guide per the [feature map](feature-blueprints.md).

**Identity/readmission:** Harness seals used Guard declarations, compiled rule
material, logical root and workflow-guard-input-v1 facts. Empty/unused additions
preserve untagged identity; tagged bindings and changed implementations require
fresh admission. Every present optional guard input remains an output dependency.
Private receipts add bounded fact/context hashes and IDs-only proof; no new
checkpoint schema or implicit session migration. Runtime/Core identity rules
remain unchanged. The two invocation caps are explicit; no independent repair
allowance or extra request is inferred from a failed rule. Unsupported guarded
acquisition/terminal/args interpolation/required read receipts refuse before effects.

Require final source/frontend checks, public-index/distribution gates, all four
Linux AMD64/ARM64×PG16/18 ordinary cells, all four installed rule/feature cells,
and both reasoning jobs. New file/PG recovery must retain accepted/refused rule
proof across a reopened store without a new HTTP request. Missing required
infrastructure fails; local source/candidate checks never substitute for it.

Require exact-head overall CI SUCCESS, expected-head merge and equal qualified/
merged trees. Publish original successful CI wheel/source archives and safe
qualification evidence; verify anonymous downloads and fresh wheel/rebuilt-source
consumers, then all post-merge CI. Keep previous release assets/tags immutable.
No live inference or production-provider certification is included.
