# Explorer review and PR qualification — 2026-10-25

This qualifies the post-0.6.2 guided onboarding and Explorer branch against the
released SDK train: Core 0.4.1, Runtime 0.9.8, recorder 0.3.0, Harness 0.9.4 and
store 0.4.0. The SDK manifest remains
`36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.
No released artifact, benchmark Markdown/input, SDK pin or live allowance changed.

## Independent review

Review covered the complete branch from main `46a2d80`, including the coordinator,
HTTP/launcher, public Runtime CLI integration, frontend, packaging, CI and guides.
Two P2 interface findings were reproduced with failing browser tests and fixed:

1. Explicit chapter navigation retained an unrelated Simulation/Live body under
   the new chapter heading. Navigation now opens Documentation and stops playback;
   scenario selection and Live entry explicitly choose their mode. Intent and
   receipt state survive navigation.
2. Polling repeatedly selected the current intent's terminal receipt, overriding
   historical receipt selection. An observed terminal request is now distinguished
   from pending submission recovery. Explicit selection also invalidates older
   in-flight refresh responses. A lost POST still recovers the exact admitted
   request, without a new dispatch.

The new contract regression also failed before the receipt fix. All new tests
pass after the fixes. An initial browser test revision tried to leave Live via
a documentation-only footer; correcting it to use chapter navigation made the
test exercise the actual available control. Independent re-review found both
findings resolved and no further actionable issue.

## Final local checks

Host: macOS ARM64, Python 3.12.15, Node 26.12.1, pinned Chromium/Playwright 1.58.2.
`LAB_PY` below denotes the environment containing the verified released SDKs.

| Command / gate | Result |
| --- | --- |
| `"$LAB_PY" -m pytest -q` | 1,979 passed, one existing Starlette deprecation warning, 489.87s |
| `"$LAB_PY" -m pytest -q tests/native_acceptance` | 14 passed, 27.97s |
| `npm ci --prefix frontend/explorer --ignore-scripts` | Passed; zero audit vulnerabilities |
| `npm test --prefix frontend/explorer` | 16 passed |
| `npm run build --prefix frontend/explorer` | TypeScript and Vite production build passed |
| `EXPLORER_PYTHON="$LAB_PY" npm run test:browser --prefix frontend/explorer` | 10 passed, 19.9s |
| `"$LAB_PY" -m build --outdir <private-output-directory>` | Wheel and source archive built |
| `scripts/conversation_distribution_smoke.py` with those archives and `dependencies/releases.json` | Passed public-index, payload, isolated import, construction, `pip check`, installed Explorer and standalone CLI gates; cleanup verified |

Each clean wheel/rebuilt-source consumer passed all 51 standalone evaluation
fixtures, plus the installed documentation-only Explorer bootstrap/resource smoke.
All 15 bundled web files in the original wheel and source archive match the final
frontend source build byte-for-byte, including eight fonts and both OFL licenses.
The checks configure synthetic providers only: **zero real model invocations**.

Qualified development archives (not published or substituted for released 0.6.2):

- Wheel SHA256: `9f790206b3816add74c19bc4fada1a6fe4b30767e7729e05a6056737bdfa67e4`.
- Source archive SHA256: `6636c481511324774c8feac607ae90e15a0cb9a1071c9e3a6b61d7e824823a07`.

These archives contain the final runtime/frontend code; this qualification note
was added afterward. The required CI builds qualify the complete committed tree.
Existing React Flow bundler and Node/Playwright tooling warnings remain; no new
frontend runtime errors were observed. The prior [visual/layout inspection](explorer-typography-navigation-2026-10-25.md)
records both themes and five viewport sizes; this review changes no CSS or fonts.

## Platform and merge boundary

The local distribution check did not execute Docker/PostgreSQL acceptance.
The PR must pass its exact head's four required Linux AMD64/ARM64 × PostgreSQL
16/18 cells, including real stack cleanup, installed distributions, locked
frontend reproduction and the Linux Chromium lane. Local results do not certify
that matrix. This request prepares a PR; it does not merge or publish a release.
