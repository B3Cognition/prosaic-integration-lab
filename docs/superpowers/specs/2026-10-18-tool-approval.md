# Provider-neutral tool authorization and human approval

The maintainer said Continue after the recommendation to merge PR19 and build
this next blueprint. Native execution and question opt-out persist. Implement
in Integration Lab with public released SDKs; no live run or SDK changes.

Add a consumer-owned single-host approval registry, not an authentication
service, workflow engine or tool-effect journal. Runtime's public CustomTool
authorizer and ToolExecutionContext supply the execution boundary. Existing
SDK journals/receipts and the PostgreSQL service example own effect evidence.

Trusted host code creates an immutable bounded action proposal. Bind the exact
canonical arguments, evidence digest, tool/version, full InvocationScope,
policy and host identity. The policy freezes an explicit tool/version allowlist
and authenticated approver identifiers. No approval function or token goes in
the model's tool catalogue. Retrieved content, critique and model JSON remain
untrusted task data. Human approval is a separate host action requiring the
digest of the exact proposal shown to the approver and an audit-decision digest.

Persist pending/approved/denied/revoked/spent state privately with fsync,
atomic replacement and process locking. Only listed authenticated host actors
may decide; the registry does not authenticate an actor string. Exact decision
replay is idempotent, conflicting decisions fail, denial cannot be upgraded,
approved work may be revoked before claim, and spent work cannot be reset.
Approval expires no later than600seconds from proposal creation, never resets
on restart, and is checked against the tool's deadline/cancellation as well.

An authorizer closure binds one host-selected proposal ID. Verify exact action
and trusted SDK context, then durably spend consent before returning True. A
concurrent or duplicate call gets no permission. Lost acknowledgement/crash
retains spent consent, including before the effect begins. Inspect/recovery
reads state only; spent is permission consumed, not proof an effect completed.
Never automatically reapprove, retry, infer success or refund the work budget.
Revocation cannot recall an in-flight operation. Consumers must use durable
SDK/domain idempotency for effects and separately reconcile uncertain outcomes.

Offline qualification: changed args/tool/version/scope/evidence or policy,
forged actor/boolean/digest, denial/revocation/expiry/cancellation, duplicate and
concurrent claims, subprocess loss after spending, restart and read-only recovery.
Both OpenAI-compatible/Anthropic scripted wires request approved, unapproved,
changed, repeated and injected actions through real public Runtime APIs.
Synthetic effects only; validate actual handler effects and persisted consent.

Per case remains4requests/2tools/8192reported tokens/600seconds/output512.
Global ceilings1558/637/1976623, charges1509/610/1835168, nine unknowns retained.
No model-tuning or resistance-to-prompt-injection efficacy claim. Prove the host
permission boundary offline; memory/correction and this blueprint stay experimental.
