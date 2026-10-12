# Conversation adoption evidence

Lab target: 0.5.0. Status: development verified, release qualification pending.
The active `dependencies/releases.json` and historic receipts retain the
published 0.4.1/0.8.1/0.2.1/0.7.1/0.2.1 SDK train. No conversation release,
public-index adoption or actual live provider result is claimed here.

## Installed development tests

On macOS ARM64, Python 3.12.14, the following command passed 866 tests with zero
skips and one existing Starlette deprecation warning (46.63 seconds):

```sh
.venv-conversation-dev/bin/python -B -m pytest -q -p no:cacheprovider tests/unit tests/functional
```

The SDKs were noneditable installed wheels: original qualified Core 0.4.1 and
Runtime 0.9.0/recorder 0.3.0, with locally built reviewed Harness 0.8.0/store 0.3.0
at `a638694096c660b5656659a81bf2c22f67b1b3fb`. All five source/metadata/import/cache
payloads and `pip check` passed. This full-suite result predates the final
PostgreSQL readiness permissions correction and subsequent fixture additions.

After the final fixture/CI additions, the same development command passed
880 tests with zero skips (46.84 seconds). The unchanged released baseline ran
868 tests with zero skips (33.38 seconds), explicitly excluding only the three
new installed conversation functional files that require the unavailable API.

Functional tests run real installed Runtime, Conversation and Harness against a
synthetic numeric-loopback OpenAI wire endpoint. Application SQL protocol doubles
are explicit; they do not qualify PostgreSQL locking or grants. Tests prove
failed correction retention, exact current selection/approval, meaningful
registered effect denial during interpretation, cross-controller restoration,
stale/foreign references and loss of host creation/start/attachment acknowledgements.

The optional conformance command has 23 unit and three real-wire functional
checks. Its fixed schedule separates balanced/strong sessions and proves
selection/confirmation without external business effects. `MemoryRecorder`
accounting is diagnostic and nondurable. A durable shared private allowance
retains the maximum for unknown requests, including command crashes. Proxy
environment isolation applies to that standalone command. No live flag was used.

## Actual native PostgreSQL development journey

A separately owned native PostgreSQL 16.15 fixture on macOS ARM64 ran two fresh
HTTP worker processes with separately provisioned migration, application,
workflow, conversation and accounting roles. The installed candidate Harness
source was `b7a5bcbe43f3b5536b03da18303dea63b0ffdef0`. Actual protocol results:

- Nine synthetic provider requests, with seven complete conversation usage
  records and two complete linked workflow usage records.
- The displayed second result retained `player-b` across the handoff.
- Exactly one actual handler/domain effect and one completed SQL tool journal
  operation; the host attachment intent reached `attached`.
- Runtime-role readiness passed and exact recorded worker/cluster processes
  stopped; successful fixture data was removed after PID/path verification.

The first native setup used SQL_ASCII and failed readiness because psycopg returned
bytes for catalog values. It was stopped and its private diagnostics retained.
The fresh successful fixture used UTF8. This is development evidence, not the
required Linux image matrix or Docker cleanup evidence.

A further fresh owned native PostgreSQL16 fixture passed 56 security/persistence/
HTTP cases with zero failures/errors/skips and verified process/cluster cleanup
using installed a638 wheels. Config-replacement/worker-container/remaining quota
and capacity cases remain part of the full required lane. Independent public SDK
wire probes also demonstrated structural depth/node exhaustion and actual
receipt/context overflow after one completed padded lookup. These isolated probes
remain development evidence. The full conversation collection is 91 cases.

## Genuine upstream CI provenance and a discovered regression

Original qualified artifacts were independently verified against exact immutable
source archives, release receipts, wheel/sdist payloads and linked upstream bytes:

| Package group | Exact source | Successful run |
| --- | --- | --- |
| Core 0.4.1 | `6ac6cfdfd47dc70ecf68e441aa004f07c3be3822` | [38077144248](https://github.com/B3Cognition/prosaic/actions/runs/38077144248) |
| Runtime 0.9.0 / recorder 0.3.0 | `a59621c5f30d766d1217b37df777d3876075dc34` | [38181785317](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38181785317) |
| Harness 0.8.0 / store 0.3.0, pre-fix | `a638694096c660b5656659a81bf2c22f67b1b3fb` | [38185470516](https://github.com/B3Cognition/prosaic-harness/actions/runs/38185470516) |

The pre-fix Harness run had 24 required records, nine source lanes with 756
tests each and four PostgreSQL lanes with 160 tests each, zero failures/errors/
skips. Lab then reproduced a substantive gap: restricted runtime readiness
accepted an accidental `UPDATE(document)` grant on receipts. The owned native
regression failed, restored its exact grant and verified exact-PID cleanup.
The original successful CI evidence is preserved; that candidate cannot be
promoted. A new Harness source/run/five-wheel manifest is required.

Readiness remains available to the trusted schema owner/operator, including
effective inherited ownership. Nonowner runtime roles must reject excess
effective table/column powers. Hosts must supply restricted worker credentials;
the SDK does not sandbox an administrator DSN.

## Remaining release gates

Final installed regression and wheel/sdist smoke must use the corrected Harness
candidate. Then all nine required lanes must pass Linux AMD64/ARM64 × PostgreSQL
16/18 with zero skips and exact-owned cleanup. Publish Runtime then Harness,
update current Lab pins from actual published bytes, and qualify ordinary public
PyPI resolution and released-mode matrix. Candidate and released evidence remain
distinct. Missing infrastructure fails; it never certifies readiness.

Current old released SDK CI retains the original eight gates and excludes only
the three newly added installed conversation functional files. Candidate CI
requires full collection plus all nine lanes and an actual extracted-sdist stack
on at least one cell. New exact public pins activate the same released checks;
unknown or incoherent trains fail instead of falling back to baseline.
