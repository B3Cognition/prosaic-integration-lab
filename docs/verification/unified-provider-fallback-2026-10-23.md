# Provider-shaped rejection fallback through the unified CLI — 2026-10-23

All **18 checks across seven scenarios passed** through the installed unified
Runtime CLI. Both simulated native quota rejections caused pre-work fallback to
local. Partial tool work and partial model text independently prevented further
dispatch for Claude and Codex. A separate bounded smoke test completed the repair
with the **real local ThinkingCap model** after the two simulated rejections.

This extends the [repeated benchmark](unified-cli-realistic-2026-10-23.md), which
tested controlled cooldown selection without observing provider-triggered
fallback. Here no cooldown was injected: real installed native adapters parsed
owned executables' provider-shaped rejection streams and learned the cooldowns.
No actual Claude or Codex subscription was exhausted or invoked.

## Scenarios and physical evidence

| Scenario | Actual attempted profiles | Local fixture HTTP requests | Outcome |
| --- | --- | ---: | --- |
| Both native profiles reject quota before work | Claude → Codex → local | 2 | Repair succeeded; two fallback events |
| New CLI process after learned cooldowns | local | 2 | Native physical calls both zero |
| Claude tool effect, then quota rejection | Claude | 0 | Stop; partial marker retained; recovery required |
| Claude pre-work rejection, then Codex tool effect/quota | Claude → Codex | 0 | Stop; partial marker retained; recovery required |
| Claude partial model text, then quota rejection | Claude | 0 | Stop; recovery required |
| Claude pre-work rejection, then Codex partial text/quota | Claude → Codex | 0 | Stop; recovery required |
| Local tool effect, then HTTP 429; native profiles next | local | 2 | Stop; valid output retained; zero native calls; recovery required |

Each case uses an actual isolated CLI subprocess with explicit policies and
owned numeric-loopback HTTP. The native fixtures emit the Claude
`rate_limit_event`/error-result shape and Codex `turn.failed` usage-limit shape.
Tool scenarios emit native tool/command events and write a visible partial file;
text scenarios emit an assistant/agent message before the same quota rejection.
The error alone does not authorize replay after either kind of work.

Independent native invocation files and HTTP request counts match Runtime's
attempt counters in all seven scenarios. In the clean rejection chain, each
native fixture saw the original calculator bytes; no partial file or skipped
profile existed before local completed the task. The event order is:

```text
select Claude → reject/fallback Claude → select Codex → reject/fallback Codex
→ select local → complete
```

Both rejected attempts carry `safe_to_fallback: true`. In every partial-native
scenario, the final attempted profile carries `safe_to_fallback: false`, and no
local request occurs. In the API-partial scenario, the saved output is valid but
execution still fails with recovery required; output validity does not authorize
a replay. The later CLI process uses the same Runtime-written capacity file and
starts neither native fixture. The harness never writes a cooldown mark.

The fixture suite starts each independent case from fresh operator storage and
workspace, apart from the explicitly tested persisted-cooldown follow-up.
Subsequent independent scenarios are not automatic retries of partial work.

## Real local completion after simulated native rejections

One additional assignment used the same canonical repair Markdown and initial
calculator input, two owned native quota fixtures, and the existing authenticated
local profile `ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ`. It succeeded in **41.22
seconds**, selected `local-strong`, and wrote the correct `return a + b` repair.
No generated Python was executed by the grader or audit.

It recorded exactly two fallback events and one physical launch of each native
fixture. Local completed four provider requests and three tool calls according
to Runtime accounting. Unlike fixture HTTP counts, these real-local API counts
were not independently proxied. The durable allowance reconciled **6/10 mixed
units**: two fixture process launches and four real local API requests, with zero
unknown reservations. Opaque native fixture token usage remains unknown;
`usage_complete` is false, and zero unknown dispatch reservations does not mean
complete token/cost accounting.

Explicit smoke limits were native 5 seconds, local 180 seconds, pool 195 seconds,
three profile attempts, two native attempts, eight API requests, seven API tool
calls, eight rounds and 65,536 API reported tokens. Native workspace-write was
separate from API read/write/edit grants, the workspace read root and exact
`calculator.py` write path. Full tests ran concurrently, so this smoke latency
is functional evidence, not another comparative benchmark measurement.

## Installed candidate and verification

- Runtime executable source: `65385bcac87da084f6fd65ce3dbaf96bafe279c9`.
- Runtime wheel: `55329005c70c17539a23ccbde7c94cfca29cf11e77f0a4279f0fb0f056d3d0be`.
- Manifest: `8a17a3f5f1323f3f668c8b5b7e688560554677bfadf0af9cad7e1a8351d552fe`.
- Final Linux ARM64 consumer image:
  `sha256:15b8e05790e2e06fc4e02a902b2693ff9875ffedf0370d700cc5b5e9db0fad67`.
- Lab runner SHA-256: `1169f3038d6e33c9ba171ca686ea30242d6b04cf335c2393b8b52bc148a96b61`.
- Host SDK-only environment: `.venv-unified-cli`, Python 3.12.15 on macOS ARM64.
- Watched test failure: missing new acceptance module; focused test then passed.
- Full Lab suite: **1,565 passed**, one existing Starlette warning, 216.60 seconds.
  This is the shared checkout's actual count, including other existing work.
- Exact offline, read-only consumer: **18 new + 13 CLI + 11 unified SDK + 9
  native checks passed**, all fixture cleanup verified.
- Independent review found no material issues. It checked the saved fixture and
  live reports, event order, physical counts, safe-fallback flags, local repair
  bytes and per-reservation allowance reconciliation without running models or
  executing generated code. Final resource shutdown is primary verified evidence.

No Runtime, Core or Harness implementation change was necessary. This qualifies
the selected candidate against these simulated error shapes; it does not claim
every future vendor error format or real remote quota exhaustion is certified.
No publication, release, push or modification of shared credentials/configuration.

## Reproduce and preserved evidence

```sh
.venv-unified-cli/bin/python -m lab_runner.native_eval unified-fallback-test \
  --manifest .cache/unified-cli-runtime/manifest.json \
  --wheel-dir .cache/unified-cli-runtime/wheels/8a17a3f5f1323f3f668c8b5b7e688560554677bfadf0af9cad7e1a8351d552fe \
  --output /absolute/new-private-fixture-report.json
```

The command is entirely synthetic and consumes no real provider calls. The
separate real-local smoke requires explicit opt-in and a private allowance; its
exact driver and plan are retained privately, not bundled into public fixtures.

Private evidence root: `reports/unified-provider-fallback-2026-10-23/`.
Fixture report SHA-256:
`4659c98ee167212978863196b32cd5876f31a9c7f7513939da75175cd70d867a`.
Real-local report SHA-256:
`73a807b30ee048148720a9bb7dc7a0793aabf8edf126553a0e118ce1e049e37c`.
Result files are 0600 within 0700 directories, with filtered structural fields,
the known synthetic output, durable allowance, driver, review and checksummed
verification receipts. No raw vendor streams, credentials or session IDs are
retained in the evidence.

After the real-local run, owned inference PID 78599 was verified against its
listener and both descriptors for `/private/tmp/prosaic-provider-fallback-omlx.log`,
then stopped with SIGTERM (exit 143). Final checks confirm port 8000 is closed,
no containers labeled `io.prosaic.lab.owner=provider-fallback-20261023` remain,
and all temporary workspaces are absent. Existing caches, profiles, historical
reports and unrelated user changes remain.
