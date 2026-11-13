# Releases and compatibility

Lab 0.9.17 supports [catalogue ontology](release-0.9.17.md) on Core 0.5.1
and Harness 0.9.18 with Runtime 0.9.23 and the existing PostgreSQL adapters.

Lab 0.9.16 adds [bounded sub-agents](release-0.9.16.md) with Runtime 0.9.23, Harness 0.9.17 and PostgreSQL store 0.4.5.

Lab **0.9.15** selected Core **0.5.0**,
Runtime **0.9.22**, Harness **0.9.16**, recorder **0.3.0**, and Harness
PostgreSQL **0.4.4**. [MCP read tools](mcp-client.md) join parallel read tools,
tool evidence, and context packs in the four Linux architecture/PostgreSQL cells.
See the [0.9.15 release notes](release-0.9.15.md).

Value-guard v2 requires explicit readmission from the old train. Header options
add no persistent identity fields. Workflow tags now have a separate V2 blueprint with explicit guarded identity
and bounded receipt proof; existing Validator V1 remains available. Session
migration remains separate work. Existing tags and release archives stay immutable.

Runtime0.9.17 adds optional frozen accounting request labels, with a separate
[copyable host](accounting-request-metadata.md). Empty labels preserve exact old
accounting bytes/hashes; present labels intentionally change accounting hashes
and private saved contexts/receipts. No artifact/rule or workflow identity fields
move. Saved labels win on resume and new labeled contexts require >=0.9.17 readers.
Published recorder0.3.0 keeps its schema/bytes; no old records are rewritten.

## Publication and previous releases

The [Lab 0.9.17 release page](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.17)
is the authority for its publication status, original archives and attached
qualification. A source version or tag alone is not proof of publication.

Earlier published versions are linked below. Backfilled notes explain changes using that version’s source, without attributing newer features or modern validation results to it. Candidate tags without a published release are not listed as releases.

| Release | Published (UTC) | Notes |
| --- | --- | --- |
| [v0.9.16](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.16) | See release page | [Bounded sub-agents](release-0.9.16.md) |
| [v0.9.15](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.15) | See release page | [MCP read tools](release-0.9.15.md) |
| [v0.9.14](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.14) | See release page | [Parallel read tools](release-0.9.14.md) |
| [v0.9.13](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.13) | See release page | [Safe tool events and citations](release-0.9.13.md) |
| [v0.9.12](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.12) | See release page | [Context-pack notes](release-0.9.12.md) |
| [v0.9.11](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.11) | See release page | [Sent-effort notes](release-0.9.11.md) |
| [v0.9.10](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.10) | 2026-11-08 | [Accounting metadata notes](release-0.9.10.md) |
| [v0.9.9](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.9) | 2026-11-07 | [Workflow enforcement notes](release-0.9.9.md) |
| [v0.9.8](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.8) | 2026-11-07 | [Feature blueprint notes](release-0.9.8.md) |
| [v0.9.7](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.7) | 2026-11-06 | Published notes |
| [v0.9.6](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.6) | 2026-11-06 | Published notes |
| [v0.9.5](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.5) | 2026-11-06 | Published notes |
| [v0.9.4](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.4) | 2026-11-04 | Published notes |
| [v0.9.3](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.3) | 2026-11-03 | Published notes |
| [v0.9.2](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.2) | 2026-11-03 | Published notes |
| [v0.9.1](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.1) | 2026-11-02 | Published notes |
| [v0.9.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.0) | 2026-11-01 | Published notes |
| [v0.8.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.8.0) | 2026-10-31 | Published notes |
| [v0.7.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.7.0) | 2026-10-25 | Published notes |
| [v0.6.2](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.6.2) | 2026-10-25 | Published notes |
| [v0.6.1](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.6.1) | 2026-10-25 | Published notes |
| [v0.6.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.6.0) | 2026-10-24 | Published notes |
| [v0.5.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.5.0) | 2026-10-17 | Published notes |
| [v0.4.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.4.0) | 2026-10-11 | Published notes |
| [v0.3.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.3.0) | 2026-10-11 | Published notes |
| [v0.2.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.2.0) | 2026-10-09 | Published notes |

## Release-note checklist

For each future publication, write version-specific notes before release: describe changed behavior, dependency floors and the exact qualified train, identity/fingerprint changes and readmission or migration steps, adapter publication versus witness status, and observed validation with its limits. Link the original qualification and public-consumer proof. Never substitute a generic “qualified release” sentence or rewrite historical package bytes to improve documentation.
