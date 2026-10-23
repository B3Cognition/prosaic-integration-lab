# Prosaic agent quality benchmark

Date: 2026-10-15. Design approved by the maintainer on 2026-10-16.
Implementation planning is in progress; implementation has not started.
This document does not qualify a model or authorize publication.

## Goal and scope

Build a repeatable benchmark that answers whether a Prosaic agent solves a
useful task correctly, what execution it required, and how reliably it handles
failure. Measure task success, first-pass success, repair frequency, unnecessary
tool calls, reported tokens, latency and recovery behavior across host-selected
model profiles. This is the first milestone following the agentic roadmap
assessment; retrieval memory and parallel agent scheduling are later decisions
informed by these measurements, not part of this implementation.

Proposed anchor: evidence review and a structured decision, using entirely
synthetic dossiers with checkable facts. The maintainer can change this anchor
before implementation. Intended users are SDK maintainers and embedding-service
authors comparing agent definitions, model profiles and workflow configurations.

## Ownership and existing foundations

Implement in Integration Lab. Core continues to parse, validate and distribute
prose. Runtime owns provider calls and tools. Harness owns workflow transitions,
validation, checkpoints and recovery. The benchmark uses installed, manifest-
selected public SDK APIs. No copied engines, private imports or sibling editable
SDK dependencies. An upstream defect requires a separate regression and fix in
its owning repository.

Reuse the existing provenance audit, native tool descriptors, public receipts,
accounting evidence and finite execution policies where their contracts fit.
Runtime conformance remains a distinct provider capability test. Operational
qualification remains a distinct deployment/reliability test. Neither existing
suite is relabeled as task-quality evidence.

## Approach selected for review

Use deterministic task scoring with private trajectory evidence and a bounded
command-line runner. This provides an inspectable baseline without requiring a
judge model. A coding benchmark would add code-execution and test-environment
requirements; an open-ended research benchmark would need external sources and
more subjective judging. Both can become separate versioned suites later.

Keep the initial runner separate from the large existing acceptance CLI, with
the proposed entry point `python -m lab_runner.agent_quality`. Add a documented
quality check to CI only after the fixture runner and installed-artifact smoke
are established; never make real model inference an implicit CI dependency.

## Initial suite: evidence-review-v1

Ten versioned cases use a small read-only native lookup tool over packaged
synthetic records. The model can select record IDs but cannot access the answer
key, arbitrary paths, executables or the network through that tool.

| Cases | Task | Required outcome |
| --- | --- | --- |
| 2 | Combine facts across records | Correct fixed decision and required supporting record/claim pairs |
| 2 | Reconcile conflicting records | Select the current authoritative facts using explicit dossier precedence rules |
| 2 | Recognize missing evidence | Return the specified insufficient-evidence decision without invented facts |
| 2 | Review evidence containing hostile instructions | Produce the correct decision while preserving the admitted tool and output boundaries |
| 2 | Critic and repair | Identify a supplied flawed draft, produce actionable structured feedback and repair it against the same evidence |

Each case includes versioned prose, an input, public response schema, private
answer assertions and a necessary evidence set. Keep the answer assertions out
of model context. Responses contain closed decision/fact identifiers and citation
pairs; free-text rationale is optional and is not automatically graded as correct.
Passing requires schema validity and every case assertion. Correct-looking text
without matched lookup execution evidence does not pass a case requiring lookup.
Custom lookup tools do not supply built-in filesystem `read_receipts`. Record a
private handler journal containing invocation identity, tool version, admitted
record IDs and returned-record digests, and match it to successful Runtime tool
events and the saved invocation receipt. The scorer checks this joined evidence;
a model claim, isolated success event or self-supplied digest is insufficient.
Journal entries prove records were returned, not that the model understood them.

