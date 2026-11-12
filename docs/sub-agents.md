# Bounded delegation

Copy the [dependency analyst and reviewer blueprint](../lab_runner/blueprints/sub_agents/README.md).

```sh
python -m lab_runner.blueprints copy sub-agents /private/my-delegation-host
```

Bind specialist packs and local reads using the service's authorized scope. The analyst receives a graph pack and a typed graph lookup. The reviewer receives its own brief and a closed draft schema. The parent owns the answer and cites delivered graph observations through the existing citation contract.

## Authored workflow and conversation

The [copied workflow YAML](../lab_runner/blueprints/sub_agents/workflow.yml) grants
`analyze` and `review` on one coordinator node. The node uses the ordinary agent
kind, and the coordinator Markdown also declares the aliases. The host registers
each alias, specialist context pack, read permissions, and output schema in
`SubAgentBindingsV1`. The blueprint's `build_workflow` passes that binding, the
journal, and the tool contracts to `Workflow.load`. An application can also pass
the binding to `WorkflowBindings` for a trusted authored graph built with
`WorkflowFactory.build`. Generated workflow proposals cannot select delegates.

Use the blueprint's `build_host` for a conversation. Both entry points require
trusted host identity, a current result grant covering the selected sources, and
a store initialized or migrated for sub-agents. The installed blueprint tests
copy and run the authored YAML and conversation with both provider protocols.

## Verify the released SDK family

After the [quickstart setup](quickstart.md#setup-once), run the published
acceptance lane with the pinned SDK wheels and an owned PostgreSQL fixture.

```sh
python scripts/prepare_dependencies.py
python scripts/install_dependencies.py --manifest dependencies/releases.json
python -m pip install --no-deps --require-hashes -r dependencies/mcp-client.lock
python scripts/build_consumer.py --manifest dependencies/releases.json --tag prosaic-integration-lab:dev
python -m lab_runner test --mode sub-agents --postgres-version 16
```

Repeat for PostgreSQL 18.

## Candidate qualification

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
