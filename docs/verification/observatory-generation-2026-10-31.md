# Observatory generation — 2026-10-31

Unreleased work on `codex/observatory-token-stream`, based on current main
`4787265953bbda9a9e7ed63b500d152b8bcf486b`. The maintainer authorized research,
implementation and bounded real-model verification. No merge, release, SDK
upgrade or model-server configuration change is included. Published 0.8.0
artifacts and historical screenshots remain unchanged.

## What the visual means

Both views share actual ordinary-output arrivals from the public Harness
provisional callback and Runtime provider metadata. Live returns visible packets
from Provider to Runtime when text chunks arrive. Inspect shows the same
provisional text, arrival marks, first-output wait and cumulative character
curve. Pause and scrubbing reveal only arrivals recorded by that cursor; Replay
uses retained observations without redispatching a model request.

The design follows the distinctions in NVIDIA's
[inference metrics guide](https://developer.nvidia.com/blog/llm-benchmarking-fundamental-concepts/)
and [AIPerf's metrics reference](https://github.com/ai-dynamo/aiperf/blob/main/docs/metrics-reference.md).
One transport chunk can contain multiple tokens. Client arrivals include
transport and model work; they cannot isolate GPU prefill, queueing or reasoning.
There are no guessed token boundaries, tokens/s or progress percentages. Token
totals remain run-wide recorder reports, with unknown, partial and unsupported
qualification preserved. Motion can be paused, and reduced-motion mode suppresses
moving provider packets, following [W3C guidance](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide/).

The projection is optional, in-memory and owner-filtered. It retains at most 32
calls/run, 512 arrival samples and 4,096 preview characters/call. It excludes
prompts, tool arguments, interpreter output, reasoning and credentials. Missing
identity suppresses attribution; truncated timing is hatched rather than drawn
as an invented stall. Interrupted output remains explicitly provisional.

## Execution evidence

All execution used the unchanged audited release train: Core 0.4.1, Runtime
0.9.8, recorder 0.3.0, Harness 0.9.4 and store 0.4.0. The SDK manifest SHA-256 is
`36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.
The installed-wheel audit passed; no SDK implementation was patched.

The owned PostgreSQL synthetic demo produced 52 actual SSE output chunks with
the default `Show generation` message. Browser observations showed first output
at approximately 1.32 seconds, a largest gap of 72 ms and the fixture's reported
25 output tokens. These are scripted fixture counts, not a model benchmark.
Both Live and Inspect were exercised. Cleanup for owner
`6d5743db7b354ffaa5bbb3eac3e9ea76` was verified.

Real requests used the configured local
`ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ`, literal loopback and its existing private
key file. No credentials or model-server settings were changed. The original
30-second deadline was retained:

| Request | Actual observation | Result |
| --- | --- | --- |
| Short explanation | No visible text before 30 seconds | Timed out; no invented generation |
| Count 1–80 | 87 chunks, 176 characters; first output 10.68 s; largest gap 338 ms | Timed out; retained partial output and unknown completion |
| Count 1–20 | 35 chunks, 71 characters; first output 12.48 s; largest gap 321 ms | Completed in 20.52 s |

The first two requests shared a hard two-request gateway allowance and had no
automatic retry. That owned stack (`349d085d887447b080e86b6fb40b6ffd`) was cleaned.
A preliminary one-request preview was rejected before dispatch because the
conversation reserved two requests. A failing regression reproduced
`sessionLimit/maxProviderRequests`; the turn reservation now respects a one-call
conversation policy. Its stack (`d72f4642ae2343b19bc96ba77ac2dc3d`) was cleaned
without consuming a model call.

The successful final request used a new hard one-request allowance. Its owner
is `164b5b4100dd44b0af5e61aa0224a931`; run
`b7bfa2c2d3fb43c5bdbe07ad98b5586d` has one completed provider call and no
truncation. Exact relative times: provider start 0.033383 s, first output
12.515894 s, last output 20.285918 s, end 20.506890 s. The stream supplied no
usable final token report, so input/output totals remain unknown. Successful
generation does not imply complete accounting evidence.

This final preview is intentionally retained at
`http://127.0.0.1:55864/observatory/` for review with its allowance spent. Use the
already-connected browser tab and Replay; it needs no further model call.
Reloading discards the in-memory connection. Its launcher owns cleanup; Ctrl+C
stops it and verifies its exact Docker resources. Other temporary stacks,
including failed early build/inventory trials, reported verified cleanup. No
global Docker cleanup was used. Preview consumer image:
`sha256:9d946522636980c24ca07d16ae26adfd53c4654a5a0967071d21dcaee624adc9`.

## Regression and distribution checks

- Final full Python suite: **2,023 passed in 518.79 seconds**, with one existing
  Starlette/httpx deprecation warning. The preceding collected run retained a
  misplaced test assertion; that assertion was corrected and this fresh full
  run passed. No implementation or SDK file changed after this final run.
- All 21 Observatory Node tests passed, including real timestamp replay,
  Unicode, bounded bursts, unknown/truncated intervals, token qualification and
  reduced-motion packet suppression. The one-request and visible-while-running
  SDK regressions passed together after the admission fix.
- Source guard passed for all 23 vendor files and unchanged Blender GLB SHA-256
  `2cd4dd1b49a15204a23d80fa7b1e17cf5affb5e46643060640b196b8e73c455c`.
- Noneditable wheel and rebuilt-source consumers passed isolated import/payload
  audits, public construction, dependency checks, source assets and launcher
  qualification. Final implementation archives also passed this qualification;
  all 21 Node regressions and the asset guard passed from the extracted source.
  These local archives are not published 0.8.0 release artifacts.
- The explicit public build inventory includes both new Python modules. A
  regression imports from a copied inventory snapshot and consumes its actual
  synthetic SSE; this caught an early missing-module failure before delivery.

Independent review found no critical issue and identified failure outcome,
identity/eviction attribution and truncated-tail timing issues. Each received a
watched failing regression and a passing fix. A minor run-wide token label was
also corrected to retain subtotal/qualification markers. Optional observation
capture cannot fail or redispatch a turn.

## Browser evidence and limits

The final frontend skill inspector passed with zero failures at 1440, 768 and
390 px. Its remaining warning concerns existing compact instrument typography;
11–12 px labels/ticks remain subordinate to the 14 px preview and larger metrics.
The earlier blank-space warning disappeared after increasing preview space,
which also reveals local-model output that begins with blank lines.
New component source lint reported zero failures or warnings. Phone Inspect
overflow was fixed and verified at exactly 390 px; ResizeObserver refreshes the
chart when switching views or viewport size. History starts collapsed so the
result does not push live generation below the fold. Browser tests covered
actual completed/failed streams, Live/Inspect, pause, scrubbing and replay.
Reduced-motion packet suppression has unit coverage; the inspector's app mode
does not itself emulate reduced motion.

This remains a source/complete-archive Observatory prototype. Generation capture
is best effort, bounded and not durable billing evidence. This local macOS
verification does not replace the normal Linux AMD64/ARM64 × PostgreSQL 16/18
exact-head CI matrix required before merge or release.
