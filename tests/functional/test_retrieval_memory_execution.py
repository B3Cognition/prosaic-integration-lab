from copy import deepcopy
import json
import pytest
from memory_helpers import development


def test_memory_arm_changes_only_recalled_context_and_requires_current_native_lookup(tmp_path):
    from lab_runner.memory.execution import execute_case,LIMITS
    from lab_runner.memory.scoring import score_case
    from lab_runner.quality.fixture import fixture_provider
    case,corpus,_,_=development();requests=[]
    for arm in ('enabled','disabled'):
        with fixture_provider() as p:
            e=execute_case(case,corpus=corpus,arm=arm,config=p.config,profile='fixture',
                           output=tmp_path/arm,sample_id='sample',limits=LIMITS)
            payload=p.payloads[0]
            request=json.loads(next(m['content'] for m in payload['messages'] if m['role']=='user').rsplit('## Arguments\n',1)[1])['request']
            requests.append(request)
            assert e['counts']['providerRequests']==p.requests==2
            assert e['counts']['toolCalls']==len(e['journal'])==1
        assert e['completed'] and score_case(case,e)['state']=='passed'
        assert 'expected' not in request and 'goldEpisodes' not in request and 'tenantId' not in request
        assert e['prepared']['retrieval']['corpusDigest']==corpus.tenant_digest('alpha')
    assert requests[0]['recalledEpisodes'] and requests[1]['recalledEpisodes']==[]
    assert {k:v for k,v in requests[0].items() if k!='recalledEpisodes'}=={k:v for k,v in requests[1].items() if k!='recalledEpisodes'}


def test_wrong_answers_remain_blocked_and_retry_does_not_leak_target(tmp_path):
    from lab_runner.memory.execution import execute_case,LIMITS
    from lab_runner.memory.scoring import score_case
    from lab_runner.quality.fixture import fixture_provider
    case,corpus,_,_=development()
    with fixture_provider(scenario='wrong') as p:
        e=execute_case(case,corpus=corpus,arm='enabled',config=p.config,profile='fixture',
                       output=tmp_path,sample_id='wrong',limits=LIMITS)
        assert p.requests==4 and len(e['journal'])==2
    assert not e['completed'] and e['reason']=='attempt_limit'
    assert e['taskRepairs']==1 and e['schemaRepairs']==0
    assert score_case(case,e)['state']=='failed'
    feedback=e['receipts'][1]['arguments']['validation_feedback']
    assert 'decision' in feedback and 'target' not in feedback and 'approve' not in feedback


def test_scoring_rejects_unmatched_lookup_or_altered_prepared_context(tmp_path):
    from lab_runner.memory.execution import execute_case,LIMITS
    from lab_runner.memory.scoring import score_case
    from lab_runner.quality.fixture import fixture_provider
    case,corpus,_,_=development()
    with fixture_provider() as p:
        e=execute_case(case,corpus=corpus,arm='enabled',config=p.config,profile='fixture',
                       output=tmp_path,sample_id='forged',limits=LIMITS)
    for field,value in [('journal',[]),('prepared',{})]:
        forged=deepcopy(e);forged[field]=value
        assert score_case(case,forged)['state']=='failed'


@pytest.mark.parametrize('phase,status,reason',[('after','completed',None),('before','blocked','interrupted_call')])
def test_recovery_uses_frozen_context_without_redispatch_or_reretrieval(tmp_path,phase,status,reason):
    from prosaic_harness import Harness,FileRunStore
    from lab_runner.memory.execution import materials,LIMITS
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.recovery import FaultStore,InjectedInterruption
    case,corpus,_,_=development()
    with fixture_provider() as p:
        w,j,events,prepared=materials(case,corpus=corpus,arm='enabled',config=p.config,profile='fixture',
                                     output=tmp_path,sample_id='recover',limits=LIMITS)
        store=FileRunStore(tmp_path/'store',namespace='memory-test');store.initialize()
        try:
            h=Harness(w,store=FaultStore(store,phase),run_id='b'*32,on_event=events)
            try:h.run(prepared['request'])
            except InjectedInterruption:pass
            before=p.requests
            def forbidden(*args,**kwargs):raise AssertionError('retrieval repeated during recovery')
            corpus.retrieve=forbidden
            w2,j2,events2,prepared2=materials(case,corpus=corpus,arm='enabled',config=p.config,profile='fixture',
                                           output=tmp_path,sample_id='recover',limits=LIMITS)
            state=Harness(w2,store=store,run_id='b'*32,on_event=events2).resume()
            assert (state['status'],state['reason'])==(status,reason)
            assert prepared2==prepared and j2==j and p.requests==before==2
        finally:store.close()


