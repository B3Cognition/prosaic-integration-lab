# Lab 0.9.17 — catalogue ontology

Copy the [catalogue ontology blueprint](catalogue-ontology.md) to attach v1
concepts and relations to existing agent and tool aliases. Explicit discovery
returns the concepts visible under the host's existing policy. The same
authored workflow reads a synthetic receipt with the attachment enabled or
disabled.

| Package | Version |
| --- | --- |
| Core | 0.5.1 |
| Runtime | 0.9.23 |
| Harness | 0.9.18 |
| Runtime PostgreSQL recorder | 0.3.0 |
| Harness PostgreSQL store | 0.4.5 |

The two active SDK manifests pin public wheel hashes and source commits.
Lab 0.9.16's manifests, benchmark provenance and freezes are archived.
The original experimental lock still reproduces the RC example.

Attaching ontology requires no workflow readmission or store migration.
The build-only [candidate matrix](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/43383408761)
passed 450 synthetic cases in each Linux x64/ARM64 and PostgreSQL 16/18
combination. It also verified cross-version recovery and both installed
package paths. The release attaches a separate qualification receipt for
the final public pins and Lab archives.
