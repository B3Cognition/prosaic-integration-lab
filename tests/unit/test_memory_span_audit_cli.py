"""Explicit synthetic audit command; default CLI still executes nothing."""
import json
from pathlib import Path
import subprocess
import sys

import pytest


def cli(*args):
    return subprocess.run([sys.executable, '-m', 'lab_runner.memory_benchmark', *map(str,args)],
                          capture_output=True,text=True,timeout=30)


def test_default_cli_does_not_enable_memory_review_or_audit():
    result=cli()
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)=={'enabled':False,'executed':False,'version':'memory-benchmark-v1'}


@pytest.mark.parametrize(('case','outcome','requests','held'),[
    ('omitted','findings',2,0),('complete','clear',2,0),('unavailable','clear',2,0),('unknown-usage','unresolved',1,65536)])
def test_explicit_fixture_checks_native_audit_without_real_inference(tmp_path,case,outcome,requests,held):
    result=cli('audit-fixture','--case',case,'--output',tmp_path/'audit')
    assert result.returncode==0,result.stderr
    summary=json.loads(result.stdout)
    assert summary['outcome']==outcome
    assert summary['syntheticProviderRequests']==requests
    assert summary['realModelCalls']==0
    assert summary['retainedTokens']==held
    assert summary['memoryDefault'] is False and summary['sueDefault'] is False
    assert summary['originalUnchanged'] is True
    assert summary['resumeProviderRequests']==0


def test_fixture_refuses_real_config_and_automatic_repair(tmp_path):
    for option in ['--config','--repair']:
        result=cli('audit-fixture','--output',tmp_path/'no-run',option)
        assert result.returncode==2
        assert not (tmp_path/'no-run').exists()
