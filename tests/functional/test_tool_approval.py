"""A scripted model may claim approval; only host consent reaches a handler."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('scenario',['approved','unicode','pending','denied','revoked','expired',
    'changed','injected','forged_tool','duplicate','wrong_scope','wrong_version'])
def test_public_runtime_enforces_host_approval_without_model_authority(tmp_path,provider,scenario):
    assert importlib.util.find_spec('lab_runner.tool_approval_fixture'),'approval wire fixture missing'
    from lab_runner.tool_approval_fixture import qualify
    report=qualify(tmp_path,provider=provider,scenario=scenario)
    assert report['effects']==(1 if scenario in ('approved','unicode','duplicate') else 0)
    assert report['providerRequests']<=4 and report['toolCalls']<=2
    assert report['reportedTokens']<=8192 and report['elapsedSeconds']<600
    assert report['networkDeniedRecovery']
    assert report['state']==('spent' if report['effects'] else scenario if scenario in ('pending','denied','revoked') else 'approved')
    assert not report['providerErrors']


def test_installed_smoke_refuses_source_imports(tmp_path):
    script=Path(__file__).resolve().parents[2]/'scripts/tool_approval_smoke.py'
    assert script.is_file(),'installed approval smoke missing'
    result=subprocess.run([sys.executable,str(script),'--source-root',str(script.parent.parent),
                           '--evidence-dir',str(tmp_path/'evidence'),'--output',str(tmp_path/'result.json')],
        capture_output=True,text=True,env=dict(os.environ,PYTHONPATH=str(script.parent.parent)))
    assert result.returncode!=0 and 'installed package required' in result.stderr
