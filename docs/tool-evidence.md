# Safe tool events and captured citations

Lab 0.9.13 uses Runtime 0.9.20, Harness 0.9.14 and Harness PostgreSQL 0.4.3.
The released manifest retains Core 0.5.0 and Runtime PostgreSQL 0.3.0 unchanged.
The required acceptance matrix includes 24 tool-evidence cases in each Linux
AMD64/ARM64 and PostgreSQL 16/18 cell, alongside every existing required lane.

Copy the complete host example from the installed Lab wheel:

```sh
python -m lab_runner.blueprints copy tool-evidence /private/my-tool-host
```

The [host example](../lab_runner/blueprints/tool_evidence/README.md) wraps an
application lookup in `CustomTool`. Its result contract checks the returned data;
its event policy selects bounded scalar fields rather than exposing arguments
or result objects wholesale. Wire its authorization callbacks to the current
authenticated principal and source permissions. The example's permissive callback
defaults are for synthetic fixtures. Replace them when embedding the host.

A typed result carries captured evidence selections separately from model-visible
data and validation facts. Applications forward approved SDK tool events through
their own SSE transport. Legacy return values keep their ordinary behavior;
contracts and citation checking require explicit configuration. Checked answers
are held until accepted, while approved tool progress remains live.

Citations resolve against captured content and the receipt, without fetching a
mutable URL. Views and later reuse recheck current permission; a citation ID in
conversation history grants no authority. Provision tool-contract storage
explicitly; workers check readiness and never migrate it. Citation checking
establishes provenance, not semantic entailment or live-model answer quality.

## Run the released acceptance lane

Prepare, install and audit `dependencies/releases.json` with
`scripts/prepare_dependencies.py`, `scripts/install_dependencies.py` and
`scripts/audit_install.py`. Build an immutable consumer with
`scripts/build_consumer.py --manifest dependencies/releases.json --tag prosaic-tools:local`.
Use the returned image ID:

```sh
python -m lab_runner test --mode tool-evidence \
  --consumer-image sha256:THE_IMMUTABLE_IMAGE_ID --postgres-version 16
```

Repeat with PostgreSQL 18. The host and consumer must contain the same audited
SDK bytes. Required cases cannot skip; each invocation owns its resources and
verifies cleanup. Archived development handoffs remain available through explicit
`--candidate --candidate-manifest PATH` execution and separate lineage checks.

See [release scope](release-0.9.13.md) and the
[implementation checkpoint](verification/tool-events-citations-2026-11-10.md).
Published archives and hosted qualification are linked from the release page.
Parallel calls, MCP and sub-agents remain separate follow-ups.
