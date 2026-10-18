# Offline typed handoff qualification — 2026-10-18

Lab `0.5.1+handoffs.2` is a local experimental candidate. Executable source is
`dc69d1f7bfa35ae80ad404fbd7ec74afbcc543c8`; the initial implementation is
`89a1383`. This milestone changes Lab only, using the same qualified installed
Runtime `0.9.8+diagnostics.1` / Harness `0.9.4` family and unchanged candidate
manifest `0d204d48743b456f82571cb85f8027d0e8589bd1ab7e777307395e5510d4396f`.
Core, SDK code, public release manifests, model profiles and live limits stay
unchanged. No live inference, push or release occurred.

The [consumer guide](../typed-handoffs.md) describes request-bound assignment,
worker result/evidence and critic review contracts. The host verifies each
independently using the worker's own lookup receipt attribution and public task.
Ready, missing, unread and conflict are separate outcomes. Correct complete
evidence can finish; semantic disagreements require human review, whose only
choice is stop. Schema/binding errors block. Unknown usage stops continuation;
intentional synthetic overruns remain visible without raising caps.

## Qualification

- Python3.12.14 / macOS ARM64, installed public SDK APIs only.
- Baseline:1333passed. Initial full suite:1370passed. Final focused:40passed.
  Final source suite:1373passed in227.79seconds, zero failures/skips, one existing
  Starlette/httpx deprecation warning. Command: `PATH=/private/tmp/prosaic-failure-lab-source-env/bin:$PATH
  /private/tmp/prosaic-failure-lab-source-env/bin/python -m pytest -q`.
  [Sanitized results and provenance](data/typed-handoffs-2026-10-18.json) retain
  every installed scenario's role verdicts and accounting outcome.
- Build: `/private/tmp/prosaic-continuation-source-env/bin/python -m build
  --no-isolation --outdir /private/tmp/prosaic-handoff-artifacts-final`.
- Final installed wheel:30 both-wire scenarios,104synthetic requests/28tools,
  plus3 independent-review regressions with12synthetic requests/3tools.
  Every case meets its expected safety/quality outcome. The2 intentional usage
  omissions and2 intentional reported overruns fail quality and stop safely.
- Reconstructed receipts retain their digests with zero new calls. Separate
  saved/missing final-critic receipt tests adopt or block without redispatch;
  earlier-stage interruption remains inspection-only.
- Installed120source files/124payload files match exact source and wheel;
  source archive includes exact handoff modules/operator. Five SDK wheels audit
  cleanly, and `pip check` reports no broken requirements. The final environment
  copies the existing audited SDK/dependency environment then installs this Lab
  wheel; it has no editable SDK or sibling source dependency.

Wheel SHA256: `10d8cfa6441e8b1d4dc440f8710edc213f8e5393c092fd86006a26f855dfdb62`.
Source archive SHA256: `acb981cb7193565b9649ce608ec8330a040d7aa18e57eddb38812a8cb44c9851`.
Initial private candidate artifacts and failed smoke log are preserved separately.
That first smoke stopped on macOS temporary-path symlink admission; resolving the
operator's own temporary root fixed it without weakening storage validation.

## Independent review and decisions

A fresh gpt-6-astra/high reviewer identified two Important reporting issues,
both reproduced RED then fixed GREEN: preserve later critic correctness after
an earlier worker failure, and retain correct escalation quality after human
stop. Final reports contain separate stage verdicts and a stopped outcome.
No Critical or Minor finding remains. The final source suite covers both fixes.

Ruling: do not add another model repair round. Planner, worker lookup/final and
critic already use the unchanged four-request cap. Cost: lower automatic
completion in exchange for bounded escalation. Caps remain4requests/2tools/
8192tokens/600seconds/output512.

Ruling: real reasoning, live tokenizers, hosted behavior, earlier-stage automatic
continuation and production failover remain outside this offline milestone.
Cost: this evidence cannot establish those capabilities. The fixed synthetic
counter is explicitly not live tokenizer qualification. No deferred minors.

## Preservation and readiness

All1902prior evidence files in five manifests verify. All36canonical live ledgers
still charge1468requests/601tools/1769171tokens with8unknown reservations retained.
Ceilings remain1475/604/1976623; remaining7/3/207452. No allowance was consumed.

The46-file [preservation receipt](data/typed-handoffs-preservation-2026-10-18.json)
binds the separate local archive `/private/tmp/prosaic-handoff-evidence-20261018.tar.gz`.
It contains final/initial artifacts, logs, operators, sanitized reports and the
execution ledger. Archive members were checked against their manifest hashes;
all36historical canonical ledger hashes were also verified individually.

This closes the offline contract/trajectory qualification step toward the
roadmap's multi-agent gap. It does not demonstrate real-model handoff quality,
autonomous production operation or a memory benefit. Memory remains experimental.
Next is a frozen real-model handoff evaluation only after its complete reservation
fits authorized allowance; a full four-sample run does not fit current headroom.
