"""Installed acceptance for the isolated catalogue ontology SDK family."""

from importlib import import_module, metadata
from pathlib import Path
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
