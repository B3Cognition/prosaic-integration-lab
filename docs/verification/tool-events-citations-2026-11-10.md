# Safe events and citations: unpublished candidate verification

The implementation is confined to safe tool events, captured evidence and citations.
Parallel tool calls, MCP clients and sub-agent orchestration remain separate work.
No release tags, publication, stable manifest replacement or hosted promotion runs
were performed. The new manual workflow qualifies only the feature lane.

## Exact SDK handoff

| SDK | Source | Original wheel SHA256 |
| --- | --- | --- |
| Runtime 0.9.20.dev1 | `524758001da0d768e398aa51b1a97812adf09032` | `9f6168078a8d8bfe3d45366877fa5ce8a0d06b05057b5415edadf1c48df63462` |
| Harness 0.9.14.dev1 | `eb0562bccd3df5dad3c5c4394a8d0ea580e361ec` | `ac5e360041166fa4a9ba7e629a591f9299174f3bd9b677697a50680dd45584da` |
| Harness PostgreSQL 0.4.3.dev1 | same Harness source | `57c9a4ec9f8b1099d43a8436fc41f5a16d00c1ca452c02bc5478a6cf3ebbe309` |

Core 0.5.0 and Runtime PostgreSQL 0.3.0 retain their original published bytes.
The local five-wheel handoff manifest has digest
`ed913a34d8000303ddf8edb62d38c4d9d579c276056e386addb1f24201c262aa`.
Its provenance explicitly says `local-tool-contract-handoff`; it contains source
and qualification receipts without inventing hosted run IDs.

Runtime source checkpoint: 2,817 passed, two existing platform skips.
Harness source checkpoint: 1,514 passed, six existing skips. The installed-only
consumer passes on both API protocols, including saved-receipt adoption with zero
new provider/tool work, and passes again using a wheel rebuilt from the retained
Harness source distribution. The installed Lab wheel copies all seven declared
blueprint resources and executes the SDK host without checkout imports.

Harness owned storage/schema/migration checks: 52 passed each on PostgreSQL 16 and
18. Explicit namespace opt-in is required. Workers cannot migrate schemas; readiness
is read-only. File marker, fencing and existing recovery regressions also pass.

## Focused consumer lane

`python -m lab_runner test --mode tool-evidence --candidate --candidate-manifest PATH
--consumer-image sha256:IMAGE --postgres-version 16` runs 12 logical cases over
`openai-compatible` and `anthropic`: 24 required cases, zero required skips.
Repeat with PostgreSQL 18. Build the image with `scripts/build_consumer.py` from the
same verified candidate manifest. The copied blueprint is `tool-evidence`.

The local ARM64 lane passed all 24 cases on PostgreSQL 16 and 18; both runs verified
cleanup and the installed payload audit. Consumer image:
`sha256:f939d38dde23936d8fec30693e0622edb9d5767e46058c1d1ec5662cc5b9b4d4`.
Owned run IDs: `1438edce1f1047fb8dac7f412c8df8e6` (16),
`241d8b3ffafd44038a680a7d12e8f90a` (18).
The added manual hosted workflow specifies AMD64/ARM64 × PostgreSQL 16/18; hosted
runs have not been dispatched. Local results do not claim hosted qualification.

The general Lab unit suite continues using its pinned stable SDKs. Existing
agent-quality/retrieval studies deliberately refuse unqualified development
versions. Candidate-specific unit/blueprint tests are gated outside the feature
lane; required owned acceptance calls capability admission directly and cannot skip.

The cases cover approved/denied event display, unchanged legacy returns, typed
output admission, fabricated references, selected inline evidence, exact partial
reads and index-only refusal, journal replay with one effect, receipt adoption,
revoked retained sources, guard isolation from metadata numbers, and unsupported
or forged delivery. Synthetic protocols establish disclosure and durability
behavior; they do not measure live-model semantic citation quality.
