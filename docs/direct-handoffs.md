# Experimental direct worker and critic

This opt-in Lab consumer supplies a deterministic host assignment and embeds each
role's closed JSON output contract in its instructions. It starts at the worker;
there is no planner call for copying host metadata. Version1 entry points and
historical evidence remain available.

Use `lab_runner.handoffs.direct.execute_case` with `mode='worker'`, `'critic'` or
`'handoff'`. The worker must perform a native lookup and return assignmentId,
status and answer (decision, fact labels and source citations). The host sends the
critic the actual invocation-scoped fetched records through the public Runtime
adapter. The worker cannot replace them with claimed values. Original Harness
arguments and receipts remain intact. Private expected answers are never inputs.

Critic-only mode requires a structurally valid host `draft` and optionally a
unique list of `record_ids` from the current snapshot. These are explicit controls,
not naturally occurring worker mistakes. The host prepares the evidence and the
critic must identify wrong binding, status, decision, facts and citations. Correct
missing, unread and conflicting evidence still requires escalation. Independent
host checks remain authoritative even when a critic misses a flaw.

Status precedence is conflict, then unread, then missing, then ready. Unread
always means an insufficient decision, including when the two required facts are
read but another current authoritative fact remains unread. Facts and citations
still list the current records actually read. Version1 behavior is unchanged.

Ordinary full execution needs three requests and one tool; worker-only needs two
requests and one tool; critic-only needs one request and no tools. All modes use
the unchanged outer limits: four requests, two tools, 8,192 reported tokens,
600 seconds and 512 output tokens. Per invocation permits at most two requests
and one tool. No automatic repair/retry is added. Unknown usage, overruns and
exhausted continuation reservations stop execution rather than raising caps.

`score_direct` reports each role separately, the first failure, task quality and
safe stopping. A detected bad worker still fails task quality in full mode; a
correct critic detecting a controlled flaw can pass its own qualification.
Taking the permitted stop action preserves that measured qualification and reports
a stopped outcome; it never authorizes approval.
`recover_case` only verifies and reads saved state; it never drives a graph node.
Reusing an execution claim fails before dispatch. Changed identities must use a
new study and output directory.

Without an explicit qualified matching token counter, execution accepts only the
named credential-free synthetic fixture at numeric HTTP loopback. A supplied
counter does not grant live-call authorization: a trusted study host must freeze
inputs, reserve the full case and enforce cumulative allowance before live use.

Installed offline qualification:

```text
python -I scripts/direct_handoff_smoke.py --source-root /absolute/lab/checkout --output /private/report.json --evidence-dir /private/fresh-evidence
```

Fixtures inspect the contracts and host arguments actually transmitted on both
OpenAI-compatible and Anthropic wires. They use independent literal expectations
and deliberate bad responses. Scripted transport success demonstrates plumbing,
contracts and host enforcement; it cannot demonstrate model obedience, critic
benefit, memory improvement or production readiness. Those require separately
authorized real-model studies. Memory remains experimental.
