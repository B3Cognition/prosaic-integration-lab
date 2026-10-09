import json
import pytest
from prosaic_integration_lab.views import public_run
from prosaic_integration_lab.execution import Execution
from fastapi import HTTPException

def state(output):
    return {'status':'waiting','current':'approval','choices':['approve','reject'],
        'outputs':{'author':output},'inputs':{'task':'PRIVATE'},'history':[{'private':'PRIVATE'}],
        'question':'PRIVATE'}

def test_approved_result_has_explicit_review_revision_and_no_private_state():
    projected = public_run('run',state({'result':'<script>fixture</script>'}),'revision',workflow='synthetic')
    assert projected['review'] == {'revision':'revision','question':'Approve this fixture output?',
        'result':{'result':'<script>fixture</script>'}}
    assert 'PRIVATE' not in json.dumps(projected)

@pytest.mark.parametrize('output',[{'result':7},{'result':'x'*257},{'result':'ok','secret':'PRIVATE'},None])
def test_invalid_result_cannot_present_an_approval_choice(output):
    projected = public_run('run',state(output),'revision',workflow='synthetic')
    assert projected['choices'] == []
    assert projected['review'] is None

def test_unknown_workflow_does_not_project_output():
    assert 'review' not in public_run('run',state({'result':'private'}),'rev',workflow='unknown')

def test_missing_review_blocks_sdk_approval_before_resume():
    execution = object.__new__(Execution)
    execution.status = lambda reservation: {'status':'waiting','review':None}
    def forbidden(reservation): raise AssertionError('SDK must not receive approval')
    execution.harness = forbidden
    with pytest.raises(HTTPException) as error:
        execution.resume({},'revision','approve',False)
    assert error.value.status_code == 409
    assert error.value.detail == 'approval_view_unavailable'
