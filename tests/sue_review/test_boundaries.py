from copy import deepcopy
import json
import hashlib
import uuid

import castle_sue as engine
import pytest
from prosaic_harness import FileRunStore
from prosaic_runtime import EndpointConfig, RuntimeConfig

from prosaic_integration_lab.sue_review.contracts import ReviewError, digest
from prosaic_integration_lab.sue_review.workflow import fold_accepted
from tests.sue_review.test_execution import CLAIM, SOURCE, answer, fixture, session


def test_fourteen_real_turns_fit_unchanged_transport_caps_and_bound_stop(tmp_path):
    state = engine.initial_state(CLAIM, max_turns=14)
    replies = []
    while not state['terminal']:
        value = answer(state['operator'])
        if state['operator'] == 'DIVIDE':
            value.update(verdict='PARTIAL', test_result='INCOMPLETE')
        replies.append(value)
        state, error = engine.advance(state, value, SOURCE.splitlines())
        assert error is None
    assert len(replies) == 14 and state['terminal'] == 'BOUNDED_STOP'
    with fixture(replies) as (url, requests), FileRunStore(tmp_path/'runs', namespace='sue-test') as store:
        flow = session(store, url)
        run_id = uuid.uuid4().hex
        waiting = flow.start(run_id, seed=CLAIM, sources=[{'sourceId':'spec', 'text':SOURCE}])
        result = flow.resume(run_id, expected_revision=waiting['revision'], choice='continue')
        assert result['status'] == 'completed' and result['terminal'] == 'BOUNDED_STOP'
        assert result['acceptedTurns'] == 14 and len(requests) == 14
        saved = store.load_run(run_id).state
        request, outputs = saved['inputs'], saved['outputs']
        expected = fold_accepted(request, outputs, engine=engine)
        assert expected == state
        # JSON map order is irrelevant; every numbered accepted predecessor is required.
        assert fold_accepted(request, dict(reversed(list(outputs.items()))), engine=engine) == state
        for key in ('answer-01', 'answer-07'):
            missing = dict(outputs); missing.pop(key)
            with pytest.raises(ReviewError, match='accepted_prefix_mismatch'):
                fold_accepted(request, missing, engine=engine)
        # A shorter contiguous prefix is valid when reporting an unfinished run.
        prefix = dict(outputs); prefix.pop('answer-14')
        assert fold_accepted(request, prefix, engine=engine)['terminal'] is None
        # Before turn fourteen, every one of its thirteen predecessors is required.
        prefix.pop('answer-13')
        with pytest.raises(ReviewError, match='accepted_prefix_mismatch'):
            fold_accepted(request, prefix, before_step='answer-14', engine=engine)
        forged = deepcopy(outputs)
        forged['answer-01']['terminal'] = 'RESOLVED'
        with pytest.raises(ReviewError, match='state_projection_mismatch'):
            fold_accepted(request, forged, engine=engine)
        forged = deepcopy(outputs)
        forged['answer-01']['stateSha256'] = digest({'forged':True})
        with pytest.raises(ReviewError, match='state_projection_mismatch'):
            fold_accepted(request, forged, engine=engine)
        assert flow.report(run_id)['usageComplete'] is True
        assert flow.report(run_id)['reportedTokens'] == 14*15
        assert all(not r.get('tools') for r in requests)
        assert max(len(json.dumps(r).encode()) for r in requests) < 262144


def test_changed_runtime_binding_is_unavailable_without_dispatch(tmp_path):
    with fixture([answer('DEFINE')]) as (url, requests), FileRunStore(tmp_path/'runs', namespace='sue-test') as store:
        flow = session(store, url)
        run_id = uuid.uuid4().hex
        waiting = flow.start(run_id, seed=CLAIM, sources=[{'sourceId':'spec', 'text':SOURCE}])
        flow.config = RuntimeConfig({'fixture':EndpointConfig(url,'changed-model', features={'streaming':False})},{},'fixture',allowed_tools=frozenset())
        for action in (lambda:flow.status(run_id), lambda:flow.report(run_id),
                       lambda:flow.resume(run_id,expected_revision=waiting['revision'],choice='continue')):
            with pytest.raises(ReviewError, match='binding_unavailable'):
                action()
        assert requests == []


