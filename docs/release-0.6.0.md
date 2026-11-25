# Integration Lab 0.6.0

Integration Lab 0.6.0 adds examples and acceptance coverage for released
Runtime 0.9.8 native and unified Claude Code, Codex CLI and local/API pools.
The pool selects eligible profiles before work starts, keeps native permissions
and API grants/budgets explicit, and requires proof of pre-work rejection before
switching after a provider failure. Partial or uncertain work is never authority
for automatic replay.

Start with the [unified pool guide](unified-runtime-pools.md),
[example configuration](../configs/unified-runtime.example.yml) and
[live benchmark recipe](realistic-runtime-benchmark.md). All live inference is
opt-in and requires private authenticated profiles and a bounded allowance.

## Released-wheel live observations

Two [Runtime 0.9.8 studies](verification/unified-cli-released-2026-10-24.md)
each passed 27/27 assignments: release brief, incident handoff and invoice SQL,
three trials per task/model. Latest medians were Claude Sonnet **11.37s**,
Codex gpt-6.1-sol at low effort **23.07s**, and local ThinkingCap Qwen 27B
**60.69s**. The preceding released study measured 10.38s, 23.61s and 66.21s.
Both used unchanged neutral Markdown, synthetic inputs and graders, with
native60s/local180s/pool300s deadlines and zero timeouts.

Each study verified 27 controlled cooldown skips and zero provider-triggered
fallback events, with all allowance entries known and owned cleanup verified.
Controlled selection is separate from the retained
[provider-rejection/no-replay fixture tests](verification/unified-provider-fallback-2026-10-23.md).
No quota exhaustion was induced. The small studies grade facts/workspace
integrity, not prose elegance; uncontrolled host/cache/provider conditions do
not establish a general ranking or isolate Runtime performance effects.

## Consumer examples and boundaries

This release also includes opt-in consumer blueprints for
[failure isolation](failure-isolation.md), [tool approval](tool-approval.md),
[trajectory evaluation](trajectory-evaluation.md) and
[sandboxed CLI admission](sandboxed-tools.md). They preserve application-owned
authorization and uncertainty, and consume public installed SDK interfaces.
The disabled-by-default [Castle example](castle-quickstart.md),
[agent-quality](agent-quality.md) and [retrieval-memory](retrieval-memory.md)
experiments retain their separate qualification and capability limits.
Memory and correction remain experimental; historical model evidence is not
rebound to this release. No new memory-efficacy claim is made.

The pinned public SDK train is Core **0.4.1**, Runtime **0.9.8**, Runtime recorder
**0.3.0**, Harness **0.9.4** and Harness store **0.4.0**. Use the checked-in
[manifest](../dependencies/releases.json) and locked install/audit commands.
Archived manifests, SDK profiles and freeze snapshots preserve their original
bytes and lineage. The active memory qualification explicitly records its
new SDK provenance without changing the task corpus or old measurements.

## Release artifacts and qualification

The [GitHub release](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.6.0)
provides the original qualified CI wheel and source archive, plus
`SHA256SUMS-0.6.0.txt` and `VERIFICATION-0.6.0.json`. The verification record
identifies the exact source, successful four-cell acceptance run, SDK manifest,
archive hashes and per-cell case/cleanup results. Check those assets before
installing a downloaded artifact.

Required qualification includes full source regressions, installed native and
unified acceptance, ordinary public-index SDK adoption, clean Lab wheel and
rebuilt-sdist consumers, and all nine real-stack lanes on Linux AMD64/ARM64 with
PostgreSQL 16/18. ARM64/PostgreSQL 16 additionally exercises the clean-sdist
service stack. Missing infrastructure and incomplete receipts fail the gates.
Private live reports, credentials and raw operational state are excluded from
the release artifacts. Release preparation performs no additional live calls.
