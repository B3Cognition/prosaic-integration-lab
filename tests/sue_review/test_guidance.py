"""Canonical instructions are restored without changing answer acceptance."""
import ast
from copy import deepcopy
import hashlib
from importlib.resources import files
import json
from types import SimpleNamespace
import uuid

import castle_sue as engine
import pytest
from prosaic_harness import FileRunStore
from prosaic_runtime import EndpointConfig, RuntimeConfig

from tests.sue_review.test_execution import CLAIM, SOURCE, answer, fixture, session


def test_guidance_exactly_matches_pinned_canonical_instruction_blocks():
    from prosaic_integration_lab.sue_review.guidance import CANONICAL_SOURCE_SHA256, INTRODUCTION, ANSWER_RULES
    source=files('castle_sue').joinpath('_vendor/sue/sue_dialectic.py').read_bytes()
    assert hashlib.sha256(source).hexdigest()==CANONICAL_SOURCE_SHA256
    tree=ast.parse(source)
    renderer=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='build_turn_prompt')
    returned=next(node for node in renderer.body if isinstance(node,ast.Return)).value
    assert isinstance(returned,ast.JoinedStr)
    assert INTRODUCTION==returned.values[0].value.split('SPECIFICATION (line-numbered):\n',1)[0].rstrip()
    assert ANSWER_RULES==returned.values[-1].value.lstrip('\n')


def test_all_answer_artifacts_include_bound_canonical_guidance():
    from prosaic_integration_lab.sue_review.guidance import INTRODUCTION, ANSWER_RULES
    from prosaic_integration_lab.sue_review.workflow import build_review_workflow
    from prosaic_integration_lab.sue_review.contracts import ReviewSettings
    config=RuntimeConfig({'fixture':EndpointConfig('http://127.0.0.1:9/v1','sue-fixture')},{},'fixture')
    workflow=build_review_workflow(config=config,settings=ReviewSettings(enabled=True),engine=engine)
    assert len(workflow.artifacts)==14
    for artifact in workflow.artifacts.values():
        assert INTRODUCTION in artifact.body and ANSWER_RULES in artifact.body
        assert 'No Markdown fences.' in artifact.body


def test_guidance_rejects_an_unmatched_canonical_policy():
    from prosaic_integration_lab.sue_review.workflow import build_review_workflow
    from prosaic_integration_lab.sue_review.contracts import ReviewSettings, ReviewError
    caps=deepcopy(engine.capabilities())
    caps['engineIdentity']['files']['_vendor/sue/sue_dialectic.py']='0'*64
    config=RuntimeConfig({'fixture':EndpointConfig('http://127.0.0.1:9/v1','sue-fixture')},{},'fixture')
    with pytest.raises(ReviewError,match='guidance_policy_mismatch'):
        build_review_workflow(config=config,settings=ReviewSettings(enabled=True),engine=SimpleNamespace(capabilities=lambda:caps))


@pytest.mark.parametrize('mutation',['missing_addresses','fenced','false_quote','future_turn','unsupported_claim'])
def test_guidance_does_not_accept_the_failed_live_response_classes(tmp_path,mutation):
    value=answer('DEFINE')
    if mutation=='missing_addresses':value.pop('addresses')
    elif mutation=='false_quote':value['evidence'][0]['quote']='A fabricated source quote.'
    elif mutation=='future_turn':value['addresses']=[1]
    elif mutation=='unsupported_claim':value.update(verdict='CONTRADICTED',test_result='CONFLICT')
    raw='```json\n'+json.dumps(value)+'\n```' if mutation=='fenced' else json.dumps(value)
    with fixture([raw]) as (url,requests),FileRunStore(tmp_path/'runs',namespace='sue-test') as store:
        flow=session(store,url);run_id=uuid.uuid4().hex
        waiting=flow.start(run_id,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}])
        result=flow.resume(run_id,expected_revision=waiting['revision'],choice='continue')
        assert result['status']=='blocked' and result['acceptedTurns']==0
        assert len(requests)==2 and store.load_run(run_id).state['outputs']=={}
        assert flow.report(run_id)['reportedTokens']==30

