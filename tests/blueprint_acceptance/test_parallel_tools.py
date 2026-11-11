from pathlib import Path
import runpy
from lab_runner.blueprints import copy_blueprint


def test_parallel_copy_is_complete_and_uses_public_sdk(tmp_path):
    project=copy_blueprint('parallel-tools',tmp_path/'consumer')
    assert {str(p.relative_to(project)) for p in project.rglob('*') if p.is_file()}=={'__init__.py','host.py','README.md','LICENSE','NOTICE','runtime.yml','.prosaic/subagents/analyst.md'}
    text=(project/'host.py').read_text();assert 'prosaic_runtime.' not in text and 'ThreadPool' not in text
    host=runpy.run_path(str(project/'host.py'))
    binding=host['build_host'](base_url='http://127.0.0.1:1/v1',provider='anthropic',lookup=lambda a,c:14)
    assert binding.run_policy.parallel_tools.max_concurrency==2
    assert binding._tools['lookup'].parallel_read


import os,pytest
@pytest.fixture(autouse=True)
def require_candidate_sdk():
    from prosaic_integration_lab.parallel_tools import require_parallel_tool_sdk
    try:require_parallel_tool_sdk()
    except (ImportError,ValueError):
        if os.environ.get('PROSAIC_PARALLEL_TOOLS_REQUIRED')=='1':pytest.fail('parallel candidate SDK required')
        pytest.skip('parallel candidate SDK environment required')
