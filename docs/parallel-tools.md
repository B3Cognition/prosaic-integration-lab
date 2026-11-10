# Parallel read tools: local candidate qualification

The copyable `parallel-tools` blueprint registers trusted independent reads and
lets Runtime run them in fixed bounded windows. Harness selects concurrency per
agent node under a host ceiling and retains versioned receipts. All existing
guards, citation permissions, operation claims and controller leases apply.

This increment covers API provider tool batches on OpenAI-compatible and
Anthropic wires. Default execution remains sequential. A host assertion
`parallel_read=True` requires a read-only handler safe to call concurrently,
including repeated calls of itself. Unmarked tools and context readers form
serial barriers. Handler entry/completion can vary; projection into guards,
model history, evidence and citations follows admitted call order. MCP clients,
sub-agents and parallel workflow nodes remain separate follow-ups.

Cancellation stops new dispatch and drains every started callback before return.
Python callbacks must cooperate; there is no forced thread cancellation. Pending
budget reservations protect every shared allowance; consumed attempts alone
increment dispatch counters. Safe `tool_execution_settled` observations contain
no arguments/results/locators and grant no evidence authority. Citations still
require current grants and actual encoded provider delivery.

Runtime uses conversation encoding v5, frozen input3 and evidence4 only for an
explicit parallel policy. Harness enabled state/receipt versions are workflow
5/4 and conversation5/5. Existing documents retain their formats and sealed
bytes. Owners opt in with `initialize(parallel_tools=True)` or
`migrate_parallel_tool_storage()` after draining writers; workflow storage
advances3→4 and conversation storage4→5, retaining parent context/tool features.
Restricted workers cannot migrate; tables, columns and grants do not expand.

The exact candidate family is Runtime0.9.21.dev1, Harness0.9.15.dev1 and Harness
PostgreSQL0.4.4.dev1, with original Core0.5.0 and Runtime recorder0.3.0 wheels.
It adds32 required witnesses (16 logical cases × both wires), preserving all
370 existing cases:12 lanes/402 cases per coherent candidate cell. Historical
families retain their original gates; mixed families and skipped new cases fail.

Build each SDK once from its committed head with its existing artifact builder.
Run installed consumers using `release_artifacts.py qualify --label
parallel-tool-consumer --junit PATH ...`; the command must select
`tests/test_parallel_tool_installed.py` and produce zero failures/errors/skips.
Harness carries the exact tested Runtime receipt/qualification. Curate locally:

```sh
python scripts/prepare_sdk_candidates.py --parallel-tools \
  --runtime-artifacts /path/to/runtime/artifacts \
  --harness-artifacts /path/to/harness/artifacts \
  --manifest /path/to/new-candidate/manifest.json
python scripts/build_consumer.py --manifest /path/to/new-candidate/manifest.json \
  --dependency-mode candidate --tag prosaic-parallel-tools:candidate
python -m lab_runner test --mode parallel-tools --candidate \
  --candidate-manifest /path/to/new-candidate/manifest.json \
  --consumer-image sha256:IMAGE_ID --postgres-version 16
```

Repeat the owned lane on PostgreSQL18. The runner audits all original installed
wheel bytes, initializes schemas through its owner job, uses restricted roles,
and verifies cleanup. Handler overlap is proved by rendezvous, not timing ratios.
Unit, copied-blueprint, installed-wheel and rebuilt-source consumers complement
these database witnesses. Existing hosted AMD64/ARM64 × PG16/18 checks remain.

These are development candidates. Public dependency manifests, immutable
historical snapshots and publication settings remain unchanged. This work does
not start a release train.
