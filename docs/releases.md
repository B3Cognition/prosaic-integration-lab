# Releases and compatibility

Versions checked against published GitHub releases on 2026-11-07.
The latest SDKs and the Lab's qualified dependency train are separate selections.
Harness 0.9.11 was qualified with Runtime 0.9.16 and Core 0.5.0; its declared
Runtime floor remains `>=0.9.14,<0.10`. Lab 0.9.7 retains its checksum-pinned
Runtime 0.9.14 / Harness 0.9.10 manifests. Newer SDK availability does not certify
that mixture in the Lab, and this documentation update changes no SDK pins.

| Component | Latest published version | Scope |
| --- | --- | --- |
| Core (`b3-prosaic`) | 0.5.0 | Canonical Markdown, native outputs and inert rule tags |
| Runtime (`b3-prosaic-runtime`) | 0.9.16 | Per-call OpenAI-compatible headers; includes 0.9.15 fee enforcement |
| Harness (`b3-prosaic-harness`) | 0.9.11 | Copyable versioned cross-step validator blueprint V1 |
| Runtime PostgreSQL recorder | 0.3.0 | Optional usage persistence; unchanged adapter release |
| Harness PostgreSQL store | 0.4.1 | Optional workflow/session persistence; unchanged adapter release |
| Integration Lab | 0.9.7 | Qualified Core 0.5.0 / Runtime 0.9.14 / Harness 0.9.10 |

Install current SDKs in a fresh environment; pin versions and archive hashes for reproducible deployments. Optional PostgreSQL adapters require explicit provisioning and operator readiness checks. Never co-install legacy and renamed distributions that own the same imports.

Runtime 0.9.15 advances `value_in_tool_output` to `value-in-tool-output-v2`; explicitly readmit affected bindings when upgrading from 0.9.14. Runtime 0.9.16 headers add no identity fields and leave guard versions unchanged. Harness 0.9.11 adds a source-archive blueprint using versioned validators; enforcement tags inside workflow agent steps remain future work.

## Published history

Every published version is linked below. Backfilled notes explain changes using that version’s source, without attributing newer features or modern validation results to it. Candidate tags without a published release are not listed as releases.

| Release | Published (UTC) | Notes |
| --- | --- | --- |
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
