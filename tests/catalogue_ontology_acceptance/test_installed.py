"""Installed acceptance for the isolated catalogue ontology SDK family."""

from importlib import import_module, metadata
import json
from pathlib import Path
import runpy
import subprocess
import sys

from packaging.utils import canonicalize_name


SDK = {
    "b3-prosaic": ("0.5.1rc1", "prosaic"),
    "b3-prosaic-harness": ("0.9.17rc1", "prosaic_harness"),
    "b3-prosaic-runtime": ("0.9.23", "prosaic_runtime"),
}


def test_exact_installed_sdk_payloads():
    expected = {name: version for name, (version, _) in SDK.items()}
    assert {name: metadata.version(name) for name in SDK} == expected

    names = set(SDK) | {"b3-prosaic-harness-postgres", "b3-prosaic-runtime-postgres"}
    sdk_names = names | {name.removeprefix("b3-") for name in names}
    installed = [
        canonicalize_name(dist.metadata["Name"])
        for dist in metadata.distributions()
        if canonicalize_name(dist.metadata["Name"]) in sdk_names
    ]
    assert sorted(installed) == sorted(SDK)

    assert sys.prefix != sys.base_prefix
    prefix = Path(sys.prefix).resolve()
    for name, (_, module) in SDK.items():
        distribution = metadata.distribution(name)
        origin = Path(import_module(module).__file__).resolve()
        assert origin.is_relative_to(prefix)
        assert any(Path(file.locate()).resolve() == origin for file in distribution.files)


def test_copied_catalogue_and_workflow(copied_blueprint, copy_command):
    project = copied_blueprint
    assert {"README.md", "LICENSE", "NOTICE", "workflow.yml", "receipt.schema.json"} <= {
        path.name for path in project.iterdir()
    }
    listed = copy_command("list")
    assert listed.returncode == 0, listed.stderr
    assert "catalogue-ontology" in listed.stdout.splitlines()

    def command(*args):
        result = subprocess.run(
            [sys.executable, "-I", str(project / "host.py"), *args],
            cwd=project.parent, capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    ordinary = command("discover")
    enriched = command("discover", "--ontology")
    assert enriched.pop("ontology") == json.loads((project / "fixtures/visible.json").read_bytes())
    assert enriched == ordinary
    assert command("run", "--ontology") == command("run") == {
        "status": "completed",
        "receipt": {"candidateId": "fixture-17", "receiptId": "receipt-17", "check": "passed"},
    }

    host = runpy.run_path(str(project / "host.py"))
    baseline = host["build_factory"](project)
    attached = host["build_factory"](project, attach_ontology=True)
    assert host["build_workflow"](project, baseline).fingerprint == host["build_workflow"](
        project, attached,
    ).fingerprint

    original = (project / "workflow.yml").read_bytes()
    duplicate = copy_command("copy", "catalogue-ontology", str(project))
    assert duplicate.returncode != 0
    assert (project / "workflow.yml").read_bytes() == original
