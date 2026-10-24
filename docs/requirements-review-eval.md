# Frozen-source requirements review v1

This separate consumer compares direct review, critic then author, and an
existing `SueReviewSession` dialogue followed by final synthesis. The runnable
demo uses scripted loopback responses only. It checks execution, accounting,
source identity and scoring mechanics; it supplies no evidence that SUE improves
review quality, finds defects, saves cost or outperforms another strategy.

Prepare the installed public SDK environment and optional pure SUE wheel using
the [SUE guide](sue-review.md). This lane pins Core 0.4.1, Runtime 0.9.8 and
Harness 0.9.4. The optional SUE engine identity is pinned separately in the
source lock. Missing optional dependencies fail the explicit enabled profile;
they are not silently skipped or installed by running the demo.

From this checkout, with that environment active:

```sh
PYTHONPATH=src python -m lab_runner.requirements_review_v1 --fixture --output /absolute/new/requirements-demo
PYTHONPATH=src python -m lab_runner.requirements_review_v1 --replay --output /absolute/new/requirements-demo
python -m pytest -q tests/unit/test_requirements_review_core.py tests/unit/test_requirements_review_legacy.py tests/requirements_review
```

`--fixture` requires a new directory. Existing or interrupted directories are
never overwritten or silently redispatched. `--replay` opens saved synthetic
artifacts and performs zero inference, source retrieval or Harness continuation.
The CLI offers no live mode, endpoint, credential or allowance option. It does
not inherit any historic approval or spend reservation. Runtime requests use a
literal owned loopback fixture with no authentication, tools or environment
proxy. Output contains only these synthetic documents and model-shaped fixtures.

## Cases and objective checks

Eight small authored dossiers cover a contradiction, an undefined term,
unmeasurable acceptance, absent failure behavior, an unsupported assumption,
missing governing context, a clean control and a contradiction accompanied by a
hostile embedded instruction. They deliberately make their known issues clear;
this is a small diagnostic family, not a representative or difficult benchmark.
Some absence statements are explicit facts in the synthetic source. A future
quality study must not infer broad defect-finding ability from these examples.

All strategies receive the same claim, exact frozen document bytes, metadata,
public issue definitions and final schema. SUE presents the same frozen text as
numbered lines through its existing public session. Direct and author prompts
carry the complete frozen record, preserving original CRLF and its UTF-8 hash.
Final citations identify `sourceId`, the exact `textSha256`, and inclusive
source-local `startLine`/`endLine`. The final artifact has a case ID, assessment,
unique known issue codes and citations. `NO_KNOWN_ISSUES` refers only to this
supplied source and its known checks; it is not truth or release approval.

The host-only keys specify exact issue-code sets, assessments and accepted
support ranges. The deterministic scorer checks these finite assertions and
hash-bound citations. It does not judge natural-language entailment, infer
whether arbitrary prose is correct, score freeform explanation quality or
certify that a document has no other defects. The public execution module imports
neither keys nor scorer. Runtime schemas provide structural validation only;
hidden semantic grades and expected support are never repair feedback. The
fixture provider derives scripted final answers from host keys, explicitly as
an oracle for testing plumbing. This must not be represented as model inference.

## Strategy and budget boundaries

Direct review has one final agent. Critic-author has a case-neutral critic
artifact followed by an author using the same source and public final contract.
SUE uses the existing source-freezing/session/engine/Harness implementation,
then a generic Harness final agent evaluates its advisory report against the
same source. Its dialogue is not copied into this package. There are no semantic
validators or key-driven correction steps in any strategy.

Every sample activates one public Runtime `ExecutionBudget` around all stages:
30 provider requests, 65,536 reported tokens and 120 elapsed seconds, with zero
tool calls. Per-agent validation allows at most two attempts. SUE can consume
up to 28 attempts before synthesis; the outer budget does not replenish on
moving to another Harness run. Failed/rejected attempts, critic calls, every
SUE turn and final synthesis all count. An incomplete or unknown-usage strategy
does not receive free synthesis or become a semantic reasoning failure. Token
and time stops, execution status, usage completeness and final semantic grade
remain separately visible. Reported-token admission is a stop threshold rather
than a qualified native-token reservation guarantee; live context/spend safety
has not been qualified here.

The synthetic owner, namespace and sample ID link all runs. SUE retains its own
public application accounting context; generic review stages use the eval
application context with that same trusted owner and sample request ID. A shared
process-local budget is the whole-sample admission boundary. It is not a durable
live allowance and grants no crash retry authority.

`RESOLVED` is an advisory SUE diagnostic indicating examined dimensions. It is
stored separately from the final semantic grade. A resolved dialogue with a
wrong final answer fails; a bounded or aporetic terminal is preserved without
being rewritten into approval. The scripted SUE dialogue intentionally exercises
valid engine transitions even for flawed documents; final oracle answers do not
demonstrate that this dialogue found those flaws.