def test_local_corpus_or_sources_drift_blocks_before_inference_but_foreign_drift_does_not(tmp_path):
    from lab_runner.memory.execution import materials,LIMITS
    from lab_runner.memory.corpus import Corpus
    from lab_runner.quality.fixture import fixture_provider
    case,corpus,d,s=development()
    with fixture_provider() as p:
        kw=dict(arm='enabled',config=p.config,profile='fixture',output=tmp_path,sample_id='drift',limits=LIMITS)
        first=materials(case,corpus=corpus,**kw)[3]
        foreign=deepcopy(d['episodes'][0]);foreign.update(tenantId='beta',episodeId='foreign');d['episodes'].append(foreign)
        fs=deepcopy(s['sources'][0]);fs['tenantId']='beta';s['sources'].append(fs)
        assert materials(case,corpus=Corpus(d,s),**kw)[3]==first
        d['episodes'][0]['note']='changed locally'
        with pytest.raises(ValueError):materials(case,corpus=Corpus(d,s),**kw)
        changed=deepcopy(case);changed['records']['metrics']['value']=0
        with pytest.raises(ValueError):materials(changed,corpus=corpus,**kw)
        assert p.requests==0


def test_prior_attempt_reads_cannot_validate_a_later_incomplete_lookup(tmp_path):
    from lab_runner.memory.execution import execute_case,LIMITS
    from lab_runner.memory.scoring import score_case
    from lab_runner.quality.fixture import fixture_provider
    case,corpus,_,_=development()
    with fixture_provider(scenario='stale_attempt') as p:
        e=execute_case(case,corpus=corpus,arm='enabled',config=p.config,profile='fixture',
                       output=tmp_path,sample_id='stale',limits=LIMITS)
    assert e['completed'] is False and score_case(case,e)['state']=='failed'
    assert e['counts']['providerRequests']==4 and e['taskRepairs']==1 and e['schemaRepairs']==0


def test_recalled_notes_cannot_expand_the_current_source_grant(tmp_path):
    from lab_runner.memory.execution import execute_case,LIMITS
    from lab_runner.memory.scoring import score_case
    from lab_runner.quality.fixture import fixture_provider
    case,corpus,_,_=development()
    with fixture_provider(scenario='wrong_record') as p:
        e=execute_case(case,corpus=corpus,arm='enabled',config=p.config,profile='fixture',
                       output=tmp_path,sample_id='foreign-source',limits=LIMITS)
    assert not e['completed'] and e['journal']==[] and score_case(case,e)['state']=='failed'


@pytest.mark.parametrize('location',['recordIndex','records'])
def test_direct_native_boundary_rejects_private_annotations_before_any_request(tmp_path,location):
    from lab_runner.memory.execution import execute_case,LIMITS
    from lab_runner.quality.fixture import fixture_provider
    case,corpus,_,_=development()
    target=case['recordIndex'][0] if location=='recordIndex' else next(iter(case['records'].values()))
    target['privateScorerAnswer']='CANARY-PRIVATE-ANSWER'
    with fixture_provider() as p:
        with pytest.raises(ValueError):execute_case(case,corpus=corpus,arm='enabled',config=p.config,profile='fixture',
            output=tmp_path,sample_id='canary',limits=LIMITS)
        assert p.requests==0
