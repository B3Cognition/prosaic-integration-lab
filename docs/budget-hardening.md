# Budget hardening candidate

See [the completed offline qualification](verification/budget-hardening-2026-10-17.md)
for source commits, wheel checksums, full-suite results and remaining limits.

This milestone fixes operational bounds without model-specific prompts,
tokenizer guesses, higher case limits or additional live inference. Core and
Harness remain unchanged. Runtime's public ExecutionBudget owns process-local
dispatch admission; Lab owns durable study authorization and settlement.

## Admission

New live `lab_runner.memory.runner.execute` and
`lab_runner.quality.runner.execute` calls require `token_counters`, a host-owned
mapping from each approved profile alias to a public
`TokenCounterRegistration`. Its exact or conservative upper-bound guarantee
must cover the final native input for the profile's provider/model. The host
must qualify the tokenizer, framing and assets; no live counter implementation
is supplied by Lab. Existing CLI live execution without registrations fails
before reserving or dispatching a sample. Use the Python host entry point once
qualified counters are available. Fixture counters certify only synthetic units.

Admission counts the entire native request again for every tool continuation
and retry, reserves input plus the profile's unchanged output bound, and rejects
requests that cannot fit. One shared ExecutionBudget surrounds each complete
Harness sample; retries cannot replenish it. Counter descriptors are included
in the study binding. Memory recovery reads frozen descriptor provenance from
`token-admission.json` and never needs executable counters or new inference.

The guarantee depends on the trusted counter and provider honoring output
bounds. Runtime records any reported excess truthfully, independently of
whether recorder persistence succeeds. Unknown outcomes keep reservations and
stop execution. Provider-reported tokens are evidence, not verified billing.

## Durable settlement

New studies explicitly use allowance format v2. Each claim stores its immutable
maximum, actual complete counts, evidence digest, state and a closed admission
violation marker. Known amounts above a reservation persist as `overrun`, even
when above aggregate ceilings. A request-bound violation also becomes `overrun`
when sample totals are below the case maximum. Both states block subsequent
reservations and remain blocked after reopening. Status separates retained
amounts, zero-clamped remaining allowance and positive aggregate excess.

Unknown claims retain their entire maximum and cannot later be refunded or
reclassified by recovered receipts. Public reports derive retained/breached
markers from durable claims, so stale evidence flags cannot hide uncertainty.
Overrun evidence never qualifies a complete baseline.

Format v1 remains the default low-level BenchmarkAllowance contract and is
readable with `version=1`; it is never silently upgraded. Historical study
ledgers, the supplemental 324-token reconciliation and all reservations remain
unchanged. New source/SDK bindings intentionally cannot adopt old study output.

## Qualification and limits

`dependencies/budget-candidate.json` selects the explicit local Runtime candidate
with its source commit and wheel checksum, retaining original released wheels
for Core, Harness and both PostgreSQL adapters. It is not a released SDK train;
`dependencies/releases.json` remains unchanged. Benchmark SDK provenance in this
candidate branch binds the candidate manifest. Build the local Lab candidate
only with these exact installed packages.

The frozen typed-evidence comparison remains incomplete: 54 executed samples,
42 not run. This milestone makes no new claim about memory or model quality.
Before a new live comparison, qualify real counters and freeze new cases and
artifacts. No live requests, model settings or ceilings were changed here.
