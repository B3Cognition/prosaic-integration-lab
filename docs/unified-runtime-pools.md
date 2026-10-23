# Unified Claude, Codex and local Runtime pools

The opt-in installed `UnifiedRuntime` candidate selects native Claude Code,
Codex CLI and local/API profiles through one ordered pool. Runtime owns execution,
capacity and safe switching; Lab consumes its public installed APIs. This is an
experimental local-source candidate, not a published or release-qualified train.

## Configuration and invocation

The original native and local configuration files stay separate. Create a
private unified file referencing them, with distinct profile aliases and explicit
quota identities for API endpoints:

```yaml
kind: unified
native_config: /private/native.yml
api_config: /private/local.yml
api_quota_keys:
  local-strong: local-service
pools:
  agents:
    profiles: [claude, codex, local-strong]
    cooldown_s: 300
default_pool: agents
capacity_file: /private/unified-capacity.json
```

File references resolve relative to the unified file. Native quota keys come
from its existing profiles. Aliases sharing the same underlying quota must share
a key; another name for a Claude login does not create another subscription.
Only one real Claude account is configured on the measured host.

Call the public Python API with an explicit `PoolPolicy`. Native permissions and
API grants are independent contracts; do not translate exact API write paths
into a claim of exact native sandbox authority:

```python
from prosaic_runtime import (
    NativePolicy, PoolPolicy, RunPolicy, UnifiedRuntime, UnifiedRuntimeConfig,
)

runtime = UnifiedRuntime(UnifiedRuntimeConfig.load('/private/unified.yml'))
result = runtime.run(inspected_agent, cwd=workspace, policy=PoolPolicy(
    timeout_s=180, max_attempts=3, max_native_attempts=2,
    native_policy=NativePolicy(permission_mode='workspace-write', timeout_s=60),
    api_policy=RunPolicy(
        allowed_tools=frozenset({'read_file', 'write_file', 'edit_file'}),
        read_roots=(str(workspace),), write_paths=(str(workspace / 'calculator.py'),),
        timeout_s=180, max_provider_requests=8, max_tool_calls=7,
        max_tool_rounds=8, max_reported_tokens=65536,
    ),
))
```

Missing backend policies exclude those backends. `required_capabilities` filters
members before work; `tools: full` excludes API endpoints. The chosen pool owns
profile selection rather than inheriting backend default/model-tier routes.
The Runtime CLI also represents these independent policies explicitly:

```sh
prosaic-runtime subagents/repair.md --source /absolute/.prosaic \
  --config /private/unified.yml --pool agents --cwd /private/workspace \
  --timeout 180 --max-attempts 3 --max-native-attempts 2 \
  --native-permissions workspace-write --native-timeout 60 \
  --enable-api --api-timeout 180 --max-api-requests 8 \
  --max-api-tool-calls 7 --max-tool-rounds 8 --max-api-reported-tokens 65536 \
  --allow-tool read_file --allow-tool write_file --allow-tool edit_file \
  --read-root /private/workspace --write-path /private/workspace/calculator.py
```

For API-only execution omit both native flags and use `--max-native-attempts 0`.
For native-only execution omit `--enable-api` and every API grant/budget.
API requests/tools accept explicit zero. `--profile` and accounting/context flags
are rejected in unified mode. `--require-capability` can be repeated. Output
supports JSON, text and JSONL `--events`; exits are 0 success, 1 execution failure,
2 invalid configuration/authority, 130 interrupted. Raw result metadata may
contain private backend data and must be filtered before sharing.

Switching requires concrete engine proof of pre-work rejection: native positive
proof with no observed model/tool work, or an initial direct API HTTP 429/TCP
refusal before acceptance and before tool dispatch. Progress events do not grant
retry authority. Authentication errors, partial output/reasoning, tools, ambiguous
HTTP failures, timeouts and unknown effects stop. All-cooled returns promptly
with `capacity_unavailable` and earliest `retry_at`, without waiting or automatic
replay. Cooldowns are eligibility hints rather than capacity reservations.

Pool evidence separates native attempts, API requests/tools and known/unknown
tokens. API token caps do not bound native internal loops or subscription spend.
The facade does not claim portable sessions, API receipts/accounting across native
members or automatic recovery of partially executed work.

## Installed-candidate validation

Run Lab commands from the Lab checkout root with its `scripts/` audit tools.
Upstream SDKs must be installed wheels, not sibling source/editable imports.
The following historical ledgers identify the exact 0.9.3 candidate measured;
the [PR finalization ledger](verification/unified-pool-pr-finalization-2026-10-23.md)
separately qualifies integration with current main.

Use a separate SDK-only environment and candidate manifest, preserving published
pins and prior experiment environments. Build the exact owning Runtime commit,
curate its wheel with the unchanged four SDKs using the existing native candidate
recipe, install/audit the five-wheel payloads, then run:

```sh
.venv-unified/bin/python -m pytest -q tests/native_acceptance
.venv-unified/bin/python -m lab_runner.native_eval unified-test \
  --manifest .cache/unified-runtime/manifest.json \
  --wheel-dir <exact-candidate-wheel-directory> \
  --output /absolute/new-private-unified-fixture-report.json
```

The CLI extension uses its own immutable manifest and environment:

```sh
.venv-unified-cli/bin/python -m lab_runner.native_eval unified-cli-test \
  --manifest .cache/unified-cli-runtime/manifest.json \
  --wheel-dir <exact-cli-candidate-wheel-directory>
```

Thirteen subprocess checks cover three-backend fallback, JSONL/text output,
graded repair, cross-process cooldowns, zero request/tool caps, all-unavailable,
native/API effects without replay, native success, explicit backend exclusion and
cleanup. This lane fails against the earlier Python-only candidate.

The new lane uses real owned fixture subprocesses and numeric-loopback HTTP
fixtures with no real model calls. Eleven checks cover mixed failover, persistence
across Python processes, no replay after native/API effects, shared quotas,
all-unavailable, independent permissions, API write scopes, request budgets and
cleanup. It fails when the installed SDK lacks the unified API; no skipped lane
can qualify an old candidate. The explicit public build inventory includes the
runner and excludes private profiles/reports. Offline containers use an executable
temporary mount for fixture CLIs and require no database.

Live checks require explicit authorization and a durable mixed-dispatch allowance.
Use fresh owned workspaces, the same neutral Markdown/inputs, and authenticated
loopback local inference. Controlled private capacity marks exercise live profile
selection without consuming subscriptions to exhaustion; provider-rejection and
no-replay correctness remain separately labeled fixture evidence. See the
[implementation and qualification ledger](verification/unified-runtime-pool-2026-10-23.md)
for exact source, wheel, test, live and cleanup receipts.
The separate [CLI qualification ledger](verification/unified-runtime-cli-2026-10-23.md)
records the subsequent CLI candidate and its installed/live results.

For provider-shaped rejection tests through the installed CLI, run
`python -m lab_runner.native_eval unified-fallback-test` with the explicit candidate
manifest and wheel directory. Its seven scenarios and 18 checks distinguish
pre-work quota rejection from partial text or tool effects, verify learned
cooldowns across CLI processes, and count actual fixture launches/HTTP requests.
The command uses only owned fixtures. The separate
[provider fallback ledger](verification/unified-provider-fallback-2026-10-23.md)
also records one bounded real-local completion after two simulated native quota
rejections, without calling real Claude/Codex providers.
