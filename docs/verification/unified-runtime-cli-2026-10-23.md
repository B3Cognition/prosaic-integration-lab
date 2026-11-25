# Unified Runtime CLI qualification — 2026-10-23

The maintainer authorized CLI support for the unified Claude/Codex/local pool,
explicit permissions/budgets, and Integration Lab validation. Runtime owns the
implementation; Lab uses installed public interfaces. Core and Harness were not
modified for this extension. Earlier Python-only evidence remains in
[the original ledger](unified-runtime-pool-2026-10-23.md).

## Candidate and provenance

- Runtime executable source: `65385bcac87da084f6fd65ce3dbaf96bafe279c9`.
- Exact archived-source build; candidate version remains 0.9.3, not published.
- Runtime wheel SHA-256: `55329005c70c17539a23ccbde7c94cfca29cf11e77f0a4279f0fb0f056d3d0be`.
- Runtime sdist SHA-256: `41ed11c96b3f28f8035b67e1b897ec878fc3efe539260e7e0f9d95ca10e7d463`.
- Five-wheel manifest: `.cache/unified-cli-runtime/manifest.json`, SHA-256
  `8a17a3f5f1323f3f668c8b5b7e688560554677bfadf0af9cad7e1a8351d552fe`.
- Other four SDK wheels remain identical to the prior unified candidate.
- Separate SDK-only environment: `.venv-unified-cli`, Python 3.12.15 on macOS ARM64.
- Final Linux ARM64 consumer image:
  `sha256:5ed88375028f79c763172a2f767b58fc73c50087be4498cac89e5b4adbefeb9f`.
- Exact wheel payload audit, `pip check`, and all four isolated installed Runtime
  smoke scripts passed. No editable sibling SDK imports were used.

## CLI contract

`kind: unified` selects the existing facade. `--timeout`, `--max-attempts` and
`--max-native-attempts` are required. Native execution requires
`--native-permissions` and `--native-timeout`. API execution requires
`--enable-api`, `--api-timeout`, `--max-api-requests`, `--max-api-tool-calls` and
`--max-tool-rounds`; tool/path grants remain explicit. Missing backend authority
excludes that family. API request/tool caps accept zero. API reported tokens have
an optional separate cap and cannot bound opaque native provider calls.

Disabled-backend flags and unified flags in legacy modes are rejected.
`--profile` and accounting/context options are rejected for unified execution.
`--pool`, repeatable `--require-capability`, JSON/text/JSONL output and ordinary
exit codes are supported. Total and backend deadlines project into the existing
policies. Selection, cooldown and pre-work-only fallback rules are unchanged.
See [the invocation guide](../unified-runtime-pools.md).

## Automated evidence

- Runtime test-first CLI suite: 17 failures before implementation; final focused
  CLI suite 29 passed. Existing/native/config focused set: 46 passed.
- Independent reviewer: no material findings; 90 focused CLI/tool/sandbox tests
  passed with one existing skip. Its native-effect CLI coverage suggestion was
  added to Lab and passed.
- Runtime full suite: **1,204 passed, two existing skips**, Python 3.11.15,
  399.45 seconds (`.venv/bin/python -m pytest -q`).
- Lab full installed-candidate suite: **1,504 passed**, one existing Starlette
  deprecation warning, 196.95 seconds. This is the shared working checkout's
  actual count, including unrelated pre-existing tests.
- Final focused installed CLI acceptance: one test, **13 checks passed**.
- Exact final image, offline/read-only containers: **13 CLI + 11 unified SDK +
  9 existing native checks passed**, all cleanup verified.

The CLI consumer fails against the previous Python-only wheel (unknown CLI
flags); missing-lane failure was also observed before implementation. Its first
new-candidate run exposed a Lab harness layout error: operator files were inside
the strictly graded workspace. Moving them outside that workspace restored the
unchanged repair task; no Runtime change or model retry was needed for that fix.

CLI checks use actual isolated installed subprocesses, numeric-loopback HTTP
and synthetic native executables. They cover three-backend fallback, JSONL/text,
graded output, cross-process cooldown, zero request/tool caps, all-unavailable,
native/API effects without replay, native success, backend exclusion and cleanup.
Fixture results are not provider quota/authentication certification.

Reproduction (substitute the exact wheel directory under the manifest SHA):

```sh
.venv-unified-cli/bin/python -m pytest -q
.venv-unified-cli/bin/python -m lab_runner.native_eval unified-cli-test \
  --manifest .cache/unified-cli-runtime/manifest.json --wheel-dir <wheel-directory>
.venv-unified-cli/bin/python scripts/build_consumer.py \
  --dependency-mode candidate --manifest .cache/unified-cli-runtime/manifest.json \
  --wheel-dir <wheel-directory> --tag prosaic-integration-lab:unified-cli
```

## Bounded live installed CLI

Fresh private evidence: `reports/unified-cli-live-2026-10-23/`.
Report SHA-256: `43e6bd1f68b96aa5e27e1cfaa42877bc315a8b4a5220d672b90da0acaf37cb09`.
All six scenarios passed with the same canonical neutral repair Markdown and
initial calculator input. Each invocation used the installed CLI module in an
isolated subprocess, with total/API deadlines 180 seconds, native deadline 60,
three profile attempts, two native attempts, eight API requests, seven API tool
calls, eight tool rounds and 65,536 API reported tokens. Native permission was
workspace-write; API permissions were read/write/edit with the exact calculator
write target. Raw backend streams were parsed in memory; private evidence keeps
filtered pool fields and the known synthetic output, not raw streams/session IDs.

| Scenario | Selected backend | CLI wall time | Result |
| --- | --- | ---: | --- |
| First available | Claude Sonnet | 7.441 s | Repair passed |
| Claude cooling | Codex gpt-6.1-sol, low effort | 15.403 s | Repair passed |
| Both native profiles cooling | Local ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ | 64.596 s | Repair passed |
| Every profile cooling | None | 0.702 s | Zero dispatch; retry time returned |
| Before Claude cooldown expiry | None | 0.614 s | Zero dispatch |
| After expiry | Claude Sonnet | 7.031 s | Repair passed |

These are validation latencies including CLI startup, not repeated comparative
benchmark estimates; full test suites were also running on the host. JSONL
events were captured with the terminal result, so captured event timestamps do
not measure real-time event delivery. The durable shared allowance retained
**7/60 mixed units** (three native assignments and four local API requests), with
zero unknown dispatch reservations. Native internal request/token cost remains
unknown. Only one Claude account was available.

Capacity marks were controlled host inputs in a private capacity file, not actual
provider quota exhaustion or simulated provider responses in the live lane.
Provider-error classification and no-replay behavior have separate fixture
evidence. No automatic replay followed uncertain work.

## Cleanup and limits

Verified owned local inference PID 57553 by listener and both log descriptors,
then stopped it with SIGTERM (exit 143). Port 8000 is closed. All containers
carrying `io.prosaic.lab.owner=unified-cli-20261023` were auto-removed; temporary
workspaces are absent. Existing model cache/profile and historical reports remain.
Private receipts contain the driver, admission records, allowance/capacity,
filtered samples, outputs, build/install/test logs and cleanup/checksum records.

This is local experimental qualification. No publication, push, release, database
qualification, portable native/API accounting or new hosted quota-exhaustion
claim is implied. Unrelated Runtime examples and Lab changes were preserved.
