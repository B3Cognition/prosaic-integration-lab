"""Generation context is advisory; canonical acceptance still owns grounding."""
from copy import deepcopy
import json
from types import SimpleNamespace
import uuid

import castle_sue as engine
import pytest
from prosaic_runtime import Result, ProsaicRuntime
from prosaic_harness import FileRunStore

from prosaic_integration_lab.sue_review.contracts import encoded
from prosaic_integration_lab.sue_review.workflow import project_answer
from tests.sue_review.test_execution import CLAIM, SOURCE, answer, fixture, session
from prosaic_integration_lab.sue_review.sources import freeze_documents


def request():
    return {'seed': CLAIM, 'lens': 'euthyphro', 'maxTurns': 14,
            'engine': engine.capabilities(), 'evidence': freeze_documents([{'sourceId':'spec','text':SOURCE}])}


def project(artifacts, step, *, constrained=True):
    calls=[]
    def execute(raw, **kw):
        calls.append((json.loads(raw), kw))
        return Result(exit_code=0, stdout=json.dumps(answer('DEFINE')), stderr='')
    project_answer(SimpleNamespace(id=step), encoded({'request':request(),'artifacts':artifacts,
                   'validation_feedback':'sue_answer_invalid'}).decode(), execute=execute,
                   engine=engine, constrained_json=constrained)
    assert len(calls)==1
    return calls[0]


def test_constrained_projection_separates_source_lines_from_accepted_turn_ids():
    from prosaic_integration_lab.sue_review.contracts import digest
    from prosaic_integration_lab.sue_review.generation import generation_schema
    data, options=project({}, 'sue/answer-01')
    assert data['groundingContext']=={'sourceLineNumbers':[1,2], 'priorTurnNumbers':[]}
    assert data['validationFeedback']=='sue_answer_invalid'
    initial=engine.initial_state(CLAIM)
    assert data['responseSchema']==engine.schema(initial)
    assert options['response_schema']==generation_schema(initial,engine.schema(initial),2)
    value=answer('DEFINE'); state, failure=engine.advance(initial,value,SOURCE.splitlines())
    assert failure is None
    accepted={'answer-01':{'rawResponse':json.dumps(value),'terminal':state['terminal'],'stateSha256':digest(state)}}
    data, options=project(accepted, 'sue/answer-02')
    assert data['groundingContext']=={'sourceLineNumbers':[1,2], 'priorTurnNumbers':[1]}
    assert data['responseSchema']==engine.schema(state)
    assert options['response_schema']==generation_schema(state,engine.schema(state),2)
    legacy, options=project({}, 'sue/answer-01', constrained=False)
    assert 'groundingContext' not in legacy and 'response_schema' not in options


@pytest.mark.parametrize('mutation',['silent_answer_citations','silent_grounded_premise','paraphrased_stated','future_turn'])
def test_observed_grounding_failure_classes_remain_rejected(mutation):
    state=engine.initial_state(CLAIM)
    value=deepcopy(answer('DEFINE'))
    if mutation.startswith('silent'):
        value.update(verdict='SILENT',test_result='UNKNOWN',claim=None)
        if mutation=='silent_grounded_premise':value.update(evidence_lines=[],evidence=[])
    elif mutation=='paraphrased_stated':value['premises'][0]['statement']='All data exports require administrator status.'
    else:value['addresses']=[1]
    after,error=engine.advance(state,value,SOURCE.splitlines())
    assert error=='invalid_turn' and after==state


def test_supported_and_silent_are_both_accepted_without_response_repair():
    state=engine.initial_state(CLAIM)
    supported=answer('DEFINE')
    assert engine.advance(state,supported,SOURCE.splitlines())[1] is None
    silent=deepcopy(supported)
    silent.update(verdict='SILENT',test_result='UNKNOWN',claim=None,evidence_lines=[],evidence=[],premises=[])
    frozen=deepcopy(silent)
    after,error=engine.advance(state,silent,SOURCE.splitlines())
    assert error is None and after['terminal']=='APORIA_UNDEFINED' and silent==frozen


@pytest.mark.parametrize('keep_answer_evidence',[True,False])
def test_constrained_silent_grounding_failures_keep_raw_receipts_and_bound_guidance(tmp_path,keep_answer_evidence):
    if 'json_schema_v1' not in ProsaicRuntime.capabilities:
        # The installed candidate lane must exercise this test, while the
        # public SDK lane must still fail closed without dispatch.
        from prosaic_integration_lab.sue_review.contracts import ReviewError
        with FileRunStore(tmp_path/'runs',namespace='sue-test') as store:
            with pytest.raises(ReviewError,match='constrained_json_unavailable'):
                session(store,'http://127.0.0.1:9/v1',constrained_json=True).start(
                    uuid.uuid4().hex,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}])
        return
    from prosaic_integration_lab.sue_review.grounding import GROUNDING_GUIDANCE, GROUNDING_SHA256
    from prosaic_integration_lab.sue_review.generation import GENERATION_SCHEMA_VERSION
    from prosaic_integration_lab.sue_review.guidance import GUIDANCE_SHA256
    from prosaic_integration_lab.sue_review.contracts import digest
    bad=answer('DEFINE');bad.update(verdict='SILENT',test_result='UNKNOWN',claim=None)
    if not keep_answer_evidence:bad.update(evidence_lines=[],evidence=[])
    raw=json.dumps(bad)
    with fixture([raw]) as (url,requests),FileRunStore(tmp_path/'runs',namespace='sue-test') as store:
        flow=session(store,url,constrained_json=True);run_id=uuid.uuid4().hex
        waiting=flow.start(run_id,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}])
        result=flow.resume(run_id,expected_revision=waiting['revision'],choice='continue')
        assert result['status']=='blocked' and result['acceptedTurns']==0 and len(requests)==2
        saved=store.load_run(run_id).state
        assert saved['outputs']=={} and len(saved['invocations'])==2
        version='sue-review-v1.5-'+digest({'engine':engine.capabilities(),
            'policy':saved['inputs']['reviewPolicy'],'answerGuidanceSha256':GUIDANCE_SHA256,
            'groundingGuidanceSha256':GROUNDING_SHA256,'generationSchemaVersion':GENERATION_SCHEMA_VERSION})
        for wire,invocation in zip(requests,saved['invocations'],strict=True):
            prompt=wire['messages'][0]['content']
            assert GROUNDING_GUIDANCE in prompt.split('\n\n## Arguments\n',1)[0]
            data=json.loads(prompt.split('\n\n## Arguments\n',1)[1])
            assert data['groundingContext']['priorTurnNumbers']==[]
            receipt=store.load_receipt(run_id,invocation['id'])
            assert receipt['result']['metadata']['sueRawResponse']==raw
            assert json.loads(receipt['result']['stdout'])['rawResponse']==raw
            assert receipt['result']['metadata']['runtime_adapter_v1']['version']==version
        assert flow.report(run_id)['reportedTokens']==30
