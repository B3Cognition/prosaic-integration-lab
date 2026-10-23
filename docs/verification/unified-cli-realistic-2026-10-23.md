# Repeated realistic unified CLI benchmark — 2026-10-23

The requested study completed **27/27 successful assignments**, with successful
CLI completion and unchanged factual/workspace grading on every assignment.
There were no timeouts, valid-but-incomplete outputs or uncertain dispatches.
The three tasks were release brief, incident handoff and invoice SQL, repeated
three times in each of three availability states. All selected models and
Markdown/input hashes matched the corresponding prior direct benchmark samples.

## Results

Each path has nine assignments (three trials per task). Success and completion
were 100% for every path. All-attempt and successful-only latency distributions
are identical because no assignment failed.

| Availability / selected profile | Success | CLI median (range) | Prior direct median (range) |
| --- | --- | --- | --- |
| No forced cooldown / Claude Code `sonnet` | 9/9 | 12.13 s (10.07–20.77) | 14.90 s (10.52–19.87) |
| Claude cooling / Codex `gpt-6.1-sol`, low effort | 9/9 | 23.99 s (20.95–33.60) | 29.54 s (24.80–39.96) |
| Both native profiles cooling / local ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ | 9/9 | 60.58 s (41.00–78.09) | 65.15 s (48.81–86.98) |

| Task | Claude CLI median | Codex CLI median | Local CLI median | Success per profile |
| --- | ---: | ---: | ---: | --- |
| Release brief | 13.33 s | 22.51 s | 60.58 s | 3/3 each |
| Incident handoff | 12.42 s | 23.79 s | 61.21 s | 3/3 each |
| Invoice SQL | 11.69 s | 29.76 s | 42.48 s | 3/3 each |

These observed medians are lower than the earlier direct study, but this is not
an isolated CLI speedup measurement. The Runtime candidates and invocation
surfaces differ; historical cache and host conditions were uncontrolled. Current
latency includes CLI startup, inspection, execution and terminal-result handling.
The direct study used in-process SDK timing. Three trials per task do not justify
a p95 estimate, general model ranking or equivalent prose-quality claim.

## Selection and fallback

The unchanged pool order was Claude → Codex → local. Every selected profile
matched the intended first eligible member. The Codex path skipped Claude nine
times; the local path skipped both native profiles nine times, giving **27
controlled cooldown skips**. Excluded profiles were never attempted.

There were **zero provider-triggered fallback events**, zero multi-profile
attempts within an assignment, and zero replays after work. All 27 assignments
used one actual profile attempt each. Controlled exclusions were temporary host
capacity inputs, not fabricated provider responses or induced quota exhaustion.
One shared capacity file preserved any real cooldown; cleanup restored only
marks owned by the experiment. No provider-reported cooldown occurred in this
study. This validates eligibility-based selection under cooldown, while actual
pre-work rejection/fallback and no-replay behavior retain separately labeled
[installed fixture evidence](unified-runtime-cli-2026-10-23.md).

## Unchanged tasks and explicit limits

The canonical Markdown, seeded packets/drafts, existing grader and model profile
files were reused without modification. The grader SHA-256 remains
`69a3409789223154cadb4894d670efb874d81bef439f638c2f924e482e58661a`.
Native configuration SHA-256 is
`905fa826678df20316e8f950f3da78f43dee1310aff4faccb693832f3fe083e9`;
local configuration SHA-256 is
`81845ceaeb416e3be4fde6bb3c143141687c3864484a10670ce1c22760b76836`.
Local retained its 2048 output-token cap and isolated no-thinking oMLX profile.

Native per-attempt deadlines stayed at **60 seconds** and local/API at **180
seconds**. The unified total ceiling was **300 seconds** to accommodate pre-work
fallback; it was not the prior tiny CLI pilot's 180-second total ceiling. No
assignment used a fallback, so every local assignment received the full local
deadline apart from ordinary deadline projection overhead.

Each invocation supplied native workspace-write permission independently from
API read/write/edit grants, a workspace read root and the exact output write
path. Shared caps were three profile attempts, two native attempts, eight API
requests, seven API tool calls, eight tool rounds and 65,536 API reported tokens.
Native inner request/tool loops remain vendor-owned and opaque.

