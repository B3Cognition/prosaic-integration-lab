from pathlib import Path
import pytest
import yaml
from prosaic_integration_lab.execution import validate_workflow_limits
from prosaic_integration_lab.views import public_run

@pytest.mark.parametrize('workflow',['approval','synthetic'])
def test_shipped_http_workflow_has_finite_call_token_and_duration_policy(workflow):
    definition = yaml.safe_load((Path(__file__).resolve().parents[2]/'assets'/(workflow+'.yml')).read_text())
    validate_workflow_limits(definition)

@pytest.mark.parametrize('limits',[{'max_calls':3,'max_run_s':120},
    {'max_calls':3,'max_tokens':None,'max_run_s':120},
    {'max_calls':3,'max_tokens':True,'max_run_s':120},
    {'max_calls':4,'max_tokens':300,'max_run_s':120},
    {'max_calls':3,'max_tokens':300,'max_run_s':float('inf')}])
def test_unbounded_workflow_policy_is_rejected_before_resource_construction(limits):
    with pytest.raises(ValueError): validate_workflow_limits({'limits':limits})

@pytest.mark.parametrize('reason,expected',[('usage_unknown','usage_reconciliation_required'),
    ('token_limit','budget_exhausted')])
def test_public_budget_block_reason_is_curated_without_private_state(reason,expected):
    result = public_run('run',{'status':'blocked','current':'author','reason':reason,'inputs':{'task':'PRIVATE'}},'r')
    assert result['recovery_status'] == expected
    assert 'PRIVATE' not in str(result)
