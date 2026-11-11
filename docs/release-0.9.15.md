# Lab 0.9.15 — MCP read tools

The SDK family is Core 0.5.0, Runtime 0.9.22, Harness 0.9.16, Runtime recorder
0.3.0 and Harness PostgreSQL store 0.4.4. Core and both adapters retain their
published wheel bytes.

The [MCP client blueprint](mcp-client.md) shows how to expose a host-approved
remote read alias. The released matrix adds 24 synthetic MCP cases to each
Linux architecture and PostgreSQL 16/18 cell, bringing the required total to
426 cases across 13 lanes. Cases cover authorization, revocation, catalog
changes, journal replay and offline receipt adoption across both provider wires.

See the [release gates](release-gates.md) for qualification and cleanup criteria.
