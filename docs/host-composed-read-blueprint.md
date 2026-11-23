# Host-composed read optimization blueprint

This is a **candidate integration pattern**, not a qualified Lab acceptance lane. A production consumer's opt-in pilot motivated it: the application combined two sequential, read-only, host-validated operations under one registered capability while preserving the same observed result. Product-specific parsing, API requests and answer admission remain in the consuming service. The Lab should test the reusable execution and evidence boundary with synthetic records before this pattern is recommended across products.

## Synthetic comparison

Use a fixed synthetic task: find a named catalogue record in a requested published period. The host owns the period and record lookup implementations, immutable tool versions, scope authorization and final result admission. The model cannot choose record IDs or provide endpoints.

- **Baseline:** a Harness agent calls `resolve_period`; a validator checks its observed outcome; a gate stops on missing or ambiguous periods; a second agent calls `read_record`; the host admits the observed record.
- **Candidate:** one Harness agent calls `read_scoped_record` with a closed, empty argument object. The host callback resolves the period and, only when uniquely verified, reads the named record. Its versioned result reports `scopeReady`, `lookupExecuted` and `complete`. A trusted validator checks the final `complete` value against host observations. A missing or ambiguous period performs no record read.

Both variants use public `WorkflowFactory`, `WorkflowBindings`, `CustomTool`, validators and Runtime model budgets. They run in separate opt-in, versioned bundles so retained executions never silently switch identity. The application authenticates the actor and supplies all tool implementations and resource scope; the model supplies none of them. This is a read-only optimization. A consequential effect or a human decision between stages must retain explicit step boundaries and recovery semantics.

## Required qualification

Run the same exact and paraphrased requests through both variants, including unique, empty, ambiguous, unavailable and denied outcomes. Compare admitted outputs and their provenance, provider requests, model tokens, latency, retries and tool-call receipts. Confirm that retries after lost acknowledgements do not reissue an uncertain callback and that each replica uses the same retained bundle identity. Report source-level and browser-level latency separately.

The candidate trades two phase-specific Harness tool receipts/checkpoints for one aggregate receipt. The host must retain a trustworthy internal sub-operation record if phase-level audit is required. Do not describe one aggregate receipt as two independent Harness receipts. Do not promote the candidate solely because a single model call is faster; success, denial and uncertainty behavior must match the baseline. If the Lab finds a generic need for model-free, receipt-bearing deterministic steps, raise that as an upstream Harness proposal with a synthetic failing case rather than copying an engine into the application.

The consumer's own pilot was a source-level comparison only; it is not Lab acceptance or production/browser certification.
