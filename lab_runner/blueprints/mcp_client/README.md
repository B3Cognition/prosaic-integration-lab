# MCP graph lookup

Install the qualified Harness and Runtime wheels with the Runtime `mcp` extra. Copy this directory and supply the host callbacks to `build_client`. The host approves a specific HTTPS endpoint, resolves scoped credentials for it, and derives access scope from the authenticated caller. Use an owned journal and operation namespace. Loopback HTTP is for credential-free local fixtures.

Enter the client context and call `discover(access_scope=...)` during host onboarding. Review the selected tool schemas, then retain `catalog.to_dict()` and independently pin `catalog.sha256` in trusted storage. On restart, use `restore_catalog` with the same host configuration, access scope and pinned digest. Pass that catalogue to `build_host`. The model sees only the locally approved alias `graph_lookup`.

Initialize an owned session store with `initialize(tool_contracts=True)` before creating sessions. Retained evidence remains subject to the evidence authorizer. A remote catalogue change requires explicit rediscovery and rebinding for new sessions. Reconcile uncertain operations in the host journal before further recovery.
