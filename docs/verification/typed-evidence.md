# Typed evidence consumer pattern

The Lab offers an opt-in, provider-independent evidence envelope. Run
`python -m lab_runner.retrieval_memory --typed-evidence` for preflight; add the
existing explicit fixture/live configuration flags to execute it. Raw records
remain the default. Each format has its own immutable execution identity.

An application supplies the authority, required fact labels, complete bounded
source index and records actually fetched. `memory.evidence.build_summary`
classifies each fact as `verified`, `absent` or `unread`. Absence refers only to
the supplied complete index's scope; it is not a claim about the world. A partial
index must be rejected or treated as incomplete by the application. The Lab
checks that its index matches the complete granted source snapshot before
asserting completeness. Metadata comes from that trusted index; values come
only from fetched records. Wrong-authority and superseded fetched records remain
visible, with explicit exclusion reasons. Tied current revisions fail closed.

The envelope does not calculate a decision or carry a private expected answer.
The model applies the public task rules. The independent consumer validator can
reject a wrong answer and provide bounded feedback; it cannot silently rewrite
the answer. Typed tool results use `lookup-summary-v1`; raw results retain
`lookup-v1`. Replay binds format, implementation, source records and exact
summary digest/size. It cannot adopt another format's run.

Consuming projects should reproduce the **contract and trust boundaries** for
their own domain: define authority, index coverage, current revision selection,
fact types, absence semantics, grants and independent validation. The generic
classifier accepts arbitrary labels and up to sixteen required facts; the Lab's
rollout adapter deliberately supports only its closed public task grammar.
Do not treat that grammar, synthetic corpus or benchmark answer rules as a
general application policy. Execution remains in Runtime and workflow state in
Harness; this retrieval and evidence policy belongs to the application.

This milestone addresses structured tool contracts, context assembly and
trajectory evaluation from the agentic-systems roadmap. It does not establish
durable memory write/forget policy, semantic/vector retrieval, resumable graph
planning, multi-agent protocols or production observability. Current local
models are regression targets. Offline provider-independent contracts are not
live certification of other models or providers.

The planned fresh study crosses raw/typed evidence with memory disabled/enabled,
using twelve new cases and the same two profiles: 96 samples. This distinguishes
host evidence assistance from memory effects. A scripted provider validates the
actual envelope for plumbing qualification; its results do not measure model
reasoning. Live results and reservations must be reported separately. If format
runs are sequential, temporal confounding must be disclosed and format effects
described as observed paired differences, not isolated causal estimates.
