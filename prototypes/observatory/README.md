# Prosaic Observatory prototype

An interactive visual prototype inspired by the plant-cell reference supplied
by the maintainer. The approved scope is one detailed execution scene first,
with Live and Inspect views and an optional authenticated Integration Lab feed.

The unreleased generation update adds actual streamed output arrivals in both
views. See the [generation verification](../../docs/verification/observatory-generation-2026-10-31.md)
for current evidence and limitations. Historical 0.8.0 real-model screenshots:
[Live](verification/observatory-real-qwen-live-final.png),
[Inspect](verification/observatory-real-qwen-inspect-final.png) and
[phone](verification/observatory-real-qwen-phone-final.png). The shown 549-token
report carries the unqualified marker described below.

## Run with the Integration Lab

Use a checksum-audited environment installed from `dependencies/releases.json`
and a consumer image built with `scripts/build_consumer.py`:

```sh
.venv/bin/python -m lab_runner.observatory --consumer-image YOUR_IMMUTABLE_IMAGE --max-calls 12 --fixture-latency 1.5
```

The launcher starts an owned PostgreSQL stack and a bounded synthetic HTTP
provider. It opens a one-use connection link; the API credential stays in browser
memory. Use **Start lab test** with the default `Show generation` for a paced,
52-chunk synthetic response, `Find players` for two provider calls, a
registered tool and workflow waiting, or `Hello` for a short completed turn. Ctrl+C
stops the UI and verifies cleanup of its owned Docker resources. Default fixture
mode needs no paid provider credential. `--no-open` writes a private launch file.

Streaming is now also the default for Lab conversations, native workflows and
the chat launcher. Explicit `streaming: false` in a trusted bundle retains
buffered transport. Existing sessions/proposals from the earlier omitted/default
buffered configuration retain their exact identities; new sessions use streaming.

Opening the one-use launcher link authorizes that browser. A process-bound,
HttpOnly, SameSite=Strict session cookie lets the same browser reconnect after
reload for up to eight hours or until the launcher stops. The API token is never
saved in localStorage/sessionStorage. Manual tokens are verified before the UI
shows Connected; a 401 reveals reconnect controls and stops polling/dispatch.
Opening the plain URL in a different browser still requires a fresh launch link
or a valid Lab API token. A successful stream cannot run again after its bounded
model allowance is spent; Replay reuses the trace without another request.

The optional owner-authorized `/conversations/{session_id}/observations` endpoint
exposes allowlisted Runtime/Harness events, a bounded ordinary-output generation
projection and separately filtered recorder usage. Default application
construction leaves this endpoint disabled. Both views follow observed activity.
**Pause** or scrubbing stops following; **Follow live** resumes. **Replay** plays
retained arrival timings without another provider request. Provider particles
return when actual output chunks arrive. A chunk may contain several tokens.
Token totals are the latest run-wide recorder counts, independent of replay time;
missing reports stay unknown and partial totals are marked as subtotals.

For the configured local model, explicitly opt in:

```sh
.venv/bin/python -m lab_runner.observatory --live-local --runtime-config configs/runtime-local.example.yml --profile local-strong --max-calls 2 --consumer-image YOUR_IMMUTABLE_IMAGE
```

The local-model gateway reads its configured key file, uses literal loopback
only and enforces a shared request allowance without automatic retries. The
tested profile is `ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ`. The initial prompt asks
for numbers 1–20; longer requests exceeded this lab's existing 30-second
execution deadline during verification. `/no_think` is only a prompt hint, not
a guarantee or a change to model-server settings. Slow generations can time out;
the retained output then stays provisional and visibly interrupted.

The shared generation panel emphasizes first visible output, chunk arrivals,
the cumulative character curve and gaps between arrivals. These are client
observations, including transport time; they do not expose GPU phases or exact
per-token timing. The optional preview retains up to 4,096 ordinary-output
characters and 512 timing samples per call, with explicit truncation. Reduced
motion suppresses moving provider packets. Committed history starts collapsed
so it does not displace the live animation.

