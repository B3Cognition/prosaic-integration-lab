import json
import pytest
from prosaic_integration_lab.tool_evidence import CASES,run_tool_evidence_scenario,require_tool_evidence_sdk

try:
    require_tool_evidence_sdk();available=True
except (ImportError,ValueError):available=False
pytestmark=pytest.mark.skipif(not available,reason="explicit tool-contract candidate SDK environment required")


@pytest.mark.parametrize('provider',['openai-compatible','anthropic'])
@pytest.mark.parametrize('case',CASES)
def test_public_sdk_scenario(case,provider):
    from tool_evidence_fixture import Journal
    report=run_tool_evidence_scenario(case,provider=provider,journal=Journal())
    assert report['passed'] is True and report['case']==case and report['provider']==provider
    assert 'PRIVATE' not in json.dumps(report) and 'locator' not in json.dumps(report)
