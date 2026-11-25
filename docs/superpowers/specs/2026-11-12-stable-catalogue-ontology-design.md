# Stable catalogue ontology

Promote the existing v1 attachment and catalogue projection to a supported,
opt-in SDK contract. A host can annotate its agent and tool catalogue with
domain concepts, then request a view filtered through the same policy as
ordinary discovery. The first stable versions are provisionally Core 0.5.1 and
Harness 0.9.18. Use the published Runtime 0.9.23 and existing PostgreSQL
adapters. These are planning targets.

The baseline is [Core main][core-main], [Harness main][harness-main] and [the
merged Lab example][lab-pr]. Port the ontology-specific code from the
[Core RC][core-rc] and [Harness RC][harness-rc] onto those maintained bases.

## Core owns the attachment format

`prosaic.ontology.load_ontology(path)` loads a trusted host-selected file.
`prosaic.ontology.validate_ontology(document)` validates a Python JSON object.
Both return a detached JSON-compatible dictionary and reject invalid input
with the existing sanitized `ValueError("Invalid ontology attachment")`.
Keep the v1 camelCase wire format and the shared attachment and projection
fixtures.

The root has exactly `schemaVersion`, `ontologyId`, `concepts`, `relations`,
`agents`, and `tools`. Version is integer `1`. Identifiers are ASCII letters
followed by up to 63 ASCII letters, digits, underscores or hyphens.
Descriptions are nonblank, NUL-free UTF-8 strings of at most 1,024 bytes.
Each map holds up to 256 entries. Each alias annotates 1–256 unique declared
concepts. There are at most 512 distinct relation triples and both endpoints
must be declared. Raw input and compact UTF-8 JSON each have a separate
65,536-byte ceiling. Duplicate JSON object keys fail at every depth. Freeze the
RC's exact types, accepted Unicode, relation and annotation shapes, and order
semantics using compatibility cases. Build the returned snapshot from the
values actually checked and bound compact encoding while checking its size.
Keep regular-file-only leaf reads, including symlink and replacement checks
with platform-specific coverage. The path is chosen by trusted host code.

## Harness owns binding and projection

`WorkflowCatalog(ontology=...)` accepts the validated v1 document as an
optional keyword. Harness verifies that agent annotations name registered
agents and that tool annotations name registered non-delegate custom tools.
This includes registered MCP tools that participate in ordinary discovery.
Keep the existing admission error codes for invalid definitions and unknown
references. Load Core's ontology API only when an attachment is supplied.
Harness continues to support Core 0.5.0 for ordinary use. The ontology option
requires Core 0.5.1 or a compatible later release.

`WorkflowFactory.describe(include_ontology=True)` adds an `ontology` field
when at least one visible alias has annotations. The default call and a call
with an empty visible projection omit the field. Reuse the current catalogue
selection, including registered aliases, host policy, Runtime's allowed-tool
set, and the exclusion of delegate aliases. Keep only annotations for those
aliases, the concepts they reference, and relation triples with both endpoints
present. Apply the existing `maximum_bytes` cap to the complete discovery
response. Each returned projection is independently owned. Hosts supply
public-facing ontology IDs, descriptions and relations for their intended
catalogue audience.

Ontology affects discovery alone. Keep the existing proposal schema and
reject ontology as a declaration in its closed schema positions and in
authored workflows. Preserve ordinary `ontology` keys in tool arguments,
run inputs and other user-defined payloads. Keep the
attachment out of the execution-only frozen factory, workflow fingerprints,
bundle identity, canonical proposal JSON, saved references, prompts, guards,
tool grants, events, and storage. Verify that workflows saved before the
upgrade resume with the same reference and attribution. The initial stable
surface is the Python SDK. Lab's existing HTTP catalogue continues to return
ordinary discovery.

## Qualification and rollout

- Keep the standard Harness build qualification on Core 0.5.0 and the
  original Runtime 0.9.23 lineage. A second required receipt binds the very
  same Harness candidate artifacts to the Core candidate and the verified
  published Runtime wheel. This records a new tested combination while
  preserving the original Runtime receipt and the strict upstream-chain
  validator. [Harness upstream-chain validation][harness-chain]
- Reuse Lab's copyable workflow and its offline installed contract suite for
  a separate candidate profile. Keep the three-wheel RC replay reproducible.
  Qualify the candidate with both wheel and sdist-rebuilt wheel installs.
  Separately run the existing 14-lane stack matrix on the two candidate SDKs
  plus the three retained public wheels.
- Keep Lab's active stable manifests, historical profiles and ordinary CI
  gates as they are during qualification. A future promotion requires
  verified public Core and Harness artifacts and a separate Lab adoption
  decision. Provider efficacy and any automatic use of ontology in product
  workflows are separate research and rollout decisions.

[core-main]: https://github.com/B3Cognition/prosaic/tree/203a60d8f98617ab84da1abbd2d31b7119e9ef3a
[core-rc]: https://github.com/B3Cognition/prosaic/releases/tag/v0.5.1rc1
[harness-main]: https://github.com/B3Cognition/prosaic-harness/tree/a32c8a09dda21fc5c3b68bd24b75c95f3ee97304
[harness-rc]: https://github.com/B3Cognition/prosaic-harness/releases/tag/v0.9.17rc1
[harness-chain]: https://github.com/B3Cognition/prosaic-harness/blob/a32c8a09dda21fc5c3b68bd24b75c95f3ee97304/scripts/release_artifacts.py#L391
[lab-pr]: https://github.com/B3Cognition/prosaic-integration-lab/pull/60
