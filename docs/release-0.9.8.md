# Lab 0.9.8 — current SDKs with feature blueprints

Adopts actual published Core 0.5.0, Runtime 0.9.16 and Harness 0.9.11, retaining
the original public recorder 0.3.0/store 0.4.1 bytes. Both active manifests bind
exact archive URLs, source commits and SHA256. No local candidate becomes a
released dependency, and SDK-release adapter witnesses are not republished.

Every added capability has a copyable example, installed acceptance and a
linked guide. See the [feature map](feature-blueprints.md):

- Per-call headers for OpenAI-compatible run/turn/prepared calls, with actual
  wire/header/body isolation and tool-continuation checks.
- Versioned cross-step review V1 using accepted first-review/revision outputs,
  bounded repair, human approval, stale/version refusal and no-call recovery.
- Value-guard v2 fee formats: `1.20 EUR`, `1.20 euros`, `120 cents`. All three
  former active-lane xfails are now ordinary required passes on both wires.
- An executable input-cap example showing ordinary and interpreter limits and
  refusal at the tighter cap. The underlying visibility API arrived in 0.9.10.

`python -m lab_runner.blueprints list` and `copy NAME DESTINATION` make the
examples available from both installed formats. Destinations are never replaced.
The review policy is the released Harness example, with an isolated-copy runner;
no SDK engine or private API is copied. Provider runners require explicit live
opt-in, and all qualification uses credential-free owned synthetic fixtures.

## Identity and migration

Runtime 0.9.15 advances the value guard to `value-in-tool-output-v2`; readmit
affected bindings when moving from the old Runtime 0.9.14 train. Never resume an
old guarded execution under changed bindings without the SDK's explicit
readmission. Header options add no persistent identity fields and must be
supplied afresh per invocation. The new workflow blueprint owns its schema,
prose and semantic/content validator identity. Existing sessions keep their
original policies; cap inspection is not a session migration.

Previous active manifests, public SDK profile and both memory freezes are
archived byte for byte as `pre-cerebro`. Historical profiles remain selectable.
Only current provenance/freezes advance; existing corpus, prompts, scoring and
live evidence are unchanged. Closed admission still refuses partial mixtures.
Workflow enforcement tags and the other deferred Cerebro requests remain the
separate SDK backlog; this release exercises the approved validator V1.

## Qualification and publication

The [verification ledger](verification/cerebro-sdk-blueprints-2026-11-07.md)
records observed results and remaining gates. Require all four ordinary native
Linux AMD64/ARM64 × PostgreSQL 16/18 cells, four installed rule/feature cells and
two reasoning jobs. Installed distribution consumers must exercise copied
blueprints from both the wheel and a rebuilt source archive, with SDK ownership,
public-index digest and cleanup checks intact. Required missing infrastructure
fails; source-only skips are not substitutes for stack evidence.

Review the complete final branch before one final push. Require exact-head
overall CI SUCCESS, expected-head merge and equal tested/merged trees. Publish
only original successful CI archives for the next free version, with sanitized
qualification and checksum records. Preserve every historical tag/asset; verify
actual anonymous downloads and fresh wheel/rebuilt-source consumers before
marking publication complete. Synthetic qualification is not live-provider or
production-deployment certification.
