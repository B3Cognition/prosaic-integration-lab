from copy import deepcopy
import json
import socket
from pathlib import Path
import pytest
from memory_helpers import development
from lab_runner.quality.contracts import digest


def bundle():
    case,_,d,s=development();case.update(caseId='dev-one',family='relevant')
    second=deepcopy(case);second.update(caseId='dev-two',family='stale')
    return dict(version=1,suiteId='memory-development',cases=[case,second],corpus=d,historicalSources=s)


def test_preflight_never_opens_network_or_constructs_runtime(monkeypatch):
    from lab_runner.memory.runner import preflight
    def forbidden(*a,**k):raise AssertionError('network in preflight')
    monkeypatch.setattr(socket,'socket',forbidden)
    report=preflight(bundle())
    assert report['origin']=='unexecuted' and report['executedSamples']==0
    assert report['scheduledSamples']==8 and report['baselineComplete'] is False


def test_paired_schedule_alternates_order_per_case_without_changing_profiles():
    from lab_runner.memory.runner import schedule
    rows=schedule(bundle(),[digest('a'),digest('b')])
    assert len(rows)==8 and len({r['sampleId'] for r in rows})==8
    assert [r['arm'] for r in rows[:4]]==['disabled','enabled','enabled','disabled']
    assert [r['caseId'] for r in rows[:4]]==['dev-one']*2+['dev-two']*2


def test_valid_foreign_history_does_not_change_study_identity():
    from lab_runner.memory.runner import identity
    b=bundle();before=identity(b)
    e=deepcopy(b['corpus']['episodes'][0]);e.update(tenantId='beta',episodeId='foreign')
    s=deepcopy(b['historicalSources']['sources'][0]);s['tenantId']='beta'
    b['corpus']['episodes'].append(e);b['historicalSources']['sources'].append(s)
    assert identity(b)==before


def test_retrieval_metrics_keep_empty_denominators_and_do_not_expose_ids():
    from lab_runner.memory.reporting import retrieval_metrics
    assert retrieval_metrics(['a'],['a','b'],['a'])==dict(goldCount=1,retrievedCount=2,hitCount=1,
        recallAt3=1,precisionAt3=.5,availableGoldCount=1,corpusCoverage=1)
    r=retrieval_metrics([],[],[])
    assert r['recallAt3'] is None and r['precisionAt3'] is None and r['corpusCoverage'] is None


def test_fixture_runner_counts_native_calls_and_replays_without_provider(tmp_path,monkeypatch):
    import lab_runner.memory.runner as runner
    report=runner.execute(output=tmp_path,bundle=bundle(),fixture=True)
    assert report['baselineComplete'] and report['usageComplete']
    assert report['taskSuccess']==dict(passed=8,attempted=8,rate=1)
    assert report['providerRequests']==16 and report['toolCalls']==8 and report['hostQueries']==4
    assert report['fixtureCounts']==dict(providerRequests=16,toolCalls=8)
    assert len(report['pairs'])==4 and all(p['transition']=='bothPassed' for p in report['pairs'])
    raw=json.dumps(report)
    assert all(secret not in raw for secret in ('Orchid previously','tenantId','recordIndex','http://','alpha'))
    before={p:p.read_bytes() for p in tmp_path.glob('*.json')}
    def forbidden(*a,**k):raise AssertionError('redispatch on replay')
    monkeypatch.setattr(runner,'execute_case',forbidden);monkeypatch.setattr(socket,'socket',forbidden)
    assert runner.execute(output=tmp_path,bundle=bundle(),fixture=True)==report
    assert before=={p:p.read_bytes() for p in tmp_path.glob('*.json')}


def test_unknown_usage_retains_full_reservation_and_stops_schedule(tmp_path):
    from lab_runner.memory.runner import execute
    report=execute(output=tmp_path,bundle=bundle(),fixture=True,fixture_scenario='missing_usage')
    assert report['executedSamples']==1 and not report['usageComplete'] and not report['baselineComplete']
    ledger=json.loads((tmp_path/'allowance.json').read_bytes())
    assert len(ledger['samples'])==1
    claim=next(iter(ledger['samples'].values()))
    assert claim['state']=='unknown' and claim['maximum']==dict(providerRequests=4,toolCalls=2,reportedTokens=8192)


