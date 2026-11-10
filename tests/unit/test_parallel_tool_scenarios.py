import json
import pytest
from prosaic_integration_lab.parallel_tools import CASES,run_case,require_parallel_tool_sdk

@pytest.mark.parametrize('provider',['openai-compatible','anthropic'])
@pytest.mark.parametrize('case',CASES)
def test_parallel_public_scenario(case,provider):
    from tool_evidence_fixture import Journal
    report=run_case(case,provider,settings={'journal':Journal()})
    assert report['passed'] and report['case']==case
    assert 'PRIVATE' not in json.dumps(report)


import os,pytest
@pytest.fixture(autouse=True)
def require_candidate_sdk():
    from prosaic_integration_lab.parallel_tools import require_parallel_tool_sdk
    try:require_parallel_tool_sdk()
    except (ImportError,ValueError):
        if os.environ.get('PROSAIC_PARALLEL_TOOLS_REQUIRED')=='1':pytest.fail('parallel candidate SDK required')
        pytest.skip('parallel candidate SDK environment required')


def test_journal_namespace_isolated_between_scenario_runs():
    from tool_evidence_fixture import Journal
    journal=Journal()
    assert run_case('uncertain-journal','openai-compatible',settings={'journal':journal})['passed']
    assert run_case('same-key-replay','anthropic',settings={'journal':journal})['passed']
