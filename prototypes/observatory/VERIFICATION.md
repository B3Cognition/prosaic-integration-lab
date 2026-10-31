# Observatory prototype verification — 2026-10-30

Initial checkpoint scope: standalone sample-data prototype in `prototypes/observatory/`. No Python
application, package configuration, released dependency, or existing user file
was modified. No model, database, or external provider was contacted.

## Browser checks

Verified in Chromium through Playwright against the loopback static server:

- Real WebGL rendering and actual GSAP playback/camera transitions.
- Live/Inspect switching, keyboard arrows, playback seeking, component focus,
  application-span selection, overview reset and completed exploded transition.
- Success: 24.0 s, two provider calls, 4,100 input + 640 output = 4,740 tokens,
  five timing lanes, eight spans and sixteen ordered boundary events.
- Timeout: 13.8 s, one provider call, 1,640 input + 128 output = 1,768 tokens,
  six spans and twelve ordered boundary events; visible tool failure.
- Before the first completed usage report, the display is unknown (`—`), not
  zero. At 21.5 s, the second report becomes available and the total is 4,740.
- At widths 1440, 1024, 390 and 320 CSS pixels, the document has no horizontal
  overflow. Desktop, component focus, exploded view and phone screenshots were
  inspected. Label collision handling was added after the narrow-screen check.
- Reduced-motion page load does not autoplay. Camera selection is immediate.
  A changed preference updates the scene and pauses playback.
- Simulated `WEBGL_lose_context` opens the Inspect fallback with the complete
  eight-span timing view. This tests context-loss recovery, not every GPU driver.
- Hiding and showing the scene skips zero-sized rendering and resumes correctly.
  This fixed framebuffer warnings found during resize testing.
- The latest normal rendering/resize pass has zero console errors or warnings.
- All resource requests are local to the prototype server; Public Sans and
  IBM Plex Mono load.

Static detail was merged by material, indexing and component while preserving
movable parts and picking. Render calls fell from approximately 622 to 110 for
the same 216,538 triangles (including postprocessing). One local 20-frame sample
averaged approximately 8 ms per animation frame; this is a development check,
not a performance guarantee or device qualification.

## Source and dependency checks

```sh
node --check prototypes/observatory/observatory.js
node --check prototypes/observatory/scene-renderer.js
node --check prototypes/observatory/sample-runs.js
```

All passed. HTML identifiers are unique and form/ARIA references resolve.
All twenty-two vendored file SHA-256 values match `vendor/manifest.json`.

The design inspector passed with zero failures and two warnings: dense 11–12 px
annotations, and a blank-band heuristic on the first cold-loading desktop shot.
The latter captured the loading state; the completed desktop scene was inspected
separately through Playwright. Component labels now stay hidden until graphics
initialization, avoiding overlapping labels during startup. The scene is the
dominant visual; its detailed biological reference is still richer in materials
than this procedural engineering specimen. This is a first art-direction
prototype, not a claim of photorealistic equivalence to that reference.

## Existing Python suite limitation

Executed the repository-prescribed command:

```sh
.venv/bin/python -m pytest -q
```

Collection stopped with twenty errors. This `.venv` contains Runtime 0.7.0 and
Harness 0.6.1; current existing tests import newer symbols including
`WorkflowBindings`. This prototype imports neither package and changes none of
the affected files. The `.venv-latest` interpreter symlink is broken on this
machine. Dependency environments were not repaired or substituted to claim a
passing suite.

The Python suite, consumer image build and real-stack acceptance are not passing
evidence for this prototype. No released lab integration, installed-wheel test,
live-provider certification, durable telemetry feed or billing claim is made.

## Blender asset checkpoint — 2026-10-30

The maintainer authorized installing Blender for improved visual quality.
`brew install --cask blender` installed Blender 5.2.3 LTS in
`/Applications/Blender.app` and linked the `blender` command. No third-party tap
was trusted or modified. The application version and actual background asset
generation were verified.

Executed:

```sh
blender --background --factory-startup --python-exit-code 1 --python prototypes/observatory/authoring/runtime_core.py
```

Exit code 0: actual Cycles ambient-occlusion bake, packed `.blend`, glTF 2.0
export and a 640px Cycles portrait render. The first export attempt exposed a
changed Blender enum (`PNG` is not an export format in 5.2); it was corrected to
`AUTO` before the successful full run.

Verified export: two meshes, 97,824 triangles, two materials, three embedded
images, 7,905,220 bytes. The GLB header/length and manifest SHA-256 match. The
glTF loader is pinned to Three.js 0.180.0, bringing vendor provenance to 23 files.

The browser confirms `assetStatus: blender`. The Cycles portrait and browser
Runtime close-up were visually inspected. Browser rendering uses approximately
107 calls and 261,562 triangles including postprocessing; the earlier performance
figures above describe the previous procedural core. At this checkpoint sample
data remained the only telemetry source.

## Authenticated Integration Lab checkpoint — 2026-10-30

