# Releases and compatibility

Versions checked on 2026-11-07. Lab 0.9.9 adopts the complete public Core
0.5.0 / Runtime 0.9.16 / Harness 0.9.12 train with original recorder 0.3.0/store
0.4.1 bytes. [Feature blueprints](feature-blueprints.md) cover every added
capability; [release qualification](release-0.9.9.md) must finish before
publication. Lab 0.9.7 and its archived profiles retain Runtime 0.9.14 and
Harness 0.9.10; older qualification is never retroactively applied to the upgrade.

Value-guard v2 requires explicit readmission from the old train. Header options
add no persistent identity fields. Workflow tags now have a separate V2 blueprint with explicit guarded identity
and bounded receipt proof; existing Validator V1 remains available. Session
migration remains separate work. Existing tags and release archives stay immutable.

## Publication and previous releases

The [Lab 0.9.9 release page](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.9)
is the authority for its publication status, original archives and attached
qualification. A source version or tag alone is not proof of publication.

Earlier published versions are linked below. Backfilled notes explain changes using that version’s source, without attributing newer features or modern validation results to it. Candidate tags without a published release are not listed as releases.

| Release | Published (UTC) | Notes |
| --- | --- | --- |
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
