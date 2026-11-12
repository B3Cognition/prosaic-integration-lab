# Bounded delegation

Copy the [dependency analyst and reviewer blueprint](../lab_runner/blueprints/sub_agents/README.md).

```sh
python -m lab_runner.blueprints copy sub-agents /private/my-delegation-host
```

Bind specialist packs and local reads using the service's authorized scope. The analyst receives a graph pack and a typed graph lookup. The reviewer receives its own brief and a closed draft schema. The parent owns the answer and cites delivered graph observations through the existing citation contract.

Qualify unpublished SDK wheels with a checksum-verified candidate manifest. Use the Runtime and Harness artifact directories containing their local build and installed-consumer receipts.

```sh
python scripts/prepare_sdk_candidates.py --sub-agents --runtime-artifacts "$RUNTIME_ARTIFACTS" \
  --harness-artifacts "$HARNESS_ARTIFACTS" --manifest "$CANDIDATE_MANIFEST"
python scripts/install_dependencies.py --manifest "$CANDIDATE_MANIFEST"
python -m pip install --no-deps --require-hashes -r dependencies/mcp-client.lock
python scripts/build_consumer.py --dependency-mode candidate --manifest "$CANDIDATE_MANIFEST" \
  --tag prosaic-integration-lab:candidate
python -m lab_runner test --mode sub-agents --postgres-version 16 \
  --candidate --candidate-manifest "$CANDIDATE_MANIFEST"
```

The required lane uses owned PostgreSQL storage and synthetic model endpoints. It runs 12 scenarios on each provider wire.

Hosted qualification accepts a successful same-repository `qualified-sub-agents` handoff with the original `runtime/` and `harness/` artifact directories. Pass that run ID as `delegation_handoff_run_id` with candidate mode enabled. The matrix verifies the same receipts and wheel checksums in each cell.
