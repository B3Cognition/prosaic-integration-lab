# Experimental catalogue ontology in Integration Lab

Approved for native implementation. Build a copyable, credential-free example of the published
Core and Harness ontology prereleases. A maintainer should be able to compare
ordinary and enriched catalogue discovery, then run the same authored workflow
to read a synthetic verification receipt. This is a demonstration of SDK wiring
and visibility. Model-quality evaluation belongs to the separate release-evidence
research experiment.

## Copy and run

Register `catalogue-ontology` with the existing blueprint copy command. Keep the
CLI and package import usable in a stable Lab installation. Run the experiment in
a dedicated Python 3.12 environment with these exact public wheels.

| Distribution | Version | Wheel SHA-256 |
| --- | --- | --- |
| `b3-prosaic` | `0.5.1rc1` | `73a15af9205faaee1db3cef96969797890d87299d0518dd71e093d311156b334` |
| `b3-prosaic-harness` | `0.9.17rc1` | `53e3f0324d0214ed47055b8187541956b74559b1cd4a1e783c9654c305474055` |
| `b3-prosaic-runtime` | `0.9.23` | `5caab59f6d0ffd14299ee0840dd5f9b58b4e4f4a1b724ff6e3e2fa1699f08fd8` |

Use a dedicated three-wheel hash lock. The example needs neither PostgreSQL
adapter. Keep the two stable SDK manifests, their SDK provenance and the 450-case
released stack contract byte-for-byte intact. Experimental acceptance runs on
manual dispatch and ontology-specific pull requests in its own environment.
Retain the existing five-distribution SDK manifest validation for service and
stack consumers.

The copied directory includes `workflow.yml`, `host.py`, two small Markdown
agent artifacts, the Core conformance attachment and expected projection, the
receipt schema, a README and licensing. Ship it in the Lab wheel and source
archive, and include its exact resources in the public build input inventory.
Use the existing copy command's destination ownership and refusal behavior.

## Host binding and workflow

Use the published [Core catalogue ontology fixture][core-fixture] for the
`release-evidence` attachment. Its public catalogue exposes the `reviewer`
agent and `read_receipt` tool. It contains a registered `private-reviewer`
agent and `read_policy` tool for the visibility test. The host workflow policy
hides the former and the Runtime allowed-tool set hides the latter. The resulting
ontology exposes `candidate` and `receipt` and the one `receipt verifies candidate`
edge. The SDK owns attachment validation, alias checks and filtering.

The host inspects the local Markdown using Core's public Python inspection
API. It loads the attachment with `prosaic.ontology.load_ontology` and constructs
`WorkflowCatalog(ontology=...)` only when requested. The graph is host-authored
native YAML with a `read_receipt` direct tool step and a finish step. It is
loaded as data and admitted with `WorkflowFactory.build` using registered aliases
and grants. The receipt handler returns a fixed synthetic record. The workflow
uses a fresh local run directory and zero provider requests, and the command
prints only the curated completion status and schema-validated receipt.

`python host.py discover` prints the ordinary catalogue. Adding `--ontology`
requests the enriched projection and requires the experimental APIs. Both
`python host.py run` and `python host.py run --ontology` admit and run the same
graph. The latter proves that the attachment can coexist with ordinary execution.
Selecting an attachment does not change the proposal schema, admitted workflow
fingerprint, runtime requests or allowed tools. The attachment is a trusted
catalogue input. Workflow definitions and proposal envelopes reject ontology
fields.

## Acceptance

- Build and install the Lab wheel and a second wheel rebuilt from the Lab sdist
  in isolated environments. Verify actual module origins and the exact public
  SDKs. Run the public copy command from a neutral working directory and
  exercise the copied files. Also verify stable list and copy from the ordinary
  installed Lab smoke.
- Exercise discovery and the direct-tool workflow in an offline child process.
  Match the Core fixture's exact projection. Cover the hidden aliases, relations
  that lose a visible endpoint, unattached concepts, an empty projection, and a
  bounded discovery result. Compare ordinary discovery, proposal schema, graph
  identity and curated workflow output for attached and unattached factories.
- Exercise malformed attachments, relations referencing nonexistent concepts,
  unregistered aliases, unsupported SDKs,
  attempted ontology fields in graph/proposal inputs and an explicitly denied
  tool. Show that these checks happen before any handler or provider call.
- Document the exact install, copy, discover and run commands in a standalone
  experimental guide, linked from the Lab README and feature map. Record
  installed qualification separately from the stable release matrix.

[core-fixture]: https://github.com/B3Cognition/prosaic/tree/v0.5.1rc1/conformance-fixtures/catalogue-ontology
