# Parallel read tools

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

Lab 0.9.14 qualifies Runtime 0.9.21, Harness 0.9.15, and Harness PostgreSQL
0.4.4 with the original Core 0.5.0 and Runtime recorder 0.3.0 wheels. It adds
32 required cases across the two provider wires, for 402 cases in 12 lanes per
architecture and database cell. The lane audits installed SDK bytes, uses
restricted worker roles, and verifies cleanup.

With the released consumer image built using `scripts/build_consumer.py`, run:

```sh
python -m lab_runner test --mode parallel-tools --postgres-version 16
python -m lab_runner test --mode parallel-tools --postgres-version 18
```

For local reproduction of the original development candidate, curate its
exact SDK archives with `scripts/prepare_sdk_candidates.py --parallel-tools`
and supply `--candidate --candidate-manifest PATH` and the immutable candidate
consumer image. Candidate and released manifests select separate exact versions.
