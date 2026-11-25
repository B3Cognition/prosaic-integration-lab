# Visual Explorer implementation plan

> **For agentic workers:** Use independent scoped frontend/coordinator tasks under superpowers:dispatching-parallel-agents; parent integrates HTTP/launcher, packaging and verification. Use TDD and a fresh final review.

**Goal:** Deliver visual documentation, deterministic playback and safe single-agent live controls.
**Architecture:** Packaged React Flow UI, a localhost Python launcher and a durable single-worker coordinator consuming the released Runtime CLI. The graph never implements provider retry or execution authority.
**Tech stack:** Python3.12/FastAPI, React/TypeScript/React Flow/Vite, pinned npm lock, bundled IBM Plex fonts, public Runtime0.9.8.
**Spec:** ../specs/2026-10-25-visual-explorer-design.md

## Global constraints

Keep existing SDK pins, Markdown/inputs, allowance formats, historical assets and no-replay rules unchanged. No actual live inference is part of implementation validation. Default mode requires no Docker, Node or credentials. Authenticated same-origin Run authorizes exactly one bounded request. No automatic resume/replay. Unknowns remain charged after reconciliation.

## Shared interfaces

Frontend source: `frontend/explorer/`; built files: `lab_runner/explore/web/`.
Parent owns HTTP app, launcher, packaging/CI/docs. Backend task owns
`lab_runner/explore/execution.py` and `tests/unit/test_explorer_execution.py`.
Frontend task owns frontend source, its tests/lock, and generated web assets.

Coordinator API: `Coordinator(root, config_path, *, manifest, wheel_dir, max_units=20)`;
`status() -> dict`; `submit(request_id, task, local_timeout_s=180) -> dict`;
`get(run_id) -> dict`; `cancel(run_id) -> dict`; `close()`;
`reconcile(root, run_id, receipt_sha256, note) -> dict` (offline, no replay).
Strict task IDs: release-brief, incident-handoff, invoice-sql. Timeout choices180/240.
`status` returns liveEnabled, profiles[{name,backend,model}], policy, allowance,
blocked, activeRunId, runs. No secrets or host/config paths.
Policy keys: nativeTimeoutSeconds60,localTimeoutSeconds180,poolTimeoutSeconds300,
maxAttempts3,maxNativeAttempts2,maxApiRequests8,maxToolCalls7,maxToolRounds8,
maxReportedTokens65536,nativePermissions workspace-write.
Run receipt: runId,requestId,task,state(running/completed/failed/uncertain/cancelled),
passed,durationMs,selectedProfile,events[{event,profile?,reason?}],output,
failureReason,recoveryRequired,usage{nativeAttempts,apiRequests,apiToolCalls,knownTokens},
startedAt,receiptSha256. Output bounded text; all event/reason fields filtered.

HTTP: POST /api/bootstrap with X-Explorer-Launch (single-use), exact Origin;
returns token. Other /api require Authorization:Bearer token.
GET /api/status; POST /api/runs {requestId,task,localTimeoutSeconds,confirmed:true};
GET /api/runs/{id}; POST /api/runs/{id}/cancel.
Mutations require exact Origin, bounded JSON <=4096bytes, no extra keys.
Static documentation works without authentication; token bootstrap hash `#connect=`
is removed immediately and never persisted. No raw logs/config paths returned.
Readonly docs links target GitHub's matching guides; user commands copied as text.

## Review focus

- Double-click/retry/reconnect must return original request, never redispatch.
- Crash between admission/reservation/dispatch must preserve uncertainty and quota.
- Cancellation cannot claim rollback, clean completion or zero usage.
- Host configs or symlinked roots must not widen authority after launch.
- Mobile/keyboard navigation, absent live config and error states remain usable.

## Tasks

- [x] Backend: write failing durable coordinator tests; implement lock/atomic private records,
  config/audit admission, public CLI subprocess, independent grader, filtered receipts,
  allowance accounting, cancellation/restart block and offline reconciliation; focused tests.
- [x] Frontend: implement real ecosystem lessons and eight playback scenarios with tests;
  Taste framed-sheet shell, custom React Flow nodes, user/developer inspector, live policy
  review/start/cancel/results, no implicit dispatch, keyboard/list/narrow/reduced-motion states;
  lock dependencies, build bundled offline assets/fonts and record tests.
- [x] HTTP/launcher: failing auth/body/origin/static tests; implement loopback bootstrap,
  async admission and bounded request contract, local launch file, inspect/acknowledge CLI,
  safe shutdown. Validate frontend against real app fixtures.
- [x] Integration: add package/static/source inclusion and reproducible frontend CI check;
  update README/quickstart/explorer guide; run full suite, frontend tests/build/Taste inspector,
  browser interaction and screenshots, clean wheel/source installed smoke; independent review.
  Commit local changes; do not push/merge/release without further user scope.

## Execution ledger

Implemented in the existing isolated clone from 9dbeb2d. Full Python suite: 1,979 passed;
frontend: 15 unit tests and 3 real Chromium tests passed. Production Taste inspection
at 1440/768/390 returned 0 FAIL / 0 WARN after three rounds; screenshots opened. Clean
wheel/rebuilt-source qualification passed against released Runtime 0.9.8, including
the installed Explorer smoke and existing 51 standalone synthetic cases per consumer.
Fresh review's subprocess-cleanup and pending-identity findings were fixed with
regressions and re-reviewed. Browser-found React Flow feedback and native fetch
receiver issues are now covered by reusable Chromium tests. SDK pins unchanged;
no live inference, Docker stack, new Linux qualification or publication performed.
See docs/verification/explorer-2026-10-25.md for details and remaining CI scope.
