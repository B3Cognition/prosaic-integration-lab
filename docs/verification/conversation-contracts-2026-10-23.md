# Conversation contract investigation — 2026-10-23

Both failures from the optional-memory checkpoint reproduced against the same
checksummed installed SDK family and unchanged hash-locked host dependencies.
The causes were stale test expectations for documented Harness 0.8.2 behavior.
No application, Runtime, Harness, provider or SDK dependency changes were needed.

## Simulated tool text

The synthetic provider returns tool-shaped prose instead of a native tool call.
Runtime records one completed provider request and **zero tool calls**. The
workflow's output fails validation and Harness blocks the workflow. Conversation
then marks its unfinished handoff `needsResolution` with `failureCode=interrupted`.
The conformance schedule correctly rejects that reply at the `reply` phase.
The old test expected a completed reply to reach a later `evidence` check.

The test now requires the exact `reply/interrupted` diagnostic and retains every
existing assertion for failure, zero effects, allowance retention, call count,
no retry and sanitized export. A new real-provider characterization test also
checks the persisted blocked run, no pending invocation, matching immutable
receipt digest, one complete metered provider request, zero tool calls, no
completed answer, and unchanged run/receipt/effects/provider counters across two
fresh-controller recoveries.

## Lost approval acknowledgement

Harness persists the unique decision ID, original revision, choice and response
before advancing a workflow. Conversation recovery can adopt an exact saved
decision only when the workflow has reached stable waiting/completed/rejected
state with no pending call. It does not call `resume` during recovery. This
public behavior is documented in the Harness conversation lifecycle guide and
implemented by its installed recovery controller.

The old assertion required `needsResolution` after both prepared and returned
commands. After the returned command has committed its exact decision and
effect, the correct reply is completed with no recovery failure. A merely
prepared command stays unresolved.

The functional test now verifies the pending command's owner-bound run,
source message, choice, response and original revision against its unique
durable decision before reconstructing the host. It requires the exact reply
for each boundary, repeated recovery idempotence, and full run snapshot equality
alongside the unchanged provider counters, domain rows and completed journal.
Two additional real HTTP tests complete the same choice with a **missing** or
**different** decision ID; both must remain unresolved after host reconstruction
and repeated recovery, with no redispatch or additional effects.

The corresponding PostgreSQL worker-loss acceptance test had the same stale
expectation. It now checks the exact prepared/committed outcomes, stable full
run snapshots, identical repeated replies and unchanged effect journal/call
count. Original safety assertions were retained and strengthened. Independent
read-only review confirmed the updated contracts and identified this related
acceptance case.

## Verification

Source baseline: `966c231`, branch `codex/optional-castle-memory`. Host Python
3.12.15, macOS/Darwin ARM64; database and consumer containers Linux ARM64.
The SDK/worker checksums remain in
[initial memory profile](../../dependencies/memory-candidates-2026-10-23-initial.json), SHA256
`76bb942041292dcee640a314c38f185c94424ec2cdd9b54e1a81f59f8b999812`.
Host third-party versions match the unchanged repository lock, SHA256
`022b22de1b5999ad7037fc3fe5d91981601a87bb1fd55e54a8b96a985df6064d`.

| Check | Result | Evidence |
| --- | --- | --- |
| Original two failures, before changes | 2 failed | Watched reproduction against pinned SDKs |
| Full unit/functional suite, including three new cases | **968 passed, 0 failures/skips** | 91.86s; existing Starlette/httpx deprecation warning |
| Installed memory lane, PostgreSQL 16 | **6 passed, 0 failures/skips**, cleanup verified | [Receipt](conversation-contracts-2026-10-23-memory-pg16.json) |
| Installed memory lane, PostgreSQL 18 | **6 passed, 0 failures/skips**, cleanup verified | [Receipt](conversation-contracts-2026-10-23-memory-pg18.json) |
| Actual worker loss before/after approval, PostgreSQL 16 | **2 passed, 0 failures/skips**, cleanup verified | [Receipt](conversation-contracts-2026-10-23-approval-pg16.json) |

The full suite ran from the isolated checkout with the Lab absent from the
SDK-only environment, as existing source-bootstrap tests require:

```sh
/private/tmp/prosaic-lab-memory-sdk-env/bin/python -m pytest -q
```

Both memory lanes ran against the installed Lab wheel with parent/child `-I`,
source-path injection disabled, the real Castle worker and separate restricted
runtime roles. Exact frozen evidence, process resume after source mutation and
worker shutdown, owner denial, no-repeat execution and disabled/optional/required
unavailability checks all passed again:

```sh
python -I -m lab_runner.memory --enable --manifest dependencies/memory-candidates.json --artifacts /private/tmp/prosaic-lab-memory-wheelhouse --worker-python /private/tmp/castle-worker-installed/bin/python --postgres-version 16 --output /private/tmp/prosaic-conversation-memory-pg16.json
python -I -m lab_runner.memory --enable --manifest dependencies/memory-candidates.json --artifacts /private/tmp/prosaic-lab-memory-wheelhouse --worker-python /private/tmp/castle-worker-installed/bin/python --postgres-version 18 --output /private/tmp/prosaic-conversation-memory-pg18.json
```

The focused PostgreSQL approval check used the existing `OwnedStack` and
`test_approval_handoff_loss_preserves_effect_journal_without_resume` node, two
HTTP replicas, actual process kills, migration/runtime role separation and
independent PostgreSQL domain/journal evidence. An offline image overlay copied
the isolated Lab source onto the prior memory candidate, retained the exact
same SDK wheel bytes, and passed the existing installed-payload audit. Its
five-SDK manifest is the first five entries of the memory manifest, encoded with
`json.dumps(..., indent=2) + '\n'`; its digest and image identity are in the
receipt. Temporary orchestration command:

```sh
/private/tmp/prosaic-lab-memory-sdk-env/bin/python /private/tmp/prosaic-conversation-qualification/run_target.py 16
```

Only sanitized receipts are committed. Temporary host configs and raw diagnostic
logs stay outside version control; exact-owned container/volume/network cleanup
was verified. The targeted approval check does not claim a rerun of the complete
conversation acceptance matrix or a published release. FTS defaults, provider
scope/provenance, memory policies, SUE and SOAR separation remain unchanged.
