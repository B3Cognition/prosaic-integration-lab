"""Exercise the copied host in an isolated consumer using real HTTP."""
import importlib.util
import os

import pytest


@pytest.fixture
def copied_host(tmp_path):
    if os.environ.get("PROSAIC_MCP_CLIENT_REQUIRED") != "1":
        pytest.skip("MCP candidate consumer lane")
    from lab_runner.blueprints import copy_blueprint
    from prosaic_integration_lab.mcp_client import require_mcp_client_sdk

    require_mcp_client_sdk()
    root = copy_blueprint("mcp-client", tmp_path / "graph")
    spec = importlib.util.spec_from_file_location("copied_graph_host", root / "host.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (root / "NOTICE").is_file() and (root / "LICENSE").is_file()
    return module


@pytest.mark.parametrize("case", ["approved-structured", "scope-denial"])
def test_copied_mcp_host(copied_host, case):
    from prosaic_runtime import ToolClaim
    from prosaic_integration_lab.mcp_client import run_case

    class Journal:
        contract_version = "tool-journal-v1"
        version = "1"
        identity = "copied-host"

        def claim(self, _namespace, _key, signature):
            return ToolClaim("new", signature, "token")

        def commit(self, _namespace, _key, token, _outcome):
            assert token == "token"

    report = run_case(case, "openai-compatible", journal=Journal(), build_host=copied_host.build_host)
    assert report["toolPosts"] == int(case == "approved-structured")
