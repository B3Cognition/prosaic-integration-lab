# Lab 0.9.2 — reasoning effort and reusable blueprints

Adds installed-SDK checks for the reasoning controls released in Runtime 0.9.12,
plus copyable canonical agents, API/native configurations, a strict answer schema
and an API-backed Harness workflow. Core inspects prose, Runtime owns execution
controls and Harness owns admitted workflow state. Native execution does not
require copying Prosaic prose into vendor folders.

Start with the [reasoning guide](reasoning-effort.md). Its dedicated manifest
selects Core 0.4.1, Runtime 0.9.12, recorder 0.3.0, Harness 0.9.4 and store 0.4.0.
The ordinary Lab manifest retains Runtime 0.9.8 and its original SDK bytes;
existing service/quality provenance guards are not weakened or silently updated.

## Reasoning controls

The seven agents differ only in effort metadata: none, low, medium, high, xhigh,
max and ultra. Actual support depends on the selected provider/model. Fixtures
inspect OpenAI-compatible JSON and owned Claude/Codex CLI arguments, including
unsupported-level rejection, profile precedence and omitted effort.

Gemma's supported positive values select the same native on switch; none is off.
Verified local ThinkingCap Qwen uses its template switch plus supported native
tiers. Ultra remains Codex-only and may enable vendor subagents. An HTTP success
or correct answer alone does not prove that a server honored thinking.

## Live runs and evidence

Real inference is explicitly opt-in. Each planned batch reserves shared allowance
atomically before dispatch; exhaustion sends no request. Completed observations
survive execution exceptions, unknown attempts retain the batch reservation and
no automatic retry/fallback occurs. Receipts separate completion, JSON format and
arithmetic correctness, omitting raw prompts, answers, URLs and credentials.
Native units count host invocations rather than vendor-internal model requests.

Fixture results do not qualify a live provider or general model quality. The
earlier Qwen/Gemma rendered-prompt evidence and incorrect answers remain preserved
in Runtime's historical report; this release performs no new real-model inference.

## Qualification and distribution

The final versioned source must pass both installed-reasoning Linux architectures
and all four ordinary Linux AMD64/ARM64 × PostgreSQL 16/18 cells. Ordinary gates
retain frontend tests, installed wheel/rebuilt-source consumers, required owned
stacks, public SDK adoption, documented demos and verified cleanup.

The GitHub release publishes the original successful CI wheel/source archives,
checksums and a verification record binding source, merge, SDK manifests and
safe receipts. Local rebuilds cannot replace those qualified archives.
Download the complete source archive for frontend/Observatory assets; the wheel
contains the packaged reasoning agents/configurations and installed CLI lane.

Package/version updates apply to the Lab only. Core, Runtime, Harness and adapter
versions stay unchanged; their separate PRs update documentation. Previous tags,
release assets, model-server settings and private credentials are preserved.
