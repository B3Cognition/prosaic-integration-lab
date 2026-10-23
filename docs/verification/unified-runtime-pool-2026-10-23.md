# Unified Runtime pool implementation and qualification — 2026-10-23

The user approved implementation in Runtime of one Claude/Codex/local pool,
switching only before work starts, with explicit permissions and budgets, and
validation in Integration Lab. The installed candidate passed all six live
scenarios: four real assignments plus two expected zero-dispatch capacity checks.
This is feature qualification on one host, not a model-quality benchmark or
release-qualified SDK train.

## Implemented contract

Runtime adds public `UnifiedRuntime`, `UnifiedRuntimeConfig` and `PoolPolicy`.
The facade delegates to the existing concrete native/API engines. Unified files
use `kind: unified` and reference existing backend configuration files. Native
and API profile aliases are distinct, API quota keys are explicit, and aliases
sharing an account use the same capacity key. Original native/API formats and
execution classes remain compatible.

Every invocation supplies an overall deadline, profile/native attempt caps and
independent backend policies. API request/tool caps are mandatory and carried
between API candidates. Native permission acceptance never inherits exact API
path grants. Missing policies and required capability mismatches exclude members
before dispatch. Native inner provider calls remain opaque. The first unified
surface is Python; the legacy Runtime CLI explicitly rejects unified config
rather than inventing policy defaults. Lab adds `native_eval unified-test`.

Switching requires concrete `prework_failure_v1` proof. API proof requires an
initial direct HTTP 429/TCP refusal before response acceptance and before any
tool dispatch. Accounting-wrapped paths conservatively withhold that proof.
Unified native switching additionally rejects observed model text/reasoning,
even when the standalone native pool's older effect-free rule would permit
fallback. Authentication errors, malformed responses, ambiguous failures,
timeouts, cancellation and partial work do not authorize another dispatch.
All unavailable returns immediately with earliest retry time and no background
retry. Native/API sessions, tool loops and accounting contracts are not merged.

## Runtime verification and review

The original Runtime baseline passed **1129 tests, 2 skips** in 378.08 s. Missing
configuration/proof tests and mixed-runtime tests were observed RED before
implementation. Focused final native/unified coverage passed **97 tests** in
26.45 s. Final `.venv/bin/python -m pytest -q` passed **1175 tests, 2 existing
skips** in 385.27 s. Host Runtime Python is 3.11.15 on macOS arm64.

Independent Runtime review found one P1: a host callback raising a transport-shaped
exception after HTTP 200 acceptance could create false safe-switch evidence.
The coordinator reproduced duplicate dispatch using a real loopback HTTP server.
Both HTTP-429-shaped and connection-refusal-shaped JSON cancellation/SSE callback
regressions were observed RED, then GREEN after proof was restricted to failed
direct acceptance. Additional RED/GREEN tests enforce the stricter partial-native
work rule. An existing malformed-stream regression caught a missing type guard
during that change; it was corrected before final full qualification. No important
review finding remains unresolved. An earlier pre-review full pass remains
preserved separately and is not substituted for the final result.

## Immutable installed candidate

Only this feature's Runtime files were committed locally; unrelated example
changes were preserved. Runtime commit:
`ecb3b4cdd1522c537c5acb9685bf39ff78bbbd1d`.
Wheel SHA-256:
`5496ebba6ab3559cf143198dcb8c44aab8fea7051d3f111af309c0795d4cd381`.
Sdist SHA-256:
`e2343468f1e68883f05b0dd181be9a3ef1b7725cb5a1012f5fc382346250db2f`.
The build used an owned clean archive of that commit, not an editable checkout.
Distribution identity remains experimental Runtime 0.9.3; no release was made.

Lab's separate candidate manifest is `.cache/unified-runtime/manifest.json`, SHA-256
`8604034b47a323500c19e69b27641f5fef114433747ead4a13547d4f40bb6e12`.
The other four SDK wheel hashes match the preceding native candidate exactly.
The five-wheel payload audit and `pip check` passed in SDK-only `.venv-unified`;
the earlier `.venv-native`, old manifests and all historic reports are preserved.
Origin is `local_exact_source`, without CI/release lineage. Installed base,
native, conversation and production smoke scripts all passed under `python -I`.

## Integration Lab acceptance

`.venv-unified/bin/python -m pytest -q tests/native_acceptance` passed **11 tests**.
The full `.venv-unified/bin/python -m pytest -q` passed **1477 tests**, with one
existing Starlette deprecation warning, in 174.59 s. This is the shared Lab
checkout's actual suite count, including other authorized changes.

The new public fixture lane uses owned Claude/Codex subprocesses and an actual
numeric-loopback HTTP fixture through public installed SDK APIs. Its **11 checks**
cover three-backend fallback, API-to-native fallback, cross-process cooldowns,
native/API effect no-replay, shared-quota no-bypass, all-unavailable no-dispatch,
explicit native permission, API write scopes, request budgets and cleanup.
The old candidate correctly failed instead of skipping the absent unified API.

The isolated public-input consumer build produced Linux/arm64 image
`sha256:29c2aa4b19efac654e2f4d71414175729e686c5452168e55b0714c6c5f2e9d71`.
Exact-owned containers with label `io.prosaic.lab.owner=unified-20261023`, read-only
roots, executable temporary storage and no external network passed **11 unified
checks plus all 9 existing native checks**, with zero real model calls. No
database lane changed. Independent Lab review separately reran the installed
unified fixture lane and found no actionable issues.

