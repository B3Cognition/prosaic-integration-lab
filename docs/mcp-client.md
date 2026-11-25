# MCP client blueprint

Install Lab's checksum-pinned SDK family and optional MCP dependency lock.
Lab 0.9.15 introduced the MCP lane with Runtime 0.9.22, Harness 0.9.16 and
PostgreSQL store 0.4.4. The [current SDK train](releases.md) continues to run it.

```sh
python -m lab_runner.blueprints copy mcp-client /private/my-mcp-host
python -m pip install --no-deps --require-hashes -r dependencies/mcp-client.lock
python -m lab_runner test --mode mcp-client --postgres-version 16
```

The copied host registers a graph lookup using a trusted destination and a
host-approved alias. Bind access to the authenticated host identity. Keep
credentials, private catalog snapshots and journals in host-controlled storage.
Reuse the saved catalog and current authorization policy for offline adoption.
See the [blueprint README](../lab_runner/blueprints/mcp_client/README.md).