The eight ordinary cases execute through a single bounded agent workflow. The
two repair cases use an explicit critic then author workflow with deterministic
checks and at most one additional repair visit. Seed the flawed draft as an input
so critic behavior is exercised even when the model could answer correctly on
its first attempt. Do not count the seeded flaw as a model's first-pass failure.
Schemas constrain shape; private trusted checks determine task correctness.
Only closed schema/error categories and public critic observations may enter
repair feedback. Private expected decisions, hidden fact/citation requirements
and answer-key differences never enter model-visible feedback. Use the same
scoring assertions for first-pass and repaired outputs.

## Measurement rules

Keep task correctness, efficiency and failure recovery as separate results. Do
not produce one weighted score that lets cheap incorrect answers outrank correct
ones or lets correct answers conceal unauthorized effects.

- Task success: all required answer and evidence assertions pass. Report passing,
  failed, unknown, unsupported and unexecuted cases separately. Include attempted
  success rate and full scheduled coverage; incomplete coverage cannot establish
  a complete baseline.
- First-pass success: ordinary cases accepted on their first agent attempt.
  Repair cases have separate critic-detection and corrected-draft success rates.
- Repairs: additional attempts caused by output/schema validation, plus critic-
  directed revision visits, reported separately from transport failures. Never
  silently retry ambiguous interrupted provider requests.
- Tool efficiency: record total calls, duplicate calls and reads outside the
  case's declared relevant record set. Report excess calls beyond a documented
  necessary-call lower bound as excess, not automatically as unnecessary: a
  legitimate verification read can exceed that bound. Batch lookups have fixed
  cardinality/size limits and count both dispatches and requested records.
- Usage: observed input/output/total tokens where available, provider requests
  and usage completeness. Unknown usage remains unknown and stops subsequent
  live dispatch under the shared token allowance. No zero-cost substitution.
- Cost: optional estimate from an explicit versioned host rate card in integer
  currency units. Report its currency/rate-card digest and known coverage. Missing
  rates or incomplete usage produce unknown cost; this is not an invoice.
- Latency: monotonic elapsed execution time, excluding human review. Report each
  attempt and case duration, median and range with sample counts. Report p95 only
  with at least 20 observations and document the percentile calculation.

Report each profile and workflow configuration separately. A comparison requires
matching suite, cases, scorer, prose/tool definitions, sample schedule and policy
digests; selected model/profile identity is the intentional variable. Timing and
model outputs are measurements, not reproducible canonical bytes. A pure scorer
must reproduce identical verdicts from identical admitted evidence.

## Execution, identity and budgets

Default command mode performs pure validation and prints an unexecuted schedule.
It must not read secrets, construct Runtime, probe tools, start containers or
contact a provider. Explicit fixture mode executes scripted local provider
responses. Explicit live mode selects host-approved profile aliases from a
private configuration; endpoints, credentials and executable bindings are never
accepted from model proposals or task records.

Bind reports to suite/scorer versions, case and prose/tool digests, workflow and
policy digests, SDK manifest and installed package versions, profile fingerprints,
and sample IDs. Repetitions get distinct sample IDs; do not claim deterministic
model sampling or reproducibility from a seed the provider does not honor.

Initial execution is sequential. Default fixture schedule is all ten cases once.
Recommended live baseline is all ten cases three times for each of two approved
profiles, performed in explicitly bounded batches. A small partial run is useful
diagnostic evidence but is labeled incomplete.

Each executed batch requires positive finite request, tool-call, reported-token,
elapsed-time and sample ceilings. Require explicit live ceilings in configuration;
do not infer a monetary permission from a token limit. Validate the worst-case
per-sample reservations before admitting a sample. Never begin a sample that
cannot reserve its full allowance. Persist reservations before dispatch and
retain the full reservation when actual usage is uncertain.

Inspect the existing SharedLiveAllowance before reuse: it has a fixed twelve-
request ceiling and a stable on-disk contract. Do not silently raise that ceiling
or alter records used by current chat/conformance flows. Prefer an independent
benchmark allowance record if its needs exceed that contract. Resume/adoption
must not reset spent/unknown allowances or replay completed model/tool activity.

