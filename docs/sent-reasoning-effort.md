# Observe the reasoning effort actually sent

Use the complete Lab0.9.11 release manifest: Core0.5.0, Runtime0.9.18,
Harness0.9.12, recorder0.3.0 and store0.4.1. Runtime release availability alone
does not qualify a partial Lab mixture. The release page supplies the exact
source, checksum, hosted matrix and public-consumer evidence.

```sh
python -m lab_runner.blueprints list
python -m lab_runner.blueprints copy sent-effort /private/my-effort-host
```

Listing and copying make no model call. The default host uses unused loopback
port9; `--live` explicitly opts in to a single configured endpoint call. Synthetic
qualification uses owned loopback providers/fake CLI executables without secrets.
No live-provider certification is implied.

The copyable host uses public installed APIs:

```python
result = host['run_review'](runtime, agent, context=trusted_host_context)
report = host['effort_report'](result)  # private operator diagnostic
```

Runtime owns transport evidence in `Result.metadata['reasoning_effort_v1']`.
Each row separates `requested_effort` (artifact), `configured_effort` (original
profile default), actual `sent` fields and `format`. HTTP forms are
`reasoning_effort`, `thinking_toggle`, `chat_template_effort`, `omitted` or
`unavailable`. Explicit none/false differs from absence; binary thinking enabled
does not imply a neutral tier. Current Qwen none sends only a false toggle.
Anthropic effort capabilities do not change; ordinary supported calls show omission.

Native rows expose only the actual effort argv subset for a launched process:
Claude `--effort value` (`claude_cli`) or Codex
`-c model_reasoning_effort="value"` (`codex_cli`), else an empty argv (`omitted`).
Metadata-discovery processes, capacity skips and startup failures are excluded.
Native inner provider calls and vendor settings remain unobserved.

`provider_confirmation` is always `not_observed`. A dispatch attempt or process
launch proves neither delivery, receipt, acceptance nor compliance. Connection,
HTTP/read and accounting-observe failures can retain attempts; failures before
dispatch do not invent them. Result evidence authorizes no retry. Existing
request/tool/token/deadline/effect budgets and human approval remain authoritative.

The invocation-local trace retains tool continuation, rule repair, adapter retry
and native/API pool histories. `attempt_count`, `complete` and `omitted_attempts`
make zero, missing, unknown and truncated evidence distinct. At most64rows and
32768canonicalJSONbytes are kept; caller turn metadata/depth/node caps can trim
more or omit the extension. Null counts mean unknown. An absent old receipt trace
means unavailable, never zero or reconstructed history.
Row indices describe retained observation order, not absolute provider-call
ordinals. An already truncated child can leave gaps before later observations;
use call IDs and completeness markers when joining or comparing histories.

HTTP `provider_call_id` joins existing accounting calls. Recorder intent and
observation schemas and the published PG adapters are unchanged; there is no DDL
or automatic raw request projection. Trusted host labels and frozen accounting
attribution remain separate from sent controls and from application authority.
Do not put secrets in profile/model names or observational labels.

The host's two-step `workflow` demonstrates pause/reopen and durable no-call
saved-receipt adoption with public Harness. Private Result receipts retain the
extension; original old receipts stay unchanged. Use `public_view` as a minimal
status/call allowlist. Do not return raw operator state, receipts or complete
Runtime metadata to application clients. No raw prompt/header/key/workspace or
unrelated native argv is copied into the new trace; older full-result diagnostics
may still contain private information.

Artifact/rule, prepared-turn, workflow and bundle input identities are unchanged.
Private saved result bytes intentionally gain additive observations. Lab SDK
provenance and current memory freeze hashes advance to describe the new train;
prior profiles/manifests/freezes remain selectable and byte-identical. Corpus,
prompts, scoring, earlier blueprint resources and live evidence remain unchanged.

Installed acceptance covers both wires, run/turn/prepared, streaming, default/
explicit-none and binary/chat-template formats, tools/repairs/adapters/pools,
failure boundaries, fake CLI argv and file/realPG no-call recovery. Missing required
PG16/18 infrastructure fails rather than skipping; migration and runtime roles
are separate with exact owned database/role cleanup. The four LinuxAMD64/ARM64×
PG16/18 cells plus two reasoning jobs and all distribution/public gates must pass.
