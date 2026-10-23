# Unified pool PR qualification — 2026-10-23

This qualification integrates the unified pool with current upstream main. It
does not replace the immutable historical live measurements or claim a new live
benchmark against the updated SDK train.

The initial candidate below is retained as pre-review evidence. The
[review correction](#review-correction-and-current-main-requalification) at the
end records the superseding replay-safety fix and its exact candidate.

## Scope and provenance

- Runtime base: `d046bb73327674123d0bdfc1121d35acc74b931a`.
- Runtime candidate source: `4e3cdd1667637f145c4dd5454810f1ac9e5e2f50`.
- Runtime candidate version: 0.9.7, an unpublished local extension of the current
  compatible release identity; this is not the published 0.9.7 wheel.
- Runtime wheel SHA-256:
  `30c96d140a29321eecd46f21625a6e57eacf3722f8e14c79abaa95d459f880b3`.
- Candidate manifest SHA-256:
  `d690c1387811100df6cb1f5e03e24f2447cab7d99dfd781518aa2f7241ff40c9`.
- Lab base: `78cfef46a19bbe49c29f945243e0b690d95fc70d`.
- Exact offline Linux ARM64 consumer image:
  `sha256:024db2ad8add74c01c7499f7d466b7785b3e77726e8eb84978a506be8dc2b965`.

The other four manifest artifacts remain the published Core 0.4.1, Harness 0.9.4,
Runtime PostgreSQL 0.3.0 and Harness PostgreSQL 0.4.0 wheels. Published dependency
pins are unchanged. The installed five-wheel payload audit and dependency check
passed. SDK imports came from installed wheels, with no sibling SDK source or
editable imports in the Lab candidate environment.

## Fresh verification

- Runtime full suite: **1,415 passed, 2 skipped**.
- Runtime focused native/unified suite: **91 passed**.
- Lab full suite with the unchanged published SDK train: **1,864 passed**, one
  existing Starlette deprecation warning.
- Lab full suite with the exact candidate SDK train: **1,864 passed**, the same
  existing warning; no failures or skips.
- Explicit installed-candidate acceptance suite: **14 passed**.
- Runtime and Lab wheel/sdist builds passed.
- All four Runtime installed-wheel smoke programs passed under isolated Python.
- Offline read-only consumer: **51/51 checks passed** — 18 provider rejection,
  13 CLI, 11 unified API and 9 native adapter checks. Each report records zero
  live invocations and verified fixture cleanup. Containers used no network,
  no credentials and an executable temporary mount for owned fixture CLIs.

The Runtime example was also loaded through the actual CLI with zero native
attempts and zero API requests: configuration and canonical Markdown inspection
succeeded, and the explicit budgets prevented dispatch.

Host fixture tests require loopback server permissions. A sandboxed candidate
attempt was interrupted after local HTTP bind failures; verification was restarted
with owned loopback fixture access. This required no product-code change.

## Historical live benchmark and fallback evidence

The [repeated realistic CLI benchmark](unified-cli-realistic-2026-10-23.md)
completed **27/27** assignments using unchanged neutral Markdown and inputs:

| Selected backend | Success | Median latency |
| --- | --- | --- |
| Claude Code, Sonnet alias | 9/9 | 12.13 s |
| Codex CLI, `gpt-6.1-sol`, low effort | 9/9 | 23.99 s |
| Local ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ | 9/9 | 60.58 s |

Each backend ran three trials of release brief, incident handoff and invoice SQL.
Native deadlines were 60 s, local 180 s and total pool 300 s. The benchmark
observed 27 controlled cooldown skips and zero provider-triggered fallback events.
These are small-sample observations, not a general model ranking.

The separate [provider rejection qualification](unified-provider-fallback-2026-10-23.md)
passed 18 checks across seven scenarios. Provider-shaped Claude and Codex quota
fixtures switched to local only before work; partial text and tool effects stopped
dispatch and required recovery. A historical real-local repair after two simulated
native rejections completed in 41.22 s with the same 180 s local deadline. Neither
remote subscription was exhausted by this test. The 18 synthetic checks were
rerun successfully against the new exact candidate image above.

Both historical studies identify executable source
`65385bcac87da084f6fd65ce3dbaf96bafe279c9` and their original wheel, manifest,
report and image hashes. Those live measurements used the earlier 0.9.3 candidate;
they must not be attributed to the new 0.9.7 integration candidate.

## Boundaries

Changes were assembled in separate clones to preserve the original working
directories. The scoped commits include native prerequisites, unified Runtime
API/CLI, examples and Lab runners/tests/results. Unrelated chat, ship evaluation,
OpenAI walkthrough work, private profiles, reports and caches are excluded.
No new live model measurement, package publication, release or credential change was
performed for this finalization. Candidate acceptance remains explicit; ordinary
released-SDK tests do not require unpublished native/unified exports.

## Review correction and current-main requalification

Fresh review reproduced three gaps in positive native pre-work proof: partial
Codex text/reasoning could replay inside a native-only pool; Claude redacted
thinking could be treated as no work by a unified pool; and unknown nested stream
activity could authorize fallback. Thirteen new regressions failed before the
fix. The native proof now excludes all observed model work, including redacted
thinking and started streams. Both native and unified physical dispatch tests
verify that subsequent profiles are not launched. A later zero-turn quota error
cannot undo earlier work evidence. Successful native execution is unchanged.

Independent follow-up review found no remaining code issues. Documentation now
uses the same rule for native/unified pools and includes a complete clean-checkout
candidate build, checksum, curate, install and audit recipe.

- Superseding Runtime source: `36cf08302dbbe2d58a2dba6b32ed2b2f1660a5d2`.
- Runtime wheel SHA-256:
  `695bb7ba551a0e5e0753e6790ee26215f2a90279b44bdcf01aeb6928ee49c2e5`.
- Candidate manifest SHA-256:
  `b0c7752ca5c1f7945cd1248ac195f74f7cafa5b401dc6001b4746f44a2bfd9db`.
- Lab now integrates main at `ae77cba066d14944eb1fca1c860f01da60a64b93`,
  preserving the independently merged Castle changes and all public build inputs.
- Superseding offline Linux ARM64 image:
  `sha256:66064d3fcb14005706d4660f054dec626314ff43dc2df1f10557ce50bf5fb9f4`.
- Runtime full suite: **1,428 passed, 2 skipped**, 456.11 seconds.
- Combined Lab full suite with released SDK pins: **1,884 passed**, one existing
  Starlette deprecation warning, 493.37 seconds.
- Watched replay regressions: **13 failed before the fix**; the selected group
  then passed **15 tests**, including two existing safety cases.
- Installed-candidate acceptance: **14 passed**, 29.05 seconds.
- All four isolated Runtime installed-wheel smoke programs passed.
- Complete five-wheel payload audit and dependency check passed. Two stale
  optimized caches for the changed module in the reused environment were
  regenerated from verified installed source before repeating the strict audit;
  SDK source bytes and audit policy were not modified.
- The exact image passed all **51 offline checks** again: 18 provider rejection,
  13 CLI, 11 unified API and 9 native cases, with no live invocations and verified
  fixture cleanup. The additional reasoning/stream edge cases are covered by the
  new Runtime regressions above; the historical fixture suite is unchanged.

No historical live task, Markdown, input, model, deadline or result was altered,
and no new model measurement was performed during review. Published dependency
pins remain unchanged. The candidate wheel is an unpublished extension of the
compatible 0.9.7 identity, not the published artifact.
