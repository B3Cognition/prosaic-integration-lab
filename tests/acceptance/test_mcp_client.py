"""MCP witnesses against installed SDKs and owned PostgreSQL storage."""
import uuid

import pytest

from prosaic_integration_lab.mcp_client import CASES, require_mcp_client_sdk, run_case


@pytest.mark.parametrize("provider", ["openai-compatible", "anthropic"])
@pytest.mark.parametrize("case", CASES)
def test_mcp_client(lab, case, provider):
    from prosaic_harness_postgres import PostgresSessionStore
    from prosaic_integration_lab.tool_journal import PgToolJournal

    require_mcp_client_sdk()
    namespace = "mcp-" + uuid.uuid4().hex
    with PostgresSessionStore(lab["conversation"]["dsn"], namespace=namespace) as store:
        store.check_ready()
        journal = PgToolJournal(lab["app_dsn"], identity=namespace)
        assert run_case(case, provider, journal=journal, store=store)["passed"]