@pytest.mark.parametrize('size,reason',[(8000,'output_limit'),(16000,'event_limit')])
def test_escaped_wire_event_stops_without_acceptance_or_redispatch(tmp_path,size,reason):
    raw = '\x00'*size
    with fixture([raw]) as (url, requests), FileRunStore(tmp_path/'runs', namespace='sue-test') as store:
        flow = session(store, url)
        run_id = uuid.uuid4().hex
        waiting = flow.start(run_id,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}],max_turns=1)
        result = flow.resume(run_id,expected_revision=waiting['revision'],choice='continue')
        assert result['status'] == 'blocked' and result['acceptedTurns'] == 0
        assert len(requests) == 1
        invocation = store.load_run(run_id).state['invocations'][0]
        receipt = store.load_receipt(run_id,invocation['id'])
        metadata = receipt['result']['metadata']
        # Runtime's event cap stops this response before the adapter receives
        # raw stdout. Preserve the actual failure, not a fabricated output hash.
        assert metadata['failure_reason'] == reason
        if reason == 'output_limit':
            assert metadata['sueOutput'] == {'bytes':size,'sha256':hashlib.sha256(raw.encode()).hexdigest()}
        assert len(json.dumps(metadata).encode()) <= 65536
        assert flow.report(run_id)['usageComplete'] is True
        flow.resume(run_id,expected_revision=result['revision'])
        assert len(requests) == 1


@pytest.mark.parametrize('raw,original_metadata',[
    ('\x00'*16000,{}),
    ('\x00'*4600+'λ'*5892,{'providerInfo':'x'*3000}),
],ids=['control-expansion','unicode-metadata-expansion'])
def test_returned_escaped_output_retains_identity_within_serialized_limits(raw,original_metadata):
    from types import SimpleNamespace
    from prosaic_runtime import Result
    from prosaic_integration_lab.sue_review.sources import freeze_documents
    from prosaic_integration_lab.sue_review.workflow import project_answer
    request = {'seed':CLAIM,'lens':'euthyphro','maxTurns':1,
               'engine':engine.capabilities(),'evidence':freeze_documents([{'sourceId':'spec','text':SOURCE}])}
    calls = []
    def execute(*arguments,**options):
        calls.append((arguments,options))
        return Result(0,raw,'',token_usage=15,metadata=original_metadata)
    result = project_answer(SimpleNamespace(id='sue/answer-01'),
        json.dumps({'request':request,'artifacts':{}}),execute=execute,engine=engine)
    assert len(calls) == 1 and result.exit_code == 1 and result.stdout == ''
    assert result.metadata['sueOutput'] == {'bytes':len(raw.encode()),'sha256':hashlib.sha256(raw.encode()).hexdigest()}
    assert result.metadata['failure_reason'] == 'output_limit'
    assert 'sueRawResponse' not in result.metadata
    assert len(json.dumps(result.metadata).encode()) <= 65536
    assert result.token_usage == 15


def test_approval_projection_is_frozen_detached_and_available_after_disable(tmp_path):
    with fixture([answer('DEFINE')]) as (url, requests), FileRunStore(tmp_path/'runs',namespace='sue-test') as store:
        flow = session(store,url,settings={'lifetime_s':172800,'max_calls':2,'max_tokens':1000})
        run_id = uuid.uuid4().hex
        waiting = flow.start(run_id,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}],max_turns=1)
        proposal = waiting['proposal']
        assert proposal['seed'] == CLAIM and proposal['lens'] == 'euthyphro' and proposal['maxTurns'] == 1
        assert proposal['policy']['lifetime_s'] == 172800 and proposal['policy']['max_calls'] == 2
        assert proposal['policy']['max_tokens'] == 1000 and proposal['engineIdentity'] == engine.capabilities()['engineIdentity']['digest']
        assert len(proposal['requestSignature']) == 64 and proposal['sourcesSha256'] == waiting['sourcesSha256']
        proposal['policy']['max_calls'] = 999
        disabled = session(store,url,settings={'enabled':False})
        saved = disabled.status(run_id)['proposal']
        assert saved['policy']['max_calls'] == 2 and disabled.report(run_id)['proposal'] == saved
        assert requests == []
