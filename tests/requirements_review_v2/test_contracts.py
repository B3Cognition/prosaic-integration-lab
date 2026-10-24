"""Stage-specific wire contracts; frozen v1 remains a historical control."""
from copy import deepcopy
import json

import pytest
from prosaic_harness import Harness
from prosaic_runtime import EndpointConfig, RuntimeConfig, Result, ProsaicArtifact
from lab_runner.requirements_review_v1.cases import load_cases, public_task
from lab_runner.requirements_review_v1.contracts import CRITIC_SCHEMA, FINAL_SCHEMA, LIMITS
from lab_runner.requirements_review_v1.fixtures import provider
from lab_runner.requirements_review_v1.host_keys import load_keys, fixture_answer


def task():return public_task(load_cases()['requirements-01'])


def test_critic_projection_has_one_output_schema_and_preserves_frozen_sources():
    from lab_runner.requirements_review_v2 import project_stage_arguments
    original={'request':{'publicTask':task(),'strategyAdvice':None},'artifacts':{}}
    before=deepcopy(original);seen=[]
    def execute(raw,**options):
        seen.append((json.loads(raw),options));return Result(0,'{"feedback":"Inspect the source."}','')
    artifact=ProsaicArtifact('requirements-v1/critic','subagent',{'name':'critic','tools':[]},'A critic.')
    project_stage_arguments(artifact,json.dumps(original),execute=execute)
    projected=seen[0][0]['request']['publicTask']
    assert projected['responseSchema']==CRITIC_SCHEMA
    assert projected['responseSchema']!=FINAL_SCHEMA
    assert 'Return only responseSchema JSON.' in projected['instructions']
    assert 'Use INSUFFICIENT_CONTEXT' not in projected['instructions']
    for key in ('evidence','caseId','claim','issueDefinitions','suiteVersion','title'):
        assert projected[key]==original['request']['publicTask'][key]
    assert original==before and len(seen)==1
    assert seen[0][1]['allowed_tools']==frozenset()


def test_direct_wire_prompt_is_identical_to_frozen_v1(tmp_path):
    from lab_runner.requirements_review_v2 import build_comparison_workflow
    from lab_runner.requirements_review_v1.execution import _workflow
    case=load_cases()['requirements-01'];final=fixture_answer(case,load_keys()[case['caseId']])
    wires=[]
    for index,build in enumerate((_workflow,build_comparison_workflow)):
        with provider([final]) as (url,rows):
            config=RuntimeConfig({'fixture':EndpointConfig(url,'requirements-fixture-v1',features={'streaming':False})},{},'fixture')
            harness=Harness(build(config,'direct',LIMITS),tmp_path/str(index));harness.run({'publicTask':task(),'strategyAdvice':None})
            assert harness.status().state['status']=='completed'
            assert len(rows)==1
            wires.append(rows[0]['request']['messages'])
    assert wires[0]==wires[1]


@pytest.mark.parametrize('wrong_schema',[False,True])
def test_real_critic_wire_and_strict_feedback_acceptance(wrong_schema,tmp_path):
    from lab_runner.requirements_review_v2 import build_comparison_workflow
    case=load_cases()['requirements-01'];final=fixture_answer(case,load_keys()[case['caseId']])
    values=[final] if wrong_schema else [{'feedback':'The two timing requirements conflict.'},final]
    with provider(values) as (url,rows):
        config=RuntimeConfig({'fixture':EndpointConfig(url,'requirements-fixture-v1',features={'streaming':False})},{},'fixture')
        harness=Harness(build_comparison_workflow(config,'critic_author',LIMITS),tmp_path/'run')
        harness.run({'publicTask':task(),'strategyAdvice':None});state=harness.status().state
        assert len(rows)==2
        for row in rows[:2 if wrong_schema else 1]:
            raw=row['request']['messages'][0]['content'].split('\nTask arguments:\n',1)[1]
            assert json.loads(raw)['request']['publicTask']['responseSchema']==CRITIC_SCHEMA
        if wrong_schema:
            assert state['status']=='blocked' and state['outputs']=={}
        else:
            assert state['status']=='completed' and state['outputs']['final']==final

