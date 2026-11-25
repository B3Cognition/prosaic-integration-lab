# Authenticated Observatory monitor — 2026-11-01

Unreleased follow-up on `codex/observatory-token-usage` and draft PR41. The
maintainer approved automatic monitoring of all their Integration Lab runs.
Published 0.9.0 artifacts, SDK pins, older previews and model settings are unchanged.

## Behavior and scope

The previous hosted page autoplayed a sample before authenticating and followed
only conversations it started itself. The new page starts with empty traffic,
unknown token counts and disabled playback. Successful authentication starts
bounded discovery of the user's captured Chat/API and standalone legacy/native
workflow activity. Discovery continues after completion; a completed trace stays
still. Selecting a demo is explicit. Scrubbing/replay pins the selected run until
Follow live. Refresh restores the same browser principal and rediscovers traces
without creating a conversation or invoking a model.

The optional capture buffer retains at most 32 recent runs in one process. Every
discovery/detail read rechecks host-owned tenant/actor, namespace/environment and
applicable current grants. Another user receives no identifiers, timing, content
or usage. No browser-supplied ownership selectors are accepted. Workflow previews
are withheld at capture and response projection, independently of review grants;
timing/character counts remain visible. Authentication handshakes are serialized
so an older Set-Cookie response cannot restore a different principal.

Capture is not durable or shared between replicas, and does not observe arbitrary
oMLX clients. Released public SDK callbacks do not cover linked conversation
workflow resumes. Recorder calls without captured timing are marked explicitly;
missing events are never reconstructed. Accounting qualification is unchanged.

## Verification

- RED: authenticated discovery returned 404 before adding the route. The new
  functional regression sends an ordinary Chat/API message, then discovers its
  trace without viewer dispatch; other actors/tenants see an empty feed.
- RED: no-agent workflow outcomes were incorrectly `ready`; model tests now
  preserve authoritative completed/rejected/blocked/start-uncertain states and
  prevent incomplete terminal traces from remaining active.
- Focused review: 57 Python checks and 31 Node checks passed at the reviewed
  checkpoint. Additional missing-timing coverage brings current Node checks to 32.
  Disclosure, handshake/cookie ordering and replay-preemption regressions are
  included. Reviewer reported no remaining Critical/Important/material Minor
  findings; final missing-timing UI uses the same recorder/public callback data.
- Final full Python suite: **2,077 passed** in 604.84s; one existing
  Starlette/httpx deprecation warning. All **32 Node tests passed**. Installed
  SDK payload audit and `git diff --check` passed.
- Isolated wheel/sdist consumer checks passed (public-index adoption, payload
  audit, isolated imports/construction, source assets, cleanup), including the
  final source archive rebuilt after the last frontend changes.
- Source asset guard passes: 23 vendors and unchanged GLB SHA256
  `2cd4dd1b49a15204a23d80fa7b1e17cf5affb5e46643060640b196b8e73c455c`.
- Final backend image:
  `sha256:03074e763f37a0114ee32d10a0193b6a09428af93b9578b19967cdf55cb721b6`.
  macOS arm64 host, Python 3.12.15, Linux/arm64 consumer, PostgreSQL16. Owned
  observability acceptance: **26 passed, zero skipped, cleanup verified**.
  Released SDK manifest SHA256 remains
  `36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.

## Actual Safari/local-model check

Safari showed disconnected/no traffic and no autoplay before authentication. An
invalid credential produced explicit Lab-versus-provider guidance. A fresh
launcher link connected the correct Lab identity and showed an idle monitor.

One ordinary Lab HTTP API turn, outside the viewer, invoked the approved local
Qwen model with a two-request shared gateway cap and no retry. Safari discovered
the run automatically, showed first-output waiting followed by 36 arriving text
chunks / 71 characters, and settled at **533 input + 111 output = 644 tokens**.
Both Flow and Inspect showed the actual counts with the existing unqualified
provider marker. HTTP200, completed; first visible output 16.18s and total 28.10s.
The recorder retains unsupported accounting qualification for oMLX extensions.

Safari refresh restored the session and selected the completed trace at its end,
without autoplay or a new request. Explicit Demo selection showed scripted labels;
Follow live restores actual captured traffic. Private launch credentials, recorder
state and proof logs remain outside the repository. One request remains available
in the retained preview; no other local-model requests were dispatched in this
monitor task.

The real PostgreSQL stack also denied a second actor's run detail with 404 and
returned an empty discovery feed. Manual browser session creation and restoration
kept that second actor's exact credential rather than the launcher's identity.
Recorder calls remained one after refresh and those ownership/session checks.
