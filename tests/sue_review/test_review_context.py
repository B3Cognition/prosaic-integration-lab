"""Frozen host review criteria never become source evidence or model authority."""
from copy import deepcopy
import json
import uuid

import pytest
from prosaic_harness import FileRunStore
from tests.sue_review.test_execution import session, fixture, answer, SOURCE, CLAIM

CONTEXT = {'purpose':'Assess the supplied document against the public criteria.',
           'issueDefinitions':{'missing_failure_behavior':'A required operation lacks failure behavior.'},
           'instructions':'Treat the seed as a hypothesis; cite demonstrated gaps only.'}


def test_review_context_and_cycle_policy_are_frozen_on_real_wire_and_resume(tmp_path):
    before=deepcopy(CONTEXT)
    with fixture([answer('DEFINE')]) as (url,rows), FileRunStore(tmp_path/'store',namespace='sue-test') as store:
        flow=session(store,url,cycle_guard=True)
        run=uuid.uuid4().hex
        pending=flow.start(run,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}],
                           max_turns=1,review_context=CONTEXT)
        assert rows==[]
        changed={**CONTEXT,'purpose':'A changed evaluation.'}
        with pytest.raises(ValueError,match='conflict'):
            flow.start(run,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}],
                       max_turns=1,review_context=changed)
        saved=store.load_run(run).state
        assert saved['inputs']['reviewContext']==CONTEXT
        assert saved['inputs']['reviewPolicy']['cycle_guard'] is True
        # Reconstructed session has no local context or opt-in settings.
        resumed=session(store,url).resume(run,expected_revision=pending['revision'],choice='continue')
        assert resumed['status']=='completed' and len(rows)==1
        projected=json.loads(rows[0]['messages'][0]['content'].split('\n\n## Arguments\n',1)[1])
        assert projected['reviewContext']==CONTEXT
        assert projected['state']['cycle_guard']=='repeated-cycle-v1'
        assert projected['sourceLines']==[{'line':1,'text':SOURCE.splitlines()[0]},
                                         {'line':2,'text':SOURCE.splitlines()[1]}]
        assert CONTEXT==before
        assert flow.report(run)['proposal']['reviewContextSha256']


@pytest.mark.parametrize('context',[{}, {'purpose':'x','issueDefinitions':{},'instructions':'x'},
    {**CONTEXT,'tenant_id':'model-owned'}, {**CONTEXT,'purpose':'x'*9000}])
def test_invalid_context_never_dispatches(tmp_path,context):
    with fixture([answer('DEFINE')]) as (url,rows), FileRunStore(tmp_path/'s',namespace='sue-test') as store:
        with pytest.raises(ValueError,match='context'):
            session(store,url).start(uuid.uuid4().hex,seed=CLAIM,
                sources=[{'sourceId':'spec','text':SOURCE}],review_context=context)
        assert rows==[]
