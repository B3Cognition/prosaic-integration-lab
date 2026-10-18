# Consumer role qualification and diagnostics — 2026-10-18

This milestone implements a reusable consumer blueprint rather than tuning the
two local models. [Adoption guide](../role-qualification.md). Core/Runtime/Harness,
existing prompts and direct execution contracts are unchanged. No live model
calls, retries, repair or model routing were added.

Generic APIs in `lab_runner.role_qualification` assess consumer field policies,
bind reports to configuration and require host-pinned complete live observations
before optional consumer role admission. Synthetic success never qualifies live
use. Evidence digests and profile fingerprints are trusted host inputs, not
client/model authorization. A separate rollout adapter produces source-scoped
diagnostics and distinguishes incomplete reviews from correct coarse warnings.
Another domain's shipping contract exercises the same generic APIs.

Final opt-in candidate: **Lab0.5.1+roles.2**. Full source suite **1524passed**,
zero failures/skips, one existing Starlette TestClient/httpx deprecation warning;
309.29seconds on Python3.12.14, macOS/arm64. Focused **46passed**16.33seconds.
Initial21generic and16adapter RED→GREEN tests were followed by9review regressions
observed RED, then GREEN. One fresh review found2Important/0critical/0minor;
both fixed in one pass, no deferred minors and no re-review.

Fixes reject incomplete/unknown/inconsistent accounting and unknown/overrun case
timing; recorded adapter versions and actual projected argument hashes bind
control selectors and fetched records to their execution. Diagnostics remain
distinct from recorder admission, call consent, host authenticity and task acceptance.

Built wheel/sdist and installed in a new isolated candidate environment.
**24scripted lanes** over both wire adapters passed; four complete synthetic
role records were all rejected for live use. A second domain exercises the
generic helpers without the rollout grammar. All **127installed payload files**
match the wheel and current source; five SDK wheel payloads re-audited unchanged.
Wheel SHA256 `2d36fd1e96009f9a093220592648a654dee19afb568d1b13b60e3c6c24dc0483`;
sdist SHA256 `a26be6877946bf8496a5010619989e2589404dfbb7641874101c0147c1fb1bc6`.
[Evidence and preservation data](data/role-qualification-2026-10-18.json).

Limits remain4requests/2tools/8192reported tokens/600seconds/output512 per case.
All38canonical ledgers verified unchanged; charged1494/605/1805193 versus ceilings
1524/625/1976623, including eight fully charged historical unknown reservations.
There are zero live inference requests in this milestone. Previous installed
environments and all historic qualification/model evidence remain intact.
Prior evidence was reverified:6415frozen guards,2596historical files,
1996prior offline files,795latest live evidence files and38ledgers. This
verification is read-only with sockets denied; no old model run was repeated.

This establishes consumer policy contracts and offline plumbing, not model
fitness, production certification or answer improvement. Consumers must supply
their own complete scenario suites, domain oracles, evidence permissions,
held-out live qualification and authorization/budget admission. Memory remains
experimental. No push or release.

Reproduction uses the existing pinned SDK manifest and a separate environment:

```text
python -m pytest -q
python -m build --no-isolation --outdir /private/fresh/artifacts
python -I scripts/role_qualification_smoke.py --source-root /path/to/checkout --evidence-dir /private/fresh/evidence --output /private/fresh/result.json
```

Private final environment `/private/tmp/prosaic-role-final-env`; artifacts
`/private/tmp/prosaic-role-artifacts-final`; results
`/private/tmp/prosaic-role-final-study`; proof metadata
`/private/tmp/prosaic-role-study-20261018`. Initial candidate/build failure,
review regressions, both installed proofs and all prior environments are retained.
Preserved **410files** in the canonical offline evidence store. Archive
`prosaic-role-evidence-20261018.tar.gz`, SHA256
`558d53effc722f728814fe3c0ea38fb71ee955a16fffce3666c032efb6a55159`.
Closing verification confirms the public projection, built/installed payloads,
source/test/smoke counts and unchanged historical ledger hashes with sockets denied.
