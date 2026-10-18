# Tool authorization and human approval

**Experimental consumer blueprint.** `lab_runner.tool_approval.ApprovalGate`
shows how a consumer can require durable host approval for an exact tool action.
It uses public Runtime `CustomTool.authorize` and `ToolExecutionContext` APIs.
The registry contains no provider, model or task-domain policy. Memory and
bounded correction stay experimental; no live/model security benefit is claimed.

## Authority and review

The authenticated host owns tenant/actor/namespace, capability policy, evidence
grants and human approval. It creates a proposal binding the exact bounded JSON
arguments, evidence digest, tool/version and full invocation scope. It selects
the permitted approvers and resolves their identities from its authentication
system. **An actor string or decision digest is not authentication.** Never map
client/model-supplied identity fields directly into this API.

`propose` stores an immutable private action and returns its digest and review
snapshot. Show the approver the actual arguments, tool/version, target, relevant
source evidence and consequences, not merely a hash. Display untrusted strings
as data with normal UI escaping. Keep the registry private; expose a deliberately
filtered review view through an authenticated host endpoint. No UI or identity
provider is implemented or certified by this blueprint.

The separate host approval endpoint must pass the digest of the proposal the
human actually reviewed, an authenticated actor from the configured policy, a
strict boolean decision and a host audit-decision digest. An approval request
cannot silently change the action. Check CSRF/session authorization and any
separation-of-duties requirements in the consuming application. A configured
approver identifier is a permission policy, not proof a human was present.

Retrieved content, critic advice, a model's `approved:true`, and tool arguments
cannot call `decide`. None of the registry's methods is offered as a model tool.
Only the host binds the proposal ID into an authorizer closure; a model does
not choose its own grant. Runtime also requires the tool in the artifact,
runtime configuration and host RunPolicy allowlists. Use closed argument schemas.

```python
from lab_runner.tool_approval import ApprovalGate
from prosaic_runtime import CustomTool

gate = ApprovalGate(private_path, identity=trusted_scope_policy_digest,
                    tools={'publish_document': 'publish-v1'},
                    approvers=authenticated_reviewer_ids)
proposal = gate.propose(proposal_id, tool_name='publish_document',
                        scope=trusted_invocation_scope,
                        arguments=host_verified_arguments,
                        evidence_digest=reviewed_evidence_digest)
# In a separate authenticated host request, after the human reviews this action:
gate.decide(proposal_id, actor=authenticated_reviewer_id,
            proposal_digest=reviewed_proposal_digest, approved=human_decision,
            decision_digest=host_audit_event_digest)
tool = CustomTool('publish_document', 'Publish an approved document',
                  closed_parameters_schema, domain_handler, 'publish-v1',
                  with_context=True, authorize=gate.authorizer(proposal_id))
```

Supply a public `InvocationScope` with invocation, run, step and operation
namespace from trusted host bindings. If Harness chooses the invocation ID,
create/bind the proposal from its trusted host adapter once that identity is
known; do not predict it from a model assignment or weaken the scope check.
The authorizer compares exact arguments and actual SDK context before granting
permission. Tool version changes require a new policy/registry and review.

Evidence digest binds the review snapshot; it is not a generic freshness oracle.
If current domain state matters, include an expected revision in the approved
arguments and recheck it transactionally at the domain effect. Revoke outdated
unclaimed proposals. Consumers supply their own capability policy and evidence
verification; they do not need to reproduce this fixture's domain or models.

## One-shot consent and recovery

States are pending, approved, denied, revoked and spent. Denial cannot become
approval; approved actions can be revoked before claiming. Exact host-decision
replay returns current state without renewing permission, including after spend.
Different/conflicting decisions fail. No reset or automatic reapproval exists.

Before returning True, the authorizer durably marks consent spent under an
exclusive process lock. Duplicate and concurrent calls get no permission. It
also checks expiry and the SDK's cancellation/deadline boundary. A denied or
altered tool request does not consume valid consent, but the attempted call
still uses its Runtime work budget. Approval expires within 600 seconds of
proposal creation; a restart cannot extend it. Revocation after spending is
rejected and cannot imply an in-flight effect was cancelled.

`inspect` is private read-only recovery. **Spent means dispatch permission was
consumed, not that an effect completed.** A crash after consent spending but
before SDK dispatch keeps it spent. An effect, response, receipt or acknowledgement
can likewise be lost. Never infer success or absence from registry state.

Runtime invokes authorization before any configured tool-effect journal claim.
Use the SDK's public ToolJournal protocol and a durable consumer/domain
implementation for consequential operations, such as the existing Lab
PostgreSQL service's `PgToolJournal`. The approval registry does not replace
that journal, workflow receipts or provider accounting. Because consent is
one-shot, a second Runtime invocation is denied even when an effect receipt
could be replayed. Read existing evidence directly through the consumer's
reconciliation path; recovery must not drive the tool again.

Quiesce old workers and reconcile SDK/domain evidence before considering new
work. Any new action needs fresh human authorization, a new proposal identifier
and its own full work reservation. A fresh approval does not prove an old effect
was absent. See [durable failure isolation](failure-isolation.md) and the
[PostgreSQL service pattern](consume-native-workflows.md). Authorization and
effect execution are separate boundaries; this local registry does not provide
distributed fencing, exactly-once external effects or in-flight revocation.

## Limits and qualification

Keep the existing per-case limits: **4 requests / 2 tools / 8192 reported tokens /
600 seconds / 512 output tokens**. Activate the encompassing Runtime execution
budget, keep qualified counters and do not treat approval as inference allowance,
retry consent or a budget refund. The consuming host owns that reservation.
Carry the original case deadline across human waiting and recovery; approval
must not start a fresh 600-second work budget. Narrow the remaining execution
time to that persisted deadline, as in the failure-isolation example.
Current cumulative ceilings1558/637/1976623 and charges1509/610/1835168,
including nine unknown reservations, remain unchanged.

Storage uses a private local file, atomic replacement, file/directory fsync and
POSIX locks. Use a trusted clock and local filesystem supporting those semantics.
Do not restore an old registry to regain consent, share it over a network mount
or expose private records to a model. Authenticate every host API separately.
Host/storage loss, malicious local edits and a production authorization service
require infrastructure controls beyond this experimental example.

From a clean installed Lab environment with the public pinned SDK family:

```text
mkdir -m 700 PRIVATE_FRESH_ROOT
python -I scripts/tool_approval_smoke.py --source-root REPO \
  --evidence-dir PRIVATE_FRESH_ROOT/lanes --output PRIVATE_FRESH_ROOT/result.json
```

The scripted OpenAI-compatible and Anthropic fixtures attempt approved,
unapproved, denied, revoked, expired, changed, injected, unknown-tool, duplicate,
cross-scope and version-drift actions, including Unicode arguments. Tests assert
actual synthetic effects and persisted consent; model text saying "done" is not
effect evidence. Unit/process tests cover forged host decisions, stale review,
concurrency and lost acknowledgements. Recovery runs with network access denied.
No real human approval, live inference, production effects or prompt-injection
resistance of a model is certified. These tests qualify deterministic host gates.
