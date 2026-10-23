# Typed evidence summaries

The maintainer requested implementing typed summaries and a fresh memory study,
with a clear preference for addressing general agentic-system gaps rather than
tuning Prosaic around oMLX or two current models. Native execution remains the
chosen working method; prior question/design opt-out remains in effect.

This is an Integration Lab consumer pattern, using published SDKs. Core, Runtime
and Harness engines and provider configuration are outside this change. It
addresses structured tool interaction, context assembly and trajectory evaluation
in the [roadmap](https://www.kdnuggets.com/the-roadmap-to-mastering-agentic-ai-systems-in-2026).
It does not implement semantic/vector retrieval, automatic memory lifecycle,
parallel agent protocols, arbitrary code sandboxing or production observability.

## Contract

A provider-independent pure function takes explicit trusted authority/fact policy,
a complete bounded public record index, and only records fetched by the current
tool call. It supports arbitrary identifier labels and one to sixteen required
facts; the rollout-task grammar stays in a small consumer adapter. A partial or
untrusted-completeness index fails closed rather than proving global absence.

The versioned JSON envelope contains `version: 1`, `indexComplete: true`,
`authority`, `requiredFacts`, `facts`, `excludedRecords`, and the unchanged fetched
`records`. Fact entries have `factId`, `status`, `recordId`, `revision`, `value`.
Statuses distinguish `verified`, `absent`, and `unread`. Absent facts have null
source/revision/value; unread facts expose only public indexed source/revision,
with null value. Authority is selected before revision. Ambiguous latest versions,
duplicate/foreign records, nonfinite values and index/source mismatches reject.
Excluded fetched sources are retained and labeled `wrongAuthority` or `superseded`.
Facts include required labels plus all indexed facts with the required authority,
because the public task requests all available current authoritative facts.

The envelope never computes a decision, evaluates thresholds, reads recalled
episodes/private expected assertions, or rewrites the model answer. The existing
public validator still rejects wrong decisions and missing/incorrect citations.
Classification assumes a complete index within the trusted bounded source scope;
it makes no claim about unknown documents outside that scope.

## Execution and compatibility

Preserve raw lookup as the default and expose an explicit typed-evidence option.
Raw uses `lookup-v1`; typed uses `lookup-summary-v1`. Both have identical grants,
readable source IDs, lookup/request/token/time limits and model profiles. Typed
mode adds only the generic summary contract guidance. All fetched decoys remain
in the response. Bind format, implementation and exact result digests to frozen
context, workflow/tool identity, journals, scoring and no-inference recovery.
Historical evidence and its original environments remain untouched.

## Study

Use a paired 2x2 design: raw/typed evidence crossed with memory disabled/enabled,
on the same twelve fresh cases and two existing model profiles: 96 samples.
Run separate raw and typed schedules using the same frozen candidate and public
SDK train, preserving current CLI/schedule contracts. Counterbalance format order
across case pairs; do not claim format-only causality if execution is wholly
sequential. Cases and corpus must match byte-for-byte across conditions. Keep
temperature, output cap and provider flags fixed. Current models are limited live
regression targets; provider independence is a contract/design claim, not a broad
live-provider qualification claim. No new vendor-specific tuning is allowed.

Expand synthetic historical topics before freezing development code/prose/corpus.
Author fresh evaluation only after that freeze; old studies/cases are development
evidence. New source IDs, task authority/fact labels, values and revisions should
exercise renamed domains, complete/missing evidence, higher-revision observers,
stale references, empty history, tenant isolation and hostile notes. Retain old
corpus entries. The final scorer stays private and unchanged in semantics.

Report each model's memory and summary contrasts, first-pass/strict success,
absence/authority/citation/decision error components, retries, tool trajectory
efficiency, bytes, reported tokens and timing. Audit SDK receipts/journals and
socket/provider-denied byte-identical replay. A small single trial supports only
observed synthetic results. Host assistance must be labeled honestly.

Finish offline qualification and exact worst-case reservations before requesting
any numerical live allowance extension. Preserve all historic charges and five
unknown reservations. No new release, push or model/settings change is implied.
