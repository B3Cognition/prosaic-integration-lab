# Optional answer-span audit

The audit checks whether an answer actually states the material facts supported
by its frozen context. It is experimental and independently opt-in. Memory and
SUE remain disabled by default. Castle retrieval, existing answer generation,
the protected critic and the previous completeness workflow are unchanged.

For example, a source may say resume works when memory is "offline, changed or
disabled." An answer saying only "offline or changed" has omitted a condition.
Attaching the complete source quote does not put that condition into the answer.
The audit must point to actual answer words before marking it covered. A correct
paraphrase is allowed; quote identity alone cannot establish its meaning.

## Try the mechanics without a model

Use the tested environment with the constrained-JSON Runtime candidate and
Harness installed. No credentials, memory palace or model endpoint are needed:

```sh
python -m lab_runner.memory_benchmark audit-fixture \
  --case omitted --output /absolute/new/private/audit-example
```

Use a fresh directory for each case:

| Case | Expected result | What it exercises |
|---|---|---|
| `omitted` | `findings` | A source qualification is missing from the actual answer. |
| `complete` | `clear` | A supported answer contains the required fact. |
| `unavailable` | `clear` | Frozen context is empty and the original correctly abstains. |
| `unknown-usage` | `unresolved` | Execution stops after one fixture request and holds the full allowance. |

The command uses a bounded loopback HTTP fixture through real installed Runtime
and Harness APIs. It also checks a zero-call resume while that same fixture
configuration exists. `syntheticProviderRequests` and synthetic token receipts
measure mechanics; `realModelCalls` is zero and review quality is unmeasured.
The fixture accepts neither a live configuration nor a repair flag.

Reopening the fixture with a newly allocated endpoint in the same directory
refuses its changed binding. For a consumer resume, retain the same frozen
packet, SDK/profile versions and Runtime configuration.

## Consumer integration

This is a trusted host API, with no new public HTTP route. Derive namespace,
allowed wings, owner and source/run binding from verified host context. Do not
treat identities supplied by clients or models as authorization.

```python
from lab_runner.memory_benchmark.completeness_profile import freeze_packet
from lab_runner.memory_benchmark.span_audit_contracts import freeze_audit
from lab_runner.memory_benchmark.span_audit_workflow import run_audit

review = freeze_packet(question, canonical_answer, frozen_frames,
                       identity=trusted_host_identity)
packet = freeze_audit(review)
result = run_audit(runtime_config, packet, private_run_directory,
                   accounting=host_accounting_recorder)
```

Calling this API explicitly opts into execution. Live inference requires its
own authorized, predeclared shared allowance and qualified serving profile.
The current implementation verification uses fixtures only. Runtime must expose
`json_schema_v1` and `json_schema_order_v1`; the existing tested candidate is
`b3-prosaic-runtime==0.9.8+jsonschema.3` with Harness `0.9.4`. Unsupported
Runtime versions fail before dispatch. No SDK internals or copied execution
engines are used.

The two stages are:

1. **Source obligations:** receives the exact question and authorized displayed
   source bodies, with the draft withheld. It identifies material conditions,
   uncertainty, conflicts and requested associations.
2. **Answer audit:** independently checks that ledger, the same bodies, actual
   canonical claim text, explicit limitations and selected citations. Every
   obligation and every claim needs a disposition.

The host supplies exact addresses and hashes. Source spans, claim-answer spans,
question spans and limitation spans have separate types. A limitation can show
that an answer correctly acknowledges an unknown; it cannot count as an answered
fact. Conditions and citation entailment remain semantic judgments to evaluate,
not guarantees supplied by JSON validation.

`result['original']` always retains the original canonical answer.
`result['audit']` is the accepted sidecar, or `None` when it was not accepted.
`outcome` is `findings`, `clear` or `unresolved`; `clear` means the auditor found
no issue. It is never approval, a truth certificate or permission to execute
anything. There is no automatic repair or host status rewrite.

## Bounds, resume and evidence

The audit allows two calls total, 120 seconds per call, 270 seconds per audit,
65536 reported tokens reserved, zero tools and zero retries. Each stage permits
4096 output tokens and 16384 raw/canonical output bytes. The packet is bounded
to 262144 UTF-8 bytes, with at most 16 question parts, 32 source obligations and
32 extra findings. Exceeding a bound fails closed; nothing is silently truncated.

Completed resume makes zero provider calls. Changed packet, provenance, scope,
SDK/validator versions or serving configuration refuses resume. A blocked or
unknown invocation is never automatically dispatched again. Unknown usage or
completion retains the full reservation, even if a later health check succeeds.
The local allowance is checked against native receipt evidence. Losing its final
record cannot silently release the reserved allowance.

The private run directory retains the packet, native Harness checkpoint and
receipts, plus reserved/final allowance files. The result's raw `evidence` is
operator-only; consumers must expose filtered views, never raw cross-owner state.
Keep failed artifacts and old reservations. New source code deliberately changes
frozen code bindings: use the preserved original wheel to replay historical
benchmark runs; do not rewrite those snapshots to match a new package.

## Qualification still needed

Fixtures establish attachment, isolation, budgeting and resume behavior. They
do not establish omission detection or answer improvement on real questions.
Before a live comparison, pin the disputed semantic adjudication, keep the same
strict scorer/contexts/denominators and predeclare calls, token reservations,
repeats and stopping rules. Report false alarms, missed obligations, citation and
status mistakes, unresolved runs and cost separately. A repair stage requires
a later design and comparison. SUE and SOAR remain separate.
