# Question-first generation candidate — 2026-10-26

Implemented the approved [serving-trace recommendations](qwen-serving-trace-2026-10-26.md)
as separate opt-in candidates. Mechanical qualification passes. The unchanged
Qwen preflight still fails its first 60-second call, so the 100-question model
comparison remains unstarted and answer quality/critic benefit remain unmeasured.
Memory and SUE stay disabled by default; SOAR is outside this workflow. Nothing
was published, pushed or merged.

## Changes and compatibility

Runtime candidate `0.9.8+jsonschema.3` adds host-only
`response_schema_order='declared'` and capability `json_schema_order_v1`.
The default remains canonical sorted order. Both modes retain bounded deep
ownership, finite JSON, schema validation, local-reference restriction and input
limits. Canonical schema hashes stay unchanged; declared calls also record an
order-sensitive wire digest. Adapters inherit the caller's schema/mode and
cannot replace its declared order.

Lab adds two explicitly frozen generation profiles:

- `compact-question-first-v1`: declared nested schema order, starting with
  question parts; existing compact guidance retained as the control.
- `compact-question-focused-v1`: the same transport plus guidance to cover the
  requested parts with distinct necessary facts, consolidate duplicate support,
  preserve material details, and finish the object. No hard claim cap.

Both retain every displayed source and address. Their frozen request includes
the wire digest, because canonical JSON workflow hashing alone ignores object
order. Changing mode or schema order cannot silently resume a saved workflow.
The existing canonical/compact profiles remain exact in the regression audit.
Canonical critic feedback and independent author composition remain separate
from SUE. Strict canonical schema, grounding, scope/provenance, scorer, retrieval
policy and budgets are unchanged.

## Verification

macOS ARM64, Python 3.12.15; Core 0.4.1, Harness 0.9.4, Runtime candidate .3,
Lab candidate 0.6.0. Tests ran through installed public SDKs; released dependency
pins were not changed. No new Linux/PostgreSQL qualification is claimed here.

| Verification | Result |
| --- | --- |
| Runtime full suite against immutable candidate revision | 1,474 passed, 1 skipped |
| Separate installed Runtime transport/metadata gate | 42 passed |
| Installed production and conversation wheel smoke | Passed, fixture-only |
| Full Lab suite with released SDKs | 2,163 passed, 73 subtests passed |
| Installed Lab candidate acceptance | 40 passed, 36 subtests passed |
| Preserved retrieval capture regression audit | 300 captures, 6,169 body spans unchanged |
| Installed serving grammar proof | Declared top-level/nested order accepted; missing/duplicate required fields rejected |
| Fresh read-only code review | No findings |

Tests cover actual HTTP transport, unchanged default mode, callback ownership,
invalid schema/order admission, full strict resolution, independent critic inputs,
zero-call resume, changed-order resume rejection and unknown-usage retention.
The 300-capture audit verifies both previous profiles' requests and schemas
against the preserved implementation and every new profile's full source text
and addresses. Grammar proof uses the installed compiler and cached tokenizer,
without model weights or inference; `any_order` remains false.

Commands and complete logs are in the private evidence archive. Main commands:

```sh
PROSAIC_RUNTIME_RELEASE_REF=d713e078a661a19a057f02482d47d3f7a23b0c5a \
  python -B -m pytest -q  # Runtime candidate worktree
python -B -m pytest -q    # Lab worktree, released SDK-only environment
python -I -B scripts/production_wheel_smoke.py
python -I -B scripts/conversation_wheel_smoke.py
python -B -m build --no-isolation
```

The Runtime revision is a local immutable verification object produced with a
temporary index; branch HEAD and real staging remain unchanged. Its exact source
archive is retained. Installed tests run from copied test packages outside source
checkouts; source/wheel/sdist/installed payload equality is verified for both
candidates and the unchanged Castle adapter/worker. One Runtime skip is the
installed-wheel test, which passes in its separate required gate. Lab reports an
existing Starlette deprecation warning.

Watched failing tests and initial qualification errors remain in the archive:
missing new APIs/profiles before implementation; loopback/Metal sandbox failures;
an obsolete exact candidate-version assertion; an archive test initially building
old HEAD; and a copied-test package layout error. They were corrected without
relaxing validation or assertions. No benchmark failure was replaced or retried.

## Same bounded Qwen preflight

Same Qwen2.5-Coder-7B 4-bit model, three questions (`q001`, `q011`, `q097`), nine
scheduled samples, source corpus, grading key, balanced retrieval policy, strict
scorer, temperature zero, 60-second/4,096-token calls and no tools/retries. The
focused profile was selected only after separate order-only verification.
The precommitted allowance remains 27 requests/884,736 tokens/3,600 seconds.

| Observation | Result |
| --- | --- |
| First sample | `q001-manual` |
| Runtime answer-stage elapsed | 60.244 seconds |
| Attempt evidence | Timeout; matching frozen declared-order wire digest |
| Retained stdout / reported usage | Empty / unknown |
| Provider requests / accepted answers / critic calls | 1 / 0 / 0 |
| Remaining samples | 8 blocked by unknown-usage policy |
| New full-sample reservation retained | 3 requests / 98,304 tokens |
| Sealed replay and repeated completed-run command | Identical results, zero dispatch and no file changes |

The outer adapter result reports `usage_unknown`; its attempt records the
timeout. The empty retained stdout does **not** establish that the server emitted
no content or identify whether queueing, cold prefill or decoding consumed the
time. This preflight has no transparent SSE trace or per-phase instrumentation.
The earlier trace used a different prompt and an already exercised cache prefix;
its timing cannot be assigned to this request. Read-only checks found the server
idle before the run and no active/waiting requests afterward.

No semantic answer can be graded, no Castle/file-search quality comparison is
established, and no critic benefit can be measured from this result. The next
useful investigation is phase-level observation of this new prompt, including
cold versus warm prefill, before another generation change or larger run. Any
further inference needs a separately bounded, precommitted experiment; the
stopped run does not authorize a retry or release its reservation.

## Evidence and local decisions

All 17 historic archive copies /33,207 indexed files verify unchanged before,
before inference and after inference. All six earlier unknown reservations remain
held; this run adds a seventh. Private archive: `memory-question-first-20261026`.
It includes source snapshots/diffs, the ledger, failed tests, qualified packages,
full logs, frozen input identities, protocol, raw receipts, strict scorer outputs,
replay proof and accounting evidence. No keys or private payloads enter Git.

Local decisions: leave branches/worktrees uncommitted for review; use a temporary
Git verification object for exact archive tests; review only the new delta while
running full suites and unchanged-function audits; judge quality only from strict
live evidence; verify full-suite terminal results and historic archive hashes
separately from the fresh code reviewer. No deferred review findings.
