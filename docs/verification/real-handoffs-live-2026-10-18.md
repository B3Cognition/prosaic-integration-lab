# Real-model typed handoff evaluation — 2026-10-18

All eight frozen evaluations ran, with four fresh cases on each model. Every
workflow stopped at the planner. No worker, tool or critic was invoked, so this
study cannot establish whether the critic helps. Zero reviews is not a measured
zero critic accuracy or evidence that the critic is ineffective.

| Model | Planner passed | Worker reached | Critic reached | Observed planner failure |
| --- | ---: | ---: | ---: | --- |
| Smaller7B |0/4|0/4|0/4|Returned JSON Schema descriptions instead of assignment values |
| Larger27B |0/4|0/4|0/4|Reached512output tokens with incomplete JSON; finish reason length |

The four families were approve, reject, missing authoritative evidence and
conflicting highest-authority revisions. Model order alternated; memory was
disabled; one trial per case/model. The graph, agent prose, schemas, serving
profiles and limits stayed frozen. No tuning, retry or replacement sample ran.

## What the evidence establishes

The smaller model returned syntactically valid schema descriptions in all four
cases; each failed the planner assignment schema. The larger model returned
incomplete JSON in all four cases at the unchanged output cap. It therefore
failed before assignment validation could establish a valid handoff. All eight
were blocked, with known usage; no incorrect assignment advanced downstream.

The live comparison exercised model-to-planner conformance and operational
enforcement. It did not exercise evidence lookup, worker decisions, critic
catch/miss/false-alarm behavior, repairs or successful multi-agent collaboration.
Critic cost was zero because it never ran; no cost-effectiveness comparison is
possible. The [primary analysis and audit](data/real-handoffs-live-2026-10-18.json)
retain all eight attempted samples and distinguish not-run from incorrect.

Code inspection identifies a provider-neutral consumer gap: the role prose says
“Return only your JSON schema,” while the closed output schema is registered for
host validation rather than included explicitly in that agent's instructions.
The planner is also asked to emit an assignment already calculated by the host
and supplied in `request.assignment`. Schema-vs-instance confusion and unnecessary
generation are plausible contributors; this frozen run does not isolate their
causal effect from model behavior or the output cap.

The next useful milestone is an explicit model-visible input/output contract,
deterministic preparation of host-owned assignments, and direct worker/critic
qualification that cannot be blocked by an unrelated planner. Keep the caps and
avoid serving-engine-specific fixes. Qualify the generic boundary offline, then
use fresh cases for a new live study. This is the next handoff gap to close before
advancing to more complex autonomous collaboration; memory stays experimental.

## Accounting and recovery

Study usage:8provider requests,0tools,7268reported tokens. Smaller:3329tokens;
larger:3939tokens. All observations have complete reconciled numerical usage,
with no timeout, new unknown, reported overrun or counter-bound violation.
All8native responses classify as message/unsupported: extended usage details
remain unsupported, not unknown numerical quantities or a billing qualification.

Approved cumulative ceilings are1500requests/617tools/1976623tokens. Prior
charged usage1468/601/1769171 plus this study gives1476/601/1776439. Remaining
allowance:24requests/16tools/200184tokens. All eight historical unknown
reservations remain charged. Actual use settles below the full32/16/65536
reservation; none of the prior reservations is forgiven.

The auditor independently reconciled receipt counts, recorder call IDs and
observations, token-counter proposal prefixes and output bounds. All eight
copied run stores reconstructed with the same receipt digests while networking
was denied, with zero additional model/tool calls. Case files, traces, approved
binding and all3155frozen guards remained unchanged through the audit.

## Exact qualification and limitations

Frozen identity: `cd6988b2f6f89197ed25a4a0f731dc657a257c96a4caee2692137374df78eb5d`.
Lab `0.5.1+handoffs.4`, executable source
`fef4182ec08742c88d6ac3f2109bb188a983c119`; installed qualified Runtime
`0.9.8+diagnostics.1` / Harness `0.9.4` family. The
[preparation record](real-handoffs-2026-10-18.md) retains1388passing source tests,
15installed regressions, eight counter-qualified fixture trajectories and four
reporting/interruption phases. Those fixtures qualify enforcement and reporting;
they do not establish real-model task competence.

No executable source, SDK, model or default changed during the live run. No push
or release is included. The study is small, exploratory and has no randomized
no-critic arm. Hosted providers, live counter guarantees beyond the existing
serving qualification, production durability/billing and autonomous readiness
are unqualified. One previously reviewed minor remains: the private auditor's
output destination is one-use; rerunning it at the same path fails rather than
overwriting earlier evidence.

## Preservation

The450-file [preservation receipt](data/real-handoffs-live-preservation-2026-10-18.json)
binds the canonical evidence archive and37thallowance ledger. All36prior ledger
hashes remain identical, as do the198prepared evidence files. Archive members
were verified against their manifest; historical unknown reservations remain
fully charged. The closed operators bind their original36-ledger baseline;
a subsequent study must use a new root and37-ledger baseline.
The final independent file check verified2596evidence files across all eight
manifests, all3155frozen input guards and37canonical ledgers. Public result
projections match the audited private evidence exactly.
