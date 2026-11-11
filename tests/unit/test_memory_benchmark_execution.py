"""An explicit longer run never silently raises legacy or reduced grants."""
import pytest

from lab_runner.memory_benchmark.dataset import freeze, load_frozen
from lab_runner.memory_benchmark.__main__ import initialize, main

PROFILE='bounded-120s-v1'


def test_execution_profile_freezes_only_when_explicit_and_cli_rejects_mixed_mode(tmp_path):
    initialize(tmp_path/'inputs',1)
    legacy=tmp_path/'legacy'
    freeze(tmp_path/'inputs/dataset.json',tmp_path/'inputs/policy.json',legacy)
    assert 'executionProfile' not in load_frozen(legacy)
    output=tmp_path/'long'
    assert main(['freeze','--dataset',str(tmp_path/'inputs/dataset.json'),'--policy',str(tmp_path/'inputs/policy.json'),
        '--execution-profile',PROFILE,'--output',str(output)])==0
    assert load_frozen(output)['executionProfile']==PROFILE
    assert main(['validate','--frozen',str(output),'--execution-profile',PROFILE])==2
    with pytest.raises(ValueError):
        freeze(tmp_path/'inputs/dataset.json',tmp_path/'inputs/policy.json',tmp_path/'invalid',execution_profile='unbounded')
    assert not (tmp_path/'invalid').exists()


def test_explicit_stage_reductions_stay_reductions_and_invalid_bounds_fail():
    from lab_runner.memory_benchmark import execution as e
    assert e.stage_seconds(e.DEFAULT_ELAPSED,PROFILE,'answer')==150
    assert e.stage_seconds(e.DEFAULT_ELAPSED,PROFILE,'review')==270
    assert e.stage_seconds(120,PROFILE,'review')==120
    for value in (True,None,0,271,float('inf')):
        with pytest.raises(ValueError):e.stage_seconds(value,PROFILE,'review')
    for profile in (True,None,'other'):
        with pytest.raises(ValueError):e.limits(profile)
    with pytest.raises(ValueError):e.stage_seconds(1,PROFILE,'unknown')
