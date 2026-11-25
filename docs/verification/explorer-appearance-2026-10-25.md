# Explorer appearance follow-up — 2026-10-25

Frontend-only refinement after the initial Explorer implementation. No SDK pins,
execution contracts, permissions, budgets or provider behavior changed. No real
model calls, new live benchmark or Linux/database qualification were performed.

The header now offers System, Light and Dark. System is the initial preference
and follows device changes; explicit choices persist under the single local
storage key `prosaic.explorer.appearance`. No credentials or execution records
are stored there. Invalid/unavailable storage falls back to System and permits
session-only switching. Appearance changes preserve component selection,
playback position and admitted-run receipts.

The visual refinement strengthens the title and node typography, gives the
inspector a distinct reading surface, and highlights selected nodes against a
quiet graph canvas. Existing keyboard, list and mobile behavior is retained.

## Design and browser inspection

Taste v2's app workflow retains Framed sheet (seed 1548770335) for Light. Dark
adapts True-black flat (seed 622026595) to the same Explorer layout: neutral
black elevation with a readable teal data accent, without gradients or glows.
No styles were redrawn. IBM Plex, the document mark and the actual Markdown →
permission → receipt graph remain the product's face and signature element.

The unmodified Taste inspector ran against the production bundle in both media
modes at 1440/768/390 widths: **0 FAIL / 0 WARN** in each theme. Light was
explicitly emulated through the inspector's CDP browser helper; the host's
default dark preference exercised Dark. Every emitted screenshot was opened.
Additional explicit-selector screenshots were inspected in both modes, including
the initial mobile list. No page-level horizontal overflow was observed.

The app critique confirms that the handoff graph remains the largest region;
sheet and reading-panel edges align; teal marks selection and graph data;
displayed versions and counts are unchanged; unknown/zero states remain honest;
graph labels remain inside their nodes; and the phone folds navigation while
keeping Appearance available. The long phone lesson list remains a deliberate
reading layout, with the optional graph available through its existing control.

Sampled WCAG contrast ratios from the rendered CSS tokens:

| Text pairing | Light | Dark |
| --- | ---: | ---: |
| Main text / surface | 18.43:1 | 17.32:1 |
| Secondary text / raised surface | 5.93:1 | 8.31:1 |
| Secondary text / selected node | 5.90:1 | 7.79:1 |
| Accent text / selected node | 5.51:1 | 7.67:1 |
| Warning text / warning surface | 7.38:1 | 9.84:1 |

These are sampled palette checks, not a claim of a full accessibility audit.
Source Taste lint returns 0 FAIL / 1 WARN for the existing `box-shadow: none`
that removes React Flow's default shadow; the browser inspector finds no shadow.

## Regressions

- `npm test --prefix frontend/explorer`: 15 passed.
- `npm run build --prefix frontend/explorer`: TypeScript and production bundle passed.
- `EXPLORER_PYTHON=<test-python> npm run test:browser --prefix frontend/explorer`:
  6 Chromium tests passed. The new appearance test first failed because the
  control did not exist, then passed after implementation.

Coverage includes system preference changes, saved choice after reload, invalid
and inaccessible storage, mobile control visibility, no overflow, retained
playback step and zero theme/playback mutation requests. The existing synthetic
live control test also switches appearance during an admitted run and retains
its receipt/cancel control with exactly one dispatch. Existing bootstrap,
escaped-output, cancellation and lost-response identity regressions remain green.

Local tooling still emits the existing React Flow `use client` bundler warning
and Node 26/Playwright deprecation/color-environment warnings. No browser runtime
errors were observed. The original Python and installed-distribution evidence is
retained separately in [the initial ledger](explorer-2026-10-25.md).
