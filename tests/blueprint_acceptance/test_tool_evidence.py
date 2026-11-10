"""The copied host is self-contained and only imports public SDK APIs."""
import json,runpy
from pathlib import Path
import pytest
from lab_runner.blueprints import copy_blueprint
from prosaic_integration_lab.tool_evidence import require_tool_evidence_sdk

@pytest.fixture(autouse=True)
def supported_sdk():
    import os
    try:require_tool_evidence_sdk()
    except (ImportError,ValueError):
        if os.environ.get("PROSAIC_TOOL_EVIDENCE_REQUIRED")=="1":pytest.fail("candidate capability missing")
        pytest.skip("tool-contract candidates required")


def test_complete_copy_contains_only_declared_public_resources(tmp_path):
    project=copy_blueprint('tool-evidence',tmp_path/'consumer')
    assert {str(path.relative_to(project)) for path in project.rglob('*') if path.is_file()}=={
        '__init__.py','host.py','README.md','LICENSE','NOTICE','runtime.yml','.prosaic/subagents/analyst.md'}
    host=runpy.run_path(str(project/'host.py'))
    calls=[];tool=host['dependents_tool'](lambda component:calls.append(component) or [{'name':str(i)} for i in range(14)])
    result=tool.handler({'component':'csb-frontend'})
    assert result.data['count']==14 and calls==['csb-frontend']
    assert 'PRIVATE-LOCATOR' not in json.dumps(result.data)
    with pytest.raises(FileExistsError):copy_blueprint('tool-evidence',project)


def test_copy_forwards_only_sdk_safe_tool_events(tmp_path):
    host=runpy.run_path(str(copy_blueprint('tool-evidence',tmp_path/'consumer')/'host.py'))
    events=[]
    host['forward_event']({'event':'tool_started','name':'dependents','toolEventV1':{'version':1}},events.append)
    host['forward_event']({'event':'telemetry','arguments':{'private':True}},events.append)
    assert len(events)==1 and 'arguments' not in events[0]
