from copy import deepcopy
import pytest


def benchmark_identity():
    from lab_runner.quality.runner import preflight
    return preflight()['identity']


def sample():
    return dict(sampleId='combine-01-p1-r1',caseId='combine-01',profileFingerprint='a'*64,
        repetition=1,state='passed',reasons=[],counts=dict(providerRequests=2,toolCalls=1,reportedTokens=300),
        toolMetrics=dict(totalCalls=1,requestedRecords=2,duplicateRecords=0,irrelevantRecords=0,excessCalls=0),
        schemaRepairs=0,taskRepairs=0,firstPass=True,criticDetected=False,elapsedSeconds=0.5,
        inputTokens=200,outputTokens=100)


@pytest.mark.parametrize('version,accepted', [('0.9.3+finalize.1',True),('0.9.3+../../private',False),('0.9.3+https://private',False)])
def test_pinned_local_candidate_versions_are_reported_without_paths(version,accepted):
    from lab_runner.quality.reporting import summarize
    identity=benchmark_identity();identity['sdkVersions']['b3-prosaic-runtime']=version
    identity['sdkManifestDigest']='b'*64
    if accepted:
        report=summarize([],[],identity=identity,origin='fixture',recovery=[])
        assert report['identity']['sdkVersions']['b3-prosaic-runtime']=='0.9.3+finalize.1'
    else:
        with pytest.raises(ValueError):summarize([],[],identity=identity,origin='fixture',recovery=[])


def test_missing_samples_and_unknown_usage_are_not_complete():
    from lab_runner.quality.reporting import summarize
    row=sample();schedule=[{k:row[k] for k in ('sampleId','caseId','profileFingerprint','repetition')}]
    report=summarize(schedule,[],identity=benchmark_identity(),origin='live',recovery=[])
    assert not report['baselineComplete'] and report['stateCounts']['notRun']==1
    row['counts']['reportedTokens']=None
    report=summarize(schedule,[row],identity=benchmark_identity(),origin='live',recovery=[])
    assert not report['baselineComplete'] and report['usageComplete'] is False


def test_cost_and_latency_preserve_coverage():
    from lab_runner.quality.reporting import summarize,estimate_cost
    row=sample();schedule=[{k:row[k] for k in ('sampleId','caseId','profileFingerprint','repetition')}]
    report=summarize(schedule,[row],identity=benchmark_identity(),origin='fixture',recovery=[])
    assert report['latency']['p95Seconds'] is None and report['latency']['observations']==1
    assert report['taskSuccess']=={'passed':1,'attempted':1,'rate':1.0}
    card=dict(version=1,currency='USD',unitExponent=6,inputUnitsPerMillion=100,outputUnitsPerMillion=200)
    assert estimate_cost(row,card)['units']==1
    row['inputTokens']=None
    assert estimate_cost(row,card)['units'] is None


def test_comparison_rejects_foreign_policies_and_mixed_origins():
    from lab_runner.quality.reporting import summarize,compare
    row=sample();schedule=[{k:row[k] for k in ('sampleId','caseId','profileFingerprint','repetition')}]
    a=summarize(schedule,[row],identity=benchmark_identity(),origin='live',recovery=[])
    b=deepcopy(a);b['identity']['policyDigest']='b'*64
    with pytest.raises(ValueError):compare([a,b])
    b=deepcopy(a);b['origin']='fixture'
    with pytest.raises(ValueError):compare([a,b])
    with pytest.raises(ValueError):compare([a,a])


def test_public_row_drops_private_values():
    from lab_runner.quality.reporting import public_result
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.contracts import digest
    from test_agent_quality_scoring import witness
    e=witness(load_suite()['cases'][0]);e.update(counts=dict(providerRequests=2,toolCalls=1,reportedTokens=300),
        elapsedSeconds=0.2,inputTokens=200,outputTokens=100,schemaRepairs=0,taskRepairs=0,firstPass=True,
        endpoint='https://private.invalid',exception='secret-canary',profile='private-alias')
    row=public_result(load_suite()['cases'][0],e,profile_fingerprint=digest({'p':1}),repetition=1)
    import json
    raw=json.dumps(row)
    assert all(v not in raw for v in ('private.invalid','secret-canary','private-alias','stdout','journal'))


