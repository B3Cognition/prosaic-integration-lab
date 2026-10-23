"""Installed image/host smoke: disabled memory has no optional side effects."""

import builtins
from importlib import metadata
import json
from pathlib import Path
import subprocess


def main():
    from prosaic_runtime import ProsaicRuntime

    assert "custom_tool_errors_v1" in ProsaicRuntime.capabilities
    assert "site-packages" in str(
        Path(__import__("prosaic_integration_lab").__file__).resolve()
    )
    for package, distribution in [
        ("prosaic", "b3-prosaic"),
        ("prosaic_runtime", "b3-prosaic-runtime"),
        ("prosaic_harness", "b3-prosaic-harness"),
        ("prosaic_memory_castle", "b3-prosaic-memory-castle"),
    ]:
        assert metadata.packages_distributions()[package] == [distribution]
    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name.split(".")[0] in {
            "prosaic_memory_castle",
            "cognitive_castle",
            "torch",
            "spacy",
        }:
            raise AssertionError("disabled memory imported an optional provider")
        return original(name, *args, **kwargs)

    def no_process(*args, **kwargs):
        raise AssertionError("disabled memory started a process")

    builtins.__import__ = guarded
    subprocess.Popen = no_process
    from prosaic_integration_lab.memory_provider import MemoryProviders
    from prosaic_integration_lab.identity import Principal
    from lab_runner.memory import main as memory_main

    provider = MemoryProviders()
    assert (
        provider.capture(Principal("tenant", "actor", "payer"), "fixture")["status"]
        == "disabled"
    )
    provider.close()
    assert memory_main([]) == 0
    print(
        json.dumps(
            {
                "installed_memory_consumer": True,
                "default_disabled": True,
                "no_optional_imports_or_worker": True,
            }
        )
    )


if __name__ == "__main__":
    main()
