from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import json

import pytest


def api():
    from lab_runner import trajectory
    return trajectory


def collector():
    return api().Trajectory('private-run', binding_digest='a'*64, key=b'k'*32)


def event(sequence=1, **fields):
    return dict(version=1, source='runtime', event='invocation_started',
                run_id='private-run', invocation_id='private-invocation',
                step_id='private-step', sequence=sequence) | fields


def assessment(status='failed', categories=None, usage=None):
    return dict(bindingDigest='a'*64, status=status,
                categories=['model_output'] if categories is None else categories,
                evidenceDigest='b'*64,
                usage=dict(providerRequests=2, toolCalls=1, reportedTokens=300) if usage is None else usage)


def test_correlates_public_records_without_exporting_raw_scope_or_payloads():
    trace=collector()
    trace.observe(event(labels={'secret':'PRIVATE-PROMPT'}, text='PRIVATE-OUTPUT'))
    trace.observe(event(2, event='tool_completed', name='PRIVATE-TOOL', tool_outcome={
        'version':1,'code':'ok','phase':'execution','effect':'completed','recovery':'none','replayed':False}))
    trace.observe(event(3, event='invocation_completed', outcome='completed', token_usage=999))
    trace.annotate('private-step', kind='evidence', status='verified', evidence_digest='c'*64)
    result=trace.report(assessment())
    assert len({o['streamRef'] for o in result['observations']}) == 1
    assert {o['stepRef'] for o in result['observations']} == {result['hostAnnotations'][0]['stepRef']}
    assert result['observations'][1]['toolCode']=='ok'
    assert result['assessment']['status']=='failed'
    assert result['assessment']['usage']['reportedTokens']==300
    assert result['monitoring']['openStreams']==0
    assert not any(secret in json.dumps(result) for secret in ('private-', 'PRIVATE-', 'c'*64, 'b'*64))


def test_foreign_records_are_rejected_without_cross_run_correlation():
    trace=collector();trace.observe(event(run_id='foreign'))
    result=trace.report(assessment('incomplete', ['evidence']))
    assert result['observations']==[]
    assert result['monitoring']['rejectedRecords']==1
    assert result['monitoring']['noRecords'] is True


def test_sequence_gaps_duplicates_and_unclosed_streams_are_visible():
    trace=collector();trace.observe(event());trace.observe(event(3));trace.observe(event(3))
    result=trace.report(assessment())
    assert len(result['observations'])==2
    assert result['monitoring']['sequenceIssues']==2
    assert result['monitoring']['openStreams']==1


def test_recovery_uses_a_distinct_observation_stream_without_invented_parentage():
    trace=collector();trace.observe(event());trace.observe(event(2,event='invocation_completed'))
    trace.observe(event(source='harness',invocation_id='recovery',event='recovery_committed'))
    result=trace.report(assessment())
    assert result['observations'][0]['streamRef'] != result['observations'][-1]['streamRef']
    assert 'parentRef' not in result['observations'][-1]


def test_bounded_capture_records_loss_and_never_authorizes_continuation():
    trace=collector()
    for n in range(1,520):trace.observe(event(n))
    for n in range(130):trace.annotate('step',kind='recovery',status='inspected',evidence_digest='c'*64)
    result=trace.report(assessment())
    assert len(result['observations'])==512 and len(result['hostAnnotations'])==128
    assert result['monitoring']['droppedRecords']==9
    assert result['assessment']['status']=='failed'


@pytest.mark.parametrize('bad',[None,[],{},event(True),event(0),event(source='unknown'),
    event(event='PRIVATE-ERROR'),event(invocation_id='x'*10000),event(version=True)])
def test_malformed_monitoring_data_does_not_raise_or_leak(bad):
    trace=collector();trace.observe(bad)
    result=trace.report(assessment())
    assert result['observations']==[] and result['monitoring']['rejectedRecords']==1


def test_unknown_usage_is_not_reconstructed_from_observer_counts():
    trace=collector();trace.observe(event(token_usage=100))
    result=trace.report(assessment('incomplete',['accounting'],
        dict(providerRequests=1,toolCalls=None,reportedTokens=None)))
    assert result['assessment']['usage']==dict(providerRequests=1,toolCalls=None,reportedTokens=None)


@pytest.mark.parametrize('change',[{'status':'PRIVATE'}, {'bindingDigest':'d'*64},
    {'categories':['PRIVATE']},{'usage':dict(providerRequests=True,toolCalls=1,reportedTokens=1)},
    {'usage':dict(providerRequests=1,toolCalls=1,reportedTokens=-1)}, {'extra':'secret'}])
def test_host_assessments_are_closed_and_bound(change):
    with pytest.raises(ValueError):collector().report(assessment()|change)


def test_passing_assessment_cannot_hide_unknown_usage():
    with pytest.raises(ValueError):
        collector().report(assessment('passed',[],dict(providerRequests=1,toolCalls=1,reportedTokens=None)))


def test_key_is_required_and_pseudonyms_do_not_correlate_between_consumers():
    with pytest.raises(ValueError):api().Trajectory('r',binding_digest='a'*64,key=b'weak')
    first=collector();second=api().Trajectory('private-run',binding_digest='a'*64,key=b'z'*32)
    first.observe(event());second.observe(event())
    assert first.report(assessment())['runRef'] != second.report(assessment())['runRef']


def test_concurrent_capture_has_unique_ordinals_and_owned_snapshots():
    trace=collector()
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda n:trace.observe(event(invocation_id=str(n))),range(40)))
    result=trace.report(assessment())
    assert sorted(o['ordinal'] for o in result['observations'])==list(range(1,41))
    result['observations'].clear()
    assert len(trace.report(assessment())['observations'])==40


def test_private_offline_roundtrip_checks_binding_integrity_and_closed_schema(tmp_path):
    trace=collector();trace.observe(event())
    path=tmp_path/'report.json';report=trace.report(assessment())
    api().save_report(path,report)
    assert path.stat().st_mode & 0o777==0o600
    assert api().read_report(path,binding_digest='a'*64)==report
    with pytest.raises(ValueError):api().read_report(path,binding_digest='d'*64)
    damaged=deepcopy(report);damaged['assessment']['status']='passed'
    path.write_text(json.dumps(damaged))
    with pytest.raises(ValueError):api().read_report(path,binding_digest='a'*64)
    damaged=deepcopy(report);damaged['secret']='PRIVATE'
    with pytest.raises(ValueError):api().save_report(path,damaged)


def test_offline_reader_rejects_shared_files_and_symlink_paths(tmp_path):
    path=tmp_path/'report.json'
    api().save_report(path,collector().report(assessment()))
    path.chmod(0o644)
    with pytest.raises(ValueError):api().read_report(path,binding_digest='a'*64)
    path.chmod(0o600)
    link=tmp_path/'link.json';link.symlink_to(path)
    with pytest.raises(ValueError):api().read_report(link,binding_digest='a'*64)


def test_parcel_unknown_usage_alone_does_not_invent_provider_failure():
    from lab_runner.trajectory_fixture import _assess
    value=_assess(dict(receipts=[{'result':{'token_usage':None,'metadata':{}}}],checkpoint={}),
        [],dict(providerRequests=1,toolCalls=0,reportedTokens=None),'a'*64)
    assert value['status']=='incomplete'
    assert value['categories']==['accounting']
