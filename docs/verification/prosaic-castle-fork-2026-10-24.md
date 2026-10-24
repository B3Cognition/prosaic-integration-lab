# Independent Prosaic Castle qualification — 2026-10-24

The independent local fork preserves Castle's Git history and all legacy
production modules. No original Castle changes, backports, push, release or live
model calls were performed. Memory and SUE remain independently disabled.

## What changed and who owns it

- `prosaic-castle` 3.4.2 is the independent worker distribution. Base installation
  retains LanceDB/PyArrow/YAML; model/NLP dependencies are explicit extras. The
  guarded `prosaic-castle-provider` command refuses detected coinstallation with
  the original distribution. Legacy imports/commands require separate environments.
- Raw `memory-fts-v1` ranking and all scope/provenance/revision checks are
  unchanged. Dense and recency are opt-in. Python's separate shipped-rule API
  reproduces the four rules with explicit project/time context; custom rules
  fail admission. Original SOAR and model transports remain compatibility paths.
- Castle owns retrieval and source evidence. Runtime owns dispatch, budgets and
  usage. Harness owns accepted state, receipts and resume. Lab owns source
  authorization and independently optional SUE/judge/entity/origin workflows.
  Optional jobs never run during normal retrieval or write source corpora.
- SUE's pure engine, execution identity and adapter payload are unchanged. Lab
  continues to admit at most 16 sources/64 KiB, distinct from legacy standalone
  SUE's 2 MiB/2,000-drawer path. Reports remain advisory.

Source lineage: original `53637196cc215e9bd5b85b9253b3430b2781b884`, fork
runtime `971dd4fe280667e7b61ea2e4b6e262ab77eaad43`, final fork source
`e810a016abab7b96b4c905b04314562065d5fed3`. The latter changes CI/archive
configuration only: legacy extras are explicit in full-suite jobs and the
inherited original PyPI publisher is archived. All runtime wheel bytes match.
Lab implementation is `0fd6567`, optional-job changes `31529bf`/`f7fc9e1`,
installed tests `cce2a72`/`76e447d`, followed by source-profile/document updates.

## Artifact proof

| Wheel | SHA-256 |
| --- | --- |
| Worker | `3d8b1d9da57b9374ca8cdd6260c793cc105788ae242dc44116d294781eee1915` |
| Adapter | `7131c12e9b1bc36cb302874d7c5dbbd349de42d74581f8b5ec9c2981aabbbc35` |
| SUE | `7dfe0697de596e745b5934570d449238d28db380e5e800a96a606d01eed0bc4d` |
| Lab | `635eb162a208c236a7d12ed95b6829a7a5e4150b0b3e61e6928b3d0eb391eed3` |

Every direct/rebuilt pair is byte-identical, including all 140 worker and 209
Lab ZIP members. Installed Lab files were checked against both wheel builds.
SUE/adapter members also match their qualified historical artifacts; timestamp
differences explain archive hashes. SUE identity remains
`bbde4669d1eb069dcb8c72e121cd08be4ca953b349f9243b9e650e0d1b596f0b`.
The [candidate profile](../../dependencies/prosaic-castle-source-2026-10-24.json)
pins the final worker source archive too. A fresh Python 3.12/macOS ARM64
[hash-locked worker](../../dependencies/prosaic-castle-worker-macos-arm64.lock)
installed offline from retained dependency wheels and passed `pip check`.
Torch, sentence-transformers, spaCy and SML are absent from that environment.

## Verification

Final qualification passed:

- Default Lab profile: 2,033 passed in 501.62 s with no Castle/SUE installed.
- Full enabled Lab profile: 2,107 passed in 594.31 s; zero skips and one existing
  Starlette deprecation warning. Installed final candidate: all 76 cases pass
  on each of PostgreSQL 16.15 and 18.6, 152 total, zero skips/failures/errors.
  Both exact inventories and owned database cleanup checks pass.
- Installed frozen hackathon matrix: 24/24, 88 synthetic requests and 1,320
  reported fixture tokens. Direct 8/8, critic-author 8/8, SUE 8/8. Normal and
  network-denied replay each added zero requests. Eight historical host examples
  pass with read traces and all eight reject without traces. This is mechanics
  evidence, not model-quality evidence.
- Pure SUE package: 75 tests; direct/rebuilt standalone smoke passes all nine
  lenses. Optional model jobs: 36 focused tests, including model-wire prompts.
