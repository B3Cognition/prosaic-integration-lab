# Accounting request metadata

Copy with `python -m lab_runner.blueprints copy accounting-metadata /private/project`.
Requires Core 0.5.0, Runtime 0.9.17 and Harness 0.9.12, with published recorder
0.3.0/store 0.4.1 when used. Final Lab qualification pins their actual public
wheel hashes. This host uses public APIs and contains no library execution engine.

The authenticated application calls `trusted_context(tenant_id=..., billing_account_id=...,
benchmark_run=..., variant=..., run_id=None)` from accepted host context. Never pass untrusted client/model
fields as authority. Runtime snapshots `request_metadata={'run': ..., 'variant': ...}`.
`LabelingRecorder.prepare(intent)` reads the optional version1 context extension
before dispatch and sends a copy of labels to an application callback. It delegates
durability, rates, storage scope and usage measurement to its backing recorder.
The callback can label a benchmark run/variant without inspecting prompts, tool
arguments, raw headers or request bodies. A callback failure prevents dispatch.

`run_benchmark` permits one request/no tools. `workflow` builds two finite agent
steps separated by approval; construct `Harness(flow, ..., runtime=runtime,
context=context)` with the same recorder and retain it across reopen/resume.
`benchmark_run` supplies the diagnostic `run` label separately from actual run
identity. Leave actual `run_id` omitted for Harness to generate/bind it, or supply
the same lowercase UUID hex used by the explicit RunStore/Harness run. Labels
never rebind another stored run identity.
Saved accounting context, including original labels, wins over new observational
labels or changed defaults. Start a new run for a new variant. Saved-receipt adoption
does not dispatch a replacement call. Accounting evidence never grants retry consent.
Return an allowlisted host view such as `public_view`, never raw Harness state.

Labels do not enter prompts/provider payloads/headers, artifact digests, rule
fingerprints, prepared-turn or workflow identities. None/empty is omitted entirely
and preserves legacy accounting hashes. Present labels intentionally change
accounting hashes and private saved contexts/receipts; same-call relabeling conflicts.
Operator `calls()` can contain labels; filter customer views and avoid secrets.
Labels never select tenant/payer, namespace/rates or billing eligibility.

At most16 ASCII-keyed labels; nonempty printable values at most256characters and
256UTF8bytes each; canonical escaped label JSON at most4096bytes. Identity/scope/
request/credential field names are reserved. Runtime validates and refuses invalid
input before effects. No raw request metadata is automatically extracted.
The published recorder0.3.0 needs no DDL/new privileges or rewritten old rows;
new labeled contexts require Runtime>=0.9.17 readers. Do not downgrade readers of
labeled saved runs. Legacy unlabeled rows retain their old shape and hashes.

Inspect without a call using `prosaic inspect subagents/benchmark.md --source .prosaic --json`.
The default endpoint is inert loopback port9. Only after private operator configuration
and explicit authorization run `python host.py --live`. The CLI demo uses a **non-durable**
MemoryRecorder. Production hosts supply a separately provisioned PostgresRecorder
and call `check_ready()` with runtime-role credentials; migration credentials never
reach replicas. No automatic schema creation or live-provider certification is added.