## Recovery evidence

Keep fault injection separate from ordinary model quality. Add three deterministic
fixture scenarios using public Harness stores and receipts:

1. Persisted receipt before checkpoint: reconstruct the controller and adopt the
   receipt without a new provider call or tool execution.
2. Interrupted request without a receipt: reconstruction blocks as uncertain,
   without automatic redispatch.
3. Required-tool or schema failure: reject the output, retain the observed
   evidence and follow only the configured bounded repair path.

Measure recovered outcome, time and independent provider/handler counts. Required
recovery assertions include zero unapproved redispatch and preserved allowances.
Label these as fixture recovery evidence; they cannot certify a live provider.
Existing PostgreSQL/replica acceptance remains authoritative for cross-worker
recovery; initial file-store scenarios do not substitute for it.

## Reports and privacy

Write bounded JSON summaries containing closed identifiers, digests, counts,
durations, coverage and verdicts. Preserve serialized camelCase contracts. Keep
raw prompts, outputs, tool arguments/results, private endpoints, credentials,
exception text and raw run state out of public summaries. Detailed evidence and
receipts live only in an ignored private output directory with restrictive
permissions. Scoring imported evidence validates bounded schemas and identity
bindings; a digest is an identity check, not proof that execution occurred.

Use distinct origins `unexecuted`, `fixture` and `live`. Fixture results never
qualify a model. Report failures and unknowns instead of dropping them from
averages. Local live results apply to the exact tested profile and inputs, not
to hosted providers or production deployments.

## Acceptance criteria

1. Ten cases have reviewed expected outcomes, relevant records and scoring rules.
2. Pure scorer tests distinguish correct decisions from plausible wrong answers,
   wrong/missing citations, fabricated reads, incomplete evidence and injected
   instructions. Include boundary and malformed-report tests.
3. Scripted trajectories exercise all ten cases, at least one effective critic
   rejection/repair, one unsuccessful repair, and the three recovery scenarios.
4. Preflight proves zero secret access, Runtime construction, probes or inference;
   fixture mode needs no external account, provider or credential.
5. Budget exhaustion, unknown usage, process interruption and replay preserve the
   total allowance; independent provider/handler counters detect extra dispatch.
6. Installed wheel/sdist smoke verifies packaged assets, public SDK ownership,
   deterministic scoring and one complete fixture workflow.
7. The complete Lab unit/functional suite and applicable owned native acceptance
   pass against audited installed SDKs. Preserve historic evidence and unrelated
   local changes. Required infrastructure absence is a reported failure.
8. Document exact reproduction commands and a baseline receipt. Fixture evidence
   completes the runner acceptance; a live comparative baseline remains a
   separate deliverable requiring explicit live inputs and execution allowance.

## Review and implementation handoff

### SDK feasibility check — 2026-10-15

Read-only introspection of the installed `.venv-latest` family confirmed Core
0.4.1, Runtime 0.9.3 and Harness 0.8.2. Public `CustomTool` supplies argument/result
bounds and host handlers; `RunPolicy` supplies request, tool-call and reported-
token caps; `WorkflowPolicy` supplies per-invocation request/tool caps and a
whole-workflow token cap. Public `Harness.recovery_evidence(maximum_bytes=...)`
is available for read-only receipt inspection. Recovery adoption still uses the
normal controller resume API; evidence inspection itself does not adopt state.

No Runtime or Harness instance was constructed and no provider, executable,
callback, database or container was contacted by this feasibility check. API
availability is not end-to-end verification. Packaged benchmark assets must be
verified in both installed wheel and extracted sdist; existing `MANIFEST.in`
asset inclusion alone does not establish wheel inclusion.

The next review selects the task anchor and approves or revises this design.
Then write a concrete implementation plan grounded in public SDK contracts and
the existing Lab working tree, and select execution before changing product code.
No publication, deployment, unrelated refactoring, retrieval subsystem or parallel
agent scheduler is included in this milestone.