- Final Castle main/isolated suites: 2,558 + 48 passed (2,606 total), 12 existing/
  explicitly unqualified SML skips and 108 slow/stress/benchmark deselections.
  Combined local coverage is 85.59%, above the unchanged 85% gate. Original
  LanceDB deprecation warnings remain. Supervision's guarded aggregate peak
  was 258.7 MiB with coverage enabled; production budgets are unchanged.

The installed gate requires exactly 76 distinct named tests: six memory tests,
14 SUE tests, all 24 hackathon cells on each of file/PostgreSQL stores, and
eight model-job tests. It verifies installed artifacts and candidate hashes,
removes inherited pytest filters, requires zero skips/failures/errors, checks
separate database runtime roles and verifies owned fixture removal. Tests cover
source removal, frozen snapshots, wrong owner, stale revisions, failed/unknown
usage, unavailable optional/required memory, saved-receipt adoption, concurrent
decisions, no redispatch and advisory fallback with untouched ranking tails.

Commands (use the absolute prepared environment paths from the evidence logs):

```sh
python -m pytest -q
python -m pytest -q tests/unit tests/functional tests/sue_review tests/requirements_review
python -I -m lab_runner.prosaic_castle_fixture --enable --postgres-version 16 ...
python -I -m lab_runner.prosaic_castle_fixture --enable --postgres-version 18 ...
python -I -m lab_runner.requirements_review_v1 --fixture --output NEW_DIRECTORY
python -I -m lab_runner.requirements_review_v1 --replay SAME_DIRECTORY
```

The [user guide](../prosaic-castle.md#maintainer-qualification-command) gives the
full installed command. Raw logs, exact artifacts, locks, sanitized failed runs,
case reports, matrix/replay evidence and source hashes are retained locally in
`reports/prosaic-castle-fork-20261024`; its manifest binds every retained file.
The final accepted receipts are the `qualified-r2-pg16`/`qualified-r2-pg18`
directories. Earlier failed and intermediate successful receipts are retained
under their original distinct names. Candidate wheels rebuilt from source
archives are byte-identical; installed bytes match the rebuilt wheels as well.

## Findings fixed without relaxing checks

1. Actual Castle snapshots failed SUE admission because Castle protocol v1
   hashes ordered fields while Lab checked sorted JSON. Lab now reconstructs
   the defined exact wire preimage after JSON normalization and also preserves
   the earlier Lab encoding for historical snapshots. All fields/text remain
   hashed; tampered revision, wing, origin and CRLF bytes still reject.
2. Judge prompting specified a permutation without a relevance objective or
   direction. It now explicitly requests query relevance, most to least.
   Corpus-origin prompting now supplies substantive criteria too. Wire-level
   regressions prove those instructions reach the model.
3. Qualification originally checked supplied/installed payload equality without
   pinning all candidate artifacts or requiring the eight new job cases. It now
   enforces fixed worker/adapter/engine hashes and the exact 76-case inventory.
4. A new entity test invalidated its quote while trying to test input drift.
   The drift now appends text, preserving the expected conflict assertion; a
   separate invalid-context check requires rejection before run creation/calls.

The initial unpartitioned Castle run also exposed missing test-only ChromaDB
and supervision failures after embedding imports exceeded the parent's fixed
RSS budget. Installing the oracle dependency and using the repository's existing
fresh-process supervision runner resolves this without changing resource limits
or assertions. All original diagnostic outputs remain retained.

## Retrieval regression and remaining gates

The unchanged 36-document/40-question benchmark (10 development/30 held-out,
three cold processes/two warm passes) reproduces every prior metric for all
three arms. Held-out recall@5 is 0.986667; no quality metric changed. Warm median:
raw FTS 4.25 ms, scoped FTS provider 14.24 ms, dense profile 301.65 ms. Provider
scope/provenance/dedup checks remain intact. Functional gates pass with zero
network/optional-engine import attempts and unchanged source hashes.

Local consumer qualification is macOS ARM64; PostgreSQL 16.15/18.6 runs on
Linux ARM64. This does not qualify native Linux consumers. Native Linux
AMD64/ARM64, real SML equivalence, deployed custom-rule inventory, live transport
parity and a blind repeated review-quality comparison remain separate gates.
The local five-root inventory found one exact shipped rules file, no custom
files and no unreadable paths; it does not inventory other deployments.
The model-facing memory-tool adapter still needs Runtime's explicit error
capability; this integration uses host snapshots. No live spend was authorized.
Historic r7 profiles, normal SDK pins, original hackathon ZIP/scorer and all old
evidence retain their original bytes. No original Castle functionality is deleted.
