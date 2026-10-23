# Repeated unified CLI benchmark plan

**Goal:** Run the unchanged realistic Markdown/inputs/graders through the installed
unified CLI, three trials per task and availability state (27 assignments).
**Architecture:** Lab owns scheduling, fresh workspaces, private evidence and
bounded admission. Installed Runtime owns selection and execution. One shared
capacity file retains observed real cooldowns; temporary host exclusions never
clear an existing cooldown. Canonical sources and prior reports are immutable.

Ruling: Execute inline within the requested benchmark scope. States are all
eligible, Claude cooling, and both native profiles cooling. These are controlled
capacity inputs, not fabricated provider errors. Report actual fallback events
separately from skipped profiles. Native 60s, API/local 180s, pool total 300s.
Maximum dispatch allowance is 243 mixed units (9 × (10 + 9 + 8)); opaque native
inner requests remain unknown. No automatic retry of an uncertain assignment.

- [x] Add failing tests for planning, safe temporary exclusions, installed CLI
  event capture/accounting, failure grading and report summaries.
- [x] Add Lab-only benchmark lane, preserving existing task files and graders.
- [x] Verify focused/full Lab tests and exact installed SDK/consumer fixtures.
- [x] Run audited installed candidate sequentially with no concurrent test load;
  three trials, rotated task/state ordering, fresh workspaces, bounded allowance.
- [x] Regrade preserved outputs; compare exact hashes/model/deadlines against the
  last direct benchmark, report success/completion/latency/fallback, verify cleanup.

Result: 27/27 successes/completions. Nine samples per path; medians Claude12.13s,
Codex23.99s, local60.58s. All27 samples match baseline Markdown/input/model and
per-backend deadlines. Independent audit regraded54 outputs and reconciled every
admission;45/243 mixed units (18native+27API), zero unknown reservations. There
were27 controlled profile skips and zero provider-triggered fallback events.
Final focused harness/grader34passed; fullLab1527passed, one existing warning;
exact consumer33checks passed. Review found cancellation cleanup and failure
timing bugs before live measurement; watched regressions passed after fixes.
Owned server68232 stopped (exit143), listener closed, owned containers and
workspaces absent. No benchmark retries, publication, pushes or library changes.
See docs/verification/unified-cli-realistic-2026-10-23.md for exact evidence.
