"""Copy the blueprint and run it using only installed SDK entry points."""
import importlib.util
import os

import pytest


@pytest.mark.parametrize("provider", ["openai-compatible", "anthropic"])
@pytest.mark.parametrize("case", ["siblings", "scope-and-citations"])
def test_copied_sub_agent_host(tmp_path, provider, case):
    if os.environ.get("PROSAIC_SUB_AGENTS_REQUIRED") != "1":
        pytest.skip("delegation candidate lane")
    from lab_runner.blueprints import copy_blueprint
    from prosaic_harness import MemorySessionStore
    from prosaic_runtime import ToolClaim
    from prosaic_runtime.accounting import MemoryRecorder
    from prosaic_integration_lab.sub_agents import require_sub_agent_sdk, run_case

    require_sub_agent_sdk()
    root = copy_blueprint("sub-agents", tmp_path / "graph")
    spec = importlib.util.spec_from_file_location("copied_delegate_host", root / "host.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (root / "NOTICE").is_file() and (root / "LICENSE").is_file()

    class Journal:
        contract_version = "tool-journal-v1"
        identity = "copied-host"
        version = "1"

        def claim(self, _namespace, _key, signature):
            return ToolClaim("new", signature, "token")

        def commit(self, _namespace, _key, token, _outcome):
            assert token == "token"

    store = MemorySessionStore(namespace="copied-host")
    store.initialize(sub_agents=True)
    run_case(case, provider, journal=Journal(), store=store, recorder=MemoryRecorder(provider_id=provider),
             build_host=module.build_host)
