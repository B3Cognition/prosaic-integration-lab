# Stable catalogue ontology implementation plan

**Goal**

Ship the published RC's v1 format and opt-in catalogue projection as
supported Core and Harness APIs. Qualify the exact pair with the existing
Runtime and verify the contract from an installed Lab blueprint.

**Design**

[Stable catalogue ontology](../specs/2026-11-12-stable-catalogue-ontology-design.md)

**Scope and order**

Core format and packaging → Harness binding and projection → same-artifact
qualification → Lab installed and stack acceptance. Start implementation in
clean worktrees based on each current remote main. Port only the feature
files from the tagged RCs. Keep the Lab stable SDK manifests and RC lock
byte-for-byte intact. This plan ends with reviewable code and build-only
qualification evidence. Release authorization is a later decision.

## Compatibility matrix

| Combination | Required result |
| --- | --- |
| Current Lab stable set (Core 0.5.0, Harness 0.9.17, Runtime 0.9.23, existing adapters) | All ordinary CI and 450 stack cases per cell pass. Blueprint list and copy work. Explicit ontology commands report the missing feature and the appropriate installation instructions. |
| Candidate Harness with Core 0.5.0 and Runtime 0.9.23 | Ordinary import, discovery, proposal admission, execution and recovery pass. Supplying an attachment fails with the existing sanitized `invalid_definition` code. |
| Candidate Core and Harness with the published Runtime 0.9.23 | Omitted ontology option preserves ordinary results. Explicit projection matches the existing v1 fixture and respects catalogue visibility. |
| Candidate pair plus public Runtime 0.9.23, Runtime PostgreSQL 0.3.0 and Harness PostgreSQL 0.4.5 | Existing 14 lanes and 450 cases per platform/database cell pass. Pre-upgrade workflows and saved references reopen without migrations. |
| Frozen experimental RC lock | Existing 11 cases pass per Lab distribution path with the original prereleases. This remains the reproducible RC installation. |

## 1. Stabilize the Core v1 format

**Files**

`src/prosaic/ontology.py`, `tests/test_ontology.py`,
`conformance-fixtures/catalogue-ontology/{attachment,visible}.json`,
README, `docs/catalogue-ontology.md`, `scripts/wheel_smoke.py`,
`scripts/release_artifacts.py`, `.github/workflows/{ci,publish}.yml`.

- [ ] Retrieve the tagged RC feature paths and record their source commit.
  Check fixture hashes against the RC and the copies already in Lab. Copy
  the v1 guide, fixtures, public module and tests onto current Core main.
  Run the contract cases first against the RC to establish acceptance and
  output parity. Run the new hardening regressions before their fixes.
- [ ] Keep both public signatures and the generic error. Build an owned
  snapshot as each accepted leaf is checked and account for its compact
  UTF-8 encoding within the existing byte limit. Verify that the exact
  boundary and Unicode handling agree with the RC. For file input, bound
  bytes before decoding and preserve duplicate-key rejection. Check the
  regular leaf before and after opening using the available platform
  facilities, verify it is the same file, and close the handle on every
  outcome. Use deterministic, simulated replacement coverage where platform
  flags differ.
- [ ] Cover exact and over-limit raw/canonical bytes, description byte
  limits, multibyte text and escaped controls, per-map and per-list limits,
  invalid identifiers, booleans for the schema version, duplicate keys and
  relation triples, unknown fields and endpoints, malformed UTF-8 and JSON,
  unsupported Python types, deep malformed input, mutation of source and
  returned state, and sanitized errors. Test regular, missing, directory,
  symlink and nonregular leaf paths. Verify valid file and in-memory inputs
  yield the same detached value and the established fixture.
- [ ] Run `python -m pytest -q` and `python scripts/verify_migration.py`.
  Keep existing Linux x64/arm64 and Python 3.11–3.13 release checks. Add a
  Windows ontology test step alongside project-lock tests. Add installed
  `python -I scripts/wheel_smoke.py` coverage of the public API, official
  fixture and sanitized negative case. Run it both with the direct wheel
  and a wheel rebuilt from the extracted sdist. Audit that the ontology
  module ships in both and the fixtures ship in the sdist. Check module
  ownership in a neutral environment with no editable install.
- [ ] Document the supported v1 limits, file scope and error contract.
  Keep existing CLI, parser, target artifacts and dependency floors
  compatible. Hand off the tested source, wheel and sdist hashes to Harness.

## 2. Stabilize Harness catalogue discovery

**Files**

`src/prosaic_harness/{factory,discovery}.py`,
`tests/test_catalogue_ontology.py`,
`tests/{test_workflow_discovery,test_workflow_bundles,test_recovery_contracts}.py`,
Harness README, discovery guide and release-note draft.

- [ ] Add `WorkflowCatalog(ontology=...)` and
  `WorkflowFactory.describe(include_ontology=False)` as keyword-only
  extensions. Import Core's API lazily when a document is provided.
  Validate agent aliases at catalogue creation and ordinary custom tool
  aliases when bindings are available at factory creation. Include
  registered MCP aliases. Refuse delegate and built-in aliases. Use the
  existing errors `invalid_definition` and `unknown_reference` without echoing
  payloads. Document the Core requirement for the opt-in feature.
