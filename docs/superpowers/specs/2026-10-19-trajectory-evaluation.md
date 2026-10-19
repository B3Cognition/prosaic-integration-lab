# Provider-neutral trajectory evaluation blueprint

The maintainer approved the recommended next milestone. Native execution and
question opt-out persist. Reuse the isolated Lab worktree from merged PR20
(`5bd896a`). No SDK change or live request is authorized.

Build a small consumer projection over public Runtime/Harness observer records,
plus explicit trusted-host evidence/validation/approval/recovery annotations.
Use existing SDK observations rather than a new execution engine or journal.
Correlate run, invocation and step using keyed pseudonyms, with no raw IDs,
labels, prompts, responses, source contents, tool names or exception messages
in exported reports. Keep observation order distinct from causal order.

Observations are best effort and never execution, consent or accounting
authority. Detect invalid/foreign records, sequence gaps/duplicates, unclosed
streams and bounded-buffer loss. Report absence honestly; do not certify
completeness from an absence of detected gaps. Correlate host annotations to
steps without inferring that approval proves an effect completed.

Trusted consumers supply a configuration/evaluator binding digest, independently
verified outcome (passed/failed/incomplete), closed diagnostic categories,
receipt/evidence digest and measured usage totals (unknown stays null).
Telemetry hints remain separately labelled from verified diagnostics. A model
claim or successful final observer event cannot manufacture a passing outcome.
The collector must not perform inference, recovery, approval or retries. It is
single-run, thread-safe and bounded to512observations/128host annotations.
Malformed monitoring data must not interrupt SDK execution; record loss instead.

Private report persistence uses existing Lab private atomic files. Offline reads
validate closed schema, expected binding and integrity; no sockets or SDK drive
calls. A hash detects accidental corruption, not malicious replacement. Hosts
must authenticate stored reports and scopes; pseudonyms do not grant access.
Reports contain aggregates and per-step safe observations. No vendor exporter,
network service, dashboard, raw trace store or whole-platform certification.

Second-domain example: synthetic parcel dispatch recommendation. Real public
Harness + Runtime perform one manifest lookup and a structured recommendation.
Host rules independently assess ready/missing evidence, wrong decisions,
malformed output, tool failure and provider failure. A separate pending approval
proposal demonstrates correlation without dispatching a consequential action.
Saved-state inspection and report replay are network-denied. Both scripted
OpenAI-compatible/Anthropic wires exercise the public boundary, not model quality.

Keep per-case4requests/2tools/8192tokens/600seconds/output512. Cumulative
ceilings1558/637/1976623 and charges1509/610/1835168 stay unchanged, with nine
unknown reservations retained. Memory/correction stay experimental. Qualify
source tests, installed both-wire example, wheel/sdist adoption and privacy,
then one fresh final review. Keep branch local; no release or live comparison.