## Artifacts, replay and provenance

Each of the 24 cells retains `report.json`, `evidence.json`, a sample hash lock
and its private synthetic Harness file store. Evidence includes the complete
wire request/response inventory, saved invocation receipts and checkpoints,
rejected attempts, frozen task identity, limits and actual SDK versions. Replay
retains the credential-free runtime binding and restores the supplied documents
into a disposable public `FileRunStore`. Public `Harness.status` validates SDK
checkpoint/receipt seals, ledger/argument hashes, accepted bindings, schemas and
workflow fingerprints. A disabled public `SueReviewSession.report` reconstructs
the full SUE diagnostic. No graph node is driven during this interpretation.
The existing host `project_answer` reconstructs each complete deterministic SUE
question/schema/state/source projection with a capture-only callback. Exact wire
prompts and RuntimeAdapter argument hashes must match it, including when an
attacker recomputes receipt seals. Replay also joins raw SUE output to wire
responses and every request/token count to Runtime budgets. Completed
SUE and final Harness replay are also checked for zero added dispatch.

The matrix lock pins all 24 cell locks and the summary. The source lock pins new
module bytes, case/key digests, SDK versions and SUE engine identity. It is
checked before dispatch. Checksums detect changes against retained locks; they
are not signatures, provider attestations or protection against coordinated
replacement of code and all locks. Missing receipts and incompatible bindings
fail interpretation rather than being silently normalized or fabricated.

The synthetic wire returns 10 input and 5 output tokens per request. Their
counts and the explicitly labeled synthetic rate-card arithmetic are fixture
bookkeeping, not actual model usage, invoices or money spent.

The legacy release-review scorer is a separate six-file byte-exact slice from
`ready-to-ship-v10.zip`, SHA256
`f9c5aa8c2e5a8d8cad6685c38a61a506fc0d34c6317b5275b77e81d3715b190b`.
`legacy-v10-source-lock.json` records archive/member identity. Its eight host
constructed example answers are graded separately, with original observed-read
requirements intact; all eight fail without traces. No old grader, public
contract, key, version identifier or historical result was changed. The original
77-file ZIP and original Runtime 0.9.3/Harness 0.8.2 execution closure remain
frozen outside this small scoring slice. The historical v2-v10 execution stack,
live runner and approvals are not copied into this experiment.

## Local verification

The implementation was developed with watched failing tests for the missing
suite, absent execution boundary and output/prompt/receipt binding defects.
The explicit enabled profile is `tests/requirements_review`; ordinary pure
core/legacy tests remain under `tests/unit`. The optional SUE CI runs both
enabled SUE and requirements directories explicitly, with no skips.

Commands actually run on October 24, 2026, in the pinned local environment:

```sh
PYTHONPATH=src /private/tmp/prosaic-sue-env/bin/python -m lab_runner.requirements_review_v1 --fixture --output /private/tmp/prosaic-requirements-review-v1-demo-20261024-sealed-final
PYTHONPATH=src /private/tmp/prosaic-sue-env/bin/python -m lab_runner.requirements_review_v1 --replay --output /private/tmp/prosaic-requirements-review-v1-demo-20261024-sealed-final
/private/tmp/prosaic-sue-env/bin/python -m pytest -q tests/unit/test_requirements_review_core.py tests/unit/test_requirements_review_legacy.py tests/requirements_review
```

The frozen CLI demo completed 24/24 scripted cells: direct used 8 requests,
critic-author 16 and SUE plus synthesis 64, totaling 88 requests and 1,320
synthetic tokens. Offline replay reproduced that result with zero added
requests. Separately, all eight legacy constructed examples passed with traces
and were rejected without them. The focused enabled test profile also asserts
zero-network replay, failure accounting and immutable output behavior.
Thirteen additional watched RED/GREEN tamper controls cover complete projections,
instruction prefixes, argument hashes, SDK seals, rehashed prefix/projection
forgeries, strategy labels, negative elapsed time and a legitimately sealed
checkpoint before finish mislabeled as completed. A completed sample requires
every saved stage to be completed. The earlier demo directories without
`-sealed-final` are retained as intermediate evidence; old implementation
bindings are not silently upgraded or reused by the final replay.

No live inference, hackathon submission, publication or final rubric compliance
is claimed. This source/case family is new October 24 pre-event preparation.
Retain the original baseline's pre-event disclosure and distinguish any future
during-event changes rather than relabeling this work as new then.

A quality claim requires a separately authorized, blinded repeated study with
new held-out sources, predeclared budgets/metrics, model snapshots, randomized
strategy order and all failed/uncertain attempts included. This fixture demo
does not authorize that study or new provider calls.
