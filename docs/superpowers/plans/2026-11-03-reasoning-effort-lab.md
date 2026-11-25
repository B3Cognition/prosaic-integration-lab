# Reasoning-effort lab implementation plan

> **For agentic workers:** Use superpowers:executing-plans for native execution.

**Goal:** Add reproducible reasoning-effort integration checks and copyable
blueprints, and correct the current ecosystem documentation.

**Architecture:** Consume installed, checksum-pinned public SDKs. Add a separate
reasoning lane, preserving the existing Lab release manifest and all historic
evidence. Fixtures observe actual loopback HTTP payloads and owned CLI argv;
live execution requires explicit opt-in and a persistent bounded allowance.

**Tech stack:** Python 3.12, pytest, public Core/Runtime/Harness APIs, YAML/Markdown.

## Constraints and review focus

- No SDK private imports, monkey-patching, copied execution engine or editable SDKs.
- Keep ultra Codex-only; Gemma positive efforts share one binary switch.
- Reject unsupported efforts before dispatch; preserve omitted profile defaults.
- Fixture control checks never certify a live provider or answer quality.
- Live receipts omit secrets, URLs, raw prompts, answers and native stderr.
- One API request/native invocation per effort; no fallback or retries.
- Preserve dirty sibling checkouts and historical qualification records.

## Tasks

### Task 1: Blueprint and control fixtures

- [x] Add failing tests for packaged Markdown, actual HTTP/native wire controls,
  unsupported-level rejection and installed Runtime version requirements.
- [x] Add `lab_runner.reasoning_eval` with packaged effort variants and public
  Runtime fixtures for OpenAI-compatible, Claude Code and Codex execution.
- [x] Add a separate five-wheel manifest selecting Runtime 0.9.12, retaining
  the current Lab's other four pins; verify public downloads and installed bytes.
- [x] Run the focused tests and complete Lab unit/functional suite.

### Task 2: Bounded live recipe

- [x] Test opt-in, invalid efforts/allowances, answer-vs-format grading and
  sanitized receipt boundaries before implementing the live command.
- [x] Reuse SharedLiveAllowance, explicit profiles and fixed synthetic prose.
  Reserve before dispatch, retain unknown outcomes, and do not retry failures.
- [x] Add API/native configs and a Harness workflow blueprint with an offline
  public-SDK admission check. Document exact command paths and package inclusion.
- [x] Verify wheel/sdist relocation and the fixture CLI from a fresh install.

### Task 3: Documentation review

- [x] Audit current Core, Runtime, Harness and both PostgreSQL adapter guides.
- [x] Explain prose distribution vs native execution and neutral/native effort
  mappings, automatic capabilities, binary toggles and profile precedence.
- [x] Correct stale candidate/install guidance using verified published releases;
  link the Lab blueprints and retain historical ledgers unchanged.
- [x] Run relevant offline docs/blueprint checks and obtain one independent review.

No new live inference or publication is part of this documentation/lab update.
