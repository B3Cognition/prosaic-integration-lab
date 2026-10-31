# Observatory port onto current main

Base: `1eae692748c3a3922f53150ded12905890dc9c73`. Branch:
`codex/prosaic-observatory-main`. The prior `codex/prosaic-observatory` branch
is historical; it is not the merge candidate.

## Scope and preserved contracts

Only Observatory assets, host launcher hooks, optional owner-scoped observations
and their qualification were ported. Main's Lab 0.7.0 metadata, Runtime 0.9.8,
Harness 0.9.4, both adapter pins, release checksums, Explorer and existing APIs
remain unchanged. This work does not merge or publish a release. It makes no
new real-model calls.

## Defects reproduced and fixed

- Lost workflow-start acknowledgement: observed the new regression fail with
  ordinary `needsResolution` versus observation `completed`. Observations now
  apply the same existing attachment-status projection; repeated reads preserve
  `needsResolution` without another provider request or workflow start.
- Incomplete source archive: the main-based archive omitted
  `prototypes/observatory`, and its extracted static-shell test failed with a
  missing-directory error. The source manifest now includes the complete tree.
  Distribution qualification checks required files, all 23 vendor hashes and the
  Blender GLB, then exercises the extracted source's static shell.
- Independent review found no critical/important issue. A minor missing-static-
  resource issue was reproduced and fixed with Starlette's exception middleware,
  so missing resources return 404 instead of escaping the ASGI shell.

## Verification before publication

- Clean current-main baseline: **1,980 passed**, **519.92 s**.
- Ported full Python suite: **1,998 passed**, **503.77 s**. The later static-404
  correction also passed the focused ten-check launcher/distribution/status suite.
- Focused integration/distribution checks: **49 passed**.
- Extracted corrected archive: **8 Python checks and 11 JavaScript checks passed**.
- Vendor provenance and GLB hashes verified; staged redacted secret scan clear.
- Current-main consumer build succeeded against the five audited release wheels.
- Isolated wheel and rebuilt-source consumption passed, including public-index
  verification, installed-payload audit, isolated imports, `pip check`, public
  construction and the extracted Observatory gate. Manifest:
  `36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.

Full updated source, isolated wheel/rebuilt-source consumers, PostgreSQL context
acceptance and the four supported Linux/database CI cells are qualified on this
branch before final handoff. Results are recorded when observed; starting a job
does not constitute a passing check.

## Review note

The recorder read uses its bounded default page of 1,000 calls. The supported
launcher allowance is at most 128 calls, so the tested default use stays below
that boundary. Custom high-budget consumer configurations need explicit paging
or truncation reporting before claiming full-run totals beyond that limit.

Source/complete-archive launch remains the host-fixture contract. A wheel-only
installation does not contain the source fixture/authoring tree. The visualization
remains best-effort and bounded in memory; it is not durable billing evidence or
an individual-token arrival trace.
