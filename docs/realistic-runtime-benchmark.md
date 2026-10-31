# Repeated realistic unified CLI benchmark

This optional live lane compares complete agent executions through one
Claude Code → Codex CLI → local/API pool. It reuses canonical neutral Markdown,
synthetic packets, initial drafts and fixed factual/workspace graders.

| Task | Work | Success contract |
| --- | --- | --- |
| Release brief | Correct a draft using current checks and a stale approval | HOLD, exact candidate, failed migration evidence, stale review exclusion and owned action |
| Incident handoff | Correct status, impact and uncertainty | MITIGATED, unconfirmed cause, 16-minute interval, exact counts, evidence and both follow-up owners |
| Invoice SQL | Repair overdue balance aggregation | Read-only query, correct payment/date/status handling, per-invoice clamp, columns and ordering |

Brief summaries contain 40–100 English words in structured JSON. Their factual
contracts are graded; narrative elegance is not. SQL is evaluated only against
synthetic in-memory SQLite with read-only authorization and instruction limits.
Generated Python is never executed. Packets must remain unchanged, with no extra
workspace files. Success requires both successful CLI exit and a passing grader;
a valid output left by a timed-out process does not count as success.

## Repeated unified CLI pool study

The configurable `unified-benchmark --local-timeout` described here requires
[Lab 0.6.2](release-0.6.2.md) or later. Published 0.6.1 accepts only 180s; the
[240s study](verification/unified-cli-lab061-local240-2026-10-25.md) used a
private deadline-only driver with unmodified installed packages. Use this
release's wheel or source archive for the configurable command.

Prepare and audit the pinned public Runtime 0.9.8 environment using the
[released-wheel guide](unified-runtime-pools.md#released-wheel-validation).
Copy the native and local [example profiles](../configs/README.md), choose
accessible model names and authenticate outside the benchmark. The lane requires
one Claude profile, one Codex profile and the API default profile; aliases must
not collide. No credentials are copied into source or reports.

```sh
LAB_PY=.venv-unified-release/bin/python
RELEASED_SHA=$("$LAB_PY" -c 'import hashlib; print(hashlib.sha256(open("dependencies/releases.json", "rb").read()).hexdigest())')
"$LAB_PY" -m lab_runner.native_eval unified-benchmark \
  --manifest dependencies/releases.json \
  --wheel-dir "$PWD/.cache/wheels/$RELEASED_SHA" \
  --runtime-config /private/native.yml --local-config /private/local.yml \
  --repetitions 3 --timeout 60 --live \
  --output /private/new-unified-benchmark-results
```

Three trials per task and availability state give 27 assignments. States apply
no host exclusion, a temporary Claude cooldown, or temporary cooldowns for both
native profiles. One capacity file preserves real cooldowns across the study;
restoring an owned exclusion never clears an existing provider mark. Task and
state order rotate across trials. Every assignment starts in a fresh workspace;
an existing output directory fails rather than resetting accounting. The output
parent must already exist. Keep each study's private evidence and allowance.

Omitting `--local-timeout` keeps the local/API deadline at **180 seconds**.
Set `--local-timeout 240` for a 240s local deadline. Finite values from 1 through
300 seconds are accepted; invalid values fail before readiness, report creation
or allowance reservation. The selected deadline is retained in the plan,
individual samples and report limitations. The separate `realistic` command
still requires 180s.

Native deadlines stay at 60 seconds and the total pool ceiling remains 300
seconds. The local deadline cannot extend that total, including time spent on
pre-work fallback. Explicit invocation authority is
native workspace-write plus API read/write/edit with a workspace read root and
exact output write path. Caps are three profile attempts, two native attempts,
eight API requests, seven API tools, eight rounds and 65,536 API reported tokens.
Native inner requests remain opaque. The durable maximum for three trials is
243 mixed units: nine assignments at each maximum of 10, 9 and 8. These are not
token/cost equivalents. Pilot selector/attempt flags are rejected rather than
silently overriding this fixed protocol.

Readiness checks versions and authenticated local catalogue availability without
inference. Live execution requires explicit `--live`. Timeouts, malformed results
and interruption retain elapsed time and uncertain allowances; the runner stops
without automatically retrying an uncertain assignment. Native Codex effort is
an explicit operator profile choice; the recorded study used `low`.

For ThinkingCap/oMLX, the recorded profile disables extended thinking to allow
normal tool use and final-response completion within the selected deadline. Prepare a new
private base without modifying shared settings:

```sh
python scripts/prepare_local_agent_server.py --source-base "$HOME/.omlx" \
  --destination /private/new-omlx-base --model ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ
omlx-cli serve --base-path /private/new-omlx-base --model-dir "$HOME/.omlx/models" \
  --paged-ssd-cache-dir /private/new-omlx-base/cache \
  --host 127.0.0.1 --port 8000 --log-level warning --headless
```

Use an unoccupied port, align the API profile, and retain authentication and
private file modes. Stop only the server instance you own after testing. The
helper never overwrites an existing destination. Local output-token cap remains
2048 in the measured profile. This is a model/server profile control, not an
early-completion shortcut.

## Reports and interpretation

Private 0700 results contain 0600 plans, admission rows, samples, outputs and a
durable allowance. Reports retain only filtered structural events, never raw
vendor streams, credentials or session IDs. Markdown, seeded-input and grader
hashes are checked across trials. Summary fields separate availability states,
actual selected profiles, attempts, skips and `profile_fallback` events. Failed
samples remain in all-attempt latency; successful-only latency is separate.

A cooldown skip is not a dispatched provider-rejection fallback. No quota
exhaustion is induced. No deliberate warmup is performed, and host/cache state
is uncontrolled. Do not infer a p95 or general model ranking from three trials.
Native/API tools and prompts differ, and historical candidate versions differ;
timing differences do not isolate CLI overhead.

The [Lab 0.6.1 / Runtime 0.9.8 240s study](verification/unified-cli-lab061-local240-2026-10-25.md)
passed all 27 assignments, with medians of Claude 10.86s, Codex 21.73s and local
62.37s. All local runs completed within 180s, so the extra timeout did not rescue
any timeout. Its private driver delta is separate from this configurable CLI
implementation; no new model calls were made to validate this code change.

Two earlier [released Runtime 0.9.8 studies](verification/unified-cli-released-2026-10-24.md)
each passed 27/27 assignments, with zero timeouts and 27 controlled cooldown
skips per study. Their comparison retains the exact release provenance,
per-model/task medians and ranges, allowance reconciliation and cleanup.
The latest run changed only the private local endpoint port to avoid the
desktop server; host/cache conditions remain uncontrolled.

The historical candidate [27-run comparison](verification/unified-cli-realistic-2026-10-23.md)
records all 27 successes, medians/ranges, exact hashes, paired historical baseline
audit and cleanup. The separate
[provider-shaped rejection tests](verification/unified-provider-fallback-2026-10-23.md)
verify fallback before work and no replay after partial text or tool effects.
