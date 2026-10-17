# Token counter qualification and held-out comparison

> **For agentic workers:** Use superpowers:executing-plans inline. One final fresh whole-change review; no implementer delegation.

**Goal:** Qualify trusted counters and compare raw/typed memory on fresh held-out
cases within the existing cumulative and per-case limits, then assess readiness.

**Architecture:** Keep Runtime's public counter protocol unchanged. Lab supplies
a local Hugging Face chat-template counter with immutable asset hashes, pinned
libraries, a closed text/tool request domain and explicit framing variants. Count
the maximum across declared variants, including canonical schema descriptions,
so qualification never invents numerical padding from observed discrepancies.
Server/model details are qualification evidence, not production model branches.

**Tech stack:** Python 3.12, installed public SDK candidates, Transformers 5.17.0,
Tokenizers 0.23.2, Jinja2 3.1.6; no remote model code or model-weight loading.

**Spec:** User request and docs/budget-hardening.md. Six failure families,
2 profiles × 2 memory arms × 2 evidence formats × 6 cases = 48 samples. Fewer
cases than the earlier 96-sample design, explicitly limiting statistical power.

## Global constraints

- Keep all current limits: cumulative 1475 requests / 604 tools / 1976623 tokens;
  currently charged 1235 / 484 / 1416750 across 27 historical ledgers.
- Each study sample reserves 4 requests / 2 tools / 8192 tokens / 600 seconds;
  max output stays 512 for both original profiles. No configuration tuning.
- Reserve 192 requests / 96 tools / 393216 tokens for the comparison. A separate
  8-request qualification allowance reserves 49152 tokens and two tools;
  the combined worst case fits remaining 240 / 120 / 559873. Stop on uncertainty,
  mismatch or breach. Do not replenish allowance from a failed/unknown attempt.
- All live model execution through installed Runtime. Preserve historical files,
  independent receipt auditing and network-denied replay. No push or release.
- Freeze reviewed implementation, assets and historical corpus before generating
  new current cases. Do not tune after evaluation freeze. Qualification uses only
  development probes; held-out generation requests are never qualification probes.
- Counter domains are text/tool OpenAI-compatible chat; unknown fields, media,
  missing assets, unsupported templates or drift fail closed. Another provider
  supplies another registration through the same public protocol.

## Tasks

- [x] Counter implementation: watched RED/GREEN tests for ownership, Unicode,
  tools/argument normalization, framing maximum, hashes, drift and closed input.
  Optional pinned tokenizer dependencies; generic configuration, no model IDs.
- [ ] Offline qualification: freeze served tokenizer assets and rendering settings;
  prove asset paths match read-only model status. Exercise real local tokenizers
  with synthetic requests and independent native framing checks. Build/checksum
  an installed Lab wheel, full source suite, fresh review and regression fixes.
- [ ] Live development qualification: at most eight reserved inference requests,
  both profiles and tool continuations/Unicode. Compare every counted input with
  provider input usage; retain all evidence. No dispatch on mismatch/unknown.
- [ ] Freeze implementation/history, generate fresh six-case evaluation, qualify
  all 48 cases with a synthetic provider, then run the prepared live comparison.
  Audit every receipt/count/claim and replay with networking denied. Report
  model results, admission limits, uncertainty and next-milestone readiness.

## Progress

Read-only catalogue confirms both original models are served. Tokenizer assets
are present, including the pinned HF snapshot for the smaller profile. Existing
isolated Lab worktree reused on codex/token-counter-qualification. Runtime/Core/
Harness unchanged. User-approved native execution avoids another design Q&A.

Counter tests: 15 watched failures, then 20 passing tests after closing the
reasoning-history domain and adding descriptor provenance. Fresh review found
one real reasoning reconstruction undercount; regression reproduced it before
rejecting that unsupported field. Both real tokenizer assets reject it. The 102
independent development framing checks matched exactly (zero underestimates).
No inference requests have been made yet. Runtime/Core/Harness remain unchanged.