- [ ] Project through the existing discovery `_selection`. Do not add a
  second policy calculation. Exclude delegate aliases, keep only concepts
  attached to visible aliases, and keep only edges with two visible
  endpoints. Ordinary schemas and `allowedDirectTools` still follow the
  existing policy. Require real booleans for the include flags. Omit an
  empty projection. Enforce the existing combined response limit and return
  independent nested data.
- [ ] Write failing projection and permission tests before porting.
  Compare the Core fixture. Exercise the two include flags independently
  and together, no attachment, no surviving annotations, shared concepts,
  edges with a filtered endpoint, hidden agents, Runtime-hidden tools,
  discovery-policy-hidden tools, and direct-tool admission. Check registered
  but hidden aliases against unregistered aliases, including delegate-only
  names. Cover size limits with and without schemas, caller mutation before
  and after factory creation, isolated catalogue scopes, and zero tool,
  provider or validator invocations during discovery.
- [ ] Assert attachment add, replace and remove preserve ordinary
  discovery, proposal schema, `Workflow.fingerprint`, canonical proposal
  JSON, `WorkflowBundle.identity` and `WorkflowReference`. Exercise
  `WorkflowBundle.prepare_json` and `reconstruct` with a reference saved by
  the published version, then reopen a pre-upgrade FileRunStore run. Verify
  equivalent curated output and no change in guard inputs, accounting
  attribution or provider/tool dispatch on replay. Check YAML/JSON/dict
  admission and the proposal schema reject ontology directives at closed
  declaration positions and accept existing opaque `ontology` payload keys.
  Keep attachment data out of `WorkflowFactory._frozen_copy` and the execution
  identity payload.
- [ ] Run `python -m pytest -q` with Core 0.5.0 and Runtime 0.9.23.
  Put the focused positive ontology contract in an explicit feature lane
  with the Core candidate. Its preflight fails if the public APIs or the
  required installed distributions are missing. Add a focused installed
  ordinary-discovery test with Core 0.5.0 and confirm the existing error
  for unsupported attachments. Keep the ordinary Core dependency floor
  and existing adapter unchanged. Keep candidate-only tests out of the
  standard qualification collection so both lanes can require zero skips.

## 3. Bind qualification to the exact SDK artifacts

**Files**

Core and Harness `scripts/release_artifacts.py` and publish workflows,
Harness `.github/workflows/{tests,promotion-checks}.yml`,
`tests/test_release_artifacts.py` and an installed ontology smoke entry.

- [ ] Build Core from the exact reviewed source in the ordinary build-only
  workflow. Use its qualified wheel and sdist pair and audited source
  receipt. Prepare the Harness candidate wheel and sdist once. Keep normal
  Harness qualification against Core 0.5.0 and the existing Runtime
  0.9.23 receipt. Preserve `validate_upstream_chain` and its comparison
  with Runtime's original Core lineage.
  Verify availability of the original qualified-release artifacts for
  [Core 0.5.0][core-qualification] and [Runtime 0.9.23][runtime-qualification]
  before building. If an archived run expires, require equivalent immutable
  release evidence with the same receipt and digest checks.
- [ ] Run a required second Harness qualification using those same Harness
  artifacts, the exact Core candidate and the retained public Runtime
  wheel. Test direct installation and the sdist rebuild path. Capture the
  source commits, run IDs and original artifact receipt digests for all
  inputs, the exact wheel/sdist hashes and tested rebuild hashes, the
  Runtime release and original upstream receipt digest, environment,
  expected test cases, results and evidence digests. Pass the verified
  compatibility receipt to Lab along with the original lineage. Carry it
  in Harness's aggregate `qualified-release` artifact and re-verify the
  receipt contents at promotion. Both proofs must bind to the same
  Harness candidate bytes.
- [ ] Test missing or unsuccessful jobs, wrong workflow/repository/ref
  or head, artifact receipt or compatibility result tampering, changed
  Runtime provenance, same-version substitutions, mismatched wheel and
  sdist sources, unexpected artifacts, and skipped or incomplete cases.
  Test the standard release-audit path with the current stable inputs.
  Update hard-coded Harness SDK filenames and the release-note path for
  the candidate. Keep the existing adapter build as a qualification witness.
  Lab uses the original published 0.4.5 bytes. Use build-only jobs during
  this implementation. Publication, tag changes and deployment settings
  are outside this plan.

The known retained Runtime wheel SHA-256 is
`5caab59f6d0ffd14299ee0840dd5f9b58b4e4f4a1b724ff6e3e2fa1699f08fd8`.
Use the published adapter wheel hashes already recorded by the stable Lab
profile. The compatibility job tests a new combination of existing
artifacts and candidate bytes. [Harness lineage validator][harness-chain]

## 4. Qualify the installed Lab blueprint

**Files**

`lab_runner/blueprints/catalogue_ontology/`,
`tests/catalogue_ontology_acceptance/{conftest,test_contract,test_installed}.py`,
the existing RC workflow and a candidate-only workflow,
`docs/{catalogue-ontology,feature-blueprints,release-gates}.md`, README,
and `docs/verification/progress.md`.

