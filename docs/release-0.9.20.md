# Lab 0.9.20

The Lab uses the published Core 0.5.1, Runtime 0.9.28, Harness 0.9.20,
Runtime PostgreSQL 0.3.0, and Harness PostgreSQL 0.4.6 wheels. Source builds
verify the exact wheel hashes in `dependencies/releases.json`.

The [guarded recovery blueprint](https://github.com/B3Cognition/prosaic-integration-lab/blob/v0.9.20/docs/guarded-recovery.md)
now shows how to turn on bounded tool recovery for a guarded workflow with a
required initial lookup. The installed wheel and rebuilt-source tests cover
Anthropic and OpenAI-compatible fixtures, including matching tool event
versions, one read, and a resume with no redispatch. Harness PostgreSQL 0.4.6
repairs stale pooled connections before use. The consumer regression was
rerun with synthetic faults on PostgreSQL 16 and 18.

The Linux images include Bubblewrap 0.12.0. Use the published multi-architecture
digest with the [dedicated sandbox policy](https://github.com/B3Cognition/prosaic-integration-lab/blob/v0.9.20/docs/sandboxed-tools.md#qualify-the-linux-image).
The wheel, source archive, and qualification evidence are attached to the
[GitHub release](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.20).
