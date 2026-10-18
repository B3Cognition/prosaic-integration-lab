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

Initial qualification:21generic tests RED→GREEN;16adapter tests RED→GREEN;
combined37passed. Built opt-in Lab0.5.1+roles.1 wheel/sdist and installed into a
separate environment. Installed smoke passed24scripted lanes over both wire
adapters, with four synthetic role reports all rejected for live use. Five SDK
wheel payloads re-audited unchanged. Source full suite and final review pending.

Limits remain4requests/2tools/8192reported tokens/600seconds/output512 per case.
All38canonical ledgers verified unchanged; charged1494/605/1805193 versus ceilings
1524/625/1976623, including eight fully charged historical unknown reservations.
There are zero live inference requests in this milestone. Previous installed
environments and all historic qualification/model evidence remain intact.

This establishes consumer policy contracts and offline plumbing, not model
fitness, production certification or answer improvement. Consumers must supply
their own complete scenario suites, domain oracles, evidence permissions,+held-out live qualification and authorization/budget admission. Memory remains
experimental. No push or release.
