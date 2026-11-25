# Explorer typography and chapter navigation — 2026-10-25

This follow-up replaces IBM Plex with locally bundled Instrument Sans for the
interface and Geist Mono for code. Both Fontsource packages are pinned to 5.3.0;
their OFL licenses ship with the generated assets. No external font service is
required.

## Layout regression and correction

At 1440 × 900, the previous content-driven layout produced document heights of
941 px for the ecosystem, agent and pool chapters, 988 px for workflow and 963 px
for results. Navigation ended below the viewport (approximately 908–955 px).

The application now occupies the window, with the chapter footer outside the
scrolling content region. At 1440 × 900, the sheet remains 836 px high and the
footer ends at 867 px across chapters. Longer lessons and live execution controls
scroll within their own keyboard-focusable regions. Changing chapters resets
lesson scroll position. Content is retained rather than truncated.

## Verification

- Frontend unit tests: **15 passed**.
- TypeScript and Vite production build: **passed**.
- Python source archive and wheel builds: **passed**. Both distributions contain
  web assets matching the current source byte-for-byte, including eight font
  files and the new licenses, with no stale Plex assets. This checks packaging
  contents; it is not a new clean-install release qualification.
- Chromium browser tests: **8 passed**, including the existing theme, playback
  and synthetic live-control regressions.
- The navigation regression checks all five chapters at 1920 × 900, 1440 × 900,
  1280 × 720, 768 × 1024 and 390 × 844. It verifies consistent frame height,
  visible Previous/Next controls, no outer-document overflow, retained navigation
  after scrolling, and scroll reset on chapter changes.
- Browser font checks verify loaded Instrument Sans and Geist Mono faces and
  same-origin font resources. The dependency install reported zero vulnerabilities.
- Taste v2 browser inspection: **0 failures, 0 warnings** in each light/dark run.
  Desktop, tablet and mobile screenshots were opened and reviewed in both modes.
- Taste source lint: zero failures; one existing false-positive warning for
  `box-shadow: none`.

This is frontend qualification on the local Chromium environment. No provider
calls were made, and the Python suite and live model benchmarks were not rerun
for this typography/layout change. Historic release verification remains in its
original ledgers.
