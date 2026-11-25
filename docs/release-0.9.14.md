# Lab 0.9.14 — parallel read tools

Adopt Runtime 0.9.21, Harness 0.9.15 and PostgreSQL store 0.4.4. Retain
the original Core 0.5.0 and Runtime recorder 0.3.0 wheels.

The copyable `parallel-tools` blueprint demonstrates opt-in concurrency
for independent read tools. The required matrix adds 32 cases per
architecture and PostgreSQL cell, covering overlap, bounded windows,
serial barriers, cancellation, ordered evidence, citations and fenced
receipt recovery across both supported provider wires. The previous
370 cases remain required.

See the [parallel tool guide](parallel-tools.md) for configuration and
verification commands.