The later integration adds an optional host-scoped SDK observer, owner-filtered
observation endpoint, separate recorder-backed token projection and owned-stack
launcher. All execution still uses public released SDK APIs. The visualizer does
not execute provider reasoning or generate one particle per token.

Created `.venv-observatory` from the locked third-party requirements and the five
exact cached release wheels. `scripts/audit_install.py` verifies installed import
payloads against those wheels, not just package version metadata. Manifest SHA:
`87862e1d37fd2f2cc1b8c6cd9965289887b0c056b26e81781dad4929a70a36c6`.
Runtime 0.9.3, Harness 0.8.2, Prosaic 0.4.1 and both PostgreSQL adapters 0.3.0.
An existing `.venv-native` failed its payload audit and was not used as evidence.

Verification results:

- Full fresh-environment suite: **1,657 passed, 1 failed**. The existing
  `test_controls_restore_only_their_own_marks_and_preserve_provider_cooldowns`
  imports `CapacityStore`, absent from pinned Runtime 0.9.3. No dependency or
  library patch was introduced to bypass it.
- Compatible suite, excluding that single test: **1,658 passed, 1 deselected**.
  A new CSP regression accounts for the additional passing test.
- Focused final Python checks: **14 passed** across observation redaction,
  actual SDK events, owner/tenant filtering, launcher security and existing chat.
- JavaScript regression checks: **9 passed**. The poll-settlement race,
  `needsResolution` lifecycle and dangling tool completion cases were first
  observed failing, then passed after fixes. Zero-input reported usage stays known.
- Rebuilt the isolated consumer image with the new observation module in its
  explicit public source inventory. Image:
  `sha256:bc345eee5d835514bb6cf75dd7aad724adf0ed46ab39b26840b5b00a51b8039a`.
- Final real-stack conversation acceptance on that image: **97 passed, zero
  skipped**, released payload audit verified, **438.18 s**, owned cleanup
  verified. Evidence: `.lab/0277f82fd35a4edf84bd9bcf53b185b5/` and
  `.lab-observatory-current-acceptance.log`.
- All **23** vendored dependency digests match. The Blender GLB retains its
  documented checksum and browser diagnostics confirm all three PBR maps load.

Chromium exercised the actual host application, installed SDKs, PostgreSQL 16
and bounded HTTP synthetic provider on owned stack
`3e978e2cd5694273a744da7341e92402`:

- `Find players`: actual provider activity before completion; usage unknown
  until a recorder report; two provider calls, `fixture_lookup` **27 ms**,
  **200 input + 50 output = 250 tokens**, eleven events, **3.441409 s** observed,
  then workflow waiting. Event-history buttons allow inspection of tiny spans.
- `Hello`: one provider call, **100 + 25 = 125 tokens**, four events,
  **1.622764 s**, completed. Starting a new run switches back to Live.
- Forced HTTP 503: failed provider in red, failure code `providerFailure`, four
  events, **1.630643 s**, unknown usage. No automatic provider retry.
- Real endpoint authorization: owner **200**, another actor **404**, anonymous
  **401**. Sanitized receipts retained privately in the owned evidence directory.
- Inspect and seeking pause following; provider call count remained **4** after
  inspection and polling. Reads did not trigger model execution.
- Width **390 px**: document width **390 px**, functional timeline and controls.
  Desktop and phone screenshots were visually inspected. This exposed a stale
  tool details card carried into a subsequent run; new runs now clear selection.
  A fresh browser run verified tool selection followed by `Hello` clears the
  card and completes normally with 125 reported tokens.
- Corrected CSP to permit same-origin glTF embedded-image blob fetches. The
  successful browser pass has **zero console warnings/errors** and
  `assetTexturesReady: true`.
- Both earlier UI stacks and this test stack completed owned-resource cleanup.

Security and evidence boundaries: credentials stay in a closure, launch codes
are one-use with a short expiry, trace reads retain host grants and frozen owner
attribution, projections drop content/arguments/URLs/credentials. Event history
is bounded in memory (32 runs, 256 events each); missing completion stays unknown.
No external or paid provider was contacted. These results do not certify a live
model, durable trace history, or exact streamed token timing.

An intentionally running review preview was started afterwards with a fresh
one-use launch link queued in the Codex browser. Owner:
`2a7ee39d3a444dd9ba6d2546bd67a992`; loopback UI:
`http://127.0.0.1:54392/observatory/`; synthetic provider allowance: 12 calls.
Launcher PID at handoff: `50938` (SIGINT performs its owned cleanup). This preview
is separate from the cleaned test stacks. The earlier sample-only server was
stopped.

## Real local-model checkpoint — 2026-10-30

The maintainer explicitly requested a real-model check. Used the configured
authenticated loopback oMLX server and actual
`ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ`, with an eight-call test/review allowance.
No external hosted provider, model-server setting or installed SDK was changed.