def test_profile_summaries_do_not_hide_model_differences():
    from lab_runner.quality.reporting import summarize
    a=sample();b=deepcopy(a);b.update(sampleId='combine-01-p2-r1',profileFingerprint='b'*64,state='failed',firstPass=False)
    schedule=[{k:r[k] for k in ('sampleId','caseId','profileFingerprint','repetition')} for r in (a,b)]
    report=summarize(schedule,[a,b],identity=benchmark_identity(),origin='fixture',recovery=[])
    assert report['profiles']['a'*64]['taskSuccess']['rate']==1
    assert report['profiles']['b'*64]['taskSuccess']['rate']==0


def test_report_does_not_echo_arbitrary_identity_or_recovery_data():
    from lab_runner.quality.reporting import summarize
    with pytest.raises(ValueError):
        summarize([],[],identity={'endpoint':'secret-canary'},origin='fixture',recovery=[])
    with pytest.raises(ValueError):
        summarize([],[],identity=benchmark_identity(),origin='fixture',recovery=[{'passed':True,'secret':'canary'}])


@pytest.mark.parametrize('runtime,filename',[('0.9.7','releases.json'),('0.9.8+diagnostics.1','response-diagnostics-candidate.json')])
def test_provenance_binds_the_selected_sdk_manifest(monkeypatch,runtime,filename):
    from lab_runner.quality import runner
    from prosaic_integration_lab.dependencies import manifest_digest
    from pathlib import Path
    monkeypatch.setattr(runner,'provenance',lambda:{'b3-prosaic':'0.4.1','b3-prosaic-runtime':runtime,'b3-prosaic-harness':'0.9.4'})
    report=runner.preflight()
    manifest=Path(__file__).resolve().parents[2]/'dependencies'/filename
    assert report['identity']['sdkManifestDigest']==manifest_digest(manifest)


def test_partial_schedules_never_establish_complete_baselines():
    from lab_runner.quality.reporting import summarize,compare
    a=sample();b=deepcopy(a);b.update(sampleId='combine-01-p2-r1',profileFingerprint='b'*64)
    reports=[summarize([{k:r[k] for k in ('sampleId','caseId','profileFingerprint','repetition')}],
        [r],identity=benchmark_identity(),origin='fixture',recovery=[]) for r in (a,b)]
    assert not any(r['baselineComplete'] for r in reports)
    assert compare(reports)['baselineComplete'] is False


def test_duplicate_logical_samples_cannot_inflate_coverage():
    from lab_runner.quality.reporting import summarize
    a=sample();b=deepcopy(a);b['sampleId']='another-id'
    schedule=[{k:r[k] for k in ('sampleId','caseId','profileFingerprint','repetition')} for r in (a,b)]
    with pytest.raises(ValueError):summarize(schedule,[a,b],identity=benchmark_identity(),origin='fixture',recovery=[])


def test_full_comparison_identity_is_required():
    from lab_runner.quality.reporting import summarize
    with pytest.raises(ValueError):summarize([],[],identity={'suiteId':'evidence-review-v1'},origin='fixture',recovery=[])
    identity=benchmark_identity()
    assert all(len(identity[key])==64 for key in ('workflowDigest','schemaDigest','scorerDigest'))


def test_unknown_durations_are_missing_and_profiles_have_separate_latency():
    from lab_runner.quality.reporting import summarize,unknown_result
    a=sample();b=deepcopy(a);b.update(sampleId='combine-01-p2-r1',profileFingerprint='b'*64,elapsedSeconds=5)
    schedule=[{k:r[k] for k in ('sampleId','caseId','profileFingerprint','repetition')} for r in (a,b)]
    report=summarize(schedule,[a,b],identity=benchmark_identity(),origin='fixture',recovery=[])
    assert report['profiles']['a'*64]['latency']['medianSeconds']==0.5
    assert report['profiles']['b'*64]['latency']['medianSeconds']==5
    report=summarize(schedule,[unknown_result(schedule[0])],identity=benchmark_identity(),origin='fixture',recovery=[])
    assert report['latency']['observations']==0 and report['latency']['medianSeconds'] is None
