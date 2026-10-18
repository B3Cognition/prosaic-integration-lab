# Bounded correction consumer blueprint — 2026-10-18

[Adoption guide](../bounded-correction.md). This opt-in Integration Lab example
adds one host-verified correction and a matched no-critic baseline. Generic
feedback/comparison helpers contain no provider, model or rollout policy. A
separate rollout adapter owns evidence grants, field checks and the graph, using
public Runtime/Harness APIs. Core and all SDK pins/payloads remain unchanged.

Both arms receive the same host diagnostics and actual fetched records. Critic
advice is filtered against verified field failures; raw critique, gold values
and new records never enter corrective feedback. Corrector has one request and
zero tools. One outer allowance covers the arm. Bad output, unknown usage,
component breaches or exhausted continuation admission cannot authorize success.
Missing/unread evidence can produce an accurate non-ready artifact, requiring
host review. Independent worker drafts must match exactly before pair scoring.

Candidate **Lab0.5.1+correction.2** is local and experimental. Initial source
suite:1577passed,1existing Starlette/httpx deprecation warning,349.23seconds.
Final source suite:1581passed,zero failures/skips,1existing warning,344.65seconds.
Final focused suite:57passed43.21seconds. The complete result is recorded in the
[machine-readable proof](data/bounded-correction-2026-10-18.json).
Initial generic/functional tests were observed RED then GREEN. One fresh
whole-change review found0critical/2Important/0minor and declined no scope.
Both Important findings were fixed in one pass, each with reproducing tests:
unusable final output cannot receive verified field-resolution credit, and
interrupted/unresolved correctors remain visible without inventing usage.
Four added regressions were observed RED; no re-review or deferred minors.

Built wheel/sdist, installed in a fresh environment and matched all131payloads
against source and wheel. Five SDK distributions re-audited against their
original manifest. Installed synthetic proof:48arms,24matched pairs across both
wire formats,54recoveries with network access denied,2malformed-output checks.
The independent fixture validates model-visible contracts and field feedback.
Scenarios include ignored/regressing corrections, partial/false critics,
missing/unread evidence, invalid critics, unknown usage, forbidden tools,
component breaches and interrupted/lost responses. Known observed costs remain
visible; unresolved requests do not become zero-cost or invented observations.

Per-arm limits unchanged:4provider requests/2tools/8192reported tokens/600seconds,
512output tokens per response. Both arms require separate full reservations for
any future live study. Live ceilings1524/625/1976623 and charged1494/605/1805193
remain unchanged. All38canonical ledger hashes and8fully charged unknown
reservations verified intact. **Zero live inference requests** this milestone.
Both preceding immutable evidence verifiers passed; historic environments,
reports and failed qualifications remain preserved.

Synthetic success establishes bounded control flow and measurement only. It
does not establish model quality, tokenizer accuracy, memory benefit, critic
benefit or production readiness. Consumers must adapt policies and qualify
their own worker/critic/corrector roles, counters, native requests and held-out
cases before authorized live execution. Memory remains experimental. No push,
release or live study was performed.

Reproduce with the pinned SDK manifest in a separate environment:

```text
python -m pytest -q
python -m build --no-isolation --outdir PRIVATE_ARTIFACTS
python -I scripts/bounded_correction_smoke.py --source-root CHECKOUT --evidence-dir PRIVATE_STUDY/lanes --output PRIVATE_STUDY/result.json
```

Final environment `/private/tmp/prosaic-correction-final-env`; artifacts
`/private/tmp/prosaic-correction-final-artifacts`; metadata and synthetic evidence
`/private/tmp/prosaic-correction-study-20261018`; read-only closing verifier
`/private/tmp/prosaic-correction-verify.py`. Initial candidate/env, failed smoke
expectations and all RED/GREEN logs are retained separately. Preservation hashes
and artifact identities are recorded in the machine-readable proof.

Preserved4177files in the new canonical offline evidence directory
`bounded-correction-evidence-20261018`. Archive
`prosaic-correction-evidence-20261018.tar.gz`, SHA256
`e90b1cf1cab8830bcb25dbdae78edbd4ef1b1d0aff59369156074f75165a221e`.
The closing verifier checks every preserved file, wheel/source/installed bytes,
selected sdist inputs and all38historical live ledger hashes with sockets denied.
