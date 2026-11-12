# Lab experimental catalogue ontology implementation plan

> Execute task by task using the executing-plans or subagent-driven-development
> skill after review. Each task includes its own verification.

**Goal** — Ship a copyable example of policy-scoped ontology discovery and
ordinary workflow admission and execution with the published prerelease SDKs.

**Architecture** — Load an optional Core attachment in the trusted host, project
it with the Harness factory, and build an authored native graph with the same
factory. The graph reads one synthetic receipt through Runtime's direct-tool
path. Install the three exact SDKs in a separate environment to qualify the copy.

**Stack** — Python 3.12, PyYAML, Core 0.5.1rc1, Harness 0.9.17rc1,
Runtime 0.9.23, pytest, setuptools and GitHub Actions.

**Design** — [Experimental catalogue ontology in Integration Lab](../specs/2026-11-12-lab-catalogue-ontology-design.md)

## Scope and review focus

- Start implementation from Lab `origin/main` containing `v0.9.16`. The two
  stable manifests, provenance and freeze files, released CI, 14 lanes and 450
  required cases per cell stay byte-for-byte intact. The experimental workflow is
  dispatch-only and separate from stable release qualification.
- The catalogue's ordinary mode works with the stable SDKs. Copying the example
  imports no ontology APIs. Enabling the attachment on an unsupported SDK pair
  must fail with an actionable message before workflow or tool execution.
- A registered alias can be hidden by policy or by Runtime grants. Relations
  lose any hidden endpoint. Core rejects a relation to an unknown concept before
  discovery. Tests cover each case independently.
- Catalogue and returned projection objects are owned snapshots. Test mutation
  isolation and the combined response byte limit.
- The workflow uses one fixture tool with an explicit host grant and no
  provider. Test a missing direct-tool grant separately from missing discovery
  permission. The YAML graph and JSON proposal schemas stay authoritative.
- Use a fresh temporary directory for each fixture run. Limit tests to public
  installed APIs and synthetic data. Preserve existing benchmark experiments
  and published artifacts.

## Task 1 — Lock the experimental SDKs and prove isolated installation

**Create** `dependencies/catalogue-ontology-rc.lock` and
`tests/catalogue_ontology_acceptance/test_installed.py`.

- [ ] Add `test_exact_installed_sdk_payloads` and run it in the ordinary SDK
  environment. Expect a version mismatch before importing ontology. In the RC
  environment require exact distribution versions and all three import origins
  owned by the corresponding distribution, located under the isolated
  environment. Check that no PostgreSQL SDK adapter or duplicate SDK
  distribution is installed.
- [ ] Create a three-entry pip hash lock using the exact PyPI wheel URLs below
  with the SHA-256 values in the design. Record the source commits in comments.
  The Runtime wheel is the same public artifact used by Lab 0.9.16.

  | Package | Source commit | Exact PyPI wheel |
  | --- | --- | --- |
  | Core | `9cab09dc9e802ae066e1187e442c2a12b62175ed` | [0.5.1rc1 wheel][core-wheel] |
  | Harness | `95c366c55d007ac6cc1c1c69da605456e9426678` | [0.9.17rc1 wheel][harness-wheel] |
  | Runtime | `48c10ac9aeb18bd06f53015df0624b35d5254646` | [0.9.23 wheel][runtime-wheel] |

- [ ] Install in a fresh Python 3.12 venv using `pip install --require-hashes
  -r dependencies/requirements.lock`, then `pip install --no-deps
  --require-hashes -r dependencies/catalogue-ontology-rc.lock`. Verify
  `pip check` and rerun the installed identity test with `python -I -m pytest
  -o pythonpath= tests/catalogue_ontology_acceptance/test_installed.py -q` from
  a neutral working directory using the absolute test path. Expect one pass.
  In a separate fresh environment, change one hash in a temporary lock copy
  and expect pip to reject the wheel. Keep the normal five-wheel manifest
  tooling out of this path.

## Task 2 — Copy, discover and run a native workflow

**Modify** `lab_runner/blueprints/__init__.py`, `pyproject.toml`,
`dependencies/public-build-inputs.json` and
`tests/unit/test_blueprint_build_context.py`.
**Create** `lab_runner/blueprints/catalogue_ontology/` with `__init__.py`,
`host.py`, `workflow.yml`, `receipt.schema.json`,
`fixtures/{attachment,visible}.json`, `.prosaic/subagents/{reviewer,private-reviewer}.md`,
`README.md`, `LICENSE` and `NOTICE`. Extend the installed test module from
Task 1.

- [ ] Add `test_copied_catalogue_and_workflow`. Run the installed public copy
  command, then run the copy's CLI in ordinary and ontology modes. First expect
  an unknown blueprint error. After implementation, assert exact equality with
  `fixtures/visible.json` for the added `ontology` field, equality of the
  remaining discovery fields and equality of the curated successful run output.
  Prove a second copy refuses the existing destination. Read the attached
  and unattached workflow fingerprints through the public `Workflow` object.
- [ ] Register `catalogue-ontology` without loading its host code from the
  registry. Include YAML, schema, fixtures, hidden Markdown, README and license
  files in package data and the public snapshot allowlist. Confirm the existing
  `MANIFEST.in` rules cover them. Extend the current stable snapshot test to
  copy this example and exercise `discover` without the attachment. Assert
  `discover --ontology` returns a nonzero exit and names the experimental
  SDK pair. Keep this coverage inside the existing stable test function.
- [ ] Copy the two Core fixture files verbatim from source
  `9cab09dc9e802ae066e1187e442c2a12b62175ed`. Record source and attribution in
  `NOTICE`. The reviewer Markdown declares `read_receipt`. The restricted
  artifact declares `read_policy`. Use the public Core `inspect_artifact`
  and Runtime `ProsaicArtifact.from_inspection` to register them.
