# Experimental catalogue ontology

The `catalogue-ontology` blueprint shows how a host attaches public concepts
and relationships to the aliases it already registers. It uses the published
Core 0.5.1rc1, Harness 0.9.17rc1 and Runtime 0.9.23 wheels in a separate
environment. The stable Lab release uses its usual SDK manifest.

## Install and copy

From the Lab checkout containing this example, use Python 3.12 and a fresh
environment. The setup downloads wheels. The copied commands run offline.

```sh
lab_ontology_dir=$(mktemp -d)
python3.12 -m venv "$lab_ontology_dir/venv"
lab_ontology_python="$lab_ontology_dir/venv/bin/python"

"$lab_ontology_python" -m pip install --require-hashes \
  -r dependencies/requirements.lock -r dependencies/rule-admission-build.lock
"$lab_ontology_python" -m pip install --no-deps --require-hashes \
  -r dependencies/catalogue-ontology-rc.lock
"$lab_ontology_python" -m build --no-isolation --wheel --outdir "$lab_ontology_dir/dist"
"$lab_ontology_python" -m pip install --no-deps "$lab_ontology_dir"/dist/*.whl
"$lab_ontology_python" -m pip check
"$lab_ontology_python" -I -m lab_runner.blueprints copy catalogue-ontology "$lab_ontology_dir/example"
```

## Inspect and run

```sh
"$lab_ontology_python" "$lab_ontology_dir/example/host.py" discover
"$lab_ontology_python" "$lab_ontology_dir/example/host.py" discover --ontology
"$lab_ontology_python" "$lab_ontology_dir/example/host.py" run
"$lab_ontology_python" "$lab_ontology_dir/example/host.py" run --ontology
```

The enriched response adds `ontology` with `candidate` and `receipt` and the
relation `receipt verifies candidate`. Harness selects annotated agents through
the workflow policy. It selects tools through both the workflow policy and the
Runtime tool grants. Relations are visible when both endpoints are visible.
Ordinary discovery and the proposal schema are identical with and without
the attachment.

The copied [host](../lab_runner/blueprints/catalogue_ontology/host.py) loads
`fixtures/attachment.json` through Core and registers it with
`WorkflowCatalog(ontology=...)`. It passes the authored
[native YAML graph](../lab_runner/blueprints/catalogue_ontology/workflow.yml) to
`WorkflowFactory.build`. Keep metadata in the host attachment and place
execution steps in the graph. Direct tool calls require a host grant even when
the alias is discoverable.

Both runs use the same workflow fingerprint and return this fixture result.

```json
{
  "receipt": {"candidateId": "fixture-17", "check": "passed", "receiptId": "receipt-17"},
  "status": "completed"
}
```

The example uses temporary file storage and one local synthetic tool call.
The tool checks no real release and performs zero provider requests.

## Verify the installed example

From the Lab checkout, run the installed suite with the RC environment above.

```sh
lab_ontology_tests="$PWD/tests/catalogue_ontology_acceptance"
(cd "$lab_ontology_dir" && "$lab_ontology_python" -I -m pytest -o pythonpath= -q "$lab_ontology_tests")
```

The dispatch-only [Experimental catalogue ontology workflow](../.github/workflows/catalogue-ontology.yml)
checks both the checkout wheel and a wheel rebuilt from the sdist. Tests copy
the installed blueprint, exercise projection and admission, and prove that the
workflow runs with sockets and subprocesses disabled.

See the [Core attachment format](https://github.com/B3Cognition/prosaic/blob/v0.5.1rc1/docs/catalogue-ontology.md),
[shared fixture](https://github.com/B3Cognition/prosaic/tree/v0.5.1rc1/conformance-fixtures/catalogue-ontology)
and [Harness prerelease](https://github.com/B3Cognition/prosaic-harness/releases/tag/v0.9.17rc1).
