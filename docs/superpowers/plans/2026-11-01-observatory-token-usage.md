# Observatory real-model usage fix

> **For agentic workers:** Use superpowers:executing-plans inline. No new
> implementation delegation is needed; obtain one final focused review.

**Goal:** Show actual model-reported token counts in both Observatory views.

**Architecture:** The local oMLX gateway translates only the exact empty
`model: keepalive` prefill heartbeat into an SSE comment. Real response events
and usage pass through unchanged to the released Runtime recorder. Existing
unsupported-report labels remain separate from qualified accounting totals.

**Tech Stack:** Python HTTP/SSE gateway, installed Runtime 0.9.8, existing
Observatory presentation and owner-filtered recorder projection.

**Spec:** The maintainer's request to fix missing real-model token reporting;
repository ownership and privacy constraints in `AGENTS.md`.

## Constraints and review focus

- Preserve published 0.9.0 assets, SDK pins, accounting records and server settings.
- Never hide real model changes, usage, content, tool calls or malformed events.
- Handle arbitrary byte fragmentation and LF/CRLF without buffering the response.
- Preserve the raw-byte/time caps, no-retry behavior and shared request allowance.
- Keep unknown, incomplete and untrusted usage unavailable; display actual
  unsupported counts only through the existing explicitly unqualified projection.

## Execution

- [x] Reproduce missing counts with a real loopback provider, gateway, installed
  Runtime and recorder; watch a valid oMLX-shaped report fail due to heartbeat.
- [x] Test strict heartbeat recognition, adversarial lookalikes, fragmentation,
  byte preservation and incremental delivery; implement the minimal adapter.
- [x] Run affected tests, full Python suite, frontend regressions and source guard.
- [x] Review the final diff, build its immutable consumer and run a new bounded
  real-model preview. Verify recorder counts and both views; retain it for use.
- [x] Record actual evidence and preserve the earlier preview and release bytes.
