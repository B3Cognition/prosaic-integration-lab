# Lab 0.9.21

The experimental bounded coordination blueprint shows how a host can run two
independent Harness workflows under one shared Runtime budget. The host assigns
each worker its own source and store, verifies its tool evidence, and combines
the verified reports. Receipt-only recovery checks saved results without
dispatching either worker. [Bounded coordination guide](https://github.com/B3Cognition/prosaic-integration-lab/blob/v0.9.21/docs/bounded-coordination.md)

The installed wheel and rebuilt-source checks each exercise 48 synthetic cases
across Anthropic and OpenAI-compatible protocols and sequential and concurrent
execution, followed by network-disabled replay. The cases cover actual worker
overlap, budget enforcement, conflicting evidence, and failure handling.

Source builds verify the published Core 0.5.1, Runtime 0.9.28, Harness 0.9.20,
Runtime PostgreSQL 0.3.0, and Harness PostgreSQL 0.4.6 wheels against the hashes
in `dependencies/releases.json`.

[Release downloads and qualified image digests](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.21)
