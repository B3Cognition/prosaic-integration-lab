# Streaming defaults and connection recovery — 2026-10-31

Follow-up to commit `4f7efa7` on `codex/observatory-token-stream`. The maintainer
authorized streaming by default in Lab/chat, proper testing and committing/pushing
the entire feature package. No merge or release is authorized here.

## Diagnosis and changes

The screenshot's 401 happened before model dispatch. Manual credential entry
previously marked any value Connected and kept Start enabled after rejection.
Reloading discarded the in-memory token and the consumed launch link could not
restore it. Separately, the retained real-model preview had already spent its
one-call allowance; another click could not generate output.

Conversations, native bindings, the chat launcher and local example profiles now
select streaming by default. An explicit `streaming: false` remains supported.
The synthetic provider emits actual, properly terminated SSE with tool deltas
and final usage. Ordinary fixtures stream without artificial delay; the explicit
`Show generation` demo retains 52 paced chunks. JSON/fault fixtures remain usable
when buffered transport is selected. No SDK code/pin or gateway limits changed.

Streaming selects provider transport. The message HTTP API and chat history
still return committed turns after validation; their JSON contract is unchanged.
Provisional output remains owner-filtered in the optional Observatory feed.

The launcher issues a random, HttpOnly, SameSite=Strict session cookie after its
one-use matching-origin launch handshake. POST `/chat/session` restores only an
already-authorized browser with the cookie, exact Origin and custom header,
bounded to eight hours and the current process. Cookies are not accepted as
generic API authentication. No API key is written to browser storage. Foreign,
missing, malformed and expired sessions are denied; API routes retain their
existing bearer guard. GET `/chat/connection` validates manual credentials
before the UI shows Connected. A 401 clears the invalid connection and timers;
losing auth during the initial poll cannot dispatch a model message. No request
is automatically retried.

Independent review found three Important compatibility issues; all have watched
regressions and fixes: explicit launcher opt-out now writes false, the bounded
local-routing preflight accepts boolean streaming, and old buffered identities
are retained alongside the new defaults. Retention reconstructs public SDK
bindings with explicit false only when the trusted definition omitted the flag;
owner/grant checks still apply. Tests restart an old conversation with a waiting
workflow and an old paused native run, then resume their exact identities.

Broader qualification also found the conversation-conformance preflight still
requiring false, plus a reservation regression introduced in the earlier
generation commit. Both received watched failures and fixes. Ordinary turns
again reserve two provider requests independently of the cumulative session
budget; an insufficient cumulative cap rejects before dispatch. The trusted
launcher explicitly sets `provider_request_limit: 1` for a one-call allowance
(otherwise 2), rather than implicitly shrinking every binding's reservation.
Both preflights now accept boolean streaming while retaining their secret,
endpoint, call, tool and token limits.

## Browser verification

Fresh owned PostgreSQL 16 preview owner `17c3cdb0d7cc40dcbf74a95bbd0fd163`, consumer
`sha256:28adc01f55a3357717f10fa4a15750f9ed72c6772b494d73117c3d238e816ca3`,
at `http://127.0.0.1:65006/observatory/`. This uses the synthetic HTTP provider
with a 32-request cap and 1-second fixture latency. It is intentionally retained
for repeated user review; other qualification stacks must clean their owned
resources. The normal per-owner conversation retention limit also applies.

Repeated fresh Start clicks completed 52 chunks each. Captured Live and Inspect
while requests were still running: each showed 6 chunks/24 characters at about
1.5 seconds, then reached 207 characters/52 chunks and the fixture's 25 reported
output tokens. Reload restored authorization without another model request.
An invalid launch code exposed Connect; submitting an invalid token kept that
form visible and Start unavailable with an explicit rejection. Reload restored
the authorized session. The separate `/chat` page also restored the launcher
session. These are actual SDK/HTTP observations of synthetic data, not a model
benchmark.

A separate local-Qwen run used a hard one-request allowance, owner
`e6317c91911d426ba6e81fa29bbb1f7f`, run
`dc6e9e5a4173467eae79d5804ba16b0c`. It completed 16 chunks/31 characters in
26.75 seconds, first output 22.32 seconds, maximum gap 331 ms. Final usage
remained unknown. Its owned stack cleanup was verified; it is not the repeated
user preview. The spent preview at 55864
(`164b5b4100dd44b0af5e61aa0224a931`) was also stopped with verified cleanup.

## Qualification

- `.venv/bin/python -m pytest -q`: **2,031 passed in 568.14 seconds**. One existing
  Starlette/httpx deprecation warning remains unchanged.
- All **24 Node tests** pass in the checkout and extracted source archive.
- Native PostgreSQL 16 acceptance: **54 passed**, zero skipped, cleanup verified,
  owner `707fb94038c34294b99815a169ebafc0`, 260.67 seconds.
- Conversation PostgreSQL 16 acceptance: **97 passed**, zero skipped, cleanup
  verified, owner `d64cb28ee93e417d8b27a084071a7e2a`, 501.13 seconds.
- Clean noneditable wheel and rebuilt-source consumers passed payload/import
  audits, dependency checks, public construction and source/launcher checks;
  owned temporary cleanup verified. These are unpublished local artifacts.
- All five SDK payloads match the unchanged verified release wheels. The source
  guard verifies 23 vendor files and the unchanged Blender GLB checksum.

The final consumer image is
`sha256:53c0a547b57be02708bac5e727c083014edbb954886a8106cfdbc3a0de92573c`.
Only documentation is edited after these implementation checks.

For the user's own browser, a separate fresh synthetic preview is intentionally
retained at `http://127.0.0.1:58632/observatory/`, owner
`c5706da474884a38b7be360f7c8d3b08`, with that final image. Health/static checks
passed, unauthenticated API admission remains401, and provider calls are zero.
Its private one-use launch link is delivered directly to the maintainer, never
committed here. Opening it authorizes that browser; subsequent reloads restore
the session. The earlier in-app preview65006 is retained for existing review
tabs. An unused intermediate handoff stack was stopped with verified cleanup.

Local macOS/ARM64 and PostgreSQL 16 checks do not replace the normal exact-head
Linux AMD64/ARM64 × PostgreSQL 16/18 CI gate before a later merge/release. Published
0.8.0 archives/tags, model-server settings, credentials and other worktrees remain
unchanged.
