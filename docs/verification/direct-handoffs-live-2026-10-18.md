# Frozen direct worker/critic evaluation — 2026-10-18

All **12 fresh held-out samples** completed across the two frozen models under
unchanged limits. The smaller critic provided a correct warning on every flawed
draft it reviewed, but never identified the complete issue set. The larger
critic produced no usable review. This supports a limited warning signal for
the smaller critic, not dependable verification or improved task answers.
[Audited data](data/direct-handoffs-live-2026-10-18.json).

## Design and qualification

Six cases were each crossed with both models, with model order counterbalanced:
one worker-only case, three host-authored critic controls, two full handoffs.
Controls cover a clean draft, wrong decision/stale citation, and missing evidence
claimed ready. Handoffs include authority/revision distractors, additional current
facts, and genuinely missing required evidence. Model-visible IDs are opaque;
gold/rules remain private. Cases, values and schedule were frozen before live
outputs. No sample was retried or tuned after observation.

Installed Lab **0.5.1+direct.2**, executable source **7c77df8**, Runtime
**0.9.8+diagnostics.1**, Harness **0.9.4**, SDKs, counters, serving assets,
prompts and schemas stayed frozen. Models:

- Smaller: `mlx-community--Qwen2.5-Coder-7B-Instruct-4bit`.
- Larger: `ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ`.

Offline preparation passed41host tests and12actual-counter scripted lanes,
including component token breaches, interruptions, missing receipts and
source-bound review classification. One fresh whole-host review found three
Important issues, all fixed before approval; no second review. All6415guards
were verified. Final binding:
`a2777498cb51b69a740bea3a9b60de02619287eed2e6668907af18377da49635`.
[Preparation](direct-live-2026-10-18.md) preserves the review corrections and
original pre-anonymization corpus without changing source values or seed.

## Results

| Measure | Smaller | Larger |
| --- | --- | --- |
| Worker-only correct | 1/1 | 1/1 |
| Full-handoff workers correct | 0/2 | 0/2 |
| Clean critic control correctly accepted | 1/1 | 0/1; unusable output |
| Seeded flawed drafts reviewed | 2 | 2; both unusable reviews |
| Seeded flaws correctly escalated with usable verdict | 2/2 | 0/2 |
| Seeded flaws with complete correct issue list | 0/2 | 0/2 |
| Actual worker flaws reaching critic | 2 | 0; workers stopped first |
| Actual worker flaws correctly escalated | 2/2 | Unmeasured |
| Actual worker flaws with complete correct issue list | 0/2 | Unmeasured |

Both smaller handoff workers returned schema-valid answers but selected evidence
incorrectly. In the ready case they omitted two of three current authoritative
records and fetched two non-current records. In the missing case they omitted
one of two current authoritative records and fetched two non-current records.
Both claimed ready before completing the required evidence lookup. Against the
records actually fetched, the correct status was unread and decision insufficient.
Host checks rejected both results. This is an evidence-selection/completeness
failure, not proof of a Runtime execution defect.

The smaller critic's issue lists were true subsets of the required lists:

| Flawed draft | Required issues | Reported issues |
| --- | --- | --- |
| Actual ready-case worker | status, decision, facts, citations | decision |
| Actual missing-case worker | status, decision, facts, citations | facts, citations |
| Seeded decision/citation flaw | decision, citations | decision |
| Seeded missing-evidence flaw | status, decision, facts, citations | status |

Thus it escalated4/4flawed drafts and accepted1/1clean draft, with no invented
issue in these five reviews. It found5of14required issue fields; **0/4**flawed
reviews were complete. The internal `incorrectEscalation` category means an
inexact review here; it must not be interpreted as an incorrect coarse warning.
Natural mistakes and host-authored controls remain separate denominators.

All three larger critic controls and both larger handoff workers ended at the
unchanged512output-token cap with `finish_reason=length`, before a complete
artifact could be trusted. Its full-handoff critics never ran. Its worker-only
case passed, so these results establish neither blanket model incapability nor
natural-flaw critic efficacy. All invalid seeded reviews remain in the control
opportunity denominator.

## Cost, safety and accounting

| Critic cost | Requests | Reported tokens |
| --- | --- | --- |
| Smaller, actual worker handoffs | 2 | 2919 |
| Smaller, controls | 3 | 4153 |
| Larger, controls | 3 | 5575 |
| All critics | 8 | 12647 |

The complete study used **18requests /4tools /28754reported tokens**. Per-case
caps stayed4requests /2tools /8192tokens /600seconds /512output tokens.
Every claim settled known; no new unknown, timeout, overrun, component counter
violation or unresolved intent. Receipt counts, public accounting observations,
diagnostics, lookup journals and original trace hashes reconciled. Recovery of
copied state denied sockets and made **zero additional provider requests**.
No wrong full-handoff result was accepted, but independent host checks already
enforced that outcome; it is not credited as a critic safety improvement.

Explicit allowance approval added24requests/8tools and no tokens. Historical
charge1476/601/1776439 plus this study gives **1494/605/1805193** versus approved
ceilings **1524/625/1976623**. Remaining **30requests /20tools /171430tokens**.
All eight historical unknown reservations stay fully charged; prior ledgers and
evidence remain unchanged. Preservation hashes and new canonical ledger identity
are recorded in the audited data.

## Interpretation and next milestone

The direct contracts let us observe worker and critic behavior, overcoming the
earlier planner-stage barrier. They do not make collaboration reliable. The
smaller critic can add a warning signal, but its incomplete diagnostics cannot
support unattended correction. The larger critic is not qualified for this role
under these limits. No repair round or randomized no-critic ablation was run,
so answer improvement and causal benefit remain unmeasured. Each family has only
one case per model; these counts do not estimate general model accuracy.

We are ready for another **controlled development milestone**: provider-neutral
role capability qualification and source-grounded review diagnostics, followed
by a separately qualified bounded correction path with a matched no-critic
baseline. Qualification should cover complete issue fields, missing/unread
evidence, authoritative source selection, and explicit abstention when a role
cannot produce a valid result within its budget. It must keep host validation
authoritative and reserve any correction before dispatch. This addresses agent
coordination, evaluation and recovery without tuning one provider's prompts.

Broader planning/delegation, memory effectiveness/durability, provider diversity,
production failover and autonomous multi-agent readiness remain open. Memory
stays experimental. No Core/Runtime/Harness source change, push or release is
part of this evaluation.

Private frozen operators: `/private/tmp/prosaic-direct-live-{run,audit,analyze}.py`;
interpreter `/private/tmp/prosaic-direct-final-env/bin/python`; study
`/private/tmp/prosaic-direct-live-study-20261018`. Closed operators expect their
original37-ledger baseline and cannot be reused after canonical publication.
Future work must use a fresh root and the updated accounting baseline.