- [ ] Implement `build_factory(project: Path, *, attach_ontology: bool = False)
  -> WorkflowFactory` and `build_workflow(project: Path, factory: WorkflowFactory)
  -> Workflow` in the copied host. Pass the attachment via
  `WorkflowCatalog(ontology=load_ontology(...))` when enabled. Probe the
  documented capability at that point so partial upgrades give the same helpful
  error. Bind the fixture read handlers via `WorkflowBindings`, use a
  loopback-only sentinel Runtime profile and grant only `read_receipt` in
  Runtime. Harness policy grants `reviewer`, schema `receipt`, both tool
  aliases in `allowed_tools`, and only `read_receipt` in
  `allowed_direct_tools`. `read_policy` is registered, excluded by Runtime,
  and raises if called. This makes the Runtime filter independently observable.
- [ ] Load trusted `workflow.yml` with `yaml.safe_load` and pass the mapping to
  `factory.build`. Use `version: 1`, `start: read`, a `read` step with
  `kind: tool`, `tool: read_receipt`, `arguments: {}`, `schema: receipt` and
  `next: done`. The `done` step is `kind: finish` and requires `read`. Set
  limits to one call, two visits, five seconds per call, fifteen seconds total,
  4,096 tokens, zero provider requests and one tool call per invocation. Match
  those limits in the host policy.
- [ ] Implement the copied CLI `discover [--ontology]` and
  `run [--ontology]`. The receipt is
  `{"candidateId":"fixture-17","receiptId":"receipt-17","check":"passed"}`.
  Require these three string fields and reject additional keys in the schema.
  Run through `Harness(workflow, run_dir=...).run({})` with an owned temporary
  directory. Print only `{"status":"completed","receipt":{...}}` on success.
  Print the policy-scoped catalogue for discovery. Convert unsupported
  experimental SDK capability to a clear command error.
- [ ] Rebuild the Lab wheel, install it with `--no-deps`, and rerun the installed
  identity and copy tests outside the checkout. Run the existing
  `tests/unit/test_blueprint_build_context.py` against the stable SDKs. Expect
  both installed and stable checks to pass.

## Task 3 — Qualify experimental boundaries and document the example

**Create** `tests/catalogue_ontology_acceptance/test_contract.py`,
`.github/workflows/catalogue-ontology.yml`, and `docs/catalogue-ontology.md`.
**Modify** `README.md`, `docs/feature-blueprints.md`,
`docs/verification/progress.md` and the copied README as needed.

- [ ] Run copied discovery, admission and execution inside an isolated child
  with an audit hook that fails socket and subprocess use. Verify the baseline
  and attached factories have the same `describe()`, `proposal_schema()`,
  workflow fingerprint and curated result. Make the fixture fail if a
  restricted handler is invoked. Assert no private fixture markers appear in
  either public projection or the curated run result.
- [ ] Add tests for explicit opt-in, no visible annotations, a relation with
  only one visible endpoint, unattached concepts and `maximum_bytes` applied
  to the enriched response. Mutate the original attachment object after
  catalogue construction and mutate a returned projection. The next describe
  call must still match the golden fixture.
- [ ] Add rejection tests for malformed JSON, duplicate keys, unknown concepts,
  and unregistered agent/tool aliases. Use the public SDK loader and factory
  directly. Expect invalid documents or `WorkflowAdmissionError` before
  handlers run. Submit ontology at the top level of a proposal and in the graph
  itself, and replace the admitted direct tool with `read_policy`. Assert
  rejection. Also construct a factory where `read_receipt` is discoverable
  but the host grants no direct tools, and assert the authored graph is denied.
- [ ] Add a dispatch-only, read-permission workflow on Ubuntu Python 3.12 with
  two independent cells. Build the checkout wheel in one cell and a wheel
  rebuilt from a clean extracted sdist in the other. Use the existing
  hash-locked build dependencies and a fresh RC consumer venv for each cell.
  Install only the Lab wheel and Task 1's locked dependencies, run `pip check`,
  then run `python -I -m pytest -o pythonpath= <absolute-ontology-tests-path>
  -q --junitxml=<owned-report-path>` from a neutral directory. Missing SDKs,
  missing assets, failures and skips fail the experimental run. Publish only
  the synthetic test summary. Use the pinned Actions revisions already in Lab.
- [ ] Document the separate venv, exact install, copy and both CLI modes. Show
  the two visible concepts and the one relationship. Explain host grants,
  graph authoring and the difference between disclosure and tool authorization.
  Link the Core and Harness RC releases, guide and fixture. Mark the example
  experimental in the README and feature map. Put actual qualification commands
  and results in the verification ledger after they run.
- [ ] Run the installed checks against both build origins, stable local
  `python -m pytest -q`, the stable public snapshot test and `actionlint`.
  Compare both stable manifests, SDK provenance, the existing acceptance
  workflow files and gate counts with the starting commit. Review the full
  diff against the design before handoff.

[core-wheel]: https://files.pythonhosted.org/packages/04/e2/c3557ccc5ef37f2a9a10a037ba5ec534323ff76301c511dbf04dd1670d1f/b3_prosaic-0.5.1rc1-py3-none-any.whl
[harness-wheel]: https://files.pythonhosted.org/packages/1b/17/f143075f18f2db10ffffeac5e504682ebd2da5b4a37179bff9793ae89fc7/b3_prosaic_harness-0.9.17rc1-py3-none-any.whl
[runtime-wheel]: https://files.pythonhosted.org/packages/05/82/31f3cb8cb46da4d72a247f1fb5ee6a2d7fb6b14f12a387ea0e4b95d7129c/b3_prosaic_runtime-0.9.23-py3-none-any.whl
