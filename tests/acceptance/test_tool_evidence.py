"""24 required cases against installed SDKs and owned restricted-role storage."""
import uuid
import pytest
from prosaic_integration_lab.tool_evidence import CASES,run_tool_evidence_scenario,require_tool_evidence_sdk


@pytest.mark.parametrize('provider',['openai-compatible','anthropic'])
@pytest.mark.parametrize('case',CASES)
def test_tool_evidence(lab,case,provider):
    from prosaic_harness_postgres import PostgresSessionStore
    from prosaic_integration_lab.tool_journal import PgToolJournal
    require_tool_evidence_sdk()
    with PostgresSessionStore(lab['conversation']['dsn'],namespace='tools-'+uuid.uuid4().hex) as store:
        store.check_ready();assert 'tool_contracts_v1' in store.capabilities
        report=run_tool_evidence_scenario(case,provider=provider,session_store=store,
            journal=PgToolJournal(lab['app_dsn'],identity='tools-'+uuid.uuid4().hex))
        assert report['passed'] is True
