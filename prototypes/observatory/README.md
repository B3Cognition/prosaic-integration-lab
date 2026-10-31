# Prosaic Observatory prototype

An interactive visual prototype inspired by the plant-cell reference supplied
by the maintainer. The approved scope is one detailed execution scene first,
with Live and Inspect views and an optional authenticated Integration Lab feed.

Verified real-model screenshots: [Live](.taste-skill/observatory-real-qwen-live-final.png),
[Inspect](.taste-skill/observatory-real-qwen-inspect-final.png) and
[phone](.taste-skill/observatory-real-qwen-phone-final.png). The shown 549-token
report carries the unqualified marker described below.

## Run with the Integration Lab

Use a checksum-audited environment installed from `dependencies/releases.json`
and a consumer image built with `scripts/build_consumer.py`:

```sh
.venv-observatory/bin/python -m lab_runner.observatory --consumer-image YOUR_IMMUTABLE_IMAGE --max-calls 12 --fixture-latency 1.5
```

The launcher starts an owned PostgreSQL stack and a bounded synthetic HTTP
provider. It opens a one-use connection link; the API credential stays in browser
memory. Use **Start lab test** with `Find players` for two provider calls, a
registered tool and workflow waiting, or `Hello` for a completed turn. Ctrl+C
stops the UI and verifies cleanup of its owned Docker resources. Default fixture
mode needs no paid provider credential. `--no-open` writes a private launch file.

The optional owner-authorized `/conversations/{session_id}/observations` endpoint
exposes allowlisted Runtime/Harness events and separately filtered recorder usage.
Default application construction leaves this endpoint disabled. Live follows
observed activity; Inspect pauses following and replays retained observations.
**Follow live** resumes. Provider particles represent activity, not individual
tokens. Token totals are the latest recorder counts, independent of replay time;
missing reports stay unknown and partial totals are marked as subtotals.

For the configured local model, explicitly opt in:

```sh
.venv-observatory/bin/python -m lab_runner.observatory --live-local --runtime-config configs/runtime-local.example.yml --profile local-strong --max-calls 2 --consumer-image YOUR_IMMUTABLE_IMAGE
```

The local-model gateway reads its configured key file, uses literal loopback
only and enforces a shared request allowance without automatic retries. The
tested profile is `ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ`. The initial short prompt
is chosen to fit this lab's existing 30-second execution deadline; slower or
longer generations can time out. It does not change model-server settings.

Both views show a bounded, owner-authorized user/assistant message preview read
from the existing history endpoint after the turn settles. Tool arguments and
reasoning blocks are excluded; history is separate from the content-free trace.
oMLX includes timing extensions in its usage object. The pinned SDK marks that
usage `unsupported` while retaining integer counts. Consistent counts from a
completed unsupported report appear with **†** and an explicit unqualified label;
the original recorder status and qualified totals remain unchanged. Untrusted,
partial and incomplete reports are not promoted. Counts arrive after completion,
not as individually timed token events.

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
- A readable timeline if WebGL is unavailable. Browser graphics are illustrative;
  particles are activity marks, not individual tokens or provider reasoning.

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
exact token-stream timing. No prompt, response, tool argument, provider URL or
credential is exposed in the observation projection.

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