Both views show a bounded, owner-authorized user/assistant message preview read
from the existing history endpoint after the turn settles. Tool arguments and
reasoning blocks are excluded; history is separate from the content-free trace.
oMLX includes timing extensions in its usage object. The pinned SDK marks that
usage `unsupported` while retaining integer counts. Consistent counts from a
completed unsupported report appear with **†** and an explicit unqualified label;
the original recorder status and qualified totals remain unchanged. Untrusted,
partial and incomplete reports are not promoted. Counts arrive after completion,
not as individually timed token events.

The local gateway translates oMLX's exact empty `model: keepalive` prefill frame
into an SSE comment. This prevents a transport heartbeat from appearing to change
the response model and quarantining its real usage report. Actual content,
usage, model changes, malformed frames and unknown fields pass through unchanged
for normal SDK validation. This compatibility fix does not change model-server
settings, SDK packages or the recorder's accounting qualification.

This branch follows current main's Runtime 0.9.8, Harness 0.9.4 and unchanged
release checksums. The launcher requires a checkout or complete source archive;
installing the wheel alone does not provide the host fixture/authoring tree.
The release gate checks the extracted source's static shell, every vendor digest
and the exported model. No Blender, Node or model call is needed for that Python
asset check; JavaScript regressions run separately in CI.

## Standalone sample preview

Run from the integration-lab checkout:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory prototypes/observatory
```

Open http://127.0.0.1:8765/. No package installation, credentials, model calls,
database, or running lab stack are required. All browser dependencies are local.

## Included

- Real Three.js 0.180.0 rendering: procedural cutaway geometry, a Blender-authored
  Runtime core with embedded PBR textures, physical
  materials, environment lighting, bloom, particle channels, and orbit controls.
- Real GSAP 3.13.0 transitions: component focus, section/exploded views,
  and a seekable sample-run clock shared by both views.
- Two labelled fixtures: a successful tool run and a tool timeout. All counts,
  durations, outcomes and token reports derive from the selected fixture.
- Inspect timeline, selectable spans, component details, usage breakdown,
  event history, keyboard controls and reduced-motion handling.
- A readable generation chart and timeline if WebGL is unavailable. Browser
  geometry is illustrative; provider particles follow output chunk arrivals,
  not individual token boundaries or provider reasoning.

## Boundaries

The sample server uses only fixtures. The owned launcher connects to actual
installed SDK execution and PostgreSQL, with scripted provider responses by
default. It does not discover external provider credentials. Structural geometry
is generated in Three.js. Blender 5.2.3 LTS authors the Runtime core, its Cycles-baked ambient
occlusion and embedded colour, roughness and normal textures. The original
procedural core remains a loading/failure fallback.

## Blender asset authoring

The browser uses `assets/runtime-core.glb`. Its editable source is
`assets/runtime-core.blend`; `assets/runtime-core-preview.png` is a Cycles render.
The version, geometry count and export checksum are in
`assets/runtime-core.manifest.json`.

Regenerate these assets from this directory with Blender 5.2.3 LTS:

```sh
blender --background --factory-startup --python-exit-code 1 --python authoring/runtime_core.py
```

The script uses four CPU threads, sixteen samples, packed 1024px textures and
two exported meshes. Blender is an authoring dependency, not a viewer or Python
application runtime dependency. No Blender MCP server is required.

The UI accepts a fixture from `sample-runs.js`; the rendering and presentation
read the same bounded run model. Lab event history is in memory: up to 32 runs,
256 events each, with explicit truncation/missing-observation markers. Restarting
the UI loses that trace. This is not persisted run history or a billing record.
Runtime observations alone are best effort and cannot prove durable history or
exact token-stream timing. The metadata event list remains content-free. The
separate owner-filtered generation projection contains bounded provisional
ordinary response text; it excludes prompts, reasoning, tool arguments, provider
URLs and credentials.

The chosen design direction is a data terminal around a cinematic specimen.
The maintainer's explicit reference overrides the design skill's usual limits
on colour, glow, and glass for the scene. Controls remain restrained; colour
identifies Runtime (coral), Provider (cyan), and tools (gold).

## Dependencies

`vendor/manifest.json` records exact source URLs and SHA-256 digests. Three.js
includes its MIT license. GSAP retains its source notices and upstream README,
which links to its standard license. No dependency is executed by Python.

## Verification

See `VERIFICATION.md` for actual checks and limitations. The visualizer remains
a prototype; synthetic-stack verification is not live-provider certification.
