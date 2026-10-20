# Sandboxed CLI consumer blueprint

Maintainer approved this next milestone. Native execution/question opt-out
persist. Start from merged PR21,5a966ae. Use public released Runtime0.9.7 APIs;
no SDK/Core change, live inference, release or push in this milestone.

Reuse Runtime required-mode Seatbelt/Bubblewrap confinement. Add a small Lab
admission helper and an independently executable qualification example. Do not
copy SDK dispatch, sandbox profiles, accounting or recovery engines. Model
network/auth stays in the parent; only the selected CLI subprocess is confined.
Python callbacks/validators remain trusted. No arbitrary hostile-code claim.

The helper requires explicit consumer controls, required sandbox mode, narrow
workspace-relative read grants, no extra runtime roots or passed environment
variables, bounded manifest timeout/output, and no sockets in granted trees.
Reject broad/escaping grants and unknown policy fields. Report unsupported CPU,
memory, process-count and detached-process cleanup controls; requirements for
these refuse admission before version probes or provider requests. This public
SDK boundary is not a hard resource-DoS defense. Never silently downgrade.

The scripted example uses a frozen host manifest/executable/evidence and a pure
public prepared conversation turn. Bind their hashes, prepared identity and
per-case bounds to trusted host approval of one complete bounded invocation.
The host spends this start permission once before preflight/turn execution,
using a public ToolExecutionContext for the host-start action and the same
InvocationScope passed to Runtime. This is host start admission, not a CLI
authorizer callback or per-effect consent. Model tools cannot approve starts;
their argument schemas constrain only declared document/slot choices. Recheck
bindings before effects; store actual TurnEvidence and usage privately.

Six scenarios on each scripted wire: contained, timeout, output overflow,
denied approval, unsupported resource requirement, sandbox off. Positive-control
canaries outside the sandbox operate only on owned synthetic fixtures, proving
that denial tests are effective. Confinement canaries test granted input,
forbidden/aliased/outside reads, outside writes, private scratch/HOME and absence
of a synthetic parent credential. Host TCP/UDP/Unix listeners independently
verify delivery. No granted host socket. Two distinct contained calls verify
fresh scratch and its removal; timeout/overflow fork bounded same-group children
and verify actual observed process cleanup. No fork bomb, resource exhaustion,
external network traffic or real secret. Detached sessions are not certified.

Use public TurnEvidence outcomes, not model claims, to verify execution and
CLI failure categories. Record approval, validation, execution hints and
read-only recovery in the existing trajectory report. Restart/report inspection
denies sockets, never invokes Runtime/resume, renews consent or refunds usage.
Missing/corrupt receipts block inspection. All reports are private/sanitized.
If backend unavailable, report blocked/unexecuted with zero provider calls;
required operational qualification fails rather than skipping or counting it
as passed. Add a mandatory Linux CI backend setup/gate without globally
weakening host security. Local actual macOS qualification comes first; Linux
platform proof remains a later PR gate. Exercise absent-backend preflight in an
owned network-disabled container if an exact public SDK image is available.

Keep4requests/2tools/8192tokens/600seconds/output512per case. Cumulative ceilings
1558/637/1976623, charged1509/610/1835168, nine unknown reservations unchanged.
Memory/correction stay experimental. Qualify source and installed wheel/sdist,
then one fresh final review; preserve initial/fixed proof and keep local branch.
