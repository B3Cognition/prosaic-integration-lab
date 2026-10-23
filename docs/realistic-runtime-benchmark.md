# Repeated realistic unified CLI benchmark

This optional candidate lane compares complete agent executions through one
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

Prepare an exact installed candidate using the
[candidate guide](unified-runtime-pools.md#installed-candidate-validation).
Copy the native and local [example profiles](../configs/README.md), choose
accessible model names and authenticate outside the benchmark. The lane requires
one Claude profile, one Codex profile and the API default profile; aliases must
not collide. No credentials are copied into source or reports.

```sh
python -m lab_runner.native_eval unified-benchmark \
  --manifest /private/candidate/manifest.json \
  --wheel-dir /private/candidate/wheels/MANIFEST_SHA256 \
  --runtime-config /private/native.yml --local-config /private/local.yml \
  --repetitions 3 --timeout 60 --local-timeout 180 --live \
  --output /private/new-unified-benchmark-results
```

Three trials per task and availability state give 27 assignments. States apply
no host exclusion, a temporary Claude cooldown, or temporary cooldowns for both
native profiles. One capacity file preserves real cooldowns across the study;
restoring an owned exclusion never clears an existing provider mark. Task and
state order rotate across trials. Every assignment starts in a fresh workspace;
an existing output directory fails rather than resetting accounting.

Native deadlines stay at 60 seconds, local/API at 180, and the total pool ceiling
is 300 seconds to accommodate pre-work fallback. Explicit invocation authority is
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
normal tool use and final-response completion within 180 seconds. Prepare a new
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

The retained [27-run comparison](verification/unified-cli-realistic-2026-10-23.md)
records all 27 successes, medians/ranges, exact hashes, paired historical baseline
audit and cleanup. The separate
[provider-shaped rejection tests](verification/unified-provider-fallback-2026-10-23.md)
verify fallback before work and no replay after partial text or tool effects.
