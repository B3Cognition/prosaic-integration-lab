from copy import deepcopy

import pytest
from prosaic_harness import Harness
from prosaic_runtime import EndpointConfig, RuntimeConfig
from lab_runner.requirements_review_v1.fixtures import provider
from lab_runner.requirements_review_v1.cases import load_cases,public_task
from lab_runner.requirements_review_v1.host_keys import load_keys,fixture_answer


@pytest.mark.parametrize('correct_retry',[True,False])
def test_inconsistent_context_result_retries_without_rewriting_or_discarding_usage(tmp_path,correct_retry):
    from lab_runner.requirements_review_v3 import build_comparison_workflow
    case=load_cases()['requirements-06'];good=fixture_answer(case,load_keys()[case['caseId']])
    bad={**deepcopy(good),'assessment':'ISSUES_FOUND'}
    with provider([bad,good if correct_retry else bad]) as (url,rows):
        config=RuntimeConfig({'x':EndpointConfig(url,'requirements-fixture-v1',features={'streaming':False})},{},'x')
        h=Harness(build_comparison_workflow(config,'direct'),tmp_path/'run')
        h.run({'publicTask':public_task(case),'strategyAdvice':None})
        state=h.status().state
        assert len(rows)==2 and len(state['invocations'])==2
        assert sum(i['token_usage'] for i in state['invocations'])==30
        assert state['status']==('completed' if correct_retry else 'blocked')
        assert state['outputs']==({'final':good} if correct_retry else {})
        evidence=h.recovery_evidence(maximum_bytes=16777216)
        assert 'ISSUES_FOUND' in evidence['receipts'][0]['result']['stdout']
        h.resume()
        assert len(rows)==2
