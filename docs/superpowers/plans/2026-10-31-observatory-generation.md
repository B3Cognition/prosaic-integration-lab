# Observable generation implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline and obtain one fresh whole-branch review.

**Goal:** Make actual model output generation unmistakably visible in both views.

**Architecture:** Enable streaming only for the Observatory, consume public
Harness provisional callbacks alongside Runtime metadata, and present bounded
owner-filtered generation arrivals through a shared UI model.

**Tech Stack:** Python/FastAPI, released Runtime/Harness, Three.js/GSAP, SVG.

**Spec:** `docs/superpowers/specs/2026-10-31-observatory-generation-design.md`.

## Global constraints

- No SDK patches, dependency/pin/version changes, merge or release.
- Default conversation streaming false; Observatory selects true.
- Generation bounds: 32 calls/run, 512 samples/call, 4096 preview chars/call.
- No reasoning, prompt, tool-argument or credential capture; owner-only preview.
- Keep final recorder usage separate from chunk timing and provisional output.
- Preserve source-only host fixture contract and all historical evidence.

## Review focus

- Concurrent/missing provider identity: skip uncorrelatable deltas, never guess.
- Stream failure or unknown handoff: keep provisional status, never replay work.
- Long/bursty outputs: bounded samples/preview, retained counts, truncation labels.
- Single/zero chunks: no divide-by-zero or invented token rate/first output.
- Background/pause/reduced motion: stop movement and retain readable evidence.

## Task 1: Capture real generation through public callbacks

Files: `run_observations.py`, `conversation_execution.py`,
`conversation_workflows.py`, `lab_runner/chat.py`, `lab_runner/model.py`,
`lab_runner/observatory.py`; corresponding Python unit/functional tests.

- [x] Write and watch failing tests for delta timing/correlation/bounds,
  owner-filtered ordinary capture, streaming bundle admission and actual SSE
  gateway/fixture delivery with exact allowance/no-retry behavior.
- [x] Implement `RunObservations.output(run_id, event)` and a `generation`
  snapshot alongside unchanged metadata events. Hook it best-effort into send.
- [x] Enable the boolean host binding feature and Observatory selection; forward
  bounded SSE through the local gateway and serve it in the synthetic fixture.
- [x] Run focused Python regressions, installed SDK audit and owned-stack check.

## Task 2: Present generation in both views

Files: new `generation-model.js` and tests; new `generation-view.js`;
`sample-runs.js`, `live-model.js`, `observatory.js`, `scene-renderer.js`,
`index.html`, `observatory.css`, existing frontend regression tests.

- [x] Write and watch failing Node tests for known arrival timings, bursts,
  gaps, replay cutoffs, call selection, missing/truncated/buffered/single output.
- [x] Derive call selection, first output, counts, largest gaps and chart points
  from one model; attach the real projection and deterministic sample data.
- [x] Build a shared generation panel and safe provisional chunk ribbon,
  cumulative step curve, cadence marks, clear metric units and playback states.
- [x] Drive obvious return bursts in 3D from arrival timestamps; keep motion
  event-driven, pauseable and compatible with reduced motion.
- [x] Browser-check both views, call switching and replay at 1440/768/390px;
  inspect screenshots and fix the largest usability issues.

## Task 3: Qualify the complete experience

Files: Observatory guide and verification ledger; source smoke/workflow if
new required files need explicit inventory coverage.

- [x] Run `.venv/bin/python -m pytest -q`, all Observatory Node tests and asset
  source guard; build wheel/source and qualify extracted source consumers.
- [x] Run the owned PostgreSQL demo with streaming, observe both browser views,
  then a bounded real local model stream; verify no duplicate execution and cleanup
  of test stacks. Intentionally retain the spent-allowance final review preview.
- [x] Obtain fresh whole-branch review, fix material findings with regressions,
  and record actual evidence, model choice, limitations and preview instructions.

Completed: 2,023 Python tests, 21 Node tests, audited SDK payloads, source/vendor
guard, isolated wheel/rebuilt-source consumers and extracted-source Node tests
passed. Browser verification and the bounded completed real stream are recorded
in `docs/verification/observatory-generation-2026-10-31.md`. No merge/release.

Follow-up requested by the maintainer: enable streaming in Lab/chat by default,
fix Start/connection recovery, test and commit/push the whole package. Completed
with legacy identity retention and explicit buffered opt-out: 2,031 Python tests,
24 Node tests, 97 conversation and 54 native PostgreSQL acceptance cases; all
passed with verified qualification cleanup. Clean wheel/source consumers and
actual synthetic/real-model browser runs passed. See the streaming-defaults ledger.
