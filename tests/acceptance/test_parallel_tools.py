"""32 required witnesses using installed SDKs and owned restricted-role storage."""
import uuid
import pytest
from prosaic_integration_lab.parallel_tools import CASES,run_case,require_parallel_tool_sdk

@pytest.mark.parametrize('provider',['openai-compatible','anthropic'])
@pytest.mark.parametrize('case',CASES)
def test_parallel_tools(lab,case,provider):
    from prosaic_harness_postgres import PostgresSessionStore
    from prosaic_integration_lab.tool_journal import PgToolJournal
    require_parallel_tool_sdk()
    with PostgresSessionStore(lab['conversation']['dsn'],namespace='parallel-'+uuid.uuid4().hex) as store:
        store.check_ready();assert 'parallel_tool_calls_v1' in store.capabilities
        report=run_case(case,provider,settings=dict(session_store=store,journal=PgToolJournal(lab['app_dsn'],identity='parallel-'+uuid.uuid4().hex),session_dsn=lab['conversation']['dsn']))
        assert report['passed']