Representative commands:

```sh
.venv-unified/bin/python -m lab_runner.native_eval unified-test \
  --manifest .cache/unified-runtime/manifest.json \
  --wheel-dir .cache/unified-runtime/wheels/8604034b47a323500c19e69b27641f5fef114433747ead4a13547d4f40bb6e12
.venv-unified/bin/python scripts/build_consumer.py --dependency-mode candidate \
  --manifest .cache/unified-runtime/manifest.json \
  --wheel-dir .cache/unified-runtime/wheels/8604034b47a323500c19e69b27641f5fef114433747ead4a13547d4f40bb6e12 \
  --tag prosaic-integration-lab:unified-pool
docker run --rm --name prosaic-unified-fixtures-20261023 \
  --label io.prosaic.lab.owner=unified-20261023 --network none --read-only \
  --tmpfs /tmp:rw,exec,nosuid,nodev \
  sha256:29c2aa4b19efac654e2f4d71414175729e686c5452168e55b0714c6c5f2e9d71 \
  python -m lab_runner.native_eval unified-test \
  --manifest /srv/lab/dependencies/releases.json --wheel-dir /srv/wheels
```

## Live controlled-capacity pilot

The same unchanged neutral `subagents/repair.md` and two-line calculator draft
were used in fresh private workspaces. The grader checks exact file bytes and
workspace integrity without executing generated Python. Pool order is Claude
(`sonnet`, renewed Gmail), Codex (`gpt-6.1-sol`, explicit low effort), then
`local-strong` (`ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ`). CLI preflight versions were
Claude Code 2.1.308 and Codex CLI 0.163.0. Only one Claude account is used.

The host explicitly reserves **60 mixed dispatch units**: up to 10 per each of
six scenarios, covering two native attempts and eight API requests. Each
assignment has 180 s total, native members at most 60 s, API at most the remaining
180 s, seven API tool calls/eight tool rounds and 65536 reported API tokens.
API authority is read/edit/write with a workspace read root and exactly
`calculator.py` writable; native authority explicitly accepts vendor workspace
writes. Unknown dispatch retains its worst-case reservation and stops the pilot.

| Scenario | Selected profile | Outcome | Assignment duration | Native attempts / API requests |
| --- | --- | --- | --- | --- |
| No capacity marks | Claude | Passed | 6.466 s | 1 / 0 |
| Claude cooling | Codex | Passed | 12.133 s | 1 / 0 |
| Claude and Codex cooling | Local | Passed | 39.336 s | 0 / 4 |
| All three cooling | None | Expected `capacity_unavailable` | 11.077 ms | 0 / 0 |
| Four-second Claude cooldown, before expiry | None | Expected `capacity_unavailable` | 10.063 ms | 0 / 0 |
| After real-time expiry | Claude | Passed | 7.340 s | 1 / 0 |

All **six validation outcomes passed**, including four successful real assignments.
Both expected negatives returned retry times and dispatched nothing. Accounting
reconciles to **7/60 known units**: three native CLI attempts and four local API
requests, zero unknown reservations. Native internal provider request counts
remain unavailable. Independent review regraded every saved calculator output
and verified all scenario selection/skips, source/input/output hashes, deadlines,
controls, private modes and accounting with no findings or additional model calls.

These are controlled host capacity marks applied only to the experiment's private
`CapacityStore`. No subscription was exhausted and no provider rejection was
fabricated. Real provider-quota failover remains separately unqualified; rejection
classification and uncertain-effect no-replay have fixture evidence. This short
pilot does not establish statistical latency rankings or general model quality.

## Evidence, setup failures and cleanup

Private evidence is `reports/unified-pool-live-2026-10-23/`, including plan,
configuration references, preserved driver, samples, synthetic outputs, control
receipts, durable allowance, full verification/build receipts, audit and cleanup.
The 22 test/build/installed-wheel receipts are in its `verification/` subdirectory;
their presence and final log contents were checked directly during final review.
Raw report SHA-256:
`7b5d336616d5d47b8f1227090091f25bcedb3c5323030080a74923a03fbd2fa9`.
Every saved output/sample hash reconciles. Original native/local config hashes
are unchanged. Files are 0600 and directories 0700; no raw CLI/model streams,
session IDs or credentials enter summary fields. Historical reports remain intact.

Preserved setup failures were corrected before qualification: an initial build
command dereferenced the virtualenv interpreter and lacked `build`; a smoke
invocation omitted required `-I`; a cross-process fixture used `.json` API config
references instead of the loader-required YAML suffix. The first live driver
assumed alias `local` instead of configured `local-strong` and stopped before
creating output or dispatching a model. No uncertain model assignment was replayed.

The local server reused the owned thinking-disabled profile/cache and bound only
authenticated loopback. After all measurements, PID 49772 was verified against
port 8000 and `/private/tmp/prosaic-unified-omlx.log`, then terminated; its session
exited 143 and port 8000 is closed. Both exact-owner fixture containers and all
temporary workspaces are absent. Private profiles, cache and evidence remain;
no shared service was stopped or global configuration modified. No push, package
publication, database migration or release qualification was performed.
