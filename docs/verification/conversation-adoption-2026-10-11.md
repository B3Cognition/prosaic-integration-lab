# Conversation adoption evidence

Lab target: 0.5.0. Status: exact-source candidate platform qualification passed;
publication and public-index/full live-provider qualification remain pending.
See the [final platform result](#candidate-platform-qualification--2026-10-12).
The active `dependencies/releases.json` and historic receipts retain the
published 0.4.1/0.8.1/0.2.1/0.7.1/0.2.1 SDK train. No conversation release or
public-index adoption is claimed here. Subsequent actual local Qwen memory,
routing, selection and blocked native-tool results are recorded separately in
[the live verification ledger](local-conversation-2026-10-12.md).

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
| Harness 0.8.0 / store 0.3.0, corrected | `f913fa18820554ffc5eb30a7bc4a8a6e302ed0ce` | [38186769826](https://github.com/B3Cognition/prosaic-harness/actions/runs/38186769826) |

The pre-fix Harness run had 24 required records, nine source lanes with 756
tests each and four PostgreSQL lanes with 160 tests each, zero failures/errors/
skips. Lab then reproduced a substantive gap: restricted runtime readiness
accepted an accidental `UPDATE(document)` grant on receipts. The owned native
regression failed, restored its exact grant and verified exact-PID cleanup.
The original successful CI evidence is preserved; that candidate cannot be
promoted. The corrected genuine run has 24 passing records, nine source lanes
with 756 tests each and four PostgreSQL lanes with 179 tests each, zero failures/
errors/skips. It retains the exact original Core/Runtime upstream lineage.
The separate corrected five-wheel manifest SHA256 is
`d5b4678788239ebf090979fcea65ee1c9774376f48b3994a4ad9cd3876b6314b`;
its original lineage digest is
`dc5ed7a9ee13f8868c7cf31daf889ec0f5058c5e0c595ab717ff1b6dac3c24c8`.
All installed SDK payloads in the fresh consumer environment match those wheels.

Readiness remains available to the trusted schema owner/operator, including
effective inherited ownership. Nonowner runtime roles must reject excess
effective table/column powers. Hosts must supply restricted worker credentials;
the SDK does not sandbox an administrator DSN.

## Release work after candidate qualification

The final result below qualifies installed regression, wheel/sdist consumption
and all nine Linux AMD64/ARM64 × PostgreSQL 16/18 lanes against the corrected
Harness candidate. Remaining release work is to publish Runtime then Harness,
release Lab, update current pins from actual published bytes, and qualify ordinary
public PyPI resolution and the released-mode matrix. Candidate and released
evidence remain distinct. Missing infrastructure fails; it never certifies readiness.

Current old released SDK CI retains the original eight gates and excludes only
the three newly added installed conversation functional files. Candidate CI
requires full collection plus all nine lanes and an actual extracted-sdist stack
on at least one cell. New exact public pins activate the same released checks;
unknown or incoherent trains fail instead of falling back to baseline.

## Independent review and explicit boundaries

One whole-branch review found zero Critical, five Important and zero Minor issues.
All five were accepted for a single fix pass: source bootstrap in CI, selection of
the execution receipt in distribution smoke, visible uncertain host start intent,
reconciliation after a lost attachment acknowledgement, and actual consequential
handoff/concurrent-session/SQL-partition recovery coverage. No second review is
used as evidence. Host status and advanced/completed replay failures were observed
before their fixes. The corrected installed SDK functional tests now prove both
approval phase failures retain zero/one actual effect and immutable journal
evidence without resuming. At that review checkpoint the real-stack collection
was 95 cases and its four added approval/race/partition cases still required
actual Linux execution; the final platform result below now supplies it.

Final corrected-SDK full source verification passed 893 tests with zero skips
(55.17 seconds), and the unchanged released baseline passed 876 with zero skips
(33.48 seconds); both retain the one existing Starlette warning. The CI bootstrap
regression executes the real workflow command without a Lab installation. The
host regressions use real installed controllers and wire requests; no SDK engine
is patched. The required new recovery cases fail missing infrastructure and are
not counted as qualified until real platform receipts pass.

The review explicitly retained these boundaries:

- Platform/database success and container cleanup require exact-source real CI
  receipts. Read-only review and local native results cannot establish them.
- SQLite host SQL doubles prove protocol behavior; only real PostgreSQL qualifies
  locking and permissions. Treating them otherwise would overstate readiness.
- SDK reducers, providers, storage and Core remain owned by their separately
  reviewed upstream plans. Consumer review cannot replace upstream qualification.
- Qwen/hosted quality, prices and customer billing require separate explicit live
  or business evidence. Diagnostic memory accounting supplies no financial claim.
- Production identity-provider operation remains the deploying host's work;
  fixture bearer/JWT authentication does not establish that deployment.
- Trusted host Python, arbitrary callbacks, administrator credentials and
  same-user filesystem mutation remain outside the sandbox boundary. Malicious
  trusted code or host credential mistakes can defeat application boundaries.
- Uncertain workflow resolution requires an operator; HTTP uses saved JSON views.
  Automatic effect resolution and durable SSE replay require a separate design.
- Deletion/retention automation, summaries, vector/multimodal memory, multiple
  actors, changing profiles and scheduling remain deferred features. This
  qualification makes no new feature or compliance claim about them.

## Candidate platform qualification — 2026-10-12

Exact executable source `018425b810c6583bd3c1e20fc8cc8088ee4cda7c` passed
[run 38195151714](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38195151714).
This later documentation-only commit records that source's evidence; it does
not claim a new executable build was qualified. All four original required and
distribution receipts were independently checked with the existing gate
validator, exact SDK manifest/lineage, pinned database images and immutable
per-cell consumer images. Both documented candidate demos passed in each cell.

| Linux architecture | PostgreSQL | Required cases | Conversation cases | Capacity p95 |
| --- | --- | --- | --- | --- |
| AMD64 | 16 | 325 passed | 95 passed | 0.2630 s |
| AMD64 | 18 | 325 passed | 95 passed | 0.2487 s |
| ARM64 | 16 | 325 passed | 95 passed | 0.2513 s |
| ARM64 | 18 | 325 passed | 95 passed | 0.2124 s |

The matrix passed 1,300 required cases with zero failures/skips and verified
owned cleanup. ARM64/16 additionally built a consumer from the extracted Lab
source distribution and passed its public demonstration plus 95 conversation
cases: 1,395 acceptance executions in total, including 475 conversation checks.
Every cell verified two fresh neutral wheel/sdist consumers, isolated imports,
all installed payloads, `pip check`, public construction and retained assets.
Each distribution receipt explicitly records `public_index_verified=false`.

Every closed capacity diagnostic is available and all five flags pass. Eighteen
offered/accepted/completed requests, read samples, tool samples and independently
observed model calls reconcile with 18 ledger calls. Two fairness windows have
zero starvation; errors, rejections, deferrals, shedding, unknown usage, read
failures and allowance rejections are zero. Record growth is 18, and measured
p95 remains below the unchanged two-second bound. These numeric/boolean
diagnostics contain no identities and do not replace required gate authority.

Original receipt SHA256 values from the run's four `acceptance-*` artifacts:

| Cell | Required receipt | Distribution receipt |
| --- | --- | --- |
| AMD64/16 | `cde98c271ae9ebb5abcd0a485448da06e65dddbe6835fc9a0034fd87a80ba6ad` | `5220664020e819674486036aefd13167b3ecc1f8d86c1f0a86181581d5f8cd05` |
| AMD64/18 | `8952c0ba61ddb1c7b0222ae8035542d60b462104800516d78c6d6e77cf21633b` | `797d77198d596c2502ac9278287ce856c53e97a14de985380b11b9fbc7bf39f2` |
| ARM64/16 | `f7a08ee73a840f9eade1215d6c6d99427b035bfe97e818bb5ccab1471ac0b6ff` | `fb3bec8e6554a007d61b7fc87063de9e55a984e111f4c41eb9ef3e6330efcc83` |
| ARM64/18 | `3e5080e9415c8c9bc83af87d0a359d54818b18bedaac410ec715d3ec6b8e2620` | `5525066dadb1a53c1775edf27ed2b3e1f630c3880411b98bf301dcf0b0e77079` |

Original CI Lab artifact SHA256 values; local rebuilds remain separate evidence:

| Cell | Lab wheel | Lab source distribution |
| --- | --- | --- |
| AMD64/16 | `a85d0bbbbc8f136b363ef6a6361c4f040dad77c82bf3c8c9f708f834b4f5e0a3` | `9c35d9b40b60758371a8ef72c5f0f74f48b927ab38df1b0a795903e9a56ecb3a` |
| AMD64/18 | `a85d0bbbbc8f136b363ef6a6361c4f040dad77c82bf3c8c9f708f834b4f5e0a3` | `0c42f32a43e03cc63cec7cacf115ca351204efbfdb1d325de06db3b69ce49bd4` |
| ARM64/16 | `5d4ee8eea05ade26d334c5f35607159cf8aa0091ab8312af45d406174134038d` | `90e3b6d98bd27eb32ba751fbd1756819ba6af65d940b0c2d384077f22e3e2375` |
| ARM64/18 | `e674788d47c15c20cca11c803f82c83113dba58b81f612768c52fb941e2a28d8` | `f5ccae1361a7ff75f55f190fce3de48eb81bd08101e0284f4353c3a7fc33fd6d` |

Final local verification passed 925 candidate tests and 908 applicable published
baseline tests with zero skips and all five SDK payload audits verified. The
old public train still excludes only the three functional files requiring the
unavailable conversation API. Native development evidence above remains separate.

Earlier runs remain failed and preserved: distribution export/setup failures
(`38188565128`, `38189159594`), delivery/fixture failures (`38190115111`,
`38190826734`) and the exact `0f7791c` run
[38192839965](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38192839965).
The latter passed all 475 conversation executions but had one AMD64/18 capacity
qualification failure. Its detailed assertion was discarded, so the cause is
unidentified. Commit `018425b` repairs that diagnostic reporting gap; it does
not claim to have fixed an identified capacity defect or change any threshold.

Runtime/Harness publication, Lab release/tagging, ordinary public-index adoption
and explicit live Qwen/hosted conformance remain pending. Current published pins
and historic evidence are unchanged; all review boundaries above remain in force.
