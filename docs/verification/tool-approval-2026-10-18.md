# Tool authorization and human approval — offline qualification

PR19 was marked ready and merged as `216941a68a83fdb4337315f78d68eb6591fc7c17`
after rechecking its reviewed head and four green required CI lanes. Its separate
CI receipts and build bytes remain preserved in `pr19-ci-evidence-20261018`;
archive SHA256 `5d92215fdf4973662440e357cff79df9a9e1a847fe72259536c3ae1298be5a84`.

This next experimental milestone starts from that merge on
`codex/tool-authorization-approval`. [Adoption guide](../tool-approval.md).

## Scope and authority

Lab0.5.1+approval.2 adds a consumer-owned private approval registry and a public
Runtime CustomTool authorization example. Proposals bind exact arguments,
tool/version, full invocation scope, evidence and host policy. Separate trusted
host decisions approve, deny or revoke; permission is durably spent once before
tool execution. Read-only recovery never renews it or infers effect completion.

Authentication, human UI and domain transactions remain consumer duties. Actor
strings and digests are not credentials. The scripted fixtures do not certify
human presence, production authorization, model prompt-injection resistance,
distributed fencing or exactly-once effects. SDK effect journals and accounting
remain their own authority; no SDK source changes or copied execution engines.
Memory/correction remain experimental. No live run, release or model tuning.

## Test-first qualification

- 23 unit RED missing-blueprint failures, then cancellation boundary corrected to
  deny before spending:23GREEN.
- 25 functional RED missing fixture/script failures. Initial both-wire run had
 36GREEN and12Anthropic errors because the fixture recorder defaulted to another
 provider. Passed the correct provider to the recorder; no SDK check weakened.
- Spec self-check found exact approval acknowledgement replay after spending
 should return spent rather than raise. Two watched RED regressions fixed;
 consent remains spent and cannot be renewed. Focused final **49 passed**.
- Installed proof **24 both-wire scenarios**, **25 network-denied recoveries**
 including subprocess loss after permission was consumed. The child exits23;
 restored state is spent and permission cannot be reissued. No provider request
 is made during recovery. Tests inspect actual synthetic effects, not model
 claims or fixture mock counts. Approval/denial, Unicode, injection/forged tool,
 changed action/scope/version, expiry/revocation and duplicate calls are covered.
- All **137** packaged payloads match source, wheel and installed files.
- Clean public-index wheel/rebuilt-sdist adoption passed with isolated imports,
 payload verification, public construction, CLI/quality/memory checks, pip
 consistency and owned cleanup. Local stack execution was not requested; PR19's
 matrix covers its exact earlier revision, not this new candidate.

Public dependencies stay Core0.4.1, Runtime0.9.7, Harness0.9.4 and adapters0.3.0/
0.4.0. Manifest SHA256:
`fc4eef2c3d32b641a9c6e12cc7b012464132e0cfbf5e87bbc4e848c72b71b95b`.
Initial candidate wheel SHA256:
`67cf702d6ed908786cd8dd81d72490d7540f0e498782e934d25f0f9a24b062cb`.
Initial candidate sdist SHA256:
`dd5d1a0686d5b8165fc53164b59325baff28aaf974c23c889808747b74da3f6a`.

Full source suite: **1727 passed**, one existing Starlette/httpx deprecation
warning,393.61seconds on Python3.12.14/Darwin arm64. One fresh independent final
review found one Important issue described below. Initial installed environment `/private/tmp/prosaic-approval-initial-env`,
proof `/private/tmp/prosaic-approval-study-20261018`, artifacts
`/private/tmp/prosaic-approval-artifacts-20261018`. Preserve these even if review
requires a new candidate. Synthetic fixtures use declared synthetic token units;
no live counter/model qualification is implied.

## One fresh review and material fix pass

Independent gpt-6-astra/high review of2b4934c passed49focused tests and inspected
the full/installed/distribution proof. One Important: replaying original approval
after later revocation raised instead of returning revoked. No permission bypass,
but lost-ack recovery broke the specified idempotence contract. The fix scans
all prior decisions by immutable audit identity and returns current state for
exact matches. A second watched regression prevents one audit ID being reused
with different contents; persisted history also rejects duplicate audit IDs.
Both regressions were RED before the fix. No Critical/Minor findings; no
re-review. The final candidate is approval.2, with new artifacts/environment;
all initial candidate proof remains unchanged.

Review scope rulings: authentication/human UI/session/deployment integration is
consumer-owned (wrong integration can authorize the wrong actor); live-model
attack resistance is unmeasured (fixture proof must not be overstated); external
effects/transactions/distributed guarantees require SDK/domain journals (risk
of duplicate or uncertain effects); production storage/clock/backup controls
remain infrastructure duties (rollback can revive consent); fresh candidate
platform CI is a later PR gate (earlier CI could miss new platform faults).
The author ran the full/package/historical checks while the reviewer reran the
focused suite and inspected receipts; independent reproduction is thus limited.
These are explicit boundaries, not deferred defects or promotion claims.

Fixed candidate approval.2 has137matching source/wheel/installed payloads.
Wheel SHA256:
`dbfb6c0887ccf19ef1829116b2fbbc47e8416f44e60412b259192b67facaa31d`.
Sdist SHA256:
`ee9ea47277499ee1e1a985dd12627211c28e198852839ce28dcf722ed89ebeb8`.
Final installed environment `/private/tmp/prosaic-approval-qualified-env`, proof
`/private/tmp/prosaic-approval-qualified-study-20261018`, artifacts
`/private/tmp/prosaic-approval-qualified-artifacts-20261018`.
Final fix qualification: **1729 source tests passed**, one existing warning,
391.50seconds; **51 focused tests passed**. Repeated installed proof passed
24both-wire scenarios,25network-denied recoveries, subprocess-loss recovery and
revoked/spent decision replay plus conflicting audit-identity checks.50synthetic
requests, zero live requests. Repeated clean public wheel/rebuilt-sdist adoption
and137payload reconciliation passed. Local stack execution remains unperformed
for this new candidate; fresh platform CI is the later PR integration gate.
One material fix pass complete; no deferred minors. Scope rulings above remain
explicit consumer/infrastructure responsibilities, with their adoption risks.

## Preserved limits

Per case4requests/2tools/8192tokens/600seconds/output512, with original deadlines
carried across human waiting/recovery. Global ceilings1558/637/1976623;
charged1509/610/1835168. All nine unknown reservations remain charged, with no
new allowance or live requests. Historical read-only verifier passed: six
frozen samples,9853guards,38oldledgers and eight earlier unknowns unchanged,
plus the latest study's charged unknown; canonical total39ledgers/nineunknowns.

Next gates: complete source/review qualification, then a review PR and platform
CI before integration. Any release or live evaluation requires a separate
maintainer decision. Keep experimental boundaries and current limits.
