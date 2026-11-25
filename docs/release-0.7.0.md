# Integration Lab 0.7.0

Lab 0.7.0 introduces **Prosaic Explorer**, an installed local application for
learning and trying the ecosystem. Run `python -m lab_runner.explore` after the
[quickstart setup](quickstart.md#setup-once). Documentation and playback need no
model credentials, Docker or Node; scripts, styles, fonts and licenses are bundled.

- Five visual chapters explain Markdown, agent execution, workflow review,
  provider pools and receipts, with user/developer explanations and an equivalent
  keyboard-friendly list.
- Eight deterministic playback scenarios explain completion, fallback,
  cooldowns, unavailable profiles, partial work and workflow review/resume.
- Separate opt-in live controls authorize one predefined task through the public
  Runtime CLI, with explicit host permissions, deadlines and durable allowance.
  Request identity survives lost responses; cancellation and uncertainty retain
  evidence and block replay across restarts.
- System/Light/Dark appearance, locally bundled Instrument Sans/Geist Mono and a
  stable chapter frame keep content readable and navigation visible.

The [Explorer guide](explorer.md) covers setup, grants, budgets and recovery.
The revised README, [guided quickstart](quickstart.md) and first-workflow example
connect the visual guide to runnable fixtures and public integration patterns.
The Harness chat/workflow browser remains a separate service.

The SDK train is unchanged: Core 0.4.1, **Runtime 0.9.8**, recorder 0.3.0,
Harness 0.9.4 and store 0.4.0. Existing benchmarks, Markdown inputs, historical
release assets and experimental boundaries remain unchanged. Qualification uses
synthetic providers and makes no new model-quality claim.

## Published and verified

[Release 0.7.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.7.0)
publishes the original qualified CI wheel and source archive with
`SHA256SUMS-0.7.0.txt` and `VERIFICATION-0.7.0.json`. All four Linux AMD64/ARM64 ×
PostgreSQL 16/18 cells passed 1,980 source tests and 334 required stack checks
each, with zero skipped/failed stack checks and verified cleanup.

Anonymous downloads matched all four audited assets. Clean public-wheel and
rebuilt-public-source installs with Runtime 0.9.8 each passed 51 standalone
fixtures, three deadline CLI checks and 10 installed-browser checks: 128 checks
across both consumers. All five visual chapters, eight playback scenarios,
themes, local fonts and stable navigation were checked. Separate actual
installed Runtime CLI execution through an owned synthetic provider verified
reviewed SQL completion, duplicate-request protection, cancellation, retained
allowance and refused admission across restart.

The [release verification ledger](verification/release-0.7.0-2026-10-25.md)
records source/tag provenance, exact asset hashes, commands, platforms and limits.
Cleanup passed and no real model calls were made; this is release qualification,
separate from the historical live benchmarks.
