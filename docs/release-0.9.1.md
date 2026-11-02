# Lab 0.9.1 — authenticated Observatory monitoring

Observatory now starts as an idle monitor. It discovers your captured Lab runs
after connecting, including Chat/API turns and standalone legacy/native workflows
started outside the viewer. Discovery continues after completion; completed
traces stay still. Explicit demo selection enables scripted playback. Pausing or
scrubbing pins replay until **Follow live** is selected.

## Connect and observe

Use the complete source archive or a checkout with the checksum-audited SDK
environment and Docker, then run:

```sh
.venv/bin/python scripts/build_consumer.py --tag prosaic-integration-lab:dev
.venv/bin/python -m lab_runner.observatory --max-calls 12 --fixture-latency 1
```

Open the private one-use launcher link. Another browser can connect using the
Lab API token from the launcher's private `.lab/<owner>/secrets/chat-service.json`.
An oMLX/provider key authenticates the model server and cannot authenticate Lab.
Manual connections are checked through ordinary host authentication. A bounded
HttpOnly, SameSite=Strict browser session restores the exact verified principal
for at most eight hours; concurrent handshakes cannot replace it with a stale
principal. API credentials remain in memory, outside browser storage.

Opening or refreshing Observatory never starts inference. Send a message through
Chat/the Lab API, or explicitly choose **Start lab test**. Synthetic execution is
the default; real local inference remains an explicit bounded opt-in. **Flow**
and **Inspect** show actual output arrivals and recorder token reports. Source
assets are not bundled in the wheel; installed Explorer remains independent.

## Usage and visibility

The local gateway translates only oMLX's exact empty prefill heartbeat into an
SSE comment. Its placeholder model name previously caused correct recorder
quarantine despite a later usage report. Actual model/usage conflicts and raw
usage payloads remain intact. Supported provider-reported counts are displayed
with their existing qualification; unsupported oMLX extensions remain unqualified
accounting evidence rather than being promoted to trusted billing totals.

Every discovery/detail read rechecks the authenticated host identity, frozen
scope and applicable grants. Workflow generation captures timing and character
counts without raw agent text, preserving existing review visibility rules.

Capture is optional, process-local and bounded to 32 recent runs. Restarts and
eviction clear timing; other replicas and arbitrary oMLX clients are outside the
monitor's scope. Some linked conversation workflow resumes lack public SDK timing
callbacks. Recorder calls without captured timing are identified explicitly,
without reconstructing activity. Arrival marks are text chunks, not exact token
boundaries or model-server prefill/queue/reasoning timing.

## Qualification

Publication requires the final versioned source to pass all four Linux
AMD64/ARM64 × PostgreSQL 16/18 CI cells, including required owned-stack lanes,
public SDK adoption, isolated wheel/rebuilt-source consumers and documented demos.
The release publishes the original successful CI wheel/source archives with
checksums and a verification record binding them to source, merge, SDK manifest
and safe receipts. Release qualification uses synthetic providers; previous
real-model observations do not constitute a model-quality benchmark.

The SDK train remains Core 0.4.1, Runtime 0.9.8, recorder 0.3.0, Harness 0.9.4
and store 0.4.0. Earlier tags/artifacts and model-server settings are preserved.
