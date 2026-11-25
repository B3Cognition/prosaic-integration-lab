"""Owned PostgreSQL witnesses on both supported provider wires."""
from uuid import uuid4

import pytest

from prosaic_integration_lab.sub_agents import CASES, require_sub_agent_sdk, run_case


@pytest.mark.parametrize("provider", ["openai-compatible", "anthropic"])
@pytest.mark.parametrize("case", CASES)
def test_sub_agents(lab, case, provider):
    from prosaic_harness_postgres import PostgresRunStore, PostgresSessionStore
    from prosaic_runtime_postgres import PostgresRecorder
    from prosaic_integration_lab.tool_journal import PgToolJournal

    require_sub_agent_sdk()
    namespace = "delegation-" + uuid4().hex
    recorder = PostgresRecorder(lab["accounting_dsn"], namespace=namespace, environment="sandbox",
                               provider_id=provider)
    with PostgresSessionStore(lab["conversation"]["dsn"], namespace=namespace) as store, \
            PostgresRunStore(lab["harness_dsn"], namespace=namespace) as run_store:
        assert "sub_agents_v1" in store.capabilities and "sub_agents_v1" in run_store.capabilities
        run_case(case, provider, journal=PgToolJournal(lab["app_dsn"], identity=namespace),
                 store=store, recorder=recorder, run_store=run_store)
