# Lab 0.9.16 — bounded sub-agents

Copy the [bounded delegation blueprint](sub-agents.md) to run a dependency analyst and reviewer from an authored YAML workflow or a conversation. Each specialist receives its own context pack. The coordinator owns the answer and can cite approved graph observations.

The release family uses Core 0.5.0, Runtime 0.9.23, Harness 0.9.17, Runtime recorder 0.3.0 and Harness PostgreSQL store 0.4.5. The store adds an owner-run migration for delegation.

The [required matrix](release-gates.md) includes 24 synthetic delegation cases per Linux architecture and PostgreSQL 16/18 cell. It exercises authorization, separate packs, citations, budgets, journal replay, interruption and offline receipt adoption. Each cell requires 450 cases across 14 lanes.