The first owned UI stack (`279b63d3e8a44a73a63dcadfa186683a`) made two
conversation requests: a 30.033163 s timeout with unknown usage, then a completed
18.314137 s request returning `Ready.`. Its recorder retained 520 input and
31 output tokens but marked usage `unsupported`. A third bounded gateway probe
confirmed oMLX adds timing fields and duplicate input/output aliases inside
`usage`; those extensions trigger the pinned SDK's conservative unsupported
classification. Probe reply `Ready`, 64 input + 37 output, 22.58 s. This probe
was not a conversation/recorder run and is not counted as one.

The Lab now projects consistent provider-reported counts separately, labeled
unqualified, without changing recorder status or qualified totals. It also
shows bounded text-only owner history in both views and retains the model label.
Regression checks were observed failing before implementation, then passed:
13 focused Python checks and 11 JavaScript checks. The isolated updated consumer
image is
`sha256:94fb02c0f56774e2212952e0dcf4f1c506fc29728a8a9aae20188822f368e4c6`.

Updated real UI stack (`c56f91c66dd64392bb9037ae411353be`), with five calls
remaining, exercised three more conversation requests:

- `1defba3faf08435290980061da387f24`: completed in **4.473916 s**; actual reply
  `Ready.`; one provider request, four observed events, **520 input + 29 output
  = 549†** in both Live and Inspect. Ledger measurement stays `unsupported`.
- `32897d384302431f96d6b81f438f2e07`: a longer prompt hit the existing
  **30.034344 s** deadline. Active provider flow was captured in Live; Inspect
  paused following and retained the two active spans. Final state timed out,
  unknown token counts, one ledger call with `unresolved` measurement. No retry.
- `7671e9bfe6e44a1dbbb496cf53447844`: completed in approximately **4.1 s**;
  actual reply `Ready.` and **549†** agreed across both views. The same owner
  history is visible in both, with tool arguments/reasoning omitted.

Sanitized observation receipts are retained privately in that owned evidence
directory. Public recorder rereads confirmed exactly one call per conversation;
inspection did not add calls. Six model calls were used in total, including the
separate metadata probe, leaving two for the review preview.

At 390 CSS pixels the document remains exactly 390 pixels wide. Actual messages,
unqualified token labels and the responsive timeline remain readable. Desktop
Live, desktop Inspect and phone screenshots were visually inspected. Browser
console: **zero warnings and errors**; Blender PBR maps loaded successfully.

These are non-streaming provider calls. The animation follows real request
activity; it is not a measurement of individual token arrival times. A successful
short response does not qualify arbitrary prompts or native tool behavior on
this local model. The 30-second deadline remains a limitation for slower prompts.

The compatible full suite after these changes passed **1,659 tests**, with the
same single existing `CapacityStore` incompatibility deselected, in **303.30 s**.
Both real-model UI test stacks completed verified owned cleanup. The earlier
synthetic preview launcher was no longer running; any remaining exact resources
were checked against its ownership labels before removal. A fresh real-model
review stack is intentionally left running with the two unused calls; none of
those review calls was spent during testing.

Final updated-image PostgreSQL 16 conversation acceptance: **97 passed, zero
skipped**, payload audit verified, **464.65 s**, owned cleanup verified. Evidence:
`.lab/eb2e581a8cf4422c98fb9a29aaab942b/` and
`.lab-observatory-real-acceptance.log`. This synthetic acceptance is separate
from the actual local-model results above. The five installed release payloads
were audited again successfully; all 11 JavaScript regressions passed again.

Current real-model review preview:
`http://127.0.0.1:55942/observatory/`, owner
`e513af72a6b0468eb104c832564cb3fe`, two-call allowance. A fresh one-use connection
link was queued in Codex's browser; its private source is the owner's
`secrets/chat-launch.json`. The earlier preview checkpoints above are historical.

## Isolated work-package publication checkpoint

The publication branch `codex/prosaic-observatory` starts at shared baseline
`dc473daafb7b80d58afd5df8465868d3db14af0d`. It includes the Observatory, chat
launcher/UI, its released SDK prerequisites and their regression coverage.
Unrelated native benchmarks, local submission commits, private run state and
browser automation logs are excluded. The original checkout is preserved.

Fresh verification on this isolated source tree:

- Full Python suite: **964 passed**, no exclusions, **91.27 s**. This count is
  for the isolated package; the larger shared-checkout suite above includes
  separate benchmark work.
- JavaScript regressions: **11 passed**; entry modules parse successfully.
- All **23 vendor checksums** and the Blender GLB digest match their manifests.
  Upstream vendor bytes and licenses are preserved, including original line
  endings; authored-file whitespace checks passed.
- Redacted secret scans of both the staged diff and the source commit found
  **zero leaks**. Three owner-authorized demo screenshots are included; no
  credentials, private receipts or raw model logs are published.
- Isolated consumer build succeeded with the five audited wheels. Image:
  `sha256:21a60cc7742ca334bede985c733811417bb20c0a8b20c5b80f65803469cbd6d2`.
- Fresh PostgreSQL 16 conversation acceptance on that image: **97 passed, zero
  skipped**, **453.07 s**, payload audit and owned cleanup both verified.
  The sanitized [acceptance receipt](.taste-skill/package-acceptance.json) records
  the source commit, image digests and exact result. Raw evidence stays private.