- [ ] Keep `dependencies/catalogue-ontology-rc.lock` and its replay lane.
  Add an explicit candidate test profile driven by verified Core, Harness
  and Runtime wheel hashes. Keep the profile check exact about version,
  installed distribution ownership and import origin. Fail a candidate run
  when it lacks either ontology API. Keep the ordinary installed list/copy
  and unsupported-feature checks on stable pins.
- [ ] Install the direct Lab wheel and a second wheel rebuilt from the
  extracted Lab sdist in fresh environments. Verify the packaged workflow,
  fixture bytes and guide; run the installed copy command with a neutral
  working directory and exercise `host.py discover` and `host.py run`
  both with and without `--ontology`. Reuse the contract suite for
  filtered and empty projections, oversize discovery, malformed inputs,
  denied tool use, identical proposal/fingerprint and credential-free
  synthetic execution. Test exact expected case IDs or the reviewed
  expected set with zero skips in each artifact path.
- [ ] Make the candidate proof required for stable ontology qualification.
  Include changes to shared blueprint, packaging, build, dependency and
  contract inputs in workflow coverage. Keep the isolated installed proof
  free of services, sockets and provider calls. Retain the independent
  installed RC result.
- [ ] Update the guide with the opt-in API, supported versions, unchanged
  ordinary commands, version mismatch behavior and the copyable example.
  Label candidate evidence separately in the feature map, README and
  progress log. Enable instructions that name stable public versions only
  after those public artifacts exist.

## 5. Verify the complete candidate stack and upgrade path

**Files**

`scripts/{prepare_sdk_candidates,build_consumer,install_dependencies,audit_install,required_acceptance}.py`
and their existing tests, `lab_runner/gates.py`,
`lab_runner/sub_agents.py`, candidate CI, and the release checklist.
Change an existing script only where the new explicit profile requires it.

- [ ] Add one explicit `catalogue-ontology` candidate lineage kind to the
  existing curation path. Accept only the qualified new Core/Harness pair
  and the three retained verified wheels. Bind source run, artifact and
  compatibility receipt identities in the manifest. Validate the manifest
  before staging it. Reuse the install and audit paths for exact hashes
  and package ownership. Refuse unknown, duplicate, mixed, tampered or
  unqualified inputs. Keep existing candidate and historical profiles.
- [ ] Recognize this exact qualified family before the existing
  mixed-delegation-family rejection. Preserve inherited conversation,
  context assembly, context packs, tool evidence, parallel tools, MCP,
  sub-agents and blueprint gates. Cover the sub-agent install preflight,
  which reads candidate lineage. Unit-test all 14 selected modes, expected
  counts, wrong hashes, incomplete provenance and ordinary stable profile
  behavior.
- [ ] Build from an isolated candidate manifest and wheel directory with
  `python scripts/build_consumer.py --dependency-mode candidate --manifest
  <manifest> --wheel-dir <wheel-dir> --tag <candidate-tag>`. Run
  `python scripts/required_acceptance.py --candidate --candidate-manifest
  <manifest> --consumer-image <image-id> --baseline-image <baseline-image>
  --postgres-version <16-or-18> --export <receipt>` on Linux amd64 and
  arm64. Require all 14 lanes and 450 existing cases per cell, no skips,
  correct image and lineage digests, and verified cleanup. Keep the
  ontology installed contract separate from those 450 cases.
- [ ] Qualify pre-upgrade recovery with a focused installed compatibility
  check outside the counted 450 cases. Produce a run with the old stable
  SDKs using an owned fixture, then reopen/resume with the candidate pair
  and the retained adapter. Check saved reference, policy, attribution and
  previously accepted evidence, and verify no extra side effects or DDL.
  Run the ordinary Lab CI and confirm its tenant and HTTP catalogue
  behavior still passes with the current pins.
- [ ] Review all three diffs independently against the design. Record exact
  candidate source and artifact digests, commands, platform results, case
  counts and any limitations. Verify byte-for-byte equality for
  `dependencies/releases.json`, `dependencies/releases-reasoning.json`
  and the RC lock. Keep the released history and active release gates
  intact. Report a missing receipt, skipped case or matrix failure as an
  open promotion blocker.

## Future release handoff

Once explicitly authorized, qualify and publish Core first, then verify its
public bytes before Harness promotion. Verify the public Harness artifact
and rerun the installed Lab proof and required stack against the verified
public set before any authorized Lab pin update or release. If an upstream
artifact changes after qualification, repeat the affected proofs with its
new digest. Runtime and both adapters can stay on the retained versions if
the recorded compatibility gates pass.

[core-qualification]: https://github.com/B3Cognition/prosaic/actions/runs/42014531336
[runtime-qualification]: https://github.com/B3Cognition/prosaic-runtime/actions/runs/43210113804
[harness-chain]: https://github.com/B3Cognition/prosaic-harness/blob/a32c8a09dda21fc5c3b68bd24b75c95f3ee97304/scripts/release_artifacts.py#L391
