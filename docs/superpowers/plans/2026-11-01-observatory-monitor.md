# Observatory as an authenticated Lab monitor

User-approved scope: all runs belonging to the authenticated user in this Integration
Lab instance, including runs started outside Observatory. No oMLX-wide monitoring.

The hosted page starts idle, never in a sample. Connecting starts a bounded,
owner-filtered discovery poll and follows the latest captured run. Samples require
an explicit selection. Completed observations remain still until Replay is chosen;
following current events and replaying past events have different labels. Losing
authentication stops updates and removes the displayed traffic. Refresh restores
an authorized browser session and rediscovers captured runs without inference.

The optional process-local observation sink retains at most 32 recent runs. The
monitor describes this retention and does not claim durable or cross-replica
capture. Discovery rechecks host ownership, namespace/environment, and current
conversation/native grants. Detail endpoints use public SDK status and recorder
calls. No new durable formats, SDK patches, or provider credential exposure.

Manual Lab-token connection may establish an eight-hour HttpOnly same-origin
browser session, bound to the exact verified token (never the launcher's default
principal). oMLX credentials remain invalid Lab credentials. No browser storage of
bearer tokens. Session restore and discovery are read-only; tests dispatch only
when the user starts a test or sends an external Chat/API message.

Implementation and verification:

1. Add failing owner-filtered discovery, external-run, workflow-output, manual
   session, and browser-client refresh/follow/race tests.
2. Connect legacy/native public observer/output callbacks to the same sink and
   add authenticated bounded discovery and workflow detail routes.
3. Implement persistent discovery, run selection, idle UI, explicit samples,
   freshness and live/replay labels, and clear credential guidance.
4. Run focused tests, full Python/Node suites, source guards, and installed-wheel
   checks. Exercise real browser behavior with synthetic external traffic and,
   if needed, one bounded real-model turn. Review the final diff before pushing.

Completed: owner/grant-filtered discovery, public standalone workflow callbacks,
timing-only workflow output, exact-principal serialized browser sessions, honest
idle/demo/replay states, missing-timing labels, and real Safari external-traffic
verification. Final regressions: 2,077 Python + 32 Node passed. Owned PostgreSQL16
observability: 26 passed, cleanup verified. Reviewed without remaining blockers.
Final archive verification passed. Commit/push complete the work package; see the
verification ledger for evidence and capture limitations.