The durable allowance retained **45/243 mixed units**: 18 native CLI attempts and
27 local API requests, zero unknown reservations. Every local assignment used
three provider requests. The conservative ceiling was nine assignments at each
maximum of 10, 9 and 8 units. Every admission token was joined to its exact ledger
entry and sample counters. These units are not subscription/API cost equivalents.

Runs were sequential, with rotated task/state order, fresh workspaces, no
deliberate warmup and no concurrent test suite from this task. One real Claude
account was available. Readiness checked CLI versions and authenticated local
catalogue availability; it did not consume inference allowances.

## Provenance and verification

- Installed Runtime executable source: `65385bcac87da084f6fd65ce3dbaf96bafe279c9`.
- Runtime wheel SHA-256: `55329005c70c17539a23ccbde7c94cfca29cf11e77f0a4279f0fb0f056d3d0be`.
- Manifest SHA-256: `8a17a3f5f1323f3f668c8b5b7e688560554677bfadf0af9cad7e1a8351d552fe`.
- Exact Linux ARM64 consumer image:
  `sha256:1061cd8ac0e749ae16fd368aece7106cb5d2928f855ad35fac93953d85976678`.
- Lab benchmark driver SHA-256:
  `4ed10924ec1a2b4200ddf2b6b306f96b4bbbc168d7103e95c4704ab96732408e`.
- Host SDK-only environment: `.venv-unified-cli`, Python 3.12.15, macOS ARM64.
- Installed wheel payload audit and `pip check` passed. No editable sibling SDKs.
- Final full Lab suite: **1,527 passed**, one existing Starlette warning,
  227.41 seconds. Final focused harness/grader suite: **34 passed**.
- Exact offline consumer: **13 CLI + 11 unified SDK + 9 native checks passed**.
- Watched regressions reproduced and fixed interruption cleanup and failure
  latency; real owned subprocess cancellation passes. Incompatible pilot flags
  are rejected before candidate audit rather than silently ignored.
- Frozen driver, config, grader and Markdown hashes remained unchanged during
  measurement. A separate audit paired all 27 samples with the prior direct
  study, regraded all 54 saved outputs, checked every output/sample hash,
  reconciled summaries and per-admission dispatch counts, verified exclusions,
  actual selected models, per-backend deadlines and private file permissions.

Independent final review found no material issues and independently regraded all
54 outputs, recomputed the metrics, verified per-token admission accounting and
confirmed all 27 exclusions/skips with zero provider fallback events. Its report
distinguishes independently checked workspace/privacy evidence from primary
service cleanup receipts. Earlier cancellation/timing review findings were fixed
and tested before any timed model assignment.

Private evidence: `reports/unified-cli-realistic-2026-10-23/`.
Raw report SHA-256:
`a99c4c56e82b2a9270e525f6a31cdeea00fbc4014434d0b54f243a785127a071`.
Unchanged baseline report SHA-256:
`924255312ab8dad4305d498c330b96a7c7b87106ca74057f882e322f5f991ee1`.
`comparison.json` and its retained `compare-baseline.py` record the paired audit.
Raw vendor streams, credentials and session IDs are not retained in the results.

Reproduce with the [unified benchmark recipe](../realistic-runtime-benchmark.md#repeated-unified-cli-pool-study)
and a new exclusive private output directory. Historical reports are never reset
or rescored. This remains local candidate evidence, without publication or new
release/hosted-provider quota qualification.

## Cleanup

After all measurements, owned local inference PID 68232 was verified against its
loopback listener and both descriptors for
`/private/tmp/prosaic-unified-cli-benchmark-omlx.log`, then stopped with SIGTERM
(exit 143). Final listener/container/workspace checks and the independent review
are retained alongside checksummed private verification receipts. Existing model
cache/profile, previous benchmark reports and unrelated user changes remain.
Port 8000 is closed and no containers bearing
`io.prosaic.lab.owner=unified-benchmark-20261023` remain.