def test_wrong_fixture_answers_cannot_be_hidden_by_repair_or_memory(tmp_path):
    from lab_runner.memory.runner import execute
    report=execute(output=tmp_path,bundle=bundle(),fixture=True,fixture_scenario='wrong')
    assert report['executedSamples']==8 and report['usageComplete']
    assert report['taskSuccess']['passed']==0 and report['providerRequests']==32 and report['toolCalls']==16


def test_different_corpus_or_arm_cannot_adopt_existing_study(tmp_path):
    from lab_runner.memory.runner import execute
    b=bundle();execute(output=tmp_path,bundle=b,fixture=True)
    b['corpus']['episodes'][0]['note']='changed local corpus'
    with pytest.raises(ValueError):execute(output=tmp_path,bundle=b,fixture=True)


def test_public_projection_drops_extra_private_counter_fields(tmp_path):
    from lab_runner.memory.runner import execute
    from lab_runner.memory.reporting import public_result
    b=bundle();report=execute(output=tmp_path,bundle=b,fixture=True)
    row=report['schedule'][0];e=json.loads((tmp_path/(row['sampleId']+'.json')).read_bytes())
    e['counts']['private']='PRIVATE-COUNTER';e['retrievalMetrics']['raw']='PRIVATE-NOTE'
    result=public_result(b['cases'][0],e,row,['prior'])
    assert 'PRIVATE-' not in json.dumps(result)
    e['firstPass']='PRIVATE-BOOL'
    with pytest.raises(ValueError):public_result(b['cases'][0],e,row,['prior'])


@pytest.mark.parametrize('location',['recordIndex','records'])
def test_private_source_annotations_are_rejected_before_admission(location):
    from lab_runner.memory.suite import validate_bundle
    b=bundle();case=b['cases'][0]
    target=case['recordIndex'][0] if location=='recordIndex' else next(iter(case['records'].values()))
    target['privateScorerAnswer']='CANARY-PRIVATE-ANSWER'
    with pytest.raises(ValueError):validate_bundle(b)


def test_interrupted_inference_retains_retrieval_and_does_not_become_a_paired_loss(tmp_path,monkeypatch):
    import lab_runner.memory.runner as runner
    from lab_runner.memory.execution import freeze
    original=runner.execute_case
    def interrupted(case,**kw):
        if kw['arm']=='enabled':
            freeze(case,kw['corpus'],kw['arm'],kw['output']/(kw['sample_id']+'-prepared.json'))
            raise RuntimeError('interrupted after retrieval')
        return original(case,**kw)
    monkeypatch.setattr(runner,'execute_case',interrupted)
    r=runner.execute(output=tmp_path,bundle=bundle(),fixture=True)
    assert r['executedSamples']==2 and r['hostQueries']==1
    unknown=r['results'][-1]
    assert unknown['state']=='unknown' and unknown['hostQueries']==1
    assert unknown['retrieval']['hitCount']==1 and unknown['resultBytes']>2
    assert r['pairs'][0]['transition']=='incomplete'


@pytest.mark.parametrize('phase,known',[('after',True),('before',False)])
def test_runner_recovers_saved_receipt_only_without_network_or_new_samples(tmp_path,monkeypatch,phase,known):
    import prosaic_harness
    import lab_runner.memory.runner as runner
    from lab_runner.quality.recovery import FaultStore,InjectedInterruption
    real_store=prosaic_harness.FileRunStore
    monkeypatch.setattr(prosaic_harness,'FileRunStore',lambda *a,**kw:FaultStore(real_store(*a,**kw),phase))
    with pytest.raises(InjectedInterruption):runner.execute(output=tmp_path,bundle=bundle(),fixture=True)
    monkeypatch.setattr(prosaic_harness,'FileRunStore',real_store)
    def forbidden(*a,**kw):raise AssertionError('network during receipt-only recovery')
    monkeypatch.setattr(socket,'socket',forbidden)
    r=runner.execute(output=tmp_path,bundle=bundle(),fixture=True,recover_only=True)
    assert r['executedSamples']==1 and not r['baselineComplete']
    claim=next(iter(json.loads((tmp_path/'allowance.json').read_bytes())['samples'].values()))
    if known:
        assert claim['state']=='known' and r['taskSuccess']['passed']==1
        assert r['fixtureCounts']==dict(providerRequests=2,toolCalls=1)
    else:assert claim['state']=='unknown' and r['results'][0]['state']=='unknown'


