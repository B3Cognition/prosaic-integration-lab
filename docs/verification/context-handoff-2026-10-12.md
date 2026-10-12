# Prepared context across model tiers

This change adds a required native acceptance case for a balanced-tier agent
preparing JSON context and a strong-tier agent consuming it on a fresh HTTP
replica. The context is an accepted Harness output stored in PostgreSQL, not a
shared file. Both invocations use the five checksum-verified published SDKs in
`dependencies/releases.json`; no sibling library source is modified.

## Scenario

The synthetic balanced model generates a unique context fact absent from the
original request and agent instructions. Harness accepts it against the `found`
schema and pauses before consumption. The test reads the context and immutable
preparation receipt through the public PostgreSQL RunStore API, stops the
producer replica, replaces the consumer replica with a fresh container, and
resumes there.

The strong-tier consumer must receive the exact context and its artifact
binding, including the preparation invocation identity and digest. Its answer
uses the generated fact and passes the `reviewed` schema. The test reads that
answer through the operator RunStore API: Lab deliberately suppresses public
review output when the graph includes an earlier pause before review. Completion
requires both outputs. The test checks distinct request models, two total invocations,
two complete accounting calls, unchanged preparation evidence and no additional
dispatch on final approval. Negative fixture tests reject missing, altered or
unbound context.

The owned native fixture explicitly enables synthetic tier routes and separate
inline/composition/tier grants for tenant A. Ordinary native configurations do
not enable those routes. Synthetic inference verifies data flow and routing;
it does not certify real model comprehension or quality.

## Verification checkpoint

- Host: macOS ARM64; Python 3.12 in `.venv-readiness`.
- `.venv-readiness/bin/python scripts/audit_install.py --manifest dependencies/releases.json`:
  all five installed SDK payloads match the pinned wheels.
- `.venv-readiness/bin/python -m pytest -q`: **749 passed**; one existing
  Starlette/httpx deprecation warning.
- Focused context and native gate tests: **26 passed**.
- Native acceptance collection: **54 tests**, matching the updated required
  lane count and fixed safe failure code `context_handoff`.
- `.venv-readiness/bin/python -m build --outdir /tmp/prosaic-lab-context-handoff-dist`:
  wheel and source distribution built successfully.
- `git diff --check`: passed.

The first source-suite attempt in `.venv-public` had 747 passes and one
environment failure: the SDK-only CLI test intentionally rejects an already
installed Lab package. The SDK-only `.venv-readiness` environment passed the
full suite without changing that test. The legacy `.venv` has older SDKs and
cannot exercise the current WorkflowFactory API.

## Native PostgreSQL acceptance

The user authorized restarting Docker Desktop. The normal restart stalled;
`docker desktop stop --force --timeout 20` recovered the daemon. The rebuilt
consumer uses immutable image ID
`sha256:9328227c708ae0243872f09a4008c26fe76eb43efb3723007cd7c71486c45f70`
and the five original released SDK wheels from manifest SHA-256
`37a7b0dcf7bffa1c64481aafc7173e947c1e083616adcf50112e53022d589aca`.
The consumer build independently audited all installed SDK payloads.

Both complete native lanes passed on Docker Desktop Linux ARM64 with Python
3.12.14 on the macOS ARM64 host:

| PostgreSQL | Required cases | Failures/errors/skips | Cleanup | Evidence owner |
| --- | --- | --- | --- | --- |
| 16 | 54 passed | 0 / 0 / 0 | Verified | `79020a01ac114b90998f945d83353307` |
| 18 | 54 passed | 0 / 0 / 0 | Verified | `2fecf5c0ad4842dbbccce359153c9859` |

Each run retains its sanitized `result.json`, `junit.xml` and ownership receipt
under `.lab/<owner>/`. The runner reports `qualification: qualified` and
`payload_audit: verified` for both. A read-only inspection before teardown also
confirmed each context workflow was completed, used exactly two model calls
(`fixture-balanced`, then `fixture-strong`), and reused the generated fact.

The first PostgreSQL 16 attempt, owner `6597f518aff14907a513935ca096bb45`,
passed 53 cases and failed the new case's public `reviewOutputs` assertion;
cleanup was verified. The agent calls and database handoff had succeeded, but
Lab intentionally hides review outputs for graphs with a pause before review.
The assertion now checks the persisted answer through the public operator
RunStore API. Production filtering was preserved. The subsequent full runs above
passed, and the final source-suite run passed all **749 tests** again.

Independent read-only code review found no important issues. No AMD64 lane,
paid provider call, real-model quality trial, push or release was performed.
Historical release receipts and counts remain unchanged.

Executed commands:

```sh
.venv-readiness/bin/python scripts/build_consumer.py \
  --manifest dependencies/releases.json --dependency-mode released \
  --tag prosaic-integration-lab:context-handoff
.venv-readiness/bin/python -m lab_runner test --mode native \
  --postgres-version 16 \
  --consumer-image sha256:9328227c708ae0243872f09a4008c26fe76eb43efb3723007cd7c71486c45f70
.venv-readiness/bin/python -m lab_runner test --mode native \
  --postgres-version 18 \
  --consumer-image sha256:9328227c708ae0243872f09a4008c26fe76eb43efb3723007cd7c71486c45f70
```
