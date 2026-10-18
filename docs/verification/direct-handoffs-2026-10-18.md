# Direct worker and critic: offline qualification — 2026-10-18

Experimental Lab 0.5.1+direct.2 closes the model-visible contract gap exposed by
the [first live handoff study](real-handoffs-live-2026-10-18.md). The host prepares
the assignment, workers return compact typed values, and critics receive actual
invocation-bound records from the host. No model planner copies host metadata.
The old version1 path and all historical evidence are preserved.

[Machine-readable result](data/direct-handoffs-2026-10-18.json) records executable
source 7c77df8, exact wheel/sdist hashes and unchanged allowance. These are local
experimental artifacts. No SDK source changed; nothing was pushed or released.

## Evidence

- Final focused tests: **90 passed**. Complete source suite: **1,478 passed** in
  389.06 seconds, with one existing Starlette/httpx deprecation warning. Source
  Python 3.12.14 uses installed SDKs and no installed Lab.
- Built and separately installed wheel/source distribution. Verified 125 source
  payloads and 129 installed files against the wheel and committed executable
  source. All five installed SDK payloads match the unchanged checksum manifest;
  dependency consistency passes.
- Installed isolated smoke: **76 scenarios across both provider wires**, all
  safely enforced. Each actual HTTP request must carry the complete normative
  schema and semantic instructions, correct host task/index and exact tool
  results. Controls cover all five draft-field flaws. Bad reviews, schema
  descriptions, malformed JSON, wrong bindings, unknown usage, overruns and
  repeated native tools cannot complete successfully.
- **36 synthetic trajectories** exercise the unchanged registered counters for
  both existing models in worker-only, critic-only and full modes. Controlled
  input-bound quotations plus 512 output tokens per request range **1,506–5,287**,
  within 8,192. Profile maxima: smaller 5,037; larger 5,287. This establishes
  supported framing and admission for tested shapes, not arbitrary continuations.
- Every installed case reconstructs receipts without more requests. Counter
  qualification also denies socket operations during recovery; receipts and
  traces remain unchanged. Source tests prove claim reuse cannot dispatch and
  worker usage can exhaust the shared budget before critic dispatch.
- Verified 2,596 prior evidence files, 3,155 frozen guards, 37 canonical live
  ledgers and all eight historical unknown reservations. Serving assets and
  prior evidence are unchanged.

## Independent review and fixes

One fresh reviewer confirmed scoped host evidence, separate controls, safe gates
and recovery identity rejection. It found an unread-decision mismatch and
insufficient semantic-wire qualification. It also found stop-scoring behavior,
regraded Important because an authorized stop must preserve measured role quality.
All three were fixed in one pass; **15 review regressions failed before fixes**.

Direct-v2 unread results now always return insufficient, including when required
facts are read but an extra current authoritative fact is unread. Version1 is
unchanged. Status precedence is explicit: conflict, unread, missing, ready.
Human stop preserves role qualification and reports a stopped outcome.

Both-wire mutation tests reject **136 removed/contradicted semantic clauses,
12 schema mutations, six public-request mutations and two changed tool results**.
The fixture compares against independent normative text/schema rather than
importing production instructions. Scripted responses still do not demonstrate
model reasoning. No deferred minors; no second review was substituted for the
failing-then-passing regressions and green full suite.

The original candidate, first smoke report-directory failure and intermediate
review logs/evidence remain retained alongside the corrected candidate. The first
smoke completed cases but its report parent was not private; successful runs use
private output directories.

## Limits and interpretation

**Zero live requests.** Per-case limits remain four requests, two tools,
8,192 reported tokens, 600 seconds and 512 output tokens. Cumulative ceilings
remain 1,500 / 617 / 1,976,623; charged usage remains 1,476 / 601 / 1,776,439.
Remaining allowance is 24 requests, 16 tools and 200,184 tokens. A trusted host
must reserve the full case before any live dispatch.

Worker and critic can now be evaluated independently. Correct missing, unread
and conflict controls escalate. Detecting a controlled flaw passes the critic's
own qualification; a naturally wrong worker still fails full-task quality even
when caught. Host checks remain authoritative.

These results establish contracts, evidence transfer and enforcement. They do
**not** show either real model following the contracts or a critic improving
accuracy. Critic benefit remains unmeasured; memory remains experimental. The
next step is a small frozen direct-role real-model evaluation under unchanged
limits. Planning/delegation, durable memory, production failover and hosted-model
behavior remain broader gaps.

## Reproduction

```text
PATH=/private/tmp/prosaic-failure-lab-source-env/bin:$PATH /private/tmp/prosaic-failure-lab-source-env/bin/python -m pytest -q
python -m build --no-isolation --outdir /private/tmp/prosaic-direct-artifacts-final
python -I scripts/direct_handoff_smoke.py --source-root /absolute/lab/checkout --output /private/fresh/report.json --evidence-dir /private/fresh/evidence
python -I scripts/audit_install.py --manifest dependencies/response-diagnostics-candidate.json --wheel-dir /verified/sdk/cache --expected-sha 0d204d48743b456f82571cb85f8027d0e8589bd1ab7e777307395e5510d4396f
```

Local counter operator: `/private/tmp/prosaic-direct-counter-qualify-final.py`;
candidate environment: `/private/tmp/prosaic-direct-final-env/bin/python`;
private results: `/private/tmp/prosaic-direct-final-study-20261018`.
The previous live environment and all prior operators remain unchanged.

[Preservation proof](data/direct-handoffs-preservation-2026-10-18.json) binds 1,996
new evidence files, including both candidates, failed/intermediate logs, review
workspace and source diff. Archive: `/private/tmp/prosaic-direct-evidence-20261018.tar.gz`;
manifest: `/private/tmp/prosaic-direct-evidence-20261018/evidence-manifest.json`.
Historical evidence and live ledgers are verified separately and remain unchanged.