def test_saved_invalid_receipt_never_dispatches_a_repair_during_recovery(tmp_path,monkeypatch):
    import prosaic_harness
    import lab_runner.memory.runner as runner
    from lab_runner.quality.recovery import FaultStore,InjectedInterruption
    real_store=prosaic_harness.FileRunStore
    monkeypatch.setattr(prosaic_harness,'FileRunStore',lambda *a,**kw:FaultStore(real_store(*a,**kw),'after'))
    with pytest.raises(InjectedInterruption):runner.execute(output=tmp_path,bundle=bundle(),fixture=True,fixture_scenario='wrong')
    monkeypatch.setattr(prosaic_harness,'FileRunStore',real_store)
    def forbidden(*a,**kw):raise AssertionError('repair dispatch during recovery')
    monkeypatch.setattr(socket,'socket',forbidden)
    r=runner.execute(output=tmp_path,bundle=bundle(),fixture=True,recover_only=True)
    assert r['executedSamples']==1 and r['results'][0]['state']=='unknown'


def test_independent_fixture_observations_survive_unrecoverable_failure_after_provider_completion(tmp_path,monkeypatch):
    import lab_runner.memory.runner as runner
    original=runner.execute_case
    def interrupted(case,**kw):
        original(case,**kw)
        raise RuntimeError('lost final evidence publication')
    monkeypatch.setattr(runner,'execute_case',interrupted)
    monkeypatch.setattr(runner,'recover_case',lambda *a,**kw:None)
    r=runner.execute(output=tmp_path,bundle=bundle(),fixture=True)
    assert r['results'][0]['state']=='unknown'
    assert r['fixtureCounts']==dict(providerRequests=2,toolCalls=1)
    assert r['stateCounts']==dict(passed=0,failed=0,unknown=1,notRun=7)


def test_transient_ordinary_publication_error_adopts_receipt_before_unknown_settlement(tmp_path,monkeypatch):
    import lab_runner.memory.runner as runner
    original_write=runner.private_write;original_recover=runner.recover_case;failed=[];recovered=[]
    def write(path,value):
        if path.name=='dev-one-p1-disabled.json' and not failed:
            failed.append(True);raise OSError('temporary publication failure')
        return original_write(path,value)
    def recover(*args,**kwargs):
        with monkeypatch.context() as m:
            def forbidden(*a,**kw):raise AssertionError('network during ordinary exception adoption')
            m.setattr(socket,'socket',forbidden)
            value=original_recover(*args,**kwargs)
        recovered.append(True);return value
    monkeypatch.setattr(runner,'private_write',write);monkeypatch.setattr(runner,'recover_case',recover)
    r=runner.execute(output=tmp_path,bundle=bundle(),fixture=True)
    assert len(recovered)==1 and r['taskSuccess']['passed']==8
    assert r['fixtureCounts']==dict(providerRequests=16,toolCalls=8)
    ledger=json.loads((tmp_path/'allowance.json').read_bytes())
    assert all(c['state']=='known' for c in ledger['samples'].values())


def test_later_receipt_adoption_keeps_an_already_unknown_reservation_fully_charged(tmp_path,monkeypatch):
    import lab_runner.memory.runner as runner
    original=runner.private_write
    def unavailable(path,value):
        if path.name=='dev-one-p1-disabled.json':raise OSError('publication unavailable')
        return original(path,value)
    monkeypatch.setattr(runner,'private_write',unavailable)
    first=runner.execute(output=tmp_path,bundle=bundle(),fixture=True)
    assert first['results'][0]['state']=='unknown'
    before=json.loads((tmp_path/'allowance.json').read_bytes())['samples']
    monkeypatch.setattr(runner,'private_write',original)
    def forbidden(*a,**kw):raise AssertionError('network during later receipt adoption')
    monkeypatch.setattr(socket,'socket',forbidden)
    recovered=runner.execute(output=tmp_path,bundle=bundle(),fixture=True,recover_only=True)
    assert recovered['taskSuccess']['passed']==1 and recovered['retainedUnknownSamples']==1
    assert json.loads((tmp_path/'allowance.json').read_bytes())['samples']==before
    assert runner.execute(output=tmp_path,bundle=bundle(),fixture=True,recover_only=True)==recovered
