# Optional SUE workflow and requirements comparison — 2026-10-24

This is synthetic local qualification of an unpublished optional candidate.
Memory and review remain independently disabled by default. No live inference,
historic allowance reuse, package publication, submission, push or merge is
included. Existing Castle PRs107–109 and selected r7 archives remain unchanged.

## Boundaries and tradeoffs

Castle adds `cognitive-castle-sue`0.1.0 in its own branch, importing as
`castle_sue`. Canonical reducer/policy files are byte-identical; the new package
has no third-party runtime dependencies. Its private loader prevents alias
collisions with Castle and binds wrapper/loader bytes into the saved identity.
The final wheel is47,924bytes. The standalone package qualification records
121focused tests,63 independent lens/scenario comparisons and clean direct/
rebuilt installations. Broad legacy Castle checks passed2518main+48supervision
tests with85.30% coverage;11 existing skips and2 deselections are retained.

The Lab owns source admission and authenticated scope. Runtime executes one
tool-free answer per attempt. Harness owns accepted dialogue, receipts, leases,
budgets and resume. SOAR and retrieval are outside review execution. Existing
memory capture remains unchanged; selected capture is an additive explicit API.

Review lifetime is now configurable wall-clock time:24hours by default,7days
maximum, including approval and downtime. The28-call,65536-reported-token and
60-second attempt caps remain bounded. Resume preserves sources, provenance,
engine, accounting owner, original policy and deadline. The detached `proposal`
view exposes these approval bindings. Adapter v1.1 rejects older intermediate
bindings; there is no migration of diagnostic intermediate runs.

## Verification

All commands below use dedicated Python3.12 environments with the unchanged
hash-locked public Core0.4.1/Runtime0.9.8/Harness0.9.4 and PostgreSQL adapters.
The source-test environment contains no installed Lab distribution; installed
wheel acceptance uses a separate environment and neutral working directory.

| Check | Actual result |
| --- | --- |
| Full default profile, neither Castle nor SUE installed |1989passed,1 existing deprecation warning |
| Reviewed SUE focused stage |102passed; later boundary and selected-composition additions pass separately |
| Fourteen real SUE turns |14requests/14accepted turns, bounded stop inside unchanged transport cap |
| Initial installed PostgreSQL16.15/18.6 stage |10passed each,0skips, verified owned cleanup |
| Final complete enabled profile |2063 passed, 1 existing deprecation warning, 0 skips |
| Final direct/rebuilt installed PostgreSQL qualification |14 passed per distribution/version; 56 total, 0 skips, cleanup verified |
| Frozen requirements comparison |39 focused tests; direct/rebuilt installed matrices 24/24 each, network-blocked replay adds 0 calls |

Source commands:

```sh
/private/tmp/prosaic-sue-base-env/bin/python -m pytest -q
/private/tmp/prosaic-sue-env/bin/python -m pytest -q \
  tests/unit tests/functional tests/sue_review tests/requirements_review
/private/tmp/prosaic-sue-env/bin/python -m build --no-isolation
```

The default run completed in 502.17 seconds; the complete enabled run in
598.83 seconds. Both exited zero. The 56 final installed acceptance cases
include concurrency, owner/revision denial, frozen-source deletion, disabled
read-only reports, unknown usage, missing-receipt uncertainty and saved-receipt
adoption. The selected-Castle composition test uses a synthetic external SDK
boundary; it is not a new real-worker/platform qualification claim.

The qualified Lab direct wheel SHA-256 is
`bf03b366179fcbc33b39ede33c510402b9a25ba2055a2d66b7f756d444ba5b99`;
the rebuilt wheel is
`2f44c251f8609c9143bfcd9da8a4d6ed622a540b22c50caa045038cb5b001d7c`.
Every ZIP member has identical bytes; ZIP timestamps may differ. Both were
installed and tested independently. The SUE direct/rebuilt wheel is byte-identical
at `fdfb1690505a85b4cbb49e2b4845c91e318efe945068a379ac230c3b4ebf9b75`.
The installed default-wheel smoke also passes with both optional engines absent
and SDK execution imports forbidden during disabled construction/start.

The explicit enabled profile must run without skips. The normal profile keeps
disabled/absent-engine and pure admission/scoring coverage without requiring the
unpublished engine. A separate CI workflow prepares Linux AMD64/ARM64×PG16/18,
including the unchanged required sandbox prerequisite and direct/rebuilt wheel
acceptance. These CI cells have not run; exact Castle source53637196 first needs
an authorized push. Local consumer execution is macOS ARM64 with Linux ARM64
PostgreSQL images, not native Linux consumer qualification.

## Review findings and failure evidence

Watched failures preceded the implementation and subsequent hardening. Review
caught/fixed package alias collision and incomplete execution identity; ordinary
CI importing an absent optional engine; lost escaped-output identity; missing
saved approval policy; missing Linux sandbox prerequisites; and eval joins that
accepted changed SUE projections, damaged seals or an unfinished checkpoint.
Independent final review found no remaining actionable defects after the fixes.

Returned output retains its hash/byte length before serialized metadata/output
caps can reject it. An earlier SDK event-limit stop cannot recover text Runtime
never returned; it retains the real failure and available usage. Real-wire8k/16k
control-character cases and a mixed Unicode/metadata case cover both boundaries.

An intermediate enabled full run was interrupted after a review finding. It
also exposed a test-environment mistake: an installed Lab candidate violated an
existing SDK-only subprocess assertion. The assertion was preserved; source and
installed environments were separated, and the regression passed unchanged.
Earlier build/backend, model-cache and test-diagnostic failures remain retained.

## Evidence and remaining gates

The local retained bundle is `reports/sue-review-20261024/`; its manifest binds
artifact/log hashes, raw intermediate diagnostics and final receipts. Candidate
package provenance is in `dependencies/sue-review-source.json`. Historical
Castle archives and the77-file Ready-to-Ship v10 ZIP retain their original bytes.

The new comparison uses8frozen requirements cases×direct/critic-author/SUE.
All stages share one Runtime budget; final synthesis and rejected/uncertain
attempts count. SDK public validation checks saved seals/ledgers/fingerprints,
and the existing host projection checks complete SUE prompts during replay.
Legacy grading remains separate and still requires observed retrieval traces.

Scripted fixture success establishes execution/scoring mechanics. SUE review
quality remains unproven. A separately authorized blinded repeated comparison
with held-out cases, model snapshots, randomized order and predeclared limits/
metrics is required before claiming value over simpler review strategies.

See [user guide](../sue-review.md) and
[comparison guide](../requirements-review-eval.md) for use and limits.
