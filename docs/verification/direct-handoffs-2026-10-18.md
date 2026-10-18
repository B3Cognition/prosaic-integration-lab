# Direct worker and critic: offline qualification — 2026-10-18

Experimental Lab0.5.1+direct.1 closes the model-visible contract gap exposed by
the [first live handoff study](real-handoffs-live-2026-10-18.md). The host prepares
the assignment, workers return compact typed values, and critics receive actual
invocation-bound records from the host. No planner/model metadata-copy step is
required. The old version1 path and all historical evidence are preserved.

[Machine-readable result](data/direct-handoffs-2026-10-18.json) records executable
source628b66f, exact wheel/sdist hashes and unchanged allowance. These are local
experimental artifacts, with no push or release. No SDK source changed.

## Evidence

- Watched initial RED for missing direct-role implementation; malformed-output
  scoring and invalid controlled record types also failed before fixes.
- Focused direct tests:68passed. Complete source suite:1456passed in286.97seconds,
  one existing Starlette/httpx deprecation warning. Source Python3.12.14 uses
  installed SDKs and no installed Lab, preserving import-isolation tests.
- Built wheel and source distribution, installed into a separate environment,
  verified125source payloads and129installed files byte-for-byte against the wheel
  and committed source. All five installed SDK payloads match the unchanged
  checksum manifest; `pip check` passes.
- Installed isolated-mode smoke:70both-wire scenarios, all safely enforced.
  Actual HTTP payloads must contain the closed role schema, host assignment and
  correctly scoped critic evidence. Controls cover all five draft-field flaws;
  bad reviews, schema descriptions, invalid JSON, wrong bindings, unknown usage,
  reported overrun and repeated native tools cannot complete successfully.
-30synthetic trajectories exercise the **unchanged registered counters** for
  both existing models in worker-only, critic-only and full modes. Controlled
  input-bound quotations plus512output tokens/request range1492–5240, within8192.
  The maxima are4991for the smaller profile and5240for the larger. This qualifies
  framing/admission for these shapes, not arbitrary future model continuations.
- Every installed smoke case reconstructs receipts without additional requests.
  Counter qualification additionally denies socket operations during recovery;
  receipts and traces remain unchanged. Source tests also block claim reuse and
  prove one shared budget can stop critic dispatch after worker usage.
- Verified2596prior evidence files,3155frozen guards,37canonical live ledgers and
  all eight historical unknown reservations. No prior evidence or serving asset
  changed. The first smoke invocation completed its cases but failed to write its
  report to a non-private parent; the successful invocation uses a private output
  directory. Both logs and evidence sets are retained.

## Limits and interpretation

Zero live requests. Per-case limits remain4requests/2tools/8192reported tokens/
600seconds/output512; cumulative ceilings1500/617/1976623 and charged usage
1476/601/1776439 remain unchanged. Remaining allowance24requests/16tools/200184
tokens; full reservations are still required before any live study.

The worker and critic can now be reached and evaluated independently. Correct
missing/unread/conflict controls require escalation. A correct critic detecting a
controlled flaw passes its own test; a bad naturally produced worker still fails
full-task quality even when caught. A host gate independently prevents acceptance.
These scripted outcomes demonstrate contracts, evidence transfer and enforcement.
They do **not** show either real model obeying the contracts or a critic improving
accuracy. Critic benefit remains unmeasured. Memory remains experimental.

The next milestone is a small frozen real-model study with direct worker and
critic lanes plus full handoffs, under the same per-case caps. Only observed
native worker mistakes and correct critic detections can establish critic value;
controlled drafts provide separate coverage. Broader planning/delegation, durable
memory, production failover and hosted-provider behavior remain open gaps.

## Reproduction

```text
PATH=/private/tmp/prosaic-failure-lab-source-env/bin:$PATH /private/tmp/prosaic-failure-lab-source-env/bin/python -m pytest -q
python -m build --no-isolation --outdir /private/tmp/prosaic-direct-artifacts
python -I scripts/direct_handoff_smoke.py --source-root /absolute/lab/checkout --output /private/fresh/report.json --evidence-dir /private/fresh/evidence
python -I scripts/audit_install.py --manifest dependencies/response-diagnostics-candidate.json --wheel-dir /verified/sdk/cache --expected-sha 0d204d48743b456f82571cb85f8027d0e8589bd1ab7e777307395e5510d4396f
```

Local counter operator:`/private/tmp/prosaic-direct-counter-qualify.py`;
candidate environment:`/private/tmp/prosaic-direct-env/bin/python`;
private results:`/private/tmp/prosaic-direct-study-20261018`.
The previous live environment and all prior operators are retained unchanged.
Final independent review is pending at this checkpoint.
